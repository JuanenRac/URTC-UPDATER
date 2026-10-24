# =============================================================================
# URTC-UPDATER - tests/test_flasher_handoff.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Opening the Flasher with a firmware image whose release signature was checked: the checks, the question, and that nothing is flashed."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pytest

from urtc_updater import flasher_handoff as fh
from urtc_updater import main as main_module
from urtc_updater.urtc_pkg import self_update as su
from urtc_updater.urtc_pkg import update_service as svc

_P, _Q = su._P, su._Q
SEED = bytes(range(32, 64))


def _compress(point) -> bytes:
    x, y, z, _ = point
    zi = pow(z, _P - 2, _P)
    x, y = x * zi % _P, y * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _expand(seed: bytes):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def sign(message: bytes) -> bytes:
    a, prefix = _expand(SEED)
    public = _compress(su._mul(a, su.BASE_POINT))
    r = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _Q
    r_bytes = _compress(su._mul(r, su.BASE_POINT))
    k = int.from_bytes(hashlib.sha512(r_bytes + public + message).digest(), "little") % _Q
    return r_bytes + ((r + k * a) % _Q).to_bytes(32, "little")


PUBLIC = _compress(su._mul(_expand(SEED)[0], su.BASE_POINT)).hex()
BODY = b"\x00\x20\x00\x20" + bytes(range(200))


@pytest.fixture(autouse=True)
def pinned_key(monkeypatch):
    monkeypatch.setattr(svc, "RELEASE_PUBLIC_KEY_HEX", PUBLIC)


def _image(tmp_path: Path, name: str = "URTC_MAIN_FIRMWARE_v1.2.3.bin", body: bytes = BODY, signed: bool = True) -> Path:
    path = tmp_path / name
    path.write_bytes(body)
    if signed:
        digest = hashlib.sha256(body).hexdigest()
        (tmp_path / (name + ".sig")).write_text(sign(fh.release_message(name, digest)).hex() + "\n", encoding="ascii")
    return path


def _args(command: str, image: Path, yes: bool = False) -> argparse.Namespace:
    return argparse.Namespace(firmware_command=command, image=str(image), yes=yes)


def test_a_signed_image_is_accepted_with_its_hash(tmp_path):
    checked = fh.check_image(_image(tmp_path))
    assert checked.sha256 == hashlib.sha256(BODY).hexdigest() and checked.size == len(BODY)


@pytest.mark.parametrize("what", ["unsigned", "edited", "renamed", "other_key", "not_bin", "missing", "empty", "garbage_sig"])
def test_every_other_image_is_refused_with_a_code(tmp_path, what):
    image = _image(tmp_path, signed=what != "unsigned")
    expected = {"unsigned": "signature_missing", "edited": "signature_bad", "renamed": "signature_bad", "other_key": "signature_bad",
                "not_bin": "not_an_image", "missing": "image_missing", "empty": "image_size", "garbage_sig": "signature_unreadable"}[what]
    if what == "edited":
        image.write_bytes(BODY + b"x")
    elif what == "renamed":
        renamed = tmp_path / "URTC_MAIN_FIRMWARE_v9.9.9.bin"
        image.rename(renamed)
        (tmp_path / (image.name + ".sig")).rename(tmp_path / (renamed.name + ".sig"))
        image = renamed
    elif what == "other_key":
        svc.RELEASE_PUBLIC_KEY_HEX = "00" * 31 + "01"  # another key is pinned; the fixture puts the real one back
    elif what == "not_bin":
        image = image.rename(tmp_path / "image.hex")
    elif what == "missing":
        image = tmp_path / "gone.bin"
    elif what == "empty":
        image.write_bytes(b"")
    elif what == "garbage_sig":
        (tmp_path / (image.name + ".sig")).write_text("not hex", encoding="ascii")
    with pytest.raises(su.UpdateError) as caught:
        fh.check_image(image)
    assert caught.value.code == expected


def test_open_asks_and_starts_the_flasher_with_the_image_only_after_a_yes(tmp_path, capsys):
    image = _image(tmp_path)
    started = []
    asked = []
    code = fh.cmd_firmware(_args("open", image), ask=lambda prompt: asked.append(prompt) or "y", start=lambda root, arguments: started.append((root, arguments)) or 0)
    assert code == 0 and started and started[0][1] == ["--firmware", str(image.resolve())]
    assert "Nothing is written to a board" in asked[0] and "signature: valid" in capsys.readouterr().out
    started.clear()
    assert fh.cmd_firmware(_args("open", image), ask=lambda prompt: "n", start=lambda *a: started.append(a) or 0) == 1 and not started


def test_open_without_a_terminal_and_without_yes_starts_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin", type("NoTerminal", (), {"isatty": lambda self: False})())
    started = []
    assert fh.cmd_firmware(_args("open", _image(tmp_path)), start=lambda *a: started.append(a) or 0) == 1 and not started
    assert fh.cmd_firmware(_args("open", _image(tmp_path), yes=True), start=lambda *a: started.append(a) or 0) == 0 and started


def test_check_only_never_starts_and_a_refused_image_never_asks(tmp_path, capsys):
    image = _image(tmp_path)
    assert fh.cmd_firmware(_args("check", image), start=lambda *a: pytest.fail("started")) == 0
    unsigned = _image(tmp_path, "URTC_X.bin", signed=False)
    assert fh.cmd_firmware(_args("open", unsigned, yes=True), ask=lambda p: pytest.fail("asked"), start=lambda *a: pytest.fail("started")) == 1
    assert "signature_missing" in capsys.readouterr().err


def test_a_flasher_that_is_not_installed_is_explained(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("URTC_UPDATE_ROOT", str(tmp_path / "nothing"))
    assert fh.cmd_firmware(_args("open", _image(tmp_path), yes=True)) == 1
    assert "package install urtc-flasher" in capsys.readouterr().err


def test_the_command_is_part_of_the_command_line(tmp_path):
    image = _image(tmp_path)
    parser = main_module.build_parser()
    args = parser.parse_args(["firmware", "check", str(image)])
    assert args.func is fh.cmd_firmware and args.firmware_command == "check"
    assert parser.parse_args(["firmware", "open", str(image), "--yes"]).yes is True
