# =============================================================================
# URTC-COMMON - src/urtc_common/compat_qt.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The Qt object behind ``CompatDialog.qml``: the compatibility matrix against the folders next to the program, in the language it is in.

It only reads. ``refresh`` looks at the workspace again (the window calls it each time it opens).
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from . import compat


class CompatModel(QObject):
    changed = Signal()

    def __init__(self, matrix: dict, workspace: Callable[[], Path], language: Callable[[], str] = lambda: "english", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._matrix = matrix
        self._workspace = workspace
        self._language = language
        self._report: dict | None = None

    def _current(self) -> dict:
        if self._report is None:
            self._report = compat.report(self._matrix, self._workspace(), self._language())
        return self._report

    def _t(self, key: str, **values: object) -> str:
        return compat.text(self._language(), key, **values)

    @Property(str, notify=changed)
    def title(self) -> str:
        return self._t("title")

    @Property(str, notify=changed)
    def intro(self) -> str:
        return self._t("intro", protocol=self._current()["protocol"])

    @Property("QVariantList", notify=changed)
    def headers(self) -> list:
        return [self._t(key) for key in ("project", "expected", "found", "state", "common")]

    @Property("QVariantList", notify=changed)
    def rows(self) -> list:
        return [
            {"repo": row.repo, "expected": row.expected, "found": row.found or "-", "state": row.state, "stateText": self._t(row.state),
             "common": f"{row.common_found or '-'} / {row.common_expected or '-'}", "commonState": row.common_state}
            for row in self._current()["rows"]
        ]

    @Property(str, notify=changed)
    def emptyText(self) -> str:
        return "" if self._current()["any_installed"] else self._t("none_installed")

    @Property(str, notify=changed)
    def firmwareTitle(self) -> str:
        return self._t("firmware")

    @Property("QVariantList", notify=changed)
    def firmwareLines(self) -> list:
        return list(self._current()["firmware"])

    @Property(str, notify=changed)
    def closeText(self) -> str:
        return self._t("close")

    @Slot()
    def refresh(self) -> None:
        self._report = None
        self.changed.emit()

    @Slot()
    def languageChanged(self) -> None:
        self.refresh()
