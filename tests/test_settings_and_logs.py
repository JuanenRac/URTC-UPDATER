# =============================================================================
# URTC-UPDATER - tests/test_settings_and_logs.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The remembered preferences (with the legacy language file and a damaged file) and the rotation of the window log files."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from urtc_updater import logs, settings


@pytest.fixture()
def paths(tmp_path, monkeypatch):
    current = tmp_path / "settings.json"
    legacy = tmp_path / "legacy_lang.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", current)
    monkeypatch.setattr(settings, "_LEGACY_LANG_PATH", legacy)
    return current, legacy


# ---- settings -------------------------------------------------------------------------------------------------------

def test_the_state_of_the_settings_file_is_missing_ok_or_corrupt(paths):
    current, _legacy = paths
    assert settings.settings_state() == "missing"
    current.write_text('{"lang": "es"}', encoding="utf-8")
    assert settings.settings_state() == "ok"
    current.write_text("[1]", encoding="utf-8")
    assert settings.settings_state() == "corrupt"
    current.write_text("{oops", encoding="utf-8")
    assert settings.settings_state() == "corrupt"
    current.write_bytes(b"\xff\xfe\x00")
    assert settings.settings_state() == "corrupt"


def test_unreadable_settings_load_as_empty(paths):
    current, _legacy = paths
    assert settings.load_settings() == {}
    current.write_text("{oops", encoding="utf-8")
    assert settings.load_settings() == {}
    current.write_text("[1]", encoding="utf-8")
    assert settings.load_settings() == {}


def test_saving_one_preference_keeps_the_others(paths):
    current, _legacy = paths
    settings.save_settings(lang="de")
    settings.save_settings(workspace_root="x")
    assert json.loads(current.read_text(encoding="utf-8")) == {"lang": "de", "workspace_root": "x"}
    assert not current.with_name("settings.json.tmp").exists()


def test_a_damaged_settings_file_is_left_alone_by_a_save(paths):
    current, _legacy = paths
    current.write_text("{oops", encoding="utf-8")
    settings.save_settings(lang="de")
    assert current.read_text(encoding="utf-8") == "{oops"


def test_replacing_the_settings_keeps_a_damaged_file_next_to_the_new_one(paths):
    current, _legacy = paths
    current.write_text("{oops", encoding="utf-8")
    settings.replace_settings({"lang": "fr"})
    assert json.loads(current.read_text(encoding="utf-8")) == {"lang": "fr"}
    assert current.with_name("settings.json.corrupt").read_text(encoding="utf-8") == "{oops"


def test_a_save_where_nothing_can_be_written_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "no_such_folder" / "settings.json")
    settings.save_settings(lang="de")   # best effort: no exception, no file
    assert not (tmp_path / "no_such_folder").exists()


def test_the_saved_workspace_is_returned_only_while_it_still_exists(paths, tmp_path):
    assert settings.get_saved_workspace_root() is None
    folder = tmp_path / "workspace"
    folder.mkdir()
    settings.save_workspace_root(folder)
    assert settings.get_saved_workspace_root() == folder
    folder.rmdir()
    assert settings.get_saved_workspace_root() is None
    settings.save_settings(workspace_root="")
    assert settings.get_saved_workspace_root() is None
    settings.save_settings(workspace_root=5)
    assert settings.get_saved_workspace_root() is None


def test_the_language_comes_from_the_settings_then_from_the_legacy_file(paths):
    current, legacy = paths
    assert settings.get_saved_lang() is None
    legacy.write_text('{"lang": "it"}', encoding="utf-8")
    assert settings.get_saved_lang() == "it"
    settings.save_lang("ja")
    assert settings.get_saved_lang() == "ja"
    assert json.loads(current.read_text(encoding="utf-8"))["lang"] == "ja"


def test_a_legacy_language_file_that_is_wrong_is_ignored(paths):
    _current, legacy = paths
    legacy.write_text("{oops", encoding="utf-8")
    assert settings.get_saved_lang() is None
    legacy.write_text("[1]", encoding="utf-8")
    assert settings.get_saved_lang() is None
    legacy.write_text('{"lang": 5}', encoding="utf-8")
    assert settings.get_saved_lang() is None


# ---- log rotation -----------------------------------------------------------------------------------------------------

def make_logs(folder: Path, count: int) -> list[Path]:
    made = []
    for index in range(count):
        path = folder / f"gui_{index:02d}.log"
        path.write_text("x", encoding="utf-8")
        os.utime(path, (1000 + index, 1000 + index))
        made.append(path)
    return made


def test_the_newest_logs_are_kept_and_the_oldest_removed(tmp_path):
    made = make_logs(tmp_path, 5)
    (tmp_path / "other.txt").write_text("keep", encoding="utf-8")
    removed = logs.prune_logs(tmp_path, keep=2)
    assert sorted(removed) == sorted(made[:3])
    assert sorted(path.name for path in tmp_path.iterdir()) == ["gui_03.log", "gui_04.log", "other.txt"]


def test_fewer_logs_than_the_limit_are_all_kept(tmp_path):
    make_logs(tmp_path, 3)
    assert logs.prune_logs(tmp_path, keep=10) == []
    assert len(list(tmp_path.glob("gui_*.log"))) == 3


def test_a_negative_limit_keeps_everything(tmp_path):
    make_logs(tmp_path, 2)
    assert len(logs.prune_logs(tmp_path, keep=-3)) == 2


def test_a_folder_that_is_not_there_gives_nothing_to_remove(tmp_path):
    assert logs.prune_logs(tmp_path / "missing", keep=1) == []


def test_a_log_that_cannot_be_removed_is_left_and_not_counted(tmp_path, monkeypatch):
    made = make_logs(tmp_path, 3)
    real_unlink = Path.unlink

    def selective(self, *args, **kwargs):
        if self == made[0]:
            raise PermissionError("in use")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", selective)
    removed = logs.prune_logs(tmp_path, keep=1)
    assert removed == [made[1]]
    assert made[0].exists()
