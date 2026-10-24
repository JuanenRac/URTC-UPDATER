# =============================================================================
# URTC-UPDATER - tests/test_wheel.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The program as an installable wheel: the command, the windows' files and the translations are inside it, and a program installed
from it does not take the folder of the Python installation for a workspace."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(importlib.util.find_spec("setuptools") is None, reason="setuptools is not installed here")


@pytest.fixture(scope="module")
def wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("wheel")
    work = tmp_path_factory.mktemp("source")
    # a copy of the sources, so building leaves no build/ or egg-info folder in the checkout
    for name in ("pyproject.toml", "README.md", "LICENSE"):
        (work / name).write_bytes((ROOT / name).read_bytes())
    (work / "src").mkdir()
    import shutil

    shutil.copytree(ROOT / "src" / "urtc_updater", work / "src" / "urtc_updater", ignore=shutil.ignore_patterns("__pycache__"))
    done = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--quiet", "-w", str(out), str(work)],
        capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL,
    )
    if done.returncode != 0:
        pytest.skip(f"a wheel cannot be built here: {done.stderr.strip()[-300:]}")
    (built,) = out.glob("urtc_updater-*.whl")
    return built


def test_the_wheel_carries_the_command_the_windows_and_the_texts(wheel: Path):
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        entry = next(n for n in names if n.endswith("entry_points.txt"))
        metadata = next(n for n in names if n.endswith("METADATA"))
        assert "urtc-updater = urtc_updater.main:main" in archive.read(entry).decode("utf-8")
        assert "Requires-Python: >=3.10" in archive.read(metadata).decode("utf-8")
    assert "urtc_updater/qml/Main.qml" in names
    assert any(n.startswith("urtc_updater/assets/") for n in names)
    assert {"urtc_updater/translations_data.py", "urtc_updater/install.py", "urtc_updater/main.py"} <= names


def test_a_program_installed_from_the_wheel_works_in_the_current_folder(wheel: Path, tmp_path: Path):
    target = tmp_path / "site"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(target)
    workspace = tmp_path / "work"
    workspace.mkdir()
    code = "from urtc_updater.main import default_workspace_root; print(default_workspace_root())"
    done = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, {str(target)!r}); {code}"],
        capture_output=True, text=True, check=False, cwd=workspace, stdin=subprocess.DEVNULL,
    )
    assert done.returncode == 0, done.stderr
    assert Path(done.stdout.strip()).resolve() == workspace.resolve()
