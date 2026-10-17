# =============================================================================
# URTC-UPDATER - tests/test_commits.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Comparing a checkout with its remote by commit, against a real local bare repository."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from repo_helpers import NAME, entry, git, make_remote

from urtc_updater import commits, install
from urtc_updater import main as main_module
from urtc_updater.github_client import RemoteDiscovery, RemoteStatus
from urtc_updater.install import clone_or_pull
from urtc_updater.version_parse import Version


def test_a_checkout_at_the_remote_head_is_the_same(tmp_path: Path):
    remote = make_remote(tmp_path)
    assert commits.remote_head(remote.checkout) == commits.local_head(remote.checkout)
    assert commits.commit_state(remote.checkout) == commits.SAME


def test_new_commits_at_the_same_version_are_detected(tmp_path: Path):
    remote = make_remote(tmp_path)
    remote.push("1.0.0", "a fix published without a build", {"fix.txt": "fixed\n"})
    assert commits.commit_state(remote.checkout) == commits.NEW_COMMITS


def test_unpushed_local_commits_are_ahead_not_new(tmp_path: Path):
    remote = make_remote(tmp_path)
    (remote.checkout / "local.txt").write_text("mine\n", encoding="utf-8")
    git("add", "-A", cwd=remote.checkout)
    git("commit", "-m", "local", cwd=remote.checkout)
    assert commits.commit_state(remote.checkout) == commits.AHEAD


def test_a_diverged_checkout_counts_as_new_commits(tmp_path: Path):
    remote = make_remote(tmp_path)
    (remote.checkout / "local.txt").write_text("mine\n", encoding="utf-8")
    git("add", "-A", cwd=remote.checkout)
    git("commit", "-m", "local", cwd=remote.checkout)
    remote.push("1.0.0", "remote moved on", {"remote.txt": "theirs\n"})
    git("fetch", "origin", cwd=remote.checkout)  # the remote commit is now known locally, but not contained
    assert commits.commit_state(remote.checkout) == commits.NEW_COMMITS


def test_an_unreachable_remote_or_a_plain_folder_is_unknown(tmp_path: Path):
    remote = make_remote(tmp_path)
    git("remote", "set-url", "origin", str(tmp_path / "gone.git"), cwd=remote.checkout)
    assert commits.commit_state(remote.checkout) == commits.UNKNOWN
    plain = tmp_path / "plain"
    plain.mkdir()
    assert commits.commit_state(plain) == commits.UNKNOWN


def test_several_checkouts_are_compared_together(tmp_path: Path):
    remote = make_remote(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    states = commits.commit_states({"a": remote.checkout, "b": plain})
    assert states == {"a": commits.SAME, "b": commits.UNKNOWN}
    assert commits.commit_states({}) == {}


def test_an_update_is_accepted_when_only_the_commit_changed(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    new_head = remote.push("1.0.0", "a fix published without a build", {"fix.txt": "fixed\n"})
    result = clone_or_pull(entry(), remote.workspace)
    assert result.ok, result.message
    assert commits.local_head(remote.checkout) == new_head
    assert commits.commit_state(remote.checkout) == commits.SAME


def _status_args(workspace: Path, *, as_json: bool = True) -> argparse.Namespace:
    return argparse.Namespace(
        workspace=str(workspace), offline=False, notes=False, json=as_json, profile=None,
    )


def _patch_remote(monkeypatch, version: str) -> None:
    remote_entry = entry()
    status = RemoteStatus(entry=remote_entry, version=Version.from_string(version))
    monkeypatch.setattr(main_module, "discover_remote_projects", lambda: RemoteDiscovery((status,), ()))


def test_status_reports_new_commits_at_the_same_version(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    remote.push("1.0.0", "a fix published without a build", {"fix.txt": "fixed\n"})
    _patch_remote(monkeypatch, "1.0.0")
    assert main_module.cmd_status(_status_args(remote.workspace)) == 0
    payload = json.loads(capsys.readouterr().out)
    (project,) = payload["projects"]
    assert project["name"] == NAME
    assert project["state"] == "NEW COMMITS" and project["commit_state"] == commits.NEW_COMMITS
    assert payload["new_commits_count"] == 1 and payload["outdated_count"] == 0


def test_status_table_says_how_many_have_new_commits(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    remote.push("1.0.0", "a fix", {"fix.txt": "fixed\n"})
    _patch_remote(monkeypatch, "1.0.0")
    assert main_module.cmd_status(_status_args(remote.workspace, as_json=False)) == 0
    output = capsys.readouterr().out
    assert "NEW COMMITS" in output and "1 with new commits at the same version" in output


def test_status_is_up_to_date_when_commits_match(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    _patch_remote(monkeypatch, "1.0.0")
    assert main_module.cmd_status(_status_args(remote.workspace)) == 0
    (project,) = json.loads(capsys.readouterr().out)["projects"]
    assert project["state"] == "up to date"


def test_offline_status_never_contacts_the_remote(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(commits, "remote_head", lambda *a, **k: (_ for _ in ()).throw(AssertionError("contacted the remote")))
    args = _status_args(remote.workspace)
    args.offline = True
    assert main_module.cmd_status(args) == 0
    (project,) = json.loads(capsys.readouterr().out)["projects"]
    assert project["commit_state"] is None
