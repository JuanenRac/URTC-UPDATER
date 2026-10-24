# =============================================================================
# URTC-UPDATER - Open the Flasher with a firmware image that was checked: flasher_handoff.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Offer to start the Flasher with a firmware image whose release signature was checked here.

    urtc-updater --cli firmware open URTC_MAIN_FIRMWARE_v1.2.3.bin          # asks, then starts the Flasher with the image selected
    urtc-updater --cli firmware open IMAGE --yes                            # answers the question (for scripts)
    urtc-updater --cli firmware check IMAGE                                 # only the checks

An official image comes with ``<image>.sig``, the Ed25519 signature of the key of the releases (the one pinned in this program) over the
name of the file and its SHA-256. The image is checked before anything is started: a missing or wrong signature is refused, and so is a
file that does not end in ``.bin``. Starting the Flasher is all that is offered. The Flasher then only *selects* the file: nothing is
written to a board until the person connects an adapter, chooses the options and confirms the update in the Flasher itself, which checks
the image again. This program never flashes.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .package import root_of
from .urtc_pkg import launcher
from .urtc_pkg import self_update as su
from .urtc_pkg import update_service as svc

SCHEME = "urtc-rel/1"
FLASHER_APP = "urtc-flasher"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CheckedImage:
    path: Path
    sha256: str
    size: int


def release_message(name: str, digest: str) -> bytes:
    return f"{SCHEME}|{name}|{digest}".encode()


def check_image(path: str | Path, public_key_hex: str | None = None) -> CheckedImage:
    """The image with its SHA-256 when its release signature matches; ``UpdateError`` (with a code) otherwise."""
    image = Path(path)
    if image.suffix.lower() != ".bin":
        raise su.UpdateError("not_an_image", f"{image.name} is not a firmware image (.bin)")
    if not image.is_file():
        raise su.UpdateError("image_missing", f"{image.name} does not exist")
    size = image.stat().st_size
    if size == 0 or size > MAX_IMAGE_BYTES:
        raise su.UpdateError("image_size", f"{image.name} has {size} bytes, not a firmware image")
    sig_path = image.with_name(image.name + ".sig")
    if not sig_path.is_file():
        raise su.UpdateError("signature_missing", f"{image.name} has no release signature ({sig_path.name} next to it)")
    try:
        signature = bytes.fromhex(sig_path.read_text(encoding="ascii").strip())
    except (OSError, ValueError) as error:
        raise su.UpdateError("signature_unreadable", f"{sig_path.name} cannot be read as a signature") from error
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    if not su.ed25519_verify(bytes.fromhex(public_key_hex or svc.RELEASE_PUBLIC_KEY_HEX), release_message(image.name, digest), signature):
        raise su.UpdateError("signature_bad", f"{image.name} does not match its release signature")
    return CheckedImage(image.resolve(), digest, size)


def _confirm(prompt: str, assume_yes: bool, ask: Callable[[str], str] | None) -> bool:
    if assume_yes:
        return True
    if ask is None:
        if not sys.stdin.isatty():
            print("Not started: confirm in a terminal, or repeat the command with --yes.", file=sys.stderr)
            return False
        ask = input
    return ask(prompt).strip().lower() in {"y", "yes"}


def cmd_firmware(
    args: argparse.Namespace,
    ask: Callable[[str], str] | None = None,
    start: Callable[..., int] | None = None,
) -> int:
    """``firmware check IMAGE`` and ``firmware open IMAGE``. ``start`` replaces the launcher (tests)."""
    try:
        checked = check_image(args.image)
    except su.UpdateError as error:
        print(f"FIRMWARE=FAIL {error.code}: {error}", file=sys.stderr)
        return 1
    print(f"{checked.path.name}: {checked.size} bytes, SHA-256 {checked.sha256}")
    print("Release signature: valid (the key of the releases pinned in this program).")
    if args.firmware_command == "check":
        return 0
    prompt = (
        f"Open the Flasher with {checked.path.name} selected? Nothing is written to a board: in the Flasher you connect, "
        "choose the options and confirm the update yourself. [y/N] "
    )
    if not _confirm(prompt, args.yes, ask):
        print("Not started. Nothing was changed.")
        return 1
    root = root_of(FLASHER_APP)
    try:
        if start is None:
            return launcher.launch(root, ["--firmware", str(checked.path)])
        return start(root, ["--firmware", str(checked.path)])
    except su.UpdateError as error:
        print(f"FIRMWARE=FAIL {error.code}: {error} (install the Flasher first: urtc-updater --cli package install {FLASHER_APP})", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"FIRMWARE=FAIL start: {error}", file=sys.stderr)
        return 1


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Adds ``firmware`` and its two actions to the command line."""
    firmware_p = subparsers.add_parser("firmware", help="Check the release signature of a firmware image and offer to open the Flasher with it (check, open).")
    firmware_p.set_defaults(func=cmd_firmware)
    actions = firmware_p.add_subparsers(dest="firmware_command", required=True)
    actions.add_parser("check", help="Check the .sig next to the image; nothing is started.").add_argument("image")
    open_p = actions.add_parser("open", help="Check the image, ask, and start the installed Flasher with the image selected (it never flashes by itself).")
    open_p.add_argument("image")
    open_p.add_argument("--yes", "-y", action="store_true", help="Answer the question with yes (for scripts). The Flasher still asks before it writes.")
