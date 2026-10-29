# =============================================================================
# URTC-UPDATER - update attempt evidence tests
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
from __future__ import annotations

import json
from pathlib import Path

from urtc_updater import install as install_module
from urtc_updater.evidence import (
    EVIDENCE_DIRECTORY,
    export_common,
    installed_state,
    read_attempts,
    record_attempt,
)


def test_an_attempt_is_recorded_with_before_and_after(tmp_path: Path) -> None:
    path = record_attempt(
        tmp_path,
        project="HYDRA-UMC-X",
        before={"version": "0.1.0", "commit": "aaa"},
        after={"version": "0.1.1", "commit": "bbb"},
        ok=True,
        message="updated",
    )
    assert path is not None and path.parent.name == EVIDENCE_DIRECTORY
    (line,) = read_attempts(tmp_path)
    assert line["versionBefore"] == "0.1.0" and line["versionAfter"] == "0.1.1"
    assert line["commitBefore"] == "aaa" and line["commitAfter"] == "bbb"
    assert line["ok"] is True


def test_attempts_accumulate_and_a_failed_one_keeps_its_reason(tmp_path: Path) -> None:
    record_attempt(tmp_path, project="p", before={}, after={}, ok=True, message="one")
    record_attempt(tmp_path, project="p", before={"version": "1.0.0"}, after={"version": "1.0.0"}, ok=False, message="build failed")
    attempts = read_attempts(tmp_path)
    assert [a["ok"] for a in attempts] == [True, False]
    assert attempts[1]["message"] == "build failed"


def test_recording_never_raises_when_the_workspace_is_not_writable(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    assert record_attempt(blocker, project="p", before={}, after={}, ok=True, message="m") is None


def test_installed_state_reads_the_manifest_and_tolerates_a_missing_checkout(tmp_path: Path) -> None:
    assert installed_state(tmp_path / "absent") == {"version": None, "commit": None}
    project = tmp_path / "proj"
    project.mkdir()
    (project / "urtc.project.json").write_text(json.dumps({"version": "0.4.2"}), encoding="utf-8")
    assert installed_state(project)["version"] == "0.4.2"


def test_install_or_update_leaves_evidence_of_a_failed_attempt(tmp_path: Path, monkeypatch) -> None:
    class Entry:
        name = "HYDRA-UMC-DEMO"

    monkeypatch.setattr(install_module, "recover_interrupted_promotions", lambda root: [])
    monkeypatch.setattr(
        install_module, "clone_or_pull", lambda entry, root, **kw: install_module.InstallResult(False, "clone refused")
    )
    results = install_module.install_or_update(Entry(), tmp_path)
    assert not results[0].ok
    (line,) = read_attempts(tmp_path)
    assert line["project"] == "HYDRA-UMC-DEMO" and line["ok"] is False
    assert "clone refused" in line["message"]

def test_the_attempts_can_be_exported_in_the_shape_the_other_programs_use(tmp_path: Path) -> None:
    from urtc_updater.urtc_pkg import evidence as common

    record_attempt(tmp_path, project="URTC-FLASHER", before={"version": "0.4.0", "commit": "a" * 40}, after={"version": "0.4.1", "commit": "b" * 40}, ok=True, message="updated")
    record_attempt(tmp_path, project="URTC-TESTER", before={"version": "0.4.1"}, after={"version": "0.4.1"}, ok=False, message="build failed")
    destination = tmp_path / "out" / "evidence.jsonl"
    assert export_common(tmp_path, destination) == (2, 0)
    records = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
    assert [r["outcome"] for r in records] == ["pass", "fail"] and all(common.verify(r) == [] for r in records)
    assert records[0]["kind"] == "install" and records[0]["subject"]["version_after"] == "0.4.1" and records[0]["tool"] == "URTC Updater"
    assert records[1]["detail"] == "build failed"


def test_a_line_that_does_not_fit_the_shape_is_left_out_and_counted(tmp_path: Path) -> None:
    folder = tmp_path / EVIDENCE_DIRECTORY
    folder.mkdir()
    (folder / "evidence.jsonl").write_text('{"project": "old", "ok": true}\n{"timestamp": "2026-01-02T03:04:05+00:00", "updaterVersion": "0.1.8", "project": "p", "ok": true, "message": "m"}\n', encoding="utf-8")
    destination = tmp_path / "e.jsonl"
    assert export_common(tmp_path, destination) == (1, 1)
    assert len(destination.read_text(encoding="utf-8").splitlines()) == 1


def test_exporting_nothing_writes_an_empty_file(tmp_path: Path) -> None:
    destination = tmp_path / "e.jsonl"
    assert export_common(tmp_path, destination) == (0, 0)
    assert destination.read_text(encoding="utf-8") == ""
