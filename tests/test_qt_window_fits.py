# =============================================================================
# URTC Updater - the Qt Quick window fits its window: no control is cut off at the right edge, in any of the eight languages
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""A row that cannot wrap makes the window layout as wide as that row, and the buttons at its end - Help and About among them - stay beyond the right
edge. Each language is loaded in its own process, headless, with GitHub not asked."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    import PySide6
except ImportError:  # PySide6 is not installed
    PySide6 = None

LANGUAGES = ("en", "es", "de", "fr", "it", "ja", "zh", "pt")

PROBE = r"""
import os, sys, tempfile, time
from pathlib import Path
root_folder, language = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root_folder, "src"))
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from urtc_updater import github_client, i18n, qt_gui, settings
scratch = Path(os.getcwd())
settings.SETTINGS_PATH = scratch / "s.json"
settings._LEGACY_LANG_PATH = scratch / "l.json"
github_client.REPO_LIST_CACHE_PATH = scratch / "c.json"
qt_gui.LOGS_DIR = scratch / "logs"
class Offline(qt_gui.UpdaterBridge):
    def refresh(self, offline):
        super().refresh(True)
QQuickStyle.setStyle("Basic")
app = QGuiApplication([])
i18n.save_lang_preference(language)
(scratch / "workspace").mkdir()
bridge = Offline(Path("workspace"))
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("backend", bridge)
engine.load(QUrl.fromLocalFile(os.path.join(root_folder, "src", "urtc_updater", "qml", "Main.qml")))
if not engine.rootObjects():
    raise SystemExit("the window did not load")
window = engine.rootObjects()[0]
window.setVisibility(QWindow.Visibility.Windowed)


def pump(seconds):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def cut(item, found):
    if not item.isVisible():
        return
    right = item.mapToScene(item.boundingRect().topRight()).x()
    if right > window.width() + 1:
        text = item.property("text")
        found.append("%s right=%d %s" % (item.metaObject().className().split("_QML")[0], right, ascii(text[:40]) if isinstance(text, str) else ""))
        return
    for child in item.childItems():
        cut(child, found)


problems = []
for width in (1100, 1500, 1920):  # the smallest and the starting width of the window, and a full screen
    window.setWidth(width)
    window.setHeight(900)
    pump(0.6)
    found = []
    cut(window.contentItem(), found)
    if found:
        problems.append("width %d: %d cut off, first %s" % (width, len(found), found[:4]))
print("\n".join(problems) or "FITS")
sys.stdout.flush()
os._exit(0)
"""


@unittest.skipIf(PySide6 is None, "PySide6 is not available")
class WindowFitsTests(unittest.TestCase):
    def test_no_control_is_cut_off_in_any_language(self):
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONDONTWRITEBYTECODE="1")
        if sys.platform == "win32":  # an offscreen Qt has no fonts of its own there
            env.setdefault("QT_QPA_FONTDIR", os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Fonts"))
        for language in LANGUAGES:
            with self.subTest(language=language), tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
                result = subprocess.run([sys.executable, "-c", PROBE, str(ROOT), language], cwd=folder, env=env, capture_output=True, text=True, timeout=120)
                self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                self.assertEqual(result.stdout.strip(), "FITS")


if __name__ == "__main__":
    unittest.main()
