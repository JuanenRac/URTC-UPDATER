#!/usr/bin/env python3
# =============================================================================
# URTC-UPDATER - tools/capture_screens.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Takes the pictures of the window that docs/WINDOW_GUIDE.md shows: the real Qt Quick window, loaded without a screen
(``QT_QPA_PLATFORM=offscreen``) and drawn to a PNG with ``grabWindow``. Nothing is installed, nothing goes over the network and no file
of the person is read or written: the window looks at an empty workspace and keeps its settings in a folder that is thrown away.

    python tools/capture_screens.py                          # docs/screenshots/updater-deck.png, -help.png, -updates.png and -packages.png
    python tools/capture_screens.py --readme                 # the pictures of the README: images/screenshots/<screen>.png at 1920x1080
    python tools/capture_screens.py --out DIR                # another folder
    python tools/capture_screens.py --language german        # the same pictures in German: updater-deck-de.png ...
    python tools/capture_screens.py --all-languages          # the English ones and those of the seven other languages

The pictures use the Basic style of Qt Quick Controls, the one the program runs with, and, on Windows, the fonts of the system (an offscreen Qt
has none of its own there).
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_FONTDIR", os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Fonts"))

SIZE = (1500, 900)  # the default size of the window
# the code the program stores -> the suffix of the picture (English has none)
LANGUAGE_SUFFIX = {"en": "", "es": "-es", "de": "-de", "fr": "-fr", "it": "-it", "ja": "-ja", "zh": "-zh", "pt": "-pt"}
LANGUAGE_NAME = {"en": "english", "es": "spanish", "de": "german", "fr": "french", "it": "italian", "ja": "japanese", "zh": "chinese", "pt": "portuguese"}
DIALOGS = (("helpDialog", "help"), ("updateDialog", "updates"), ("packagesDialog", "packages"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "docs" / "screenshots"))
    parser.add_argument("--readme", action="store_true", help="the pictures of the README: 1920x1080, in images/screenshots/, named after the screen only")
    parser.add_argument("--language", choices=sorted(LANGUAGE_NAME.values()), default="english", help="the interface language of the pictures")
    parser.add_argument("--all-languages", action="store_true", help="one run per language (each in its own process)")
    args = parser.parse_args(argv)
    if args.all_languages:
        import subprocess

        for name in LANGUAGE_NAME.values():
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--language", name, "--out", args.out], check=False)
            if result.returncode != 0:
                return result.returncode
        return 0
    code = next(code for code, name in LANGUAGE_NAME.items() if name == args.language)
    sys.path.insert(0, str(ROOT / "src"))
    scratch = Path(tempfile.mkdtemp(prefix="urtc_capture_"))
    os.chdir(scratch)  # whatever the program writes next to where it runs does not go into the repository
    workspace = scratch / "workspace"
    workspace.mkdir()
    if args.readme:
        # the pictures of the README show a workspace with the family in it: the manifests of the sibling repositories are copied in (nothing else of them)
        for manifest in sorted(ROOT.parent.glob("URTC-*/urtc.project.json")):
            (workspace / manifest.parent.name).mkdir()
            (workspace / manifest.parent.name / "urtc.project.json").write_bytes(manifest.read_bytes())

    from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
    from PySide6.QtGui import QGuiApplication, QWindow
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtQuickControls2 import QQuickStyle

    from urtc_updater import github_client, i18n, qt_gui, settings

    # the settings, the language choice and the repository cache of the person are neither read nor written; the network is not touched
    settings.SETTINGS_PATH = scratch / ".urtc_updater_settings.json"
    settings._LEGACY_LANG_PATH = scratch / ".urtc_updater_lang.json"
    github_client.REPO_LIST_CACHE_PATH = scratch / ".urtc_updater_repo_cache.json"
    qt_gui.LOGS_DIR = scratch / "logs"

    class OfflineBridge(qt_gui.UpdaterBridge):
        """The window as it opens with the box "Offline" ticked: it scans the workspace and asks GitHub nothing."""

        def refresh(self, offline: bool) -> None:
            super().refresh(True)

    QQuickStyle.setStyle("Basic")
    app = QGuiApplication([])
    i18n.save_lang_preference(code)  # chosen before the window exists, so its first lines of the log are already in that language
    bridge = OfflineBridge(Path("workspace"))  # a relative name: the picture does not show where the folder of the person is
    assert bridge._lang == code
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", bridge)
    engine.load(QUrl.fromLocalFile(str(ROOT / "src" / "urtc_updater" / "qml" / "Main.qml")))
    if not engine.rootObjects():
        print("CAPTURE=FAIL the window did not load", file=sys.stderr)
        return 1
    root = engine.rootObjects()[0]

    def pump(seconds: float) -> None:
        end = time.time() + seconds
        while time.time() < end:
            app.processEvents()
            time.sleep(0.01)

    root.setVisibility(QWindow.Visibility.Windowed)
    size = (1920, 1080) if args.readme else SIZE
    root.setWidth(size[0])
    root.setHeight(size[1])
    pump(1.0)
    out = Path(args.out) if not args.readme or args.out != str(ROOT / "docs" / "screenshots") else ROOT / "images" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    written = []

    def shot(label: str) -> None:
        image = QQuickWindow.grabWindow(root)
        path = out / (f"{label}.png" if args.readme else f"updater-{label}{LANGUAGE_SUFFIX[code]}.png")
        if not image.save(str(path)):
            raise SystemExit(f"CAPTURE=FAIL could not write {path}")
        written.append(path.name)

    shot("deck")
    for dialog_name, label in DIALOGS:
        dialog = root.findChild(QObject, dialog_name)
        if dialog is None:
            raise SystemExit(f"CAPTURE=FAIL no {dialog_name} in the window")
        QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
        pump(0.8)
        shot(label)
        QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)
        pump(0.3)
    print("CAPTURE=PASS " + ", ".join(written))
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
