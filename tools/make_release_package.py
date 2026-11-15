#!/usr/bin/env python3
# =============================================================================
# URTC-UPDATER - tools/make_release_package.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Builds the unsigned update packages of this program, one for each system, the way its own updater looks for them.

    python tools/make_release_package.py build  --out out/      # the four packages and SHA256SUMS
    python tools/make_release_package.py reproduce              # two builds give the same bytes
    python tools/make_release_package.py check  out/            # the names, the contents and a start of the program

The updater of a release (``urtc-updater --cli package``, and the window of packages) looks for
``urtc-updater-<version>-<system>-<arch>.zip`` (Windows) or ``.tar.gz`` (Linux and macOS) with ``<package>.sha256`` and
``<package>.sig`` next to it. This tool makes the package; the two companions are made later, on the maintainer's computer,
from the very bytes it wrote (``tools/make_update_package.py sign``), because no key is ever held in Actions.

The package holds the source of the program (``src/urtc_updater``), the licence, the readme and a small start file
(``run_urtc_updater.py``) that ``app_info.json`` names as its entry. It needs a Python 3.10 or newer on the computer, like
the checkout does; the command line is the standard library only and the window needs PySide6.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform as host
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import make_update_package as mup  # noqa: E402

APP = "urtc-updater"
ENTRY = "run_urtc_updater.py"
PLATFORMS = ("windows-x64", "linux-x64", "linux-arm64", "macos-arm64")
EXTRA_FILES = ("LICENSE", "NOTICE", "README.md", "urtc.project.json")
START_FILE = '''"""Starts URTC-UPDATER from the folder of this release (python run_urtc_updater.py [--cli ...])."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from urtc_updater.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
'''


def version_of(root: Path = ROOT) -> str:
    return str(json.loads((root / "urtc.project.json").read_text(encoding="utf-8"))["version"])


def stage(root: Path, destination: Path) -> None:
    """The files that go into the package, in a new folder: the program, the licence and readme, and the start file."""
    program = root / "src" / "urtc_updater"
    for relative in mup.collect(program):
        if relative.suffix in {".pyc", ".pyo"}:
            continue
        target = destination / "src" / "urtc_updater" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(program / relative, target)
    for name in EXTRA_FILES:
        if (root / name).is_file():
            shutil.copyfile(root / name, destination / name)
    start = destination / ENTRY
    start.write_text(START_FILE, encoding="utf-8", newline="\n")
    start.chmod(0o755)


def package_names(version: str) -> list[str]:
    return [mup.su.package_name(APP, version, platform) for platform in PLATFORMS]


def build(root: Path, out: Path) -> list[Path]:
    """The four packages of the version of ``root``, written to ``out``; the same bytes on every run."""
    version = version_of(root)
    mup.su.parse_version(version)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    with tempfile.TemporaryDirectory() as scratch:
        source = Path(scratch) / "program"
        source.mkdir()
        stage(root, source)
        files = mup.collect(source)
        for platform in PLATFORMS:
            info = {"name": APP, "version": version, "platform": platform, "entry": ENTRY}
            path = out / mup.su.package_name(APP, version, platform)
            data = mup.build_archive(source, files, info, platform)
            if not platform.startswith("windows"):
                data = data[:4] + bytes(4) + data[8:]   # the gzip header holds the time of the build: zero it so the bytes repeat
            path.write_bytes(data)
            written.append(path)
    return written


def write_sums(out: Path, version: str) -> None:
    lines = [f"{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}" for name in package_names(version)]
    (out / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def reproduce(root: Path) -> list[str]:
    """Builds twice in two folders; returns the names whose bytes differ (empty when the build is reproducible)."""
    with tempfile.TemporaryDirectory() as scratch:
        first = {p.name: p.read_bytes() for p in build(root, Path(scratch) / "a")}
        second = {p.name: p.read_bytes() for p in build(root, Path(scratch) / "b")}
    return sorted(name for name in first if first[name] != second.get(name))


def check(out: Path, expected_version: str, smoke: bool = True) -> list[str]:
    """Returns the problems found in a folder of packages (empty = good): the names the updater looks for, the content of each
    package and, for the one of this system, a start of the program."""
    problems = []
    for name in package_names(expected_version):
        package = out / name
        if not package.is_file():
            problems.append(f"missing {name}")
            continue
        app, version, platform = mup.split_name(name)
        try:
            info = mup.read_app_info(package)
        except (OSError, KeyError, ValueError, mup.zipfile.BadZipFile, mup.tarfile.TarError) as error:
            problems.append(f"{name}: unreadable app_info.json ({error})")
            continue
        if (info.get("name"), info.get("version"), info.get("platform"), info.get("entry")) != (app, version, platform, ENTRY):
            problems.append(f"{name}: app_info.json says {info}")
        if name.endswith(".zip") != platform.startswith("windows"):
            problems.append(f"{name}: wrong archive kind for {platform}")
        with tempfile.TemporaryDirectory() as scratch:
            try:
                count = mup.su.safe_extract(package, scratch)
            except mup.su.UpdateError as error:
                problems.append(f"{name}: does not extract safely ({error.code})")
                continue
            for must in (ENTRY, "app_info.json", "src/urtc_updater/main.py", "src/urtc_updater/urtc_pkg/self_update.py", "LICENSE"):
                if not (Path(scratch) / must).is_file():
                    problems.append(f"{name}: lacks {must}")
            if any("__pycache__" in path.relative_to(scratch).parts for path in Path(scratch).rglob("*")):
                problems.append(f"{name}: carries compiled files")
            if smoke and platform == mup.su.platform_tag(host.system(), host.machine()):
                result = subprocess.run([sys.executable, "-I", str(Path(scratch) / ENTRY), "--cli", "--version"], capture_output=True, text=True, cwd=scratch, timeout=120, check=False)
                if result.stdout.strip() != f"urtc-updater {expected_version}":
                    problems.append(f"{name}: the program says {result.stdout.strip()!r} {result.stderr.strip()[:200]!r}, not urtc-updater {expected_version}")
            if count < 20:
                problems.append(f"{name}: only {count} files")
    extra = sorted(p.name for p in out.iterdir() if p.is_file() and p.name not in package_names(expected_version) and p.name not in {"SHA256SUMS", "build-manifest.json"})
    if extra:
        problems.append("unexpected files: " + ", ".join(extra))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    build_p = sub.add_parser("build")
    build_p.add_argument("--out", required=True)
    sub.add_parser("reproduce")
    check_p = sub.add_parser("check")
    check_p.add_argument("out")
    check_p.add_argument("--no-smoke", action="store_true")
    args = parser.parse_args(argv)
    version = version_of()
    if args.command == "build":
        out = Path(args.out)
        for path in build(ROOT, out):
            print(f"{path.name} {path.stat().st_size} bytes")
        write_sums(out, version)
        return 0
    if args.command == "reproduce":
        differ = reproduce(ROOT)
        print("REPRODUCE=FAIL " + ", ".join(differ) if differ else "REPRODUCE=PASS two builds give the same bytes")
        return 1 if differ else 0
    problems = check(Path(args.out), version, smoke=not args.no_smoke)
    for problem in problems:
        print("PACKAGE_CHECK problem:", problem, file=sys.stderr)
    print("PACKAGE_CHECK=FAIL" if problems else f"PACKAGE_CHECK=PASS {len(package_names(version))} packages for {version}")
    return 1 if problems else 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    raise SystemExit(main())
