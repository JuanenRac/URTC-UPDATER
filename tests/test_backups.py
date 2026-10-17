# =============================================================================
# URTC-UPDATER - tests/test_backups.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Retention of kept previous installations, the clean-backups command,
restoring one, and the preview of an update."""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pytest
from repo_helpers import NAME, entry, git, make_remote, manifest_text

from urtc_updater import install, settings
from urtc_updater import main as main_module
from urtc_updater.install import (
    InstallResult,
    backups_to_keep,
    clean_workspace,
    install_or_update,
    list_backups,
    preview_update,
    prune_backups,
    restore_backup,
    workspace_lock,
)


def _backup(workspace: Path, suffix: str, age_s: int, version: str = "1.0.0", name: str = NAME) -> Path:
    folder = workspace / f"{name}.backup-{suffix}"
    folder.mkdir()
    (folder / "urtc.project.json").write_text(manifest_text(version, name), encoding="utf-8")
    (folder / "marker.txt").write_text(suffix, encoding="utf-8")
    stamp = time.time() - age_s
    os.utime(folder, (stamp, stamp))
    return folder


# --- listing and retention ---------------------------------------------------

def test_backups_are_listed_per_project_newest_first(tmp_path: Path):
    old = _backup(tmp_path, "00000001", 300)
    new = _backup(tmp_path, "00000002", 10)
    other = _backup(tmp_path, "00000003", 50, name="URTC-OTHER")
    (tmp_path / "URTC-EXAMPLE.backup").mkdir()  # not one of ours
    (tmp_path / "notes.backup-1a2b3c4d").write_text("a file", encoding="utf-8")
    found = list_backups(tmp_path)
    assert found == {NAME: [new, old], "URTC-OTHER": [other]}
    assert list_backups(tmp_path, NAME) == {NAME: [new, old]}
    assert list_backups(tmp_path / "absent") == {}


def test_pruning_keeps_the_newest_n_of_each_project(tmp_path: Path):
    folders = [_backup(tmp_path, f"0000000{i}", 100 - i * 10) for i in range(1, 5)]  # 1 oldest ... 4 newest
    other = _backup(tmp_path, "0000000a", 999, name="URTC-OTHER")
    removed = prune_backups(tmp_path, keep=2)
    assert sorted(removed) == sorted(folders[:2])
    assert [p.exists() for p in folders] == [False, False, True, True]
    assert other.exists()  # one backup is within the limit


def test_pruning_one_project_leaves_the_others_alone(tmp_path: Path):
    mine = [_backup(tmp_path, f"0000000{i}", 100 - i) for i in range(1, 4)]
    other = [_backup(tmp_path, f"000000a{i}", 100 - i, name="URTC-OTHER") for i in range(1, 4)]
    prune_backups(tmp_path, keep=1, name=NAME)
    assert [p.exists() for p in mine] == [False, False, True]
    assert all(p.exists() for p in other)


def test_a_dry_run_removes_nothing(tmp_path: Path):
    folders = [_backup(tmp_path, f"0000000{i}", 100 - i) for i in range(1, 4)]
    would = prune_backups(tmp_path, keep=1, dry_run=True)
    assert len(would) == 2 and all(p.exists() for p in folders)


def test_the_retention_setting_is_read_and_validated(tmp_path: Path):
    assert backups_to_keep() == install.DEFAULT_BACKUPS_TO_KEEP
    settings.save_settings(backups_to_keep=5)
    assert backups_to_keep() == 5
    settings.save_settings(backups_to_keep=0)
    assert backups_to_keep() == 0
    for bad in (-1, "3", True, 2.5, None):
        settings.save_settings(backups_to_keep=bad)
        assert backups_to_keep() == install.DEFAULT_BACKUPS_TO_KEEP


def test_a_successful_update_prunes_old_backups_of_that_project_only(tmp_path: Path, monkeypatch):
    project = tmp_path / NAME
    (project / ".git").mkdir(parents=True)
    kept_other = _backup(tmp_path, "000000a1", 500, name="URTC-OTHER")
    made = [_backup(tmp_path, f"0000000{i}", 100 - i * 10) for i in range(1, 5)]
    monkeypatch.setattr(install, "clone_or_pull", lambda *a, **k: InstallResult(True, "ok"))
    monkeypatch.setattr(install, "recover_interrupted_promotions", lambda root: [])
    results = install_or_update(entry(), tmp_path, build=False)
    assert all(r.ok for r in results)
    assert [p.exists() for p in made] == [False, False, True, True]
    assert kept_other.exists()


def test_a_failed_update_prunes_nothing(tmp_path: Path, monkeypatch):
    project = tmp_path / NAME
    (project / ".git").mkdir(parents=True)
    made = [_backup(tmp_path, f"0000000{i}", 100 - i * 10) for i in range(1, 5)]
    monkeypatch.setattr(install, "clone_or_pull", lambda *a, **k: InstallResult(False, "nope"))
    monkeypatch.setattr(install, "recover_interrupted_promotions", lambda root: [])
    install_or_update(entry(), tmp_path, build=False)
    assert all(p.exists() for p in made)


def test_real_updates_leave_at_most_the_configured_number_of_backups(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    settings.save_settings(backups_to_keep=1)
    for number in range(2, 5):
        remote.push(f"1.{number}.0", f"v{number}")
        (result,) = install_or_update(entry(), remote.workspace)
        assert result.ok, result.message
    assert len(list_backups(remote.workspace, NAME)[NAME]) == 1
    # and the one kept is the most recent: it holds the previous release
    (kept,) = list_backups(remote.workspace, NAME)[NAME]
    assert '"1.3.0"' in (kept / "urtc.project.json").read_text(encoding="utf-8")


# --- the clean-backups command ----------------------------------------------

def test_clean_workspace_removes_backups_and_orphan_staging(tmp_path: Path):
    old = _backup(tmp_path, "00000001", 300)
    new = _backup(tmp_path, "00000002", 10)
    staging_update = tmp_path / f".{NAME}.update-{'a' * 32}"
    staging_clone = tmp_path / f".{NAME}.clone-{'b' * 32}"
    for folder in (staging_update, staging_clone):
        folder.mkdir()
        (folder / "file").write_text("x", encoding="utf-8")
    unrelated_hidden = tmp_path / ".cache"
    unrelated_hidden.mkdir()
    report = clean_workspace(tmp_path, keep=1)
    assert report.backups == [old]
    assert sorted(report.staging) == sorted([staging_update, staging_clone])
    assert not old.exists() and new.exists()
    assert not staging_update.exists() and not staging_clone.exists()
    assert unrelated_hidden.exists()


def test_clean_workspace_dry_run_only_lists(tmp_path: Path):
    folder = _backup(tmp_path, "00000001", 10)
    staging = tmp_path / f".{NAME}.update-{'a' * 32}"
    staging.mkdir()
    report = clean_workspace(tmp_path, keep=0, dry_run=True)
    assert report.backups == [folder] and report.staging == [staging]
    assert folder.exists() and staging.exists()


def test_clean_workspace_refuses_while_an_install_holds_the_lock(tmp_path: Path):
    folder = _backup(tmp_path, "00000001", 10)
    with workspace_lock(tmp_path):
        with pytest.raises(install.InstallError, match="another URTC-UPDATER instance"):
            clean_workspace(tmp_path, keep=0)
    assert folder.exists()


def _clean_args(workspace: Path, **overrides) -> argparse.Namespace:
    values = {"workspace": str(workspace), "keep": 0, "dry_run": False}
    values.update(overrides)
    return argparse.Namespace(**values)


def test_the_clean_backups_command_reports_what_it_removed(tmp_path: Path, capsys):
    _backup(tmp_path, "00000001", 300)
    _backup(tmp_path, "00000002", 10)
    assert main_module.cmd_clean_backups(_clean_args(tmp_path, keep=1)) == 0
    output = capsys.readouterr().out
    assert "Removed 1 previous installation(s) and 0 leftover staging folder(s); kept the newest 1 per project." in output
    assert len(list_backups(tmp_path)[NAME]) == 1


def test_the_clean_backups_command_fails_cleanly_when_busy(tmp_path: Path, capsys):
    with workspace_lock(tmp_path):
        assert main_module.cmd_clean_backups(_clean_args(tmp_path)) == 1
    assert "another URTC-UPDATER instance" in capsys.readouterr().err


def test_the_parser_knows_the_new_commands():
    parser = main_module.build_parser()
    assert parser.parse_args(["clean-backups", "--keep", "3", "--dry-run"]).keep == 3
    assert parser.parse_args(["restore-backup", "URTC-X", "--list"]).list is True
    assert parser.parse_args(["update", "URTC-X", "--preview"]).preview is True
    assert parser.parse_args(["check", "--notify", "--quiet"]).notify is True
    assert parser.parse_args(["evidence", "--export", "out.json"]).export == "out.json"


# --- restoring a kept installation ------------------------------------------

def test_restore_swaps_in_the_backup_and_keeps_what_was_there(tmp_path: Path):
    current = tmp_path / NAME
    current.mkdir()
    (current / "urtc.project.json").write_text(manifest_text("2.0.0"), encoding="utf-8")
    (current / "marker.txt").write_text("current", encoding="utf-8")
    backup = _backup(tmp_path, "00000001", 10, version="1.0.0")
    result = restore_backup(NAME, tmp_path)
    assert result.ok, result.message
    assert (tmp_path / NAME / "marker.txt").read_text(encoding="utf-8") == "00000001"
    assert "v1.0.0" in result.message
    assert not backup.exists()
    # what was in place is still there, as a backup, so the swap can be undone
    (kept,) = list_backups(tmp_path, NAME)[NAME]
    assert (kept / "marker.txt").read_text(encoding="utf-8") == "current"
    again = restore_backup(NAME, tmp_path)
    assert again.ok and (tmp_path / NAME / "marker.txt").read_text(encoding="utf-8") == "current"


def test_restore_picks_the_newest_or_the_named_backup(tmp_path: Path):
    _backup(tmp_path, "00000001", 300, version="1.0.0")
    newest = _backup(tmp_path, "00000002", 10, version="1.5.0")
    older = tmp_path / f"{NAME}.backup-00000001"
    assert "v1.5.0" in restore_backup(NAME, tmp_path).message
    assert not newest.exists() and older.exists()
    named = restore_backup(NAME, tmp_path, backup=older.name)
    assert named.ok and "v1.0.0" in named.message


def test_restore_with_nothing_kept_or_a_wrong_name_changes_nothing(tmp_path: Path):
    result = restore_backup(NAME, tmp_path)
    assert not result.ok and "no kept previous installation" in result.message
    _backup(tmp_path, "00000001", 10)
    missing = restore_backup(NAME, tmp_path, backup=f"{NAME}.backup-ffffffff")
    assert not missing.ok and (tmp_path / f"{NAME}.backup-00000001").exists()
    assert not (tmp_path / NAME).exists()


def test_restore_refuses_a_backup_whose_manifest_is_not_this_project(tmp_path: Path):
    folder = _backup(tmp_path, "00000001", 10)
    (folder / "urtc.project.json").write_text(manifest_text("1.0.0", "URTC-SOMETHING-ELSE"), encoding="utf-8")
    result = restore_backup(NAME, tmp_path)
    assert not result.ok and "not a usable installation" in result.message
    assert folder.exists() and not (tmp_path / NAME).exists()


def test_restore_puts_the_original_back_when_the_second_rename_fails(tmp_path: Path, monkeypatch):
    current = tmp_path / NAME
    current.mkdir()
    (current / "marker.txt").write_text("current", encoding="utf-8")
    backup = _backup(tmp_path, "00000001", 10)
    real_rename = Path.rename

    def flaky(self: Path, target):
        if self == backup:
            raise PermissionError("locked")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", flaky)
    result = restore_backup(NAME, tmp_path)
    assert not result.ok and "was left as it was" in result.message
    assert (tmp_path / NAME / "marker.txt").read_text(encoding="utf-8") == "current"
    assert backup.exists()


def test_restore_refuses_to_replace_the_running_program(tmp_path: Path, monkeypatch):
    _backup(tmp_path, "00000001", 10)
    monkeypatch.setattr(install, "is_running_checkout", lambda _path: True)
    result = restore_backup(NAME, tmp_path)
    assert not result.ok and "cannot replace itself" in result.message


def test_restore_leaves_evidence(tmp_path: Path):
    from urtc_updater.evidence import read_attempts

    _backup(tmp_path, "00000001", 10)
    assert restore_backup(NAME, tmp_path).ok
    (line,) = read_attempts(tmp_path)
    assert line["project"] == NAME and line["ok"] is True and "Restored" in line["message"]


def test_the_restore_command_lists_and_restores(tmp_path: Path, capsys):
    folder = _backup(tmp_path, "00000001", 10)
    listing = argparse.Namespace(workspace=str(tmp_path), project=NAME, backup=None, list=True)
    assert main_module.cmd_restore_backup(listing) == 0
    assert capsys.readouterr().out.split() == [folder.name]
    restoring = argparse.Namespace(workspace=str(tmp_path), project=NAME, backup=None, list=False)
    assert main_module.cmd_restore_backup(restoring) == 0
    assert capsys.readouterr().out.startswith("OK  Restored")
    assert main_module.cmd_restore_backup(restoring) == 1  # nothing left to restore


# --- previewing an update ----------------------------------------------------

def test_preview_describes_the_candidate_without_changing_the_checkout(tmp_path: Path):
    remote = make_remote(tmp_path)
    before = git("rev-parse", "HEAD", cwd=remote.checkout)
    sha = remote.push(
        "1.1.0", "change what runs",
        {"build-test.sh": "#!/bin/sh\necho changed\n", "tools/extra.py": "print(1)\n", "docs/readme.txt": "doc\n"},
    )
    preview = preview_update(entry(), remote.workspace)
    assert preview.commit == sha
    assert preview.author == "Contract <contract@example.invalid>"
    assert (preview.installed_version, preview.version) == ("1.0.0", "1.1.0")
    assert preview.signature == "not required"
    assert sorted(preview.changed_scripts) == ["build-test.sh", "tools/extra.py"]
    assert "tools/extra.py" in preview.diffstat
    assert git("rev-parse", "HEAD", cwd=remote.checkout) == before
    assert git("status", "--porcelain", cwd=remote.checkout) == ""


def test_preview_reports_no_script_changes_when_only_docs_changed(tmp_path: Path):
    remote = make_remote(tmp_path)
    remote.push("1.0.0", "docs only", {"docs/readme.txt": "doc\n"})
    preview = preview_update(entry(), remote.workspace)
    assert preview.changed_scripts == []


def test_preview_shows_the_signature_state_under_a_policy(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    remote.push("1.0.0", "unsigned", {"x.txt": "x\n"})
    monkeypatch.setenv("URTC_UPDATER_REQUIRE_SIGNED", "1")
    preview = preview_update(entry(), remote.workspace)
    assert "not signed by a trusted key" in preview.signature


def test_preview_of_a_missing_checkout_or_remote_is_an_error(tmp_path: Path):
    with pytest.raises(install.InstallError, match="isn't a git checkout"):
        preview_update(entry(), tmp_path)
    (tmp_path / "r").mkdir()
    remote = make_remote(tmp_path / "r")
    git("remote", "set-url", "origin", str(tmp_path / "gone.git"), cwd=remote.checkout)
    with pytest.raises(install.InstallError, match="git fetch failed"):
        preview_update(entry(), remote.workspace)


def test_the_update_command_with_preview_prints_and_changes_nothing(tmp_path: Path, capsys):
    remote = make_remote(tmp_path)
    before = git("rev-parse", "HEAD", cwd=remote.checkout)
    remote.push("1.1.0", "new", {"build-test.sh": "#!/bin/sh\necho changed\n"})
    args = argparse.Namespace(workspace=str(remote.workspace), project=NAME, no_build=False, preview=True, profile=None)
    assert main_module.cmd_update(args) == 0
    output = capsys.readouterr().out
    assert "Version:          1.0.0 -> 1.1.0" in output and "build-test.sh" in output
    assert "Nothing was changed" in output
    assert git("rev-parse", "HEAD", cwd=remote.checkout) == before
    assert not list(remote.workspace.glob(f"{NAME}.backup-*"))
