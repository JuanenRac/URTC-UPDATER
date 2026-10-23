# =============================================================================
# URTC-UPDATER - tests/test_common_copy.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The update modules and the dialog are copies of URTC-COMMON: nobody edits them by hand, and they do not fall behind the shared repository when it is next to this one."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
COMMON = ROOT.parent / "URTC-COMMON"
LOCKS = (
    ROOT / "src" / "urtc_updater" / "urtc_pkg" / "urtc_common.lock.json",
    ROOT / "src" / "urtc_updater" / "qml" / "urtc_common.lock.json",
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@pytest.mark.parametrize("lock_path", LOCKS, ids=lambda path: path.parent.name)
def test_a_copied_file_is_not_edited_by_hand(lock_path):
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["files"], "the lock lists no file"
    for name, expected in lock["files"].items():
        assert _digest(lock_path.parent / name) == expected["sha256"], f"{name} differs from the lock: sync it again instead of editing it"


@pytest.mark.parametrize("lock_path", LOCKS, ids=lambda path: path.parent.name)
def test_the_copies_have_not_fallen_behind_the_shared_repository(lock_path):
    if not COMMON.is_dir():
        pytest.skip("URTC-COMMON is not next to this repository")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    for name, entry in lock["files"].items():
        assert _digest(lock_path.parent / name) == _digest(COMMON / entry["from"]), f"{name} fell behind URTC-COMMON: run vendor_copy.py sync again"
