# =============================================================================
# URTC-UPDATER - tests/test_evidence_export_signing.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The export of the attempts as evidence records, signed with the Ed25519 key of the user when asked, and the offline check of one file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from urtc_updater import main as main_module
from urtc_updater import settings
from urtc_updater.evidence import export_common, record_attempt
from urtc_updater.urtc_pkg import evidence, record_signing

SEED = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
OTHER = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
PUBLIC = record_signing.public_key(SEED)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    record_attempt(tmp_path, project="URTC-FLASHER", before={"version": "0.4.0"}, after={"version": "0.4.1"}, ok=True, message="updated")
    record_attempt(tmp_path, project="URTC-TESTER", before={"version": "0.4.1"}, after={"version": "0.4.1"}, ok=False, message="build failed")
    return tmp_path


@pytest.fixture
def key_file(tmp_path: Path, monkeypatch) -> Path:
    path = tmp_path / "keys" / "records.key"
    path.parent.mkdir()
    path.write_text(SEED.hex() + "\n", encoding="ascii")
    monkeypatch.setenv(record_signing.KEY_ENV, str(path))
    return path


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def evidence_args(**extra) -> argparse.Namespace:
    values = dict(workspace=None, export=None, export_common=None, history=None, json=False, sign=False, verify=None, public_key=None)
    values.update(extra)
    return argparse.Namespace(**values)


@pytest.fixture(autouse=True)
def plain_settings(monkeypatch):
    monkeypatch.setattr(settings, "load_settings", lambda: {})


# -- characterization: the export is what it was unless the switch is on ---------------------------------------------------------------------------
def test_the_export_is_not_signed_by_default(workspace, key_file):
    destination = workspace / "out.jsonl"
    assert export_common(workspace, destination) == (2, 0)
    assert all("signature" not in r and evidence.verify(r) == [] for r in lines(destination))


# -- signing ----------------------------------------------------------------------------------------------------------------------------------
def test_with_sign_every_record_carries_the_signature_of_the_key_file(workspace, key_file, capsys):
    destination = workspace / "out.jsonl"
    assert export_common(workspace, destination, sign=True) == (2, 0)
    records = lines(destination)
    assert len(records) == 2 and all(evidence.verify(r) == [] and record_signing.verify_evidence(r, PUBLIC) for r in records)
    assert SEED.hex() not in destination.read_text(encoding="utf-8") and SEED.hex() not in capsys.readouterr().out


def test_the_key_file_of_the_setting_is_used(workspace, tmp_path):
    other = tmp_path / "other.key"
    other.write_text(OTHER.hex() + "\n", encoding="ascii")
    destination = workspace / "out.jsonl"
    export_common(workspace, destination, sign=True, key_file=str(other))
    assert {r["signature"]["public_key"] for r in lines(destination)} == {record_signing.public_key(OTHER).hex()}


def test_a_key_that_cannot_be_used_writes_nothing_and_does_not_show_the_key(workspace, tmp_path, monkeypatch):
    bad = tmp_path / "bad.key"
    bad.write_text("not hexadecimal secret-ish text\n", encoding="ascii")
    monkeypatch.setenv(record_signing.KEY_ENV, str(bad))
    destination = workspace / "out.jsonl"
    with pytest.raises(ValueError) as caught:
        export_common(workspace, destination, sign=True)
    assert "secret-ish" not in str(caught.value) and not destination.exists()


# -- the command line -------------------------------------------------------------------------------------------------------------------------
def test_the_flag_signs_and_says_so_and_the_file_verifies_offline(workspace, key_file, capsys):
    destination = workspace / "out.jsonl"
    assert main_module.cmd_evidence(evidence_args(workspace=str(workspace), export_common=str(destination), sign=True)) == 0
    assert "signed with your Ed25519 key" in capsys.readouterr().out
    assert main_module.cmd_evidence(evidence_args(verify=str(destination), public_key=PUBLIC.hex())) == 0
    out = capsys.readouterr().out
    assert "NOT VALID" not in out and "URTC-FLASHER" in out
    assert main_module.cmd_evidence(evidence_args(verify=str(destination), public_key=record_signing.public_key(OTHER).hex())) == 1


def test_a_file_edited_after_signing_fails_the_check_offline(workspace, key_file):
    destination = workspace / "out.jsonl"
    export_common(workspace, destination, sign=True)
    records = lines(destination)
    records[0]["detail"] = "changed"
    records[0]["evidence_sha256"] = evidence.digest(records[0])        # the digest is fixed, the signature cannot be
    destination.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    assert main_module.cmd_evidence(evidence_args(verify=str(destination))) == 1


def test_an_unsigned_file_verifies_by_its_digest_only(workspace, capsys):
    destination = workspace / "out.jsonl"
    export_common(workspace, destination)
    assert main_module.cmd_evidence(evidence_args(verify=str(destination))) == 0
    records = lines(destination)
    records[0]["outcome"] = "fail"
    destination.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    assert main_module.cmd_evidence(evidence_args(verify=str(destination))) == 1


def test_the_setting_in_the_saved_settings_signs_too(workspace, key_file, monkeypatch, capsys):
    monkeypatch.setattr(settings, "load_settings", lambda: {"sign_evidence": True})
    destination = workspace / "out.jsonl"
    assert main_module.cmd_evidence(evidence_args(workspace=str(workspace), export_common=str(destination))) == 0
    assert all("signature" in r for r in lines(destination))
    monkeypatch.setattr(settings, "load_settings", lambda: {"sign_evidence": "true"})        # anything but the plain true keeps it off
    other = workspace / "plain.jsonl"
    main_module.cmd_evidence(evidence_args(workspace=str(workspace), export_common=str(other)))
    assert all("signature" not in r for r in lines(other))


def test_a_key_that_cannot_be_used_is_an_error_and_writes_no_file(workspace, tmp_path, monkeypatch, capsys):
    bad = tmp_path / "bad.key"
    bad.write_text("nope\n", encoding="ascii")
    monkeypatch.setenv(record_signing.KEY_ENV, str(bad))
    destination = workspace / "out.jsonl"
    assert main_module.cmd_evidence(evidence_args(workspace=str(workspace), export_common=str(destination), sign=True)) == 2
    assert not destination.exists() and "ERROR" in capsys.readouterr().err


def test_verify_and_history_are_two_ways_and_a_missing_file_is_a_usage_error(workspace, capsys):
    assert main_module.cmd_evidence(evidence_args(verify=str(workspace / "x.jsonl"), history=str(workspace))) == 2
    assert main_module.cmd_evidence(evidence_args(verify=str(workspace / "missing.jsonl"))) == 2
    assert main_module.cmd_evidence(evidence_args(verify=str(workspace), public_key="zz")) == 2


def test_the_parser_has_the_new_options():
    parsed = main_module.build_parser().parse_args(["evidence", "--export-common", "x", "--sign", "--verify", "y"])
    assert parsed.sign is True and parsed.verify == "y"
