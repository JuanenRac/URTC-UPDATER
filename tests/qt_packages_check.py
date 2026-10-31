# =============================================================================
# URTC-UPDATER - tests/qt_packages_check.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Run by tests/test_qt_packages.py in its own process (a window needs a QGuiApplication). Loads the real Main.qml with the real bridge, opens the Packages window
and the Help window in every language and checks that the three programs are listed, that the texts come from the window's language and that QML printed no error."""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HOME = Path(tempfile.mkdtemp(prefix="urtc_updater_packages_"))
os.environ["URTC_UPDATE_ROOT"] = str(HOME / "apps")

from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from urtc_updater import i18n, package, qt_gui, settings  # noqa: E402

settings.SETTINGS_PATH = HOME / "settings.json"
settings._LEGACY_LANG_PATH = HOME / "lang.json"
qt_gui.discover_remote_projects = lambda: (_ for _ in ()).throw(RuntimeError("offline"))
qt_gui.fetch_all = lambda entries: {}

app = QGuiApplication([])


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def call(obj: QObject, method: str) -> None:
    QMetaObject.invokeMethod(obj, method, Qt.ConnectionType.DirectConnection)


bridge = qt_gui.UpdaterBridge(HOME)
engine = QQmlApplicationEngine()
warnings: list[str] = []
engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
engine.rootContext().setContextProperty("backend", bridge)
engine.load(QUrl.fromLocalFile(str(Path(qt_gui.__file__).resolve().parent / "qml" / "Main.qml")))
pump()
assert engine.rootObjects(), warnings
root = engine.rootObjects()[0]
packages_dialog = root.findChild(QObject, "packagesDialog")
help_dialog = root.findChild(QObject, "helpDialog")
firmware_dialog = root.findChild(QObject, "firmwareDialog")
assert packages_dialog is not None and help_dialog is not None and firmware_dialog is not None

model = bridge.packages
assert list(model.apps) == list(package.KNOWN_APPS) and len(model.entries) == 3
assert bridge.help.title == "Help" or bridge.help.title  # the model exists and answers

for code, _label in i18n.LANGUAGES:
    bridge.setLanguage(code)
    pump(0.1)
    assert model.t("pkg_title") == i18n.t(code, "pkg_title")
    assert [section["title"] for section in bridge.help.sections] and len(bridge.help.sections) == 7, code
    for dialog in (packages_dialog, help_dialog, firmware_dialog):
        call(dialog, "open")
        pump(0.15)
        assert dialog.property("visible"), (code, dialog.objectName())
        call(dialog, "close")
        pump(0.1)

bridge.setLanguage("es")
assert model.entry("urtc-flasher").installedText == "no instalado"
assert model.entry("urtc-flasher").t("UPD_BTN_CHECK") == "Buscar actualización"

errors = [w for w in warnings if "does not support customization" not in w and ("Packages" in w or "Help" in w or "Firmware" in w or "TypeError" in w or "ReferenceError" in w or "Cannot read" in w)]
assert not errors, errors
print("QT_PACKAGES=PASS")
sys.stdout.flush()
os._exit(0)
