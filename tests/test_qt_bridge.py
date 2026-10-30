# =============================================================================
# URTC-UPDATER - tests/test_qt_bridge.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
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
from urtc_updater.install import InstallError, InstallResult, UpdatePreview  # noqa: E402
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


def _preview(scripts=()):
    return UpdatePreview(
        commit="0123456789abcdef", author="Someone", version="1.1.0", installed_version="1.0.0",
        signature="not required", changed_scripts=list(scripts), diffstat="",
    )


def test_the_preview_is_shown_in_the_window_language_and_changes_nothing(bridge, monkeypatch):
    monkeypatch.setattr(qt_gui, "preview_update", lambda entry_, root: _preview(["build.sh"]))
    lines = bridge.preview_lines(_local())
    assert "0123456789ab" in lines[0] and "1.0.0 -> 1.1.0" in lines[0]
    assert lines[0].startswith(NAME) and "Someone" in lines[0]
    assert "build.sh" in lines[1]
    assert i18n.TRANSLATIONS["pt"]["log_preview_scripts"].split("{scripts}")[0].format(name=NAME) in lines[1]


def test_a_preview_without_changed_scripts_says_so(bridge, monkeypatch):
    monkeypatch.setattr(qt_gui, "preview_update", lambda entry_, root: _preview())
    lines = bridge.preview_lines(_local())
    assert lines[1] == i18n.TRANSLATIONS["pt"]["log_preview_no_scripts"].format(name=NAME)


def test_a_failed_preview_gives_the_reason_translated(bridge, monkeypatch):
    def fail(entry_, root):
        raise InstallError(coded("not_git", path="x"))

    monkeypatch.setattr(qt_gui, "preview_update", fail)
    lines = bridge.preview_lines(_local())
    assert len(lines) == 1
    assert lines[0].startswith(NAME) and i18n.t("pt", "inst_not_git", path="x") in lines[0]


def test_restore_needs_a_kept_installation_and_reports_the_result(bridge, monkeypatch):
    monkeypatch.setattr(qt_gui, "list_backups", lambda root, name=None: {})
    assert bridge.restore_result(_local()) == [i18n.TRANSLATIONS["pt"]["msg_no_backup"].format(name=NAME)]
    monkeypatch.setattr(qt_gui, "list_backups", lambda root, name=None: {NAME: [Path("kept")]})
    calls = []
    monkeypatch.setattr(qt_gui, "restore_backup", lambda name, root: calls.append(name) or InstallResult(True, "Restored."))
    lines = bridge.restore_result(_local())
    assert calls == [NAME] and lines == [f"{NAME}: Restored."]


def test_the_restore_button_needs_an_installed_project_with_a_kept_installation(bridge, monkeypatch):
    bridge._locals = [_local()]
    bridge._selected = NAME
    monkeypatch.setattr(qt_gui, "list_backups", lambda root, name=None: {})
    assert bridge.canRestore is False
    monkeypatch.setattr(qt_gui, "list_backups", lambda root, name=None: {NAME: [Path("kept")]})
    assert bridge.canRestore is True
    bridge._locals = [_local(installed=False)]
    assert bridge.canRestore is False


# -- the Firmware window: check the signature of an image, open the Flasher with it ------------------------------------------------------------------------


def _signed_image(tmp_path: Path, monkeypatch, signed: bool = True) -> Path:
    import test_flasher_handoff as handoff
    from urtc_updater.urtc_pkg import update_service as svc

    monkeypatch.setattr(svc, "RELEASE_PUBLIC_KEY_HEX", handoff.PUBLIC)
    return handoff._image(tmp_path, signed=signed)


def test_the_firmware_window_confirms_a_signed_image_in_the_language_of_the_window(bridge, tmp_path, monkeypatch):
    image = _signed_image(tmp_path, monkeypatch)
    answer = bridge.firmwareCheck(str(image))
    assert answer == i18n.t("pt", "fw_valid", name=image.name, size=image.stat().st_size, digest=__import__("hashlib").sha256(image.read_bytes()).hexdigest())
    assert "assinatura" in answer
    assert bridge.firmwareCheck(image.as_uri()) == answer  # the chooser gives a file: address


def test_the_firmware_window_refuses_an_unsigned_image_with_its_reason_translated(bridge, tmp_path, monkeypatch):
    image = _signed_image(tmp_path, monkeypatch, signed=False)
    assert bridge.firmwareCheck(str(image)) == i18n.t("pt", "fw_refused", reason=i18n.t("pt", "fw_err_signature_missing"))
    assert bridge.firmwareCheck(str(tmp_path / "nothing.bin")) == i18n.t("pt", "fw_refused", reason=i18n.t("pt", "fw_err_image_missing"))


def test_opening_the_flasher_starts_it_with_the_image_selected_and_never_without_a_valid_signature(bridge, tmp_path, monkeypatch):
    started: list[tuple[object, list[str]]] = []
    done = __import__("threading").Event()

    def fake_launch(root, arguments):
        started.append((root, list(arguments)))
        done.set()
        return 0

    monkeypatch.setattr(qt_gui.launcher, "launch", fake_launch)
    monkeypatch.setattr(qt_gui.launcher, "resolve_entry", lambda root: Path(root) / "run")
    monkeypatch.setattr(qt_gui.flasher_handoff, "root_of", lambda app: tmp_path / "flasher-root")
    image = _signed_image(tmp_path, monkeypatch)
    assert bridge.firmwareOpen(str(image)) == i18n.t("pt", "fw_started", name=image.name)
    assert done.wait(5) and started == [(tmp_path / "flasher-root", ["--firmware", str(image.resolve())])]
    started.clear()
    (tmp_path / "other").mkdir()
    unsigned = _signed_image(tmp_path / "other", monkeypatch, signed=False)
    assert bridge.firmwareOpen(str(unsigned)) == i18n.t("pt", "fw_refused", reason=i18n.t("pt", "fw_err_signature_missing"))
    assert started == []


def test_opening_the_flasher_says_so_when_the_flasher_is_not_installed(bridge, tmp_path, monkeypatch):
    from urtc_updater.urtc_pkg import self_update as su

    def missing(root):
        raise su.UpdateError("no_current_release", "current.txt is missing")

    monkeypatch.setattr(qt_gui.launcher, "resolve_entry", missing)
    monkeypatch.setattr(qt_gui.flasher_handoff, "root_of", lambda app: tmp_path / "none")
    image = _signed_image(tmp_path, monkeypatch)
    assert bridge.firmwareOpen(str(image)) == i18n.t("pt", "fw_refused", reason=i18n.t("pt", "fw_err_flasher"))
