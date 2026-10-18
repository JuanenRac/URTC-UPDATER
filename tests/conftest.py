# =============================================================================
# URTC-UPDATER - tests/conftest.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Every test runs with the commit-signature policy explicitly OFF unless it
turns it on itself, so a developer whose own ~/.urtc_updater_settings.json
requires signed commits does not see unrelated tests fail on unsigned test
repositories. git also runs without the machine's global/system config, so
a developer's own commit-signing or hook settings cannot change what the
tests see."""
import pytest

from urtc_updater import github_client, settings


@pytest.fixture(autouse=True)
def _signature_policy_off(monkeypatch, tmp_path_factory):
    monkeypatch.setenv("URTC_UPDATER_REQUIRE_SIGNED", "0")
    monkeypatch.delenv("URTC_UPDATER_ALLOWED_SIGNERS", raising=False)
    empty = tmp_path_factory.mktemp("gitconfig") / "config"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    # Preferences and the cached repository listing live in the home folder:
    # each test gets its own, so nothing is read from or written to the real one.
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setattr(settings, "SETTINGS_PATH", home / ".urtc_updater_settings.json")
    monkeypatch.setattr(settings, "_LEGACY_LANG_PATH", home / ".urtc_updater_lang.json")
    monkeypatch.setattr(github_client, "REPO_LIST_CACHE_PATH", home / ".urtc_updater_repo_cache.json")
