# =============================================================================
# URTC-UPDATER - tests/test_notify_profiles_edges.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The edges of the desktop notification and of the station profiles: quotes in the text, a system with no tool, a tool that fails or hangs, and every
shape a profile in the settings file can have."""
from __future__ import annotations

import subprocess

import pytest

from urtc_updater import profiles
from urtc_updater.notify import notification_command, send_notification


# --- notification ------------------------------------------------------------

def test_linux_passes_the_text_as_two_arguments_and_never_through_a_shell():
    assert notification_command("Title; rm -rf /", "$(id)", "linux") == ["notify-send", "Title; rm -rf /", "$(id)"]


def test_macos_escapes_quotes_and_backslashes_in_both_texts():
    command = notification_command('He said "hi"', "a\\b", "darwin")
    assert command is not None and command[:2] == ["osascript", "-e"]
    script = command[2]
    assert 'display notification "a\\\\b"' in script
    assert 'with title "He said \\"hi\\""' in script


def test_windows_doubles_the_single_quotes_of_the_text():
    command = notification_command("It's", "don't", "win32")
    assert command is not None and command[0] == "powershell"
    script = command[-1]
    assert "'It''s'" in script and "'don''t'" in script
    assert "-NoProfile" in command and "Hidden" in command


def test_a_system_with_no_known_tool_has_no_command():
    assert notification_command("t", "b", "freebsd14") is None


def test_no_command_means_nothing_is_run_and_false_comes_back():
    calls = []
    assert send_notification("t", "b", runner=lambda *a, **k: calls.append(a), platform="freebsd14") is False
    assert calls == []


@pytest.mark.parametrize("error", [FileNotFoundError("notify-send"), PermissionError("no"), subprocess.TimeoutExpired("notify-send", 30),
                                   subprocess.CalledProcessError(1, "notify-send")])
def test_a_tool_that_cannot_start_or_hangs_gives_false_and_never_raises(error):
    def runner(*_a, **_k):
        raise error
    assert send_notification("t", "b", runner=runner, platform="linux") is False


def test_the_tool_runs_with_a_time_limit_and_does_not_check_its_exit_code():
    seen = {}

    def runner(command, **options):
        seen["command"], seen["options"] = command, options
    assert send_notification("t", "b", runner=runner, platform="linux") is True
    assert seen["options"]["timeout"] == 30 and seen["options"]["check"] is False
    assert seen["command"][0] == "notify-send"


# --- profiles ----------------------------------------------------------------

def _settings(monkeypatch, data):
    monkeypatch.setattr(profiles, "load_settings", lambda: data)


def test_no_profile_in_use_when_neither_the_name_nor_the_settings_give_one(monkeypatch):
    _settings(monkeypatch, {})
    assert profiles.load_profile() is None
    assert profiles.load_profile("") is None


@pytest.mark.parametrize("value", [None, 5, ["a"], ""])
def test_a_profile_name_that_is_not_text_means_no_profile(monkeypatch, value):
    _settings(monkeypatch, {"profile": value, "profiles": {"a": {}}})
    assert profiles.load_profile() is None


def test_a_name_that_is_not_defined_is_an_error_and_not_a_free_pass(monkeypatch):
    _settings(monkeypatch, {"profile": "bench", "profiles": {"other": {}}})
    with pytest.raises(ValueError, match="bench"):
        profiles.load_profile()


@pytest.mark.parametrize("definitions", [None, [], "x", 3, {"bench": None}, {"bench": []}, {"bench": "x"}])
def test_a_profile_table_or_entry_of_the_wrong_shape_is_an_error(monkeypatch, definitions):
    _settings(monkeypatch, {"profiles": definitions})
    with pytest.raises(ValueError):
        profiles.load_profile("bench")


def test_the_command_line_name_wins_over_the_name_in_the_settings(monkeypatch):
    _settings(monkeypatch, {"profile": "a", "profiles": {"a": {"projects": ["A"]}, "b": {"projects": ["B"]}}})
    assert profiles.load_profile("b").projects == ("B",)
    assert profiles.load_profile().projects == ("A",)


def test_an_empty_or_missing_project_list_covers_every_project(monkeypatch):
    _settings(monkeypatch, {"profiles": {"all": {}, "empty": {"projects": []}, "bad": {"projects": "URTC"}}})
    for name in ("all", "empty", "bad"):
        profile = profiles.load_profile(name)
        assert profile.projects == () and profile.allows("URTC") and profile.allows("anything")


def test_entries_that_are_not_text_are_dropped_from_the_project_list(monkeypatch):
    _settings(monkeypatch, {"profiles": {"p": {"projects": ["URTC", 7, None, ["x"], "URTC-FLASHER"]}}})
    profile = profiles.load_profile("p")
    assert profile.projects == ("URTC", "URTC-FLASHER")
    assert profile.allows("URTC") and profile.allows("URTC-FLASHER") and not profile.allows("URTC-TESTER")


@pytest.mark.parametrize("value, expected", [(False, False), (True, True), (None, True), (0, True), ("no", True), ([], True)])
def test_only_a_real_false_turns_batches_off(monkeypatch, value, expected):
    _settings(monkeypatch, {"profiles": {"p": {"allow_batch": value}}})
    assert profiles.load_profile("p").allow_batch is expected


def test_batches_are_allowed_when_the_key_is_missing(monkeypatch):
    _settings(monkeypatch, {"profiles": {"p": {}}})
    assert profiles.load_profile("p").allow_batch is True


def test_a_profile_is_immutable():
    profile = profiles.Profile("p", ("A",))
    with pytest.raises(Exception):
        profile.allow_batch = False  # type: ignore[misc]
