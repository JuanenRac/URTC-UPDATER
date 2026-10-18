# =============================================================================
# URTC-UPDATER - tests/test_build_validation.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""What the updater does with the answer of a build-test: "validation unavailable" (exit code 75) is not "validation failed", and a build-test
that changed a file git tracks must not leave the promoted checkout dirty. Real local git repositories, real scripts."""
from __future__ import annotations

import os
from pathlib import Path

from repo_helpers import NAME, entry, git, make_remote

from urtc_updater import install
from urtc_updater.install import BUILD_TEST_UNAVAILABLE_EXIT, clone_or_pull


def _write_build_test(path: Path, posix_body: str, windows_body: str) -> dict[str, str]:
    """The files of a build-test for this operating system, as pushed by Remote.push."""
    if os.name == "nt":
        return {"build-test.bat": "@echo off\r\n" + windows_body + "\r\n"}
    return {"build-test.sh": "#!/bin/sh\n" + posix_body + "\n"}


def test_an_unavailable_validation_is_reported_as_such_and_refuses_by_default(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    before = git("rev-parse", "HEAD", cwd=remote.checkout)
    remote.push("1.1.0", "needs a tool", _write_build_test(remote.seed, f"exit {BUILD_TEST_UNAVAILABLE_EXIT}", f"exit /b {BUILD_TEST_UNAVAILABLE_EXIT}"))
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.code == "candidate_build_failed"
    assert result.message.params["detail"].code == "script_unavailable"
    assert "validation unavailable" in str(result.message)
    assert git("rev-parse", "HEAD", cwd=remote.checkout) == before


def test_an_ordinary_failure_is_not_taken_for_an_unavailable_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION", "1")
    remote = make_remote(tmp_path, "1.0.0")
    remote.push("1.1.0", "broken", _write_build_test(remote.seed, "exit 3", "exit /b 3"))
    result = clone_or_pull(entry(), remote.workspace)
    assert not result.ok
    assert result.message.params["detail"].code == "script_failed"


def test_the_person_can_accept_an_update_whose_validation_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION", "1")
    remote = make_remote(tmp_path, "1.0.0")
    remote.push("1.1.0", "needs a tool", _write_build_test(remote.seed, f"exit {BUILD_TEST_UNAVAILABLE_EXIT}", f"exit /b {BUILD_TEST_UNAVAILABLE_EXIT}"))
    calls: list = []
    result = clone_or_pull(entry(), remote.workspace, progress=lambda phase, message: calls.append((phase, message)))
    assert result.ok, result.message
    assert any(getattr(message, "code", "") == "cp_build_unavailable_accepted" for _phase, message in calls)
    assert git("rev-parse", "HEAD", cwd=remote.checkout) == git("rev-parse", "HEAD", cwd=remote.seed)


def test_the_setting_accepts_it_too(tmp_path, monkeypatch):
    from urtc_updater import settings

    assert not install.accepts_unavailable_validation()
    settings.save_settings(validation_unavailable="accept")
    assert install.accepts_unavailable_validation()
    settings.save_settings(validation_unavailable="refuse")
    assert not install.accepts_unavailable_validation()


def test_a_file_that_the_build_test_changed_is_put_back_before_the_promotion(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    files = {"generated.txt": "committed\n"}
    files.update(_write_build_test(remote.seed, "echo changed > generated.txt", "echo changed> generated.txt"))
    remote.push("1.1.0", "a build-test that writes into the tree", files)
    calls: list = []
    result = clone_or_pull(entry(), remote.workspace, progress=lambda phase, message: calls.append((phase, message)))
    assert result.ok, result.message
    assert git("status", "--porcelain", "--untracked-files=no", cwd=remote.checkout) == ""
    assert (remote.checkout / "generated.txt").read_text(encoding="utf-8").strip() == "committed"
    restored = [message for _phase, message in calls if getattr(message, "code", "") == "cp_build_restored_files"]
    assert restored and restored[0].params["count"] == 1 and "generated.txt" in restored[0].params["files"]


def test_a_build_test_that_leaves_the_tree_alone_says_nothing(tmp_path):
    remote = make_remote(tmp_path, "1.0.0")
    remote.push("1.1.0", "plain update")
    calls: list = []
    result = clone_or_pull(entry(), remote.workspace, progress=lambda phase, message: calls.append((phase, message)))
    assert result.ok, result.message
    assert not any(getattr(message, "code", "") == "cp_build_restored_files" for _phase, message in calls)


def test_a_fresh_install_is_left_clean_after_its_build_test(tmp_path, monkeypatch):
    remote = make_remote(tmp_path, "1.0.0", clone=False)
    files = {"generated.txt": "committed\n"}
    files.update(_write_build_test(remote.seed, "echo changed > generated.txt", "echo changed> generated.txt"))
    remote.push("1.0.1", "a build-test that writes into the tree", files)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    results = install.install_or_update(entry(), remote.workspace)
    assert all(r.ok for r in results), [str(r.message) for r in results]
    assert git("status", "--porcelain", "--untracked-files=no", cwd=remote.workspace / NAME) == ""


def test_every_language_words_the_new_messages():
    from urtc_updater import i18n

    for code in ("script_unavailable", "cp_build_unavailable_accepted", "cp_build_restored_files"):
        english = i18n.t("en", f"inst_{code}", script="x", count=1, files="a")
        assert english != f"inst_{code}"
        for lang, _name in i18n.LANGUAGES:
            assert i18n.t(lang, f"inst_{code}", script="x", count=1, files="a") != f"inst_{code}"
