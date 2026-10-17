# =============================================================================
# URTC-UPDATER - tests/test_workspace_safety.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Workspace hygiene, locking, carry-over rules, evidence fields and the
smaller robustness rules of the update flow."""
from __future__ import annotations

import builtins
import email.message
import json
import os
import subprocess
import sys
import textwrap
import urllib.error
from pathlib import Path

import pytest

from urtc_updater import github_client, install, settings
from urtc_updater import main as main_module
from urtc_updater.detect import discover_workspace, is_updater_leftover
from urtc_updater.evidence import read_attempts, record_attempt
from urtc_updater.install import (
    _carry_over_local_data,
    install_or_update,
    is_running_checkout,
    workspace_lock,
)
from urtc_updater.registry import ProjectEntry, github_raw_url


def _entry(name: str = "URTC-EXAMPLE") -> ProjectEntry:
    return ProjectEntry(name, "python", "pyproject.toml", r"(\d+)\.(\d+)\.(\d+)")


def _manifest(name: str) -> str:
    return json.dumps({
        "schema_version": "1.0", "ecosystem": "URTC", "name": name, "version": "1.0.0",
        "role": "service", "stack": "python", "technologies": ["Python"],
        "deployment_target": "cm5", "maturity": "functional", "family": "Test", "parent": None,
        "native_version": {"file": "pyproject.toml", "pattern": "(\\d+)\\.(\\d+)\\.(\\d+)"},
        "build": "python -m compileall src", "notes": "Test manifest.",
    })


# --- discovery ignores what the updater itself leaves behind -----------------

def test_discovery_ignores_kept_backups_and_hidden_staging_folders(tmp_path: Path):
    for folder in ("URTC-EXAMPLE", "URTC-EXAMPLE.backup-1a2b3c4d", ".URTC-EXAMPLE.update-abc", ".URTC-EXAMPLE.clone-abc"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "urtc.project.json").write_text(_manifest("URTC-EXAMPLE"), encoding="utf-8")
    discovery = discover_workspace(tmp_path)
    assert [p.entry.name for p in discovery.projects] == ["URTC-EXAMPLE"]
    assert discovery.errors == ()


def test_leftover_name_rules():
    assert is_updater_leftover(".URTC-X.update-1")
    assert is_updater_leftover("URTC-X.backup-0123abcd")
    assert not is_updater_leftover("URTC-X")
    assert not is_updater_leftover("URTC-X.backup")


# --- instance lock -----------------------------------------------------------

# Looked up on the module at call time: other tests reload it, which
# creates a new exception class.
def test_second_holder_of_the_workspace_lock_is_refused_until_release(tmp_path: Path):
    with workspace_lock(tmp_path):
        with pytest.raises(install.InstallError, match="another URTC-UPDATER instance"):
            with workspace_lock(tmp_path):
                pass
    with workspace_lock(tmp_path):
        pass


def test_lock_is_held_across_processes(tmp_path: Path):
    code = textwrap.dedent(
        """
        import sys
        from pathlib import Path
        from urtc_updater.install import InstallError, workspace_lock
        try:
            with workspace_lock(Path(sys.argv[1])):
                print("acquired")
        except InstallError:
            print("busy")
        """
    )
    src = str(Path(install.__file__).resolve().parents[1])
    env = {**os.environ, "PYTHONPATH": src}
    with workspace_lock(tmp_path):
        busy = subprocess.run([sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, env=env)
    assert busy.stdout.strip() == "busy", busy.stderr
    free = subprocess.run([sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, env=env)
    assert free.stdout.strip() == "acquired", free.stderr


def test_install_or_update_reports_a_busy_workspace_as_a_result(tmp_path: Path):
    with workspace_lock(tmp_path):
        results = install_or_update(_entry(), tmp_path)
    assert len(results) == 1 and not results[0].ok
    assert "another URTC-UPDATER instance" in results[0].message


# --- the running program never replaces itself -------------------------------

def test_the_running_checkout_is_detected_and_refused(tmp_path: Path, monkeypatch):
    package_root = Path(install.__file__).resolve().parents[2]
    assert is_running_checkout(package_root)
    assert not is_running_checkout(tmp_path / "somewhere-else")
    monkeypatch.setattr(install, "is_running_checkout", lambda _path: True)
    results = install_or_update(_entry(), tmp_path)
    assert not results[0].ok and "cannot replace itself" in results[0].message


# --- carry-over of local data ------------------------------------------------

def test_nested_build_directories_are_not_carried_over(tmp_path: Path, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    for base in (old, new):
        base.mkdir()
    (old / "tools" / "node_modules").mkdir(parents=True)
    (old / "tools" / "node_modules" / "x.js").write_text("x", encoding="utf-8")
    (old / "app" / "src" / "__pycache__").mkdir(parents=True)
    (old / "app" / "src" / "__pycache__" / "m.pyc").write_text("x", encoding="utf-8")
    (old / "data").mkdir()
    (old / "data" / "settings.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        install, "_real_untracked_paths",
        lambda _p: ["tools/node_modules/", "app/src/__pycache__/", "data/"],
    )
    _carry_over_local_data(old, new)
    assert (new / "data" / "settings.json").is_file()
    assert not (new / "tools").exists()
    assert not (new / "app").exists()


# --- evidence ----------------------------------------------------------------

def test_evidence_lines_carry_time_version_host_and_user(tmp_path: Path):
    record_attempt(tmp_path, project="URTC-EXAMPLE", before={}, after={}, ok=True, message="done")
    line = read_attempts(tmp_path)[0]
    assert line["timestamp"].endswith("+00:00")
    assert line["updaterVersion"]
    assert {"host", "user"} <= set(line)


# --- settings are written atomically ----------------------------------------

def test_saving_settings_swaps_a_complete_file_in(tmp_path: Path, monkeypatch):
    target = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", target)
    settings.save_settings(lang="es")
    settings.save_settings(workspace_root="x")
    assert json.loads(target.read_text(encoding="utf-8")) == {"lang": "es", "workspace_root": "x"}
    assert not list(tmp_path.glob("*.tmp"))


# --- retry limits and branches ----------------------------------------------

def _http_error(code: int, headers: dict[str, str]) -> urllib.error.HTTPError:
    message = email.message.Message()
    for key, value in headers.items():
        message[key] = value
    return urllib.error.HTTPError("https://example.invalid", code, "x", message, None)


def test_a_very_long_retry_after_is_not_waited_out():
    assert github_client._retry_after_seconds(_http_error(429, {"Retry-After": "3600"})) is None
    assert github_client._retry_after_seconds(_http_error(429, {"Retry-After": "5"})) == 5.0


def test_raw_urls_use_the_repository_default_branch():
    entry = ProjectEntry("URTC-EXAMPLE", "python", "pyproject.toml", "", default_branch="master")
    assert "/URTC-EXAMPLE/master/" in github_raw_url(entry)
    assert "/URTC-EXAMPLE/dev/" in github_raw_url(entry, branch="dev")


# --- entry point -------------------------------------------------------------

def test_default_workspace_is_never_inside_a_python_installation(tmp_path: Path, monkeypatch):
    fake = tmp_path / "site-packages" / "urtc_updater" / "main.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("", encoding="utf-8")
    monkeypatch.setattr(main_module, "__file__", str(fake))
    monkeypatch.chdir(tmp_path)
    assert main_module.default_workspace_root() == Path.cwd()


def test_without_any_gui_the_exit_code_is_not_success(monkeypatch):
    real_import = builtins.__import__

    def refuse(name, globals=None, locals=None, fromlist=(), level=0):
        if fromlist and ("launch_qt_gui" in fromlist or "launch_gui" in fromlist):
            raise ImportError(name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(sys, "argv", ["urtc-updater"])
    monkeypatch.setattr(builtins, "__import__", refuse)
    assert main_module.main() == 2
