# =============================================================================
# URTC-UPDATER - Desktop notification: notify.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Best-effort desktop notification for the notify-only check.

Uses the notification tool each system already has (notify-send on Linux,
osascript on macOS, a PowerShell balloon on Windows). It only informs: an
update is never applied by this module, so the rule that nothing changes
without a person approving it stays intact.
"""
from __future__ import annotations

import subprocess
import sys
from typing import Callable

Runner = Callable[..., object]


def _powershell_script(title: str, body: str) -> str:
    def quote(text: str) -> str:
        return "'" + text.replace("'", "''") + "'"

    return (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
        "$n.Visible = $true; "
        f"$n.ShowBalloonTip(10000, {quote(title)}, {quote(body)}, 'Info'); "
        "Start-Sleep -Seconds 11; $n.Dispose()"
    )


def notification_command(title: str, body: str, platform: str | None = None) -> list[str] | None:
    """The command that shows the notification on `platform`, or None."""
    platform = platform or sys.platform
    if platform.startswith("linux"):
        return ["notify-send", title, body]
    if platform == "darwin":
        escaped_body = body.replace("\\", "\\\\").replace('"', '\\"')
        escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')
        return ["osascript", "-e", f'display notification "{escaped_body}" with title "{escaped_title}"']
    if platform.startswith("win"):
        return ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", _powershell_script(title, body)]
    return None


def send_notification(title: str, body: str, *, runner: Runner = subprocess.run, platform: str | None = None) -> bool:
    """True when the notification command ran; False when there is none for
    this system or it could not be started."""
    command = notification_command(title, body, platform)
    if command is None:
        return False
    try:
        runner(command, check=False, timeout=30, capture_output=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return True
