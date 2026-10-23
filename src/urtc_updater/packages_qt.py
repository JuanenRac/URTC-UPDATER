# =============================================================================
# URTC-UPDATER - The Packages view of the window: packages_qt.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The Qt objects behind ``PackagesDialog.qml``: the list of the signed packages of the releases and the steps on each of them.

It is the window of what ``urtc-updater --cli package`` does, with the same rules and the same service
(``urtc_pkg/update_service.py``, a copy of the one of URTC-COMMON): one request per check, a download only after a check that found a newer
version, the announced size and SHA-256, the Ed25519 signature of the key of the releases pinned in the program, a safe extraction, the
previous version kept for a rollback. Nothing is checked by itself, nothing is installed without the person saying yes in the dialog, and the
options of security (``update_auto_check``, ``update_require_confirmation``) are the ones of the Check-for-updates window and the settings.
An install is refused while an install or an update of a project runs (``busy``).
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Property, QObject, Signal, Slot

from . import i18n, package
from .urtc_pkg import self_update as su
from .urtc_pkg import update_strings
from .urtc_pkg.update_qt import UpdateModel

_LANGUAGE_NAMES = {"en": "english", "es": "spanish", "it": "italian", "fr": "french", "de": "german", "zh": "chinese", "ja": "japanese", "pt": "portuguese"}
_SETTLED = {"installed", "rolled_back"}


class PackageEntry(UpdateModel):
    """One program of the list: the steps of ``UpdateModel`` (check, download and verify, install, go back) plus what the row shows."""

    rowChanged = Signal()

    def __init__(self, app: str, language_code: Callable[[], str], busy: Callable[[], str | None] | None, parent: QObject | None = None) -> None:
        service = package.make_service(app, busy=busy)
        super().__init__(service, language=lambda: _LANGUAGE_NAMES.get(language_code(), "english"), parent=parent)
        self.app = app
        self._language_code = language_code

    def _take(self, shot: dict) -> None:
        if shot.get("state") in _SETTLED:
            # the version in use changed on disk: the next check compares with it
            self.controller.service.installed = package.installed_version(self.app)
        super()._take(shot)
        self.rowChanged.emit()

    @Slot()
    def languageChanged(self) -> None:
        super().languageChanged()
        self.rowChanged.emit()

    @Property(str, constant=True)
    def appName(self) -> str:
        return self.app

    @Property(str, notify=rowChanged)
    def installedText(self) -> str:
        found = su.current_version(self.controller.service.root)
        return found if found else i18n.t(self._language_code(), "pkg_not_installed")

    @Property(str, notify=rowChanged)
    def keptText(self) -> str:
        try:
            kept = su.installed_versions(self.controller.service.root)
        except OSError:
            kept = []
        return ", ".join(kept) if kept else "-"

    @Property(str, constant=True)
    def folder(self) -> str:
        return str(self.controller.service.root)


class PackagesModel(QObject):
    """The list of ``package.KNOWN_APPS`` with one ``PackageEntry`` each, made when first asked for."""

    changed = Signal()

    def __init__(self, language_code: Callable[[], str], busy: Callable[[], str | None] | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._language_code = language_code
        self._busy = busy
        self._entries: dict[str, PackageEntry] = {}

    @Property("QStringList", constant=True)
    def apps(self) -> list:
        return list(package.KNOWN_APPS)

    @Property("QVariantList", constant=True)
    def entries(self) -> list:
        """The rows of the list, one ``PackageEntry`` per program."""
        return [self.entry(app) for app in package.KNOWN_APPS]

    @Slot(str, result=QObject)
    def entry(self, app: str) -> QObject:
        if app not in package.KNOWN_APPS:
            raise ValueError(f"{app} is not one of: {', '.join(package.KNOWN_APPS)}")
        if app not in self._entries:
            self._entries[app] = PackageEntry(app, self._language_code, self._busy, parent=self)
        return self._entries[app]

    @Slot(str, result=str)
    def t(self, key: str) -> str:
        """A text of the dialog: its own (``pkg_*``) from the table of the window, the words of the update steps (``UPD_*``) from the shared ones."""
        if key.startswith("UPD_"):
            return update_strings.text(_LANGUAGE_NAMES.get(self._language_code(), "english"), key)
        return i18n.t(self._language_code(), key)

    @Slot()
    def languageChanged(self) -> None:
        """The program changed language: the texts of the dialog and of every row are read again."""
        for entry in self._entries.values():
            entry.languageChanged()
        self.changed.emit()
