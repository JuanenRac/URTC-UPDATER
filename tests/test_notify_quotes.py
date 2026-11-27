# =============================================================================
# URTC-UPDATER - tests/test_notify_quotes.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The text of a notification stays text for PowerShell, whatever quotes it holds."""
from __future__ import annotations

import shutil
import subprocess
import sys

import pytest

from urtc_updater import notify

MARKS = ["'", "\u2018", "\u2019", "\u201a", "\u201b"]
HOSTILE = "a'b \u2018c\u2019 d\u201ae\u201bf \u201cg\u201d \u2019); $x = 1; ('"


@pytest.mark.parametrize("mark", MARKS)
def test_every_single_quote_of_powershell_is_written_twice(mark):
    script = notify._powershell_script(f"t{mark}t", f"b{mark}b")
    assert f"'t{mark}{mark}t', 'b{mark}{mark}b', 'Info'" in script


@pytest.mark.skipif(sys.platform != "win32" or not shutil.which("powershell"), reason="needs Windows PowerShell")
def test_powershell_reads_back_the_same_text():
    quoted = notify._powershell_script(HOSTILE, "x").split("ShowBalloonTip(10000, ", 1)[1].split(", 'x', 'Info')", 1)[0]
    done = subprocess.run(["powershell", "-NoProfile", "-Command", f"([int[]][char[]]{quoted}) -join ','"], capture_output=True, text=True, encoding="ascii", timeout=60)
    assert done.returncode == 0, done.stderr
    assert [int(code) for code in done.stdout.strip().split(",")] == [ord(char) for char in HOSTILE]
