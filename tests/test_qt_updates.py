# =============================================================================
# URTC-UPDATER - tests/test_qt_updates.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The "Check for updates" model of the window: conservative defaults, saved options, nothing while an install runs, the language of the window."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from urtc_updater import qt_gui, settings  # noqa: E402
from urtc_updater.urtc_pkg import update_service  # noqa: E402


@pytest.fixture
def bridge(tmp_path: Path, monkeypatch):
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])

    def unavailable():
        raise RuntimeError("offline in tests")

    monkeypatch.setattr(qt_gui, "discover_remote_projects", unavailable)
    monkeypatch.setattr(qt_gui, "fetch_all", lambda entries: {})
    return qt_gui.UpdaterBridge(tmp_path)


def test_the_model_starts_idle_with_the_conservative_options(bridge):
    model = bridge.updates
    assert model is bridge.updates
    assert model.state == "idle" and not model.autoCheck and model.requireConfirmation
    service = model.controller.service
    assert service.app == "urtc-updater" and service.repo == "JuanenRac/URTC-UPDATER"
    assert service.public_key_hex == update_service.RELEASE_PUBLIC_KEY_HEX


def test_nothing_goes_over_the_network_on_start_unless_the_person_turned_it_on(bridge):
    calls = []
    bridge.updates.controller.service.fetch = lambda url: calls.append(url)
    bridge.updates.startupCheck()
    assert calls == [] and bridge.updates.state == "idle"


def test_the_options_are_saved_in_the_settings_file(bridge):
    bridge.updates.setAutoCheck(True)
    bridge.updates.setRequireConfirmation(False)
    saved = settings.load_settings()
    assert saved["update_auto_check"] is True and saved["update_require_confirmation"] is False


def test_an_update_is_refused_while_a_project_is_being_installed(bridge):
    service = bridge.updates.controller.service
    bridge._busy = False
    assert service.busy() is None
    bridge._busy = True
    assert service.busy() == "install/update"


def test_the_texts_follow_the_language_of_the_window(bridge):
    bridge._lang = "pt"
    assert bridge.updates.t("UPD_BTN_CLOSE") == "Fechar"
    bridge._lang = "de"
    assert bridge.updates.t("UPD_BTN_CLOSE") == "Schließen"
    bridge._lang = "xx"
    assert bridge.updates.t("UPD_BTN_CLOSE") == "Close"


def test_the_update_dialog_is_in_the_window_and_the_button_opens_it():
    qml = (Path(qt_gui.__file__).with_name("qml") / "Main.qml").read_text(encoding="utf-8")
    assert "UpdateDialog {" in qml and "updateDialog.open()" in qml and "backend.updates" in qml
    assert (Path(qt_gui.__file__).with_name("qml") / "UpdateDialog.qml").is_file()
