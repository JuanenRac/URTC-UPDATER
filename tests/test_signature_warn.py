# =============================================================================
# URTC-UPDATER - tests/test_signature_warn.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""The default signature policy is "warn": an unsigned revision is installed or updated and the steps say that it is not signed; "require" refuses it."""
from __future__ import annotations

import json
from pathlib import Path

from urtc_updater import i18n, install, settings
from urtc_updater.install import clone_or_pull
from urtc_updater.signature import SignaturePolicy, current_policy, unsigned_reason
from test_install import entry, git, write_manifest
from test_signature import _remote_with_one_commit


def test_the_default_policy_is_warn(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("URTC_UPDATER_REQUIRE_SIGNED", raising=False)
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    policy = current_policy()
    assert policy.required is False and policy.mode == "warn"


def test_require_can_be_chosen_in_the_settings_both_ways(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("URTC_UPDATER_REQUIRE_SIGNED", raising=False)
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", path)
    path.write_text(json.dumps({"signature_policy": "require"}), encoding="utf-8")
    assert current_policy().mode == "require"
    path.write_text(json.dumps({"require_signed_commits": True}), encoding="utf-8")
    assert current_policy().mode == "require"
    path.write_text(json.dumps({"signature_policy": "warn"}), encoding="utf-8")
    assert current_policy().mode == "warn"


def test_an_unsigned_revision_has_a_reason_whatever_the_mode(tmp_path: Path):
    remote = _remote_with_one_commit(tmp_path, signing_key=None)
    clone = tmp_path / "clone"
    git("clone", str(remote), str(clone), cwd=tmp_path)
    assert unsigned_reason(clone, "HEAD", SignaturePolicy(required=False)) is not None


def test_an_unsigned_fresh_install_goes_ahead_and_the_steps_say_it_is_not_signed(tmp_path: Path, monkeypatch):
    remote = _remote_with_one_commit(tmp_path, signing_key=None)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote))
    monkeypatch.delenv("URTC_UPDATER_REQUIRE_SIGNED", raising=False)
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    steps: list[object] = []
    result = clone_or_pull(entry(), workspace, verify_build=False, progress=lambda phase, text: steps.append(text))
    assert result.ok, result.message
    warnings = [step for step in steps if getattr(step, "code", "") == "cp_unsigned_warning"]
    assert len(warnings) == 1 and "not signed" in str(warnings[0]) and warnings[0].params["commit"]


def test_the_warning_exists_in_every_language():
    for code, _label in i18n.LANGUAGES:
        text = i18n.t(code, "inst_cp_unsigned_warning", commit="abc123", reason="no key")
        assert "abc123" in text and "no key" in text and "{" not in text, code


def test_require_still_refuses_an_unsigned_revision(tmp_path: Path, monkeypatch):
    remote = _remote_with_one_commit(tmp_path, signing_key=None)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote))
    monkeypatch.setenv("URTC_UPDATER_REQUIRE_SIGNED", "1")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    steps: list[object] = []
    result = clone_or_pull(entry(), workspace, verify_build=False, progress=lambda phase, text: steps.append(text))
    assert not result.ok and "signature policy" in result.message
    assert not [step for step in steps if getattr(step, "code", "") == "cp_unsigned_warning"]
    assert list(workspace.iterdir()) == []


def test_an_unsigned_update_goes_ahead_with_the_warning(tmp_path: Path, monkeypatch):
    remote = _remote_with_one_commit(tmp_path, signing_key=None)
    local = tmp_path / entry().name
    git("clone", str(remote), str(local), cwd=tmp_path)
    seed = tmp_path / "seed"
    write_manifest(seed, "1.1.0")
    git("add", "-A", cwd=seed)
    git("commit", "-m", "v2 unsigned", cwd=seed)
    git("push", "origin", "HEAD", cwd=seed)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote))
    monkeypatch.delenv("URTC_UPDATER_REQUIRE_SIGNED", raising=False)
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    steps: list[object] = []
    result = clone_or_pull(entry(), tmp_path, verify_build=False, progress=lambda phase, text: steps.append(text))
    assert result.ok, result.message
    assert [step for step in steps if getattr(step, "code", "") == "cp_unsigned_warning"]
