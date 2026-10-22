# =============================================================================
# URTC-UPDATER - tests/qt_security_dialogs_check.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Run by tests/test_qt_security_dialogs.py in its own process (a window needs a QGuiApplication, and another test of the suite may already have made a plain
Qt application). Loads the real Main.qml with the real bridge, opens the question before the build check and answers it from the window side."""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HOME = Path(tempfile.mkdtemp(prefix="urtc_updater_check_"))

from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from urtc_updater import i18n, qt_gui, security, settings  # noqa: E402

settings.SETTINGS_PATH = HOME / "settings.json"
settings._LEGACY_LANG_PATH = HOME / "lang.json"
for variable in (security.ENV_REQUIRE_SIGNED, security.ENV_CONFIRM_BUILD, security.ENV_ASSUME_YES):
    os.environ.pop(variable, None)
qt_gui.discover_remote_projects = lambda: (_ for _ in ()).throw(RuntimeError("offline"))
qt_gui.fetch_all = lambda entries: {}

app = QGuiApplication([])


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def wait_visible(dialog) -> None:
    for _ in range(100):
        pump(0.05)
        if dialog.property("visible"):
            return
    raise AssertionError("the dialog did not open")


bridge = qt_gui.UpdaterBridge(HOME)
bridge._lang = "de"
engine = QQmlApplicationEngine()
warnings: list[str] = []
engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
engine.rootContext().setContextProperty("backend", bridge)
engine.load(QUrl.fromLocalFile(str(Path(qt_gui.__file__).resolve().parent / "qml" / "Main.qml")))
pump()
assert engine.rootObjects(), warnings
root = engine.rootObjects()[0]
assert not [w for w in warnings if "ecurity" in w or "buildDialog" in w or "lowerDialog" in w], warnings
for name in ("securityDialog", "lowerDialog", "buildDialog"):
    assert root.findChild(QObject, name) is not None, name

# the two options
assert bridge.securityRequireSigned is False and bridge.securityConfirmBuild is False
bridge.saveSecurity(True, True)
assert bridge.securityRequireSigned and bridge.securityConfirmBuild
assert security.saved_require_signed() and security.saved_confirm_build()
assert i18n.t("de", "security_saved", signed=i18n.t("de", "security_on"), confirm=i18n.t("de", "security_on")) in bridge._activity[-1]
assert bridge.securityLowering(True, True) == ""
assert bridge.securityLowering(False, True) == i18n.t("de", "security_item_signed")
both = bridge.securityLowering(False, False)
assert i18n.t("de", "security_item_signed") in both and i18n.t("de", "security_item_confirm") in both


def ask(answer_with) -> object:
    result: list[object] = []
    request = security.BuildRequest("URTC-X", "build-test.sh", "abc123def456", "Someone <s@example.invalid>", "not signed", ("build-test.sh",))
    worker = threading.Thread(target=lambda: result.append(security.decide_build(request)))
    worker.start()
    dialog = root.findChild(QObject, "buildDialog")
    wait_visible(dialog)
    assert "URTC-X" in bridge.buildRequestTitle and "abc123def456" in bridge.buildRequestDetails
    assert "Someone" in bridge.buildRequestDetails and "build-test.sh" in bridge.buildRequestDetails
    answer_with(dialog)
    pump(0.2)
    worker.join(5)
    assert not worker.is_alive()
    return result[0]


def yes(_dialog) -> None:
    bridge.answerBuild(True)
    bridge.answerBuild(False)  # the dialog closing afterwards must not change the answer


def no(_dialog) -> None:
    bridge.answerBuild(False)
    bridge.answerBuild(True)


def close_without_button(dialog) -> None:
    QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)


assert ask(yes) == security.BuildDecision(True, "confirmed")
assert ask(no) == security.BuildDecision(False, "declined")
assert ask(close_without_button) == security.BuildDecision(False, "declined")
print("QT_SECURITY_DIALOGS=PASS")
sys.stdout.flush()
os._exit(0)
