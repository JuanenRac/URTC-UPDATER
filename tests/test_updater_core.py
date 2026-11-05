# =============================================================================
# URTC-UPDATER - tests/test_updater_core.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The names of the family come from the profile, and the profile keeps the values this updater has always used."""
from __future__ import annotations

import pytest

from urtc_updater import github_client, settings, updater_core
from urtc_updater.project_manifest import ECOSYSTEM_ID, MANIFEST_FILE

PROFILE = updater_core.PROFILE


def test_the_profile_keeps_the_values_of_this_updater():
    assert PROFILE.ecosystem_id == ECOSYSTEM_ID
    assert PROFILE.manifest_file == MANIFEST_FILE == "urtc.project.json"
    assert PROFILE.env_prefix == "URTC_UPDATER"
    assert PROFILE.state_directory == ".urtc-updater"
    assert PROFILE.user_agent == "URTC-UPDATER"
    assert PROFILE.file_prefix == ".urtc_updater"
    assert PROFILE.repo_prefix == "URTC"
    assert PROFILE.batch_last == ("URTC-UPDATER",)


def test_the_modules_take_their_names_from_the_profile(tmp_path):
    assert github_client.USER_AGENT == "URTC-UPDATER"
    assert settings.SETTINGS_PATH.name == ".urtc_updater_settings.json"
    assert PROFILE.thread_prefix("github") == "urtc-github"
    assert PROFILE.env_name("REQUIRE_SIGNED") == "URTC_UPDATER_REQUIRE_SIGNED"
    assert updater_core.profile_for(ECOSYSTEM_ID) is PROFILE


def test_an_unknown_family_is_an_error_and_never_another_family():
    with pytest.raises(KeyError):
        updater_core.profile_for("NOT-A-FAMILY")


def test_the_environment_helpers_read_the_prefix_of_the_family(monkeypatch):
    monkeypatch.setenv("URTC_UPDATER_X", " yes ")
    assert PROFILE.env_flag("X") is True
    monkeypatch.setenv("URTC_UPDATER_X", "off")
    assert PROFILE.env_flag("X") is False
    monkeypatch.setenv("URTC_UPDATER_X", "maybe")
    assert PROFILE.env_flag("X") is None
    monkeypatch.delenv("URTC_UPDATER_X")
    assert PROFILE.env_text("X") == ""


def test_every_module_of_the_core_exists():
    import importlib

    for name in updater_core.CORE_MODULES:
        module = importlib.import_module(f"urtc_updater.{name}")
        assert getattr(module, "_PROFILE", None) is PROFILE, f"{name} does not read the profile"
