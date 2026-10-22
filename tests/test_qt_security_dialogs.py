# =============================================================================
# URTC-UPDATER - tests/test_qt_security_dialogs.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The window's side of the security options: the real Main.qml is loaded (offscreen) with the real bridge, the Security dialog and the question before the build check
are opened, and the answers reach the worker thread that is waiting for them. It runs in its own process (tests/qt_security_dialogs_check.py). Skipped where PySide6 is
not installed."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

ROOT = Path(__file__).resolve().parent.parent


def test_the_security_dialogs_load_open_and_answer_the_waiting_worker():
    environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "qt_security_dialogs_check.py")],
        capture_output=True, text=True, timeout=120, env=environment, check=False,
    )
    assert result.returncode == 0 and "QT_SECURITY_DIALOGS=PASS" in result.stdout, result.stdout + result.stderr
