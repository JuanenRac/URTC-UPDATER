# =============================================================================
# URTC-UPDATER - tests/test_qt_bridge.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""The QML bridge's own logic (state per row, checkpoint and failure text in
the window's language), run headless with Qt's offscreen platform. Skipped
where PySide6 is not installed."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from repo_helpers import NAME, entry, manifest_text  # noqa: E402

from urtc_updater import commits, i18n, qt_gui  # noqa: E402
from urtc_updater.detect import LocalStatus  # noqa: E402
from urtc_updater.github_client import RemoteStatus  # noqa: E402
from urtc_updater.install import InstallResult  # noqa: E402
from urtc_updater.messages import coded  # noqa: E402
from urtc_updater.version_parse import Version  # noqa: E402


@pytest.fixture
def bridge(tmp_path: Path, monkeypatch):
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])

    def unavailable():
        raise RuntimeError("offline in tests")

    monkeypatch.setattr(qt_gui, "discover_remote_projects", unavailable)
    monkeypatch.setattr(qt_gui, "fetch_all", lambda entries: {})
    instance = qt_gui.UpdaterBridge(tmp_path)
    instance._lang = "pt"
    return instance


def _local(version: str = "1.0.0", installed: bool = True) -> LocalStatus:
    return LocalStatus(entry=entry(), path=Path("."), installed=installed, version=Version.from_string(version) if installed else None)


def _remote(version: str) -> RemoteStatus:
    return RemoteStatus(entry=entry(), version=Version.from_string(version))


def test_a_row_with_new_commits_at_the_same_version_has_its_own_state():
    assert qt_gui._state_key(_local(), _remote("1.0.0")) == "state_up_to_date"
    assert qt_gui._state_key(_local(), _remote("1.0.0"), commits.NEW_COMMITS) == "state_new_commits"
    assert qt_gui._state_key(_local(), _remote("1.0.0"), commits.AHEAD) == "state_up_to_date"
    assert qt_gui._state_key(_local(), _remote("1.1.0"), commits.NEW_COMMITS) == "state_outdated"
    assert qt_gui._state_key(_local(installed=False), _remote("1.0.0"), commits.NEW_COMMITS) == "state_not_installed"


def test_update_is_offered_for_new_commits_and_counted(bridge):
    bridge._locals = [_local()]
    bridge._remotes = {NAME: _remote("1.0.0")}
    bridge._selected = NAME
    assert bridge.canUpdate is False and bridge.updateCount == 0
    bridge._commits = {NAME: commits.NEW_COMMITS}
    assert bridge.canUpdate is True and bridge.updateCount == 1 and bridge.canUpdateAll is True
    row = bridge.projects[0]
    assert row["stateKey"] == "state_new_commits"
    assert row["state"] == i18n.TRANSLATIONS["pt"]["state_new_commits"]


def test_a_checkpoint_is_shown_in_the_language_of_the_window(bridge):
    bridge._start_operation(False)
    bridge._on_operation_checkpoint("preflight", coded("cp_workspace"), "")
    assert bridge._operation_steps[0]["detail"] == i18n.TRANSLATIONS["pt"]["inst_cp_workspace"]
    bridge._lang = "es"
    bridge._on_operation_checkpoint("source", coded("cp_fetching"), "[2/3] URTC-X: ")
    assert bridge._operation_steps[1]["detail"] == "[2/3] URTC-X: " + i18n.TRANSLATIONS["es"]["inst_cp_fetching"]


def test_a_failure_is_shown_in_the_language_of_the_window(bridge):
    bridge._start_operation(False)
    bridge._finish_operation(False, [InstallResult(False, coded("lock_busy"))])
    failed = next(step for step in bridge._operation_steps if step["state"] == "failed")
    assert failed["detail"] == i18n.TRANSLATIONS["pt"]["inst_lock_busy"]
    assert "instância" in failed["detail"]


def test_plain_text_checkpoints_still_work(bridge):
    bridge._start_operation(False)
    bridge._on_operation_checkpoint("preflight", "plain text", "")
    assert bridge._operation_steps[0]["detail"] == "plain text"


def test_the_unavailable_discovery_message_is_translated(bridge):
    assert i18n.t("pt", "inst_remote_unavailable", error="x") == "Deteção remota indisponível: x"


def test_a_station_profile_limits_the_projects_and_batches(tmp_path: Path, monkeypatch):
    from urtc_updater import settings

    settings.save_settings(profiles={"bench": {"projects": [NAME], "allow_batch": False}}, profile="bench")
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])
    monkeypatch.setattr(qt_gui, "discover_remote_projects", lambda: (_ for _ in ()).throw(RuntimeError("offline in tests")))
    monkeypatch.setattr(qt_gui, "fetch_all", lambda entries: {})
    for folder, version in ((NAME, "1.0.0"), ("URTC-OTHER", "1.0.0")):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "urtc.project.json").write_text(manifest_text(version, folder), encoding="utf-8")
    instance = qt_gui.UpdaterBridge(tmp_path)
    assert [item.entry.name for item in instance._locals] == [NAME]
    assert instance._allowed(NAME) and not instance._allowed("URTC-OTHER")
    instance._locals = [_local(installed=False)]
    assert instance.missingCount == 1 and instance.canInstallAll is False
    instance._busy = False  # the start-up scan is still waiting for an event loop that tests do not run
    instance.performBatch("install", False)
    assert instance._busy is False
    assert instance._activity[-1] == i18n.t(instance._lang, "msg_batch_not_allowed")


def test_without_a_profile_batches_are_allowed(bridge):
    bridge._locals = [_local(installed=False)]
    assert bridge.canInstallAll is True
