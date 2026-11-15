# =============================================================================
# URTC-UPDATER - tests/test_release_package.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The packages of a release carry the names and the contents that the updater looks for, and the workflow that builds them signs nothing."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import make_release_package as tool  # noqa: E402

from urtc_updater import package  # noqa: E402
from urtc_updater.urtc_pkg import self_update as su  # noqa: E402

SEED = bytes(range(32))
WORKFLOW = ROOT / ".github" / "workflows" / "package-build.yml"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("packages")
    tool.build(ROOT, out)
    tool.write_sums(out, tool.version_of())
    return out


def test_the_names_are_the_ones_the_updater_looks_for():
    version = tool.version_of()
    for platform in tool.PLATFORMS:
        assert su.package_name(tool.APP, version, platform) in tool.package_names(version)
    assert tool.APP in package.KNOWN_APPS
    assert tool.package_names("0.3.1") == [
        "urtc-updater-0.3.1-windows-x64.zip",
        "urtc-updater-0.3.1-linux-x64.tar.gz",
        "urtc-updater-0.3.1-linux-arm64.tar.gz",
        "urtc-updater-0.3.1-macos-arm64.tar.gz",
    ]


def test_every_name_has_the_shape_the_release_check_and_the_updater_expect():
    for name in tool.package_names("0.3.1"):
        assert re.fullmatch(r"urtc-updater-\d+\.\d+\.\d+-(windows|linux|macos)-(x64|arm64)\.(zip|tar\.gz)", name)
        assert tool.mup.split_name(name) == ("urtc-updater", "0.3.1", name.split("-", 3)[3].rsplit(".", 1)[0].removesuffix(".tar"))


def test_the_four_packages_exist_with_the_right_kind_of_archive(built):
    assert sorted(p.name for p in built.glob("urtc-updater-*")) == sorted(tool.package_names(tool.version_of()))
    assert zipfile.is_zipfile(built / f"urtc-updater-{tool.version_of()}-windows-x64.zip")
    for platform in ("linux-x64", "linux-arm64", "macos-arm64"):
        assert tarfile.is_tarfile(built / f"urtc-updater-{tool.version_of()}-{platform}.tar.gz")


def test_each_package_says_what_it_is_and_holds_the_program(built):
    version = tool.version_of()
    for platform in tool.PLATFORMS:
        file = built / su.package_name(tool.APP, version, platform)
        info = tool.mup.read_app_info(file)
        assert info == {"name": "urtc-updater", "version": version, "platform": platform, "entry": "run_urtc_updater.py"}
        names = zipfile.ZipFile(file).namelist() if file.suffix == ".zip" else tarfile.open(file, "r:gz").getnames()
        for must in ("run_urtc_updater.py", "src/urtc_updater/main.py", "src/urtc_updater/urtc_pkg/self_update.py", "LICENSE", "app_info.json"):
            assert must in names, (file.name, must)
        assert not [n for n in names if "__pycache__" in n or n.endswith(".pyc")]


def test_the_check_of_the_tool_passes_on_the_real_packages_and_starts_the_program(built):
    assert tool.check(built, tool.version_of()) == []


def test_the_check_finds_a_missing_package_a_wrong_version_and_a_stranger(built, tmp_path):
    for p in built.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())
    next(tmp_path.glob("*linux-arm64*")).unlink()
    (tmp_path / "notes.txt").write_text("x", encoding="ascii")
    problems = tool.check(tmp_path, tool.version_of(), smoke=False)
    assert any(p.startswith("missing urtc-updater-") and "linux-arm64" in p for p in problems)
    assert any("unexpected files: notes.txt" in p for p in problems)
    assert any("missing" in p for p in tool.check(tmp_path, "9.9.9", smoke=False))


def test_two_builds_give_the_same_bytes():
    assert tool.reproduce(ROOT) == []


def test_the_sums_file_matches_the_packages(built):
    lines = (built / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    assert [line.split("  ")[1] for line in lines] == tool.package_names(tool.version_of())
    for line in lines:
        digest, name = line.split("  ")
        assert hashlib.sha256((built / name).read_bytes()).hexdigest() == digest


def test_a_package_signed_with_a_test_key_is_accepted_by_the_verifier_of_the_program(built, tmp_path):
    version = tool.version_of()
    name = su.package_name(tool.APP, version, "windows-x64")
    copy = tmp_path / name
    copy.write_bytes((built / name).read_bytes())
    assert tool.mup.sign_existing(copy, SEED) == hashlib.sha256(tool.mup.public_key_of(SEED)).hexdigest()[:16]
    sha = copy.with_name(name + ".sha256").read_text(encoding="ascii").split()[0]
    assert sha == hashlib.sha256(copy.read_bytes()).hexdigest()
    signature = bytes.fromhex(copy.with_name(name + ".sig").read_text(encoding="ascii").strip())
    message = su.package_message(tool.APP, version, "windows-x64", sha, copy.stat().st_size)
    assert su.ed25519_verify(tool.mup.public_key_of(SEED), message, signature)


def test_the_updater_finds_the_package_of_a_release_that_carries_the_three_files():
    release = {"tag_name": "v9.0.0", "assets": []}
    for platform in tool.PLATFORMS:
        name = su.package_name(tool.APP, "9.0.0", platform)
        release["assets"] = [{"name": n, "size": 10, "browser_download_url": f"https://github.com/JuanenRac/URTC-UPDATER/releases/download/v9.0.0/{n}"} for n in (name, name + ".sha256", name + ".sig")]
        offer = su.find_update(release, tool.APP, "0.3.0", platform)
        assert offer is not None and offer.package.name == name


def test_the_tool_trusts_the_key_the_program_trusts():
    assert tool.mup.svc.RELEASE_PUBLIC_KEY_HEX == "4020c46d76c8ebacb64c5c7b9f3e7c62475afeb133d7421591988174e0f5dc90"


def test_the_workflow_is_manual_holds_no_key_and_attests_the_artifact():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"^on:\n  workflow_dispatch:\n", text, re.M)
    assert not re.search(r"^  (push|pull_request|schedule):", text, re.M)
    for name in ("dry_run:", "ref:", "attest-build-provenance", "make_release_package.py reproduce", "make_release_package.py build", "make_release_package.py check"):
        assert name in text
    assert "secrets." not in text
    assert "URTC_RELEASE_KEY" in text and "nothing is signed here" in text
    assert "package-urtc-updater-${{ needs.plan.outputs.version }}" in text


def test_the_workflow_builds_the_names_the_tool_makes():
    text = WORKFLOW.read_text(encoding="utf-8")
    for platform in tool.PLATFORMS:
        assert f"-{platform}." in text
    manifest = json.loads(json.dumps({"platforms": list(tool.PLATFORMS)}))
    assert all(platform in text for platform in manifest["platforms"])
