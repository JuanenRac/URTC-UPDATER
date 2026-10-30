# =============================================================================
# URTC-UPDATER - tests/test_firmware_sync.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Bringing the firmware of the tool head repository to the Flasher: only what is signed, only after a yes, nothing deleted, off by default."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pytest
from test_flasher_handoff import PUBLIC, sign

from urtc_updater import firmware_sync as fs
from urtc_updater import flasher_handoff as fh
from urtc_updater import main as main_module
from urtc_updater import settings


def write_image(folder: Path, name: str, body: bytes, signed: bool = True) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(body)
    (folder / (name + ".sha256")).write_text(hashlib.sha256(body).hexdigest() + "  " + name, encoding="utf-8")
    (folder / (name + ".manifest.json")).write_text("{}", encoding="utf-8")
    if signed:
        (folder / (name + ".sig")).write_text(sign(fh.release_message(name, hashlib.sha256(body).hexdigest())).hex() + "\n", encoding="ascii")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    source = tmp_path / "URTC" / "firmware"
    write_image(source, "URTC_MAIN_FIRMWARE_v0.4.1.bin", b"main-041" * 20)
    write_image(source, "URTC_MAIN_FIRMWARE_v0.3.9.bin", b"main-039" * 20)
    write_image(source, "URTC_SLAVE_FIRMWARE_v0.2.4.bin", b"slave-024" * 20)
    (source / "firmware_manifest.json").write_text('{"components": {}}', encoding="utf-8")
    target = tmp_path / "URTC-FLASHER" / "firmware"
    write_image(target, "URTC_MAIN_FIRMWARE_v0.3.9.bin", b"main-039" * 20)
    write_image(target, "URTC_SLAVE_FIRMWARE_v0.2.3.bin", b"slave-023" * 20)
    return tmp_path


def test_the_plan_takes_the_newest_signed_image_of_each_kind_with_its_files(workspace):
    work = fs.plan(workspace, PUBLIC)
    assert work.problems == [] and work.refused == []
    assert work.images == ["URTC_MAIN_FIRMWARE_v0.4.1.bin", "URTC_SLAVE_FIRMWARE_v0.2.4.bin"]
    names = sorted(dst.name for _, dst in work.copies)
    assert "URTC_MAIN_FIRMWARE_v0.4.1.bin.sig" in names and "URTC_MAIN_FIRMWARE_v0.4.1.bin.sha256" in names and "firmware_manifest.json" in names
    assert not any("v0.3.9" in name and "SLAVE" not in name for name in names)                       # the older image of the source is not offered
    assert sorted(old.name for old in work.replaced if old.name.endswith(".bin")) == ["URTC_MAIN_FIRMWARE_v0.3.9.bin", "URTC_SLAVE_FIRMWARE_v0.2.3.bin"]
    assert (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").exists() is False  # planning writes nothing


def test_an_image_without_a_valid_release_signature_is_left_out_and_nothing_replaces_its_kind(workspace):
    write_image(workspace / "URTC" / "firmware", "URTC_MAIN_FIRMWARE_v0.4.2.bin", b"unsigned" * 20, signed=False)
    work = fs.plan(workspace, PUBLIC)
    assert work.refused == ["URTC_MAIN_FIRMWARE_v0.4.2.bin: signature_missing"]
    assert work.images == ["URTC_SLAVE_FIRMWARE_v0.2.4.bin"]                                          # the main image is not replaced by an older one by accident
    assert all("MAIN" not in old.name for old in work.replaced)
    (workspace / "URTC" / "firmware" / "URTC_SLAVE_FIRMWARE_v0.2.4.bin").write_bytes(b"edited")      # now the slave image no longer matches its signature either
    again = fs.plan(workspace, PUBLIC)
    assert again.copies == [] and len(again.refused) == 2
    assert fs.describe(again)[-1] == "Nothing can be copied."


def test_apply_copies_the_files_and_moves_the_replaced_images_without_deleting_them(workspace):
    work = fs.plan(workspace, PUBLIC)
    done = fs.apply(workspace, work, now=lambda: 1_700_000_000)
    target = workspace / "URTC-FLASHER" / "firmware"
    assert (target / "URTC_MAIN_FIRMWARE_v0.4.1.bin").read_bytes() == b"main-041" * 20
    assert (target / "URTC_SLAVE_FIRMWARE_v0.2.4.bin.sig").is_file() and (target / "firmware_manifest.json").is_file()
    assert not (target / "URTC_MAIN_FIRMWARE_v0.3.9.bin").exists() and not list(target.glob("*.part"))
    backups = list((workspace / ".urtc-updater" / "firmware-replaced").iterdir())
    assert len(backups) == 1 and (backups[0] / "URTC_MAIN_FIRMWARE_v0.3.9.bin").read_bytes() == b"main-039" * 20
    assert (backups[0] / "URTC_SLAVE_FIRMWARE_v0.2.3.bin").is_file() and any(line.startswith("moved") for line in done)
    assert fs.plan(workspace, PUBLIC).copies == []                                                    # a second run has nothing to do


def test_the_question_comes_first_and_a_no_changes_nothing(workspace, capsys):
    asked = []
    assert fs.run(workspace, ask=lambda prompt: asked.append(prompt) or "n", public_key_hex=PUBLIC) == 1
    assert "Nothing is written to a board" in asked[0] and "Not copied" in capsys.readouterr().out
    assert not (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").exists()
    assert fs.run(workspace, dry_run=True, public_key_hex=PUBLIC) == 0 and "Dry run" in capsys.readouterr().out
    assert not (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").exists()
    assert fs.run(workspace, ask=lambda prompt: "y", public_key_hex=PUBLIC) == 0
    assert (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").is_file()


def test_without_a_terminal_and_without_yes_nothing_is_copied(workspace, monkeypatch):
    monkeypatch.setattr("sys.stdin", type("NoTty", (), {"isatty": lambda self: False})())
    assert fs.run(workspace, public_key_hex=PUBLIC) == 1
    assert not (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").exists()
    assert fs.run(workspace, assume_yes=True, public_key_hex=PUBLIC) == 0


def test_a_missing_flasher_or_an_empty_source_is_said_and_refused(tmp_path, capsys):
    assert fs.run(tmp_path, assume_yes=True) == 1
    assert "not installed" in capsys.readouterr().out
    (tmp_path / "URTC-FLASHER").mkdir()
    (tmp_path / "URTC" / "firmware").mkdir(parents=True)
    assert fs.run(tmp_path, assume_yes=True) == 1
    assert "holds no firmware image" in capsys.readouterr().out


def test_the_option_is_off_by_default_and_the_environment_wins(monkeypatch):
    monkeypatch.delenv(fs.ENV, raising=False)
    monkeypatch.setattr(settings, "load_settings", lambda: {})
    assert fs.enabled() is False
    monkeypatch.setattr(settings, "load_settings", lambda: {fs.SETTING: True})
    assert fs.enabled() is True
    monkeypatch.setenv(fs.ENV, "0")
    assert fs.enabled() is False
    monkeypatch.setattr(settings, "load_settings", lambda: {})
    monkeypatch.setenv(fs.ENV, "1")
    assert fs.enabled() is True


def test_the_offer_after_an_update_applies_only_to_the_tool_head_repository_and_only_when_on(workspace, monkeypatch):
    monkeypatch.delenv(fs.ENV, raising=False)
    monkeypatch.setattr(settings, "load_settings", lambda: {})
    assert fs.offer_after_update(workspace, "URTC", ask=lambda p: pytest.fail("asked")) is None      # off: no offer at all
    monkeypatch.setenv(fs.ENV, "1")
    assert fs.offer_after_update(workspace, "URTC-TESTER", ask=lambda p: pytest.fail("asked")) is None  # another project
    monkeypatch.setattr(fs, "plan", lambda ws, key=None: fs.Plan(ws / "URTC" / "firmware", ws / "URTC-FLASHER" / "firmware", problems=["stop here"]))
    assert fs.offer_after_update(workspace, "URTC") == 1                                                # on: the plan is shown (here it cannot be carried out)


def test_the_command_line_has_the_sync_action():
    parsed = main_module.build_parser().parse_args(["firmware", "sync", "--dry-run", "--yes", "--workspace", "x"])
    assert parsed.firmware_command == "sync" and parsed.dry_run and parsed.yes and parsed.workspace == "x"
    namespace = argparse.Namespace(firmware_command="sync", yes=True, dry_run=True, workspace=None)
    assert hasattr(fh, "cmd_firmware") and namespace.firmware_command == "sync"


def test_the_option_is_saved_and_can_be_switched_off_again(monkeypatch, capsys):
    saved: dict = {}
    monkeypatch.setattr(settings, "save_settings", lambda **updates: saved.update(updates))
    assert fs.cmd_sync(argparse.Namespace(option="on", yes=False, dry_run=False, workspace=None)) == 0
    assert saved == {fs.SETTING: True} and "ON" in capsys.readouterr().out
    assert fs.cmd_sync(argparse.Namespace(option="off", yes=False, dry_run=False, workspace=None)) == 0
    assert saved == {fs.SETTING: False}
