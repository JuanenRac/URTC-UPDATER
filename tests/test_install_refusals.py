# =============================================================================
# URTC-UPDATER - tests/test_install_refusals.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Install and update refusals, each against real local git repositories: a
remote that cannot be reached, a manifest that is broken or names another
project, a checkout that is not a git repository. In every case the
installation that is already there stays exactly as it was and nothing is
left half-made next to it."""
from __future__ import annotations

from pathlib import Path

import pytest
from repo_helpers import NAME, entry, git, make_remote

from urtc_updater import install
from urtc_updater.install import clone_or_pull


def _head(path: Path) -> str:
    return git("rev-parse", "HEAD", cwd=path)


def _tree_names(path: Path) -> set[str]:
    return {item.name for item in path.iterdir()}


def test_an_unreachable_remote_is_a_fetch_failure_and_leaves_the_checkout_alone(tmp_path):
    remote = make_remote(tmp_path)
    before = _head(remote.checkout)
    git("remote", "set-url", "origin", str(tmp_path / "does-not-exist.git"), cwd=remote.checkout)
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "fetch_failed"
    assert _head(remote.checkout) == before


def test_a_remote_manifest_that_is_not_json_is_refused(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    before = _head(remote.checkout)
    remote.push("1.1.0", "broken manifest", {"urtc.project.json": "{ this is not json"})
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "remote_manifest_invalid"
    assert _head(remote.checkout) == before


def test_a_remote_manifest_for_another_project_is_refused(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    before = _head(remote.checkout)
    from repo_helpers import manifest_text
    remote.push("1.1.0", "wrong project", {"urtc.project.json": manifest_text("1.1.0", name="URTC-SOMETHING-ELSE")})
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "remote_manifest_invalid"
    assert _head(remote.checkout) == before


def test_a_remote_without_a_manifest_is_refused(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    before = _head(remote.checkout)
    git("rm", "-q", "urtc.project.json", cwd=remote.seed)
    git("commit", "-q", "-m", "no manifest any more", cwd=remote.seed)
    git("push", "-q", "origin", "HEAD", cwd=remote.seed)
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "remote_manifest_invalid"
    assert _head(remote.checkout) == before


def test_an_installed_checkout_whose_own_manifest_is_broken_is_not_updated(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    (remote.checkout / "urtc.project.json").write_text("{ broken", encoding="utf-8")
    git("commit", "-q", "-am", "local breakage", cwd=remote.checkout)
    before = _head(remote.checkout)
    remote.push("1.1.0", "update")
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "installed_manifest_invalid"
    assert _head(remote.checkout) == before


def test_a_directory_that_is_not_a_git_checkout_is_never_touched(tmp_path):
    remote = make_remote(tmp_path, "1.0.0", clone=False)
    target = remote.workspace / NAME
    target.mkdir()
    (target / "precious.txt").write_text("keep me", encoding="utf-8")
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "not_git"
    assert _tree_names(target) == {"precious.txt"}
    assert (target / "precious.txt").read_text(encoding="utf-8") == "keep me"


def test_a_fresh_clone_with_a_broken_manifest_leaves_nothing_behind(tmp_path, monkeypatch):
    remote = make_remote(tmp_path, "1.0.0", clone=False)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    remote.push("1.0.1", "broken", {"urtc.project.json": "not json at all"})
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "clone_manifest_invalid"
    assert not (remote.workspace / NAME).exists()
    leftovers = [item.name for item in remote.workspace.iterdir()]
    assert leftovers == [], leftovers


def test_a_fresh_clone_of_a_good_remote_installs_it(tmp_path, monkeypatch):
    remote = make_remote(tmp_path, "1.0.0", clone=False)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    result = clone_or_pull(entry(), remote.workspace)
    assert result.ok and result.message.code == "cloned"
    assert (remote.workspace / NAME / ".git").is_dir()


def test_without_the_build_check_a_good_update_is_a_fast_forward_in_place(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    remote.push("1.0.1", "update")
    result = clone_or_pull(entry(), remote.workspace, verify_build=False)
    assert result.ok and result.message.code == "pulled"
    assert _head(remote.checkout) == git("rev-parse", "HEAD", cwd=remote.seed)


def test_without_the_build_check_a_diverged_checkout_is_not_merged(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    (remote.checkout / "local.txt").write_text("local work", encoding="utf-8")
    git("add", "-A", cwd=remote.checkout)
    git("commit", "-q", "-m", "local work", cwd=remote.checkout)
    before = _head(remote.checkout)
    remote.push("1.0.1", "remote work", {"remote.txt": "remote work"})
    result = clone_or_pull(entry(), remote.workspace, verify_build=False)
    assert not result.ok
    assert result.message.code == "merge_failed"
    assert _head(remote.checkout) == before


@pytest.mark.parametrize("version", ["1.0.0"])
def test_an_up_to_date_checkout_is_accepted_without_changes(tmp_path, version):
    remote = make_remote(tmp_path, version)
    before = _head(remote.checkout)
    result = clone_or_pull(entry(), remote.workspace)
    assert result.ok
    assert _head(remote.checkout) == before
