# =============================================================================
# URTC-UPDATER - tests/test_compat_view.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The compatibility command and window: the matrix that travels with the program, compared with the folders of a workspace. Read-only."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from urtc_updater.compat_view import compat_matrix_path
from urtc_updater.main import build_parser
from urtc_updater.urtc_pkg import compat


def _workspace(tmp_path: Path) -> Path:
    matrix = compat.load_matrix(compat_matrix_path())
    first, second = matrix["projects"][1], matrix["projects"][2]
    for item, version in ((first, first["version"]), (second, "0.0.1")):
        folder = tmp_path / item["repo"]
        folder.mkdir()
        (folder / "urtc.project.json").write_text(json.dumps({"name": item["repo"], "version": version}), encoding="utf-8")
    return tmp_path


def test_the_matrix_that_travels_with_the_program_is_valid_and_has_the_whole_family():
    matrix = compat.load_matrix(compat_matrix_path())
    names = {item["repo"] for item in matrix["projects"]}
    assert {"URTC", "URTC-FLASHER", "URTC-TESTER", "URTC-WEB-STUDIO", "URTC-UPDATER", "URTC-COMMON"} <= names


def test_the_command_parses_and_defaults_to_english():
    args = build_parser().parse_args(["compat"])
    assert args.command == "compat" and args.language == "english" and args.json is False


def test_json_output_has_one_entry_per_project_and_the_states(tmp_path, capsys):
    workspace = _workspace(tmp_path)
    args = build_parser().parse_args(["compat", "--json", "--workspace", str(workspace)])
    assert args.func(args) == 0
    data = json.loads(capsys.readouterr().out)
    matrix = compat.load_matrix(compat_matrix_path())
    assert [p["repo"] for p in data["projects"]] == [item["repo"] for item in matrix["projects"]]
    states = {p["repo"]: p["state"] for p in data["projects"]}
    installed = [item["repo"] for item in matrix["projects"][1:3]]
    assert states[installed[0]] == "match" and states[installed[1]] == "older"
    assert all(state == "missing" for repo, state in states.items() if repo not in installed)
    assert data["protocol"] == matrix["protocol_version"]
    assert sum(data["counts"].values()) == len(matrix["projects"])


def test_text_output_in_another_language(tmp_path, capsys):
    workspace = _workspace(tmp_path)
    args = build_parser().parse_args(["compat", "--language", "portuguese", "--workspace", str(workspace)])
    assert args.func(args) == 0
    out = capsys.readouterr().out
    assert "Projeto" in out and "não instalado" in out


def test_an_empty_workspace_says_so_and_is_not_an_error(tmp_path, capsys):
    args = build_parser().parse_args(["compat", "--workspace", str(tmp_path)])
    assert args.func(args) == 0
    assert compat.text("english", "none_installed") in capsys.readouterr().out


def test_a_missing_workspace_or_matrix_exits_with_2(tmp_path, capsys, monkeypatch):
    args = build_parser().parse_args(["compat", "--workspace", str(tmp_path / "absent")])
    assert args.func(args) == 2
    args = build_parser().parse_args(["compat", "--workspace", str(tmp_path)])
    monkeypatch.setattr("urtc_updater.compat_view.compat_matrix_path", lambda: tmp_path / "nothing.json")
    assert args.func(args) == 2
    assert "cannot be read" in capsys.readouterr().err


def test_the_command_changes_nothing_in_the_workspace(tmp_path):
    workspace = _workspace(tmp_path)
    before = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*"))
    args = build_parser().parse_args(["compat", "--workspace", str(workspace)])
    args.func(args)
    assert sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*")) == before


def test_the_menu_text_exists_in_the_eight_languages():
    from urtc_updater import i18n

    for code, _label in i18n.LANGUAGES:
        assert i18n.t(code, "compat_menu") not in ("", "compat_menu"), code


def test_the_window_is_part_of_the_bridge_and_loads(tmp_path):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QCoreApplication

    from urtc_updater import qt_gui

    QCoreApplication.instance() or QCoreApplication([])
    bridge = qt_gui.UpdaterBridge(_workspace(tmp_path))
    model = bridge.compat
    assert model is bridge.compat and model.title
    assert len(model.rows) == len(compat.load_matrix(compat_matrix_path())["projects"])
    bridge.setLanguage("pt")
    assert model.title == "Compatibilidade"
    qml = (Path(qt_gui.__file__).parent / "qml" / "Main.qml").read_text(encoding="utf-8")
    assert "CompatDialog" in qml and 'ui("compat_menu")' in qml
