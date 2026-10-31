# =============================================================================
# URTC-UPDATER - tests/test_qt_history.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The history window of the updater: it shows the attempts of the workspace as ``urtc-evidence/1`` records, each one checked, in the language of the
window, and leaves the evidence file as it was."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from urtc_updater import evidence, qt_gui  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bridge(tmp_path: Path, monkeypatch):
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])
    monkeypatch.setattr(qt_gui, "discover_remote_projects", lambda: (_ for _ in ()).throw(RuntimeError("offline in tests")))
    monkeypatch.setattr(qt_gui, "fetch_all", lambda entries: {})
    window = qt_gui.UpdaterBridge(tmp_path)
    window.setLanguage("en")                                  # the saved language is the test's own (see conftest), not the person's
    return window


def attempt(workspace: Path, project: str, ok: bool) -> None:
    evidence.record_attempt(workspace, project=project, before={"version": "0.3.9", "commit": "a" * 7}, after={"version": "0.4.1", "commit": "b" * 7}, ok=ok, message="done")


def test_the_window_starts_empty_and_says_why(bridge):
    assert bridge.history is bridge.history
    assert bridge.history.rows == [] and bridge.history.emptyText.startswith("There is no folder of records yet")


def test_the_window_shows_the_attempts_of_the_workspace_in_the_language_of_the_window(bridge, tmp_path):
    attempt(tmp_path, "URTC-FLASHER", True)
    attempt(tmp_path, "URTC-TESTER", False)
    log = tmp_path / evidence.EVIDENCE_DIRECTORY / evidence.EVIDENCE_FILE
    before = log.read_bytes()
    bridge.history.refresh()
    rows = bridge.history.rows
    assert {r["board"] for r in rows} == {"URTC-FLASHER", "URTC-TESTER"} and all(r["valid"] and r["kind"] == "install" for r in rows)
    assert {r["board"]: r["outcome"] for r in rows} == {"URTC-FLASHER": "pass", "URTC-TESTER": "fail"}
    bridge.setLanguage("pt")
    assert bridge.history.title == "Histórico de operações" and {r["outcomeText"] for r in bridge.history.rows} == {"Aprovado", "Falhou"}
    assert log.read_bytes() == before                      # the evidence file is not touched: the window reads a second view of it


def test_the_window_is_in_the_main_window_with_a_button_that_opens_it():
    main = (ROOT / "src" / "urtc_updater" / "qml" / "Main.qml").read_text(encoding="utf-8")
    assert "EvidenceHistoryDialog {" in main and "model: backend.history" in main and "historyDialog.open()" in main
    assert (ROOT / "src" / "urtc_updater" / "qml" / "EvidenceHistoryDialog.qml").is_file()
