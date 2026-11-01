# =============================================================================
# URTC-UPDATER - The Doctor view of the window: doctor_qt.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The Qt object behind ``DoctorDialog.qml``: the report of ``doctor.py``, the probe of the adapters and the offer to bring the firmware to the Flasher.

The report only reads. The adapters are opened only when the person presses the probe. The firmware is copied only after the person answers the question of
the dialog, never because an option is on: the option (off by default, ``sync_firmware_to_flasher``) only makes the question appear after URTC is updated.
Whatever is decided about the firmware is recorded in the evidence file of the workspace, like an update.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from . import doctor, doctor_texts, firmware_sync, settings

_LANGUAGE_NAMES = {"en": "english", "es": "spanish", "it": "italian", "fr": "french", "de": "german", "zh": "chinese", "ja": "japanese", "pt": "portuguese"}


class DoctorModel(QObject):
    changed = Signal()
    _reportReady = Signal(object)
    offerRequested = Signal()

    def __init__(self, workspace: Callable[[], Path], language_code: Callable[[], str], busy: Callable[[], bool] = lambda: False, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._workspace = workspace
        self._code = language_code
        self._busy_install = busy
        self._checks: list[doctor.Check] = []
        self._probe_done = False
        self._running = False
        self._message = ""
        self._reportReady.connect(self._take)

    # ---- words ----------------------------------------------------------------------------------
    def _language(self) -> str:
        return _LANGUAGE_NAMES.get(self._code(), "english")

    def t(self, key: str) -> str:
        return doctor_texts.text(self._language(), key)

    @Slot(str, result=str)
    def text(self, key: str) -> str:
        return self.t(key)

    # ---- the report -----------------------------------------------------------------------------
    @Property(bool, notify=changed)
    def running(self) -> bool:
        return self._running

    @Property(str, notify=changed)
    def title(self) -> str:
        return self.t("title")

    @Property(str, notify=changed)
    def intro(self) -> str:
        return self.t("intro")

    @Property("QVariantList", notify=changed)
    def lines(self) -> list:
        language = self._language()
        rows: list[dict] = []
        shown: set[str] = set()
        for check in self._checks:
            if check.section not in shown:
                shown.add(check.section)
                rows.append({"header": True, "text": self.t(f"section_{check.section}"), "state": "info", "stateText": ""})
            rows.append({"header": False, "text": check.text(language), "state": check.state, "stateText": self.t(f"state_{check.state}")})
        return rows

    def run_now(self, probe: bool = False) -> None:
        """Make the report in this thread (the window uses ``refresh`` / ``probe``, which do it in another)."""
        self._take((doctor.run_doctor(self._workspace(), self._language(), probe=probe), probe))

    def _start(self, probe: bool) -> None:
        if self._running:
            return
        self._running = True
        self.changed.emit()
        workspace, language = self._workspace(), self._language()

        def work() -> None:
            try:
                checks = doctor.run_doctor(workspace, language, probe=probe)
            except (OSError, ValueError):
                checks = []
            self._reportReady.emit((checks, probe))

        threading.Thread(target=work, daemon=True).start()

    def _take(self, result: object) -> None:
        checks, probe = result
        self._checks, self._probe_done = list(checks), bool(probe)
        self._running = False
        self.changed.emit()

    @Slot()
    def refresh(self) -> None:
        self._start(False)

    @Slot()
    def probe(self) -> None:
        self._start(True)

    @Slot()
    def languageChanged(self) -> None:
        self._start(self._probe_done)

    # ---- the firmware of the Flasher ------------------------------------------------------------
    @Property(bool, notify=changed)
    def syncEnabled(self) -> bool:
        return firmware_sync.enabled()

    @Slot(bool)
    def setSyncEnabled(self, value: bool) -> None:
        settings.save_settings(**{firmware_sync.SETTING: bool(value)})
        self.changed.emit()

    @Property(str, notify=changed)
    def message(self) -> str:
        return self._message

    @Slot(result="QStringList")
    def syncPlanLines(self) -> list[str]:
        """What the copy would do, for the question (read only)."""
        return firmware_sync.describe(firmware_sync.plan(self._workspace()))

    @Property(bool, notify=changed)
    def syncCanRun(self) -> bool:
        if self._busy_install():
            return False
        work = firmware_sync.plan(self._workspace())
        return not work.problems and bool(work.copies)

    @Slot(bool)
    def answerSync(self, yes: bool) -> None:
        """The answer to the question: copy (and record) or leave everything as it is (and record that too)."""
        work = firmware_sync.plan(self._workspace())
        if work.problems or not work.copies:
            self._message = self.t("sync_unavailable").format(reason="; ".join(work.problems) or "-")
        elif not yes:
            firmware_sync.record(self._workspace(), work, "declined: the person did not confirm in the window, nothing was copied", ok=False)
            self._message = self.t("sync_declined")
        else:
            try:
                firmware_sync.apply_recorded(self._workspace(), work)
                self._message = self.t("sync_done")
            except (OSError, ValueError) as exc:
                self._message = self.t("sync_unavailable").format(reason=str(exc))
        self.changed.emit()
        self._start(self._probe_done)

    def offer_after_update(self, project: str) -> bool:
        """After a successful update of URTC: with the option on and something to copy, ask the window to put the question. Returns whether it did."""
        if project != firmware_sync.SOURCE_REPO or not firmware_sync.enabled() or not self.syncCanRun:
            return False
        self.offerRequested.emit()
        return True
