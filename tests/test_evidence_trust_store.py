# =============================================================================
# URTC-UPDATER - tests/test_evidence_trust_store.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The trust store of public keys (alias -> key in the saved settings) in the history of the updater: ``signed by <alias>``, ``unknown key`` and ``not valid``;
a public key given on the command line wins over the store."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from urtc_updater import main as main_module
from urtc_updater import settings
from urtc_updater.urtc_pkg import evidence, record_signing

SEED = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
OTHER = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
PUB, OTHER_PUB = record_signing.public_key(SEED), record_signing.public_key(OTHER)


def _record(detail: str) -> dict:
    return evidence.build(kind="install", outcome="pass", timestamp_utc="2026-01-02T10:00:00Z", tool="URTC-UPDATER", tool_version="0.2.2", subject={"name": "URTC-FLASHER"}, detail=detail)


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    base = tmp_path / "records"
    base.mkdir()
    for name, item in {"a": record_signing.sign_evidence(_record("a"), SEED), "b": record_signing.sign_evidence(_record("b"), OTHER), "c": _record("c")}.items():
        (base / f"{name}.json").write_text(json.dumps(item), encoding="utf-8")
    return base


def _settings(monkeypatch, data):
    monkeypatch.setattr(settings, "load_settings", lambda: data)


def _args(folder, **extra):
    return argparse.Namespace(workspace=None, export=None, export_common=None, history=str(folder), json=False, **extra)


def test_the_store_comes_from_the_settings_and_names_what_it_leaves_out(monkeypatch):
    _settings(monkeypatch, {"trusted_keys": {"Ana": PUB.hex(), "Bad": "zz"}})
    store, problems = settings.trusted_keys_store()
    assert store == {"Ana": PUB} and len(problems) == 1 and "zz" not in problems[0]
    _settings(monkeypatch, {})
    assert settings.trusted_keys_store() == ({}, [])


def test_without_a_store_the_history_is_as_it_was(folder, monkeypatch, capsys):
    _settings(monkeypatch, {})
    assert main_module.cmd_evidence(_args(folder)) == 0
    assert "trust store" not in capsys.readouterr().out


def test_with_a_store_the_history_counts_trusted_and_unknown_keys(folder, monkeypatch, capsys):
    _settings(monkeypatch, {"trusted_keys": {"Ana": PUB.hex()}})
    assert main_module.cmd_evidence(_args(folder)) == 0                # an unknown key is shown and does not fail the status
    assert "1 signed by a trusted key (Ana), 1 by an unknown key, 0 not valid, 1 unsigned" in capsys.readouterr().out


def test_the_public_key_given_wins_over_the_store(folder, monkeypatch, capsys):
    _settings(monkeypatch, {"trusted_keys": {"Ana": PUB.hex(), "Bea": OTHER_PUB.hex()}})
    assert main_module.cmd_evidence(_args(folder, public_key=PUB.hex())) == 1        # b is by another key than the one given
    assert "trust store" not in capsys.readouterr().out
    assert main_module.cmd_evidence(_args(folder)) == 0
    assert "2 signed by a trusted key (Ana, Bea)" in capsys.readouterr().out


def test_a_bad_public_key_is_a_usage_error(folder, monkeypatch, capsys):
    _settings(monkeypatch, {})
    assert main_module.cmd_evidence(_args(folder, public_key="zz")) == 2
    assert "ERROR" in capsys.readouterr().err


def test_a_forged_signature_fails_the_history(folder, monkeypatch, capsys):
    _settings(monkeypatch, {"trusted_keys": {"Ana": PUB.hex()}})
    path = folder / "a.json"
    forged = json.loads(path.read_text(encoding="utf-8"))
    forged["detail"] = "changed"
    forged["evidence_sha256"] = evidence.digest(forged)
    path.write_text(json.dumps(forged), encoding="utf-8")
    assert main_module.cmd_evidence(_args(folder)) == 1
    assert "1 not valid" in capsys.readouterr().out


def test_a_bad_entry_is_a_warning_and_nothing_is_trusted(folder, monkeypatch, capsys):
    _settings(monkeypatch, {"trusted_keys": {"Ana": "nope"}})
    assert main_module.cmd_evidence(_args(folder)) == 0
    captured = capsys.readouterr()
    assert "WARNING" in captured.err and "nope" not in captured.err and "trusted key" not in captured.out


def test_the_parser_has_the_public_key_option():
    parsed = main_module.build_parser().parse_args(["evidence", "--history", "x", "--public-key", PUB.hex()])
    assert parsed.public_key == PUB.hex()


def test_the_window_has_the_signature_column_with_the_store(folder, monkeypatch):
    pytest.importorskip("PySide6")
    from urtc_updater.urtc_pkg.evidence_history_qt import EvidenceHistoryModel

    _settings(monkeypatch, {"trusted_keys": {"Ana": PUB.hex()}})
    model = EvidenceHistoryModel(lambda: folder, trusted=lambda: settings.trusted_keys_store()[0] or None)
    assert len(model.headers) == 8
    assert {r["signatureText"] for r in model.rows} == {"Signed by Ana", "Valid signature, unknown key", "Not signed"}
