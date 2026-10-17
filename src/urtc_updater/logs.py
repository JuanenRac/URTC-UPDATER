# =============================================================================
# URTC-UPDATER - Log file rotation: logs.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Keeps the folder of window log files from growing without limit.

The window writes one log file per run. This keeps the newest ones and
removes the rest; a file that cannot be removed is simply left."""
from __future__ import annotations

from pathlib import Path

#: How many window log files are kept.
DEFAULT_LOGS_TO_KEEP = 20


def prune_logs(directory: Path, keep: int = DEFAULT_LOGS_TO_KEEP, pattern: str = "gui_*.log") -> list[Path]:
    """Removes the oldest files matching `pattern` in `directory` beyond the
    newest `keep`. Returns the files removed."""
    try:
        files = sorted(
            (path for path in directory.glob(pattern) if path.is_file()),
            key=lambda path: (path.stat().st_mtime, path.name),
            reverse=True,
        )
    except OSError:
        return []
    removed: list[Path] = []
    for path in files[max(keep, 0):]:
        try:
            path.unlink()
        except OSError:
            continue
        removed.append(path)
    return removed
