# =============================================================================
# URTC-UPDATER - Bring the firmware of the tool head repository to the Flasher: firmware_sync.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Offer to copy the firmware images of the tool head repository (URTC) into the folder of the Flasher.

    urtc-updater --cli firmware sync                # shows what would be copied, asks, copies
    urtc-updater --cli firmware sync --dry-run      # only shows it
    urtc-updater --cli firmware sync --yes          # answers the question (for scripts)

The Flasher carries the firmware it flashes. After the tool head repository is updated, the images in its ``firmware`` folder are newer than the ones
the Flasher carries (``compat`` shows it). This copies the newest image of each kind (main and slave, application and bootloader) with the files that
travel with it, and it refuses anything it cannot prove: an image whose release signature does not match the key of the releases pinned in this program
is left out and said so, and nothing is copied for it. The images the Flasher already carried and that are replaced are not deleted: they are moved to
``.urtc-updater/firmware-replaced/<time>`` of the workspace. Nothing is written to a board, and the Flasher checks every image again before it flashes.

The option ``sync_firmware_to_flasher`` of the settings (or ``URTC_UPDATER_SYNC_FIRMWARE=1``) makes ``update`` of the tool head repository offer this at the
end. It is OFF by default, and the offer is always a question: without a person to answer (or ``--yes``) nothing is copied.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from . import settings
from .flasher_handoff import check_image
from .urtc_pkg import firmware_names
from .urtc_pkg import self_update as su

SOURCE_REPO = "URTC"
TARGET_REPO = "URTC-FLASHER"
FOLDER = "firmware"
SETTING = "sync_firmware_to_flasher"
ENV = "URTC_UPDATER_SYNC_FIRMWARE"
SET_FILES = ("firmware_manifest.json", "firmware_manifest.json.sig")
REPLACED_FOLDER = Path(".urtc-updater") / "firmware-replaced"


def enabled() -> bool:
    """Is the offer after an update of the tool head repository switched on? Off unless the settings or the environment say so (the environment wins)."""
    value = os.environ.get(ENV, "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return settings.load_settings().get(SETTING) is True


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


@dataclass
class Plan:
    """What a synchronisation would do. ``problems`` is empty when it can be carried out; ``copies`` may still be empty (nothing to do)."""

    source: Path
    target: Path
    copies: list[tuple[Path, Path]] = field(default_factory=list)
    replaced: list[Path] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)

    @property
    def images(self) -> list[str]:
        return sorted({src.name for src, _ in self.copies if firmware_names.parse_image_name(src.name)})


def plan(workspace: Path, public_key_hex: str | None = None) -> Plan:
    """Compare the firmware folder of the tool head repository with the one of the Flasher. Reads only."""
    source = workspace / SOURCE_REPO / FOLDER
    target = workspace / TARGET_REPO / FOLDER
    result = Plan(source, target)
    if not (workspace / TARGET_REPO).is_dir():
        result.problems.append(f"{TARGET_REPO} is not installed in the workspace")
    if not source.is_dir():
        result.problems.append(f"{SOURCE_REPO} has no {FOLDER} folder in the workspace")
    if result.problems:
        return result
    newest: dict[tuple[str, str], tuple[tuple[int, ...], Path]] = {}
    for item in sorted(source.iterdir()):
        parsed = firmware_names.parse_image_name(item.name)
        if parsed and item.is_file():
            key, version = parsed[:2], _version(parsed[2])
            if key not in newest or version > newest[key][0]:
                newest[key] = (version, item)
    if not newest:
        result.problems.append(f"{SOURCE_REPO}/{FOLDER} holds no firmware image")
        return result
    chosen: list[Path] = []
    for key in sorted(newest):
        image = newest[key][1]
        try:
            check_image(image, public_key_hex)
        except su.UpdateError as error:
            result.refused.append(f"{image.name}: {error.code}")
            continue
        chosen.append(image)
    for image in chosen:
        for name in sorted(path.name for path in source.iterdir() if path.is_file() and path.name.startswith(image.name)):
            _consider(result, source / name, target / name)
    if chosen:
        for name in SET_FILES:
            if (source / name).is_file():
                _consider(result, source / name, target / name)
    kept = {dst.name for _, dst in result.copies} | set(result.unchanged)
    wanted_kinds = {parsed[:2] for image in chosen if (parsed := firmware_names.parse_image_name(image.name))}
    if target.is_dir():
        for item in sorted(target.iterdir()):
            parsed = firmware_names.parse_image_name(item.name.split(".bin")[0] + ".bin") if ".bin" in item.name else None
            if parsed and parsed[:2] in wanted_kinds and item.name not in kept and item.is_file():
                result.replaced.append(item)
    return result


def _consider(result: Plan, src: Path, dst: Path) -> None:
    if dst.is_file() and dst.read_bytes() == src.read_bytes():
        result.unchanged.append(dst.name)
    else:
        result.copies.append((src, dst))


def apply(workspace: Path, work: Plan, now: Callable[[], float] = time.time) -> list[str]:
    """Carry the plan out: the replaced images go to a folder of the workspace (never deleted), the new files are written next to their final name and renamed."""
    if work.problems:
        raise ValueError("; ".join(work.problems))
    done: list[str] = []
    work.target.mkdir(parents=True, exist_ok=True)
    if work.replaced:
        backup = workspace / REPLACED_FOLDER / time.strftime("%Y%m%d_%H%M%S", time.localtime(now()))
        backup.mkdir(parents=True, exist_ok=True)
        for old in work.replaced:
            shutil.move(str(old), str(backup / old.name))
            done.append(f"moved {old.name} to {backup}")
    for src, dst in work.copies:
        temporary = dst.with_name(dst.name + ".part")
        shutil.copyfile(src, temporary)
        os.replace(temporary, dst)
        done.append(f"copied {dst.name}")
    return done


def describe(work: Plan) -> list[str]:
    lines: list[str] = []
    for problem in work.problems:
        lines.append(f"cannot sync: {problem}")
    for refused in work.refused:
        lines.append(f"left out (its release signature is not valid): {refused}")
    if not work.problems:
        if not work.copies:
            lines.append("The Flasher already carries the firmware of the tool head repository." if not work.refused else "Nothing can be copied.")
        for name in work.images:
            lines.append(f"copy {name} (with its signature and checksums)")
        for old in work.replaced:
            lines.append(f"move the replaced {old.name} to {REPLACED_FOLDER} of the workspace (not deleted)")
    return lines


def _confirm(prompt: str, assume_yes: bool, ask: Callable[[str], str] | None) -> bool:
    if assume_yes:
        return True
    if ask is None:
        if not sys.stdin.isatty():
            print("Not copied: confirm in a terminal, or repeat the command with --yes.", file=sys.stderr)
            return False
        ask = input
    return ask(prompt).strip().lower() in {"y", "yes"}


def run(workspace: Path, *, assume_yes: bool = False, dry_run: bool = False, ask: Callable[[str], str] | None = None, public_key_hex: str | None = None) -> int:
    """Show the plan, ask, copy. 0 when the Flasher carries the firmware at the end (or already did), 1 when nothing was copied because it could not be or was declined."""
    work = plan(workspace, public_key_hex)
    for line in describe(work):
        print(line)
    if work.problems or work.refused and not work.copies:
        return 1
    if not work.copies:
        return 0
    if dry_run:
        print("Dry run: nothing was changed.")
        return 0
    prompt = f"Copy the firmware of {SOURCE_REPO} into {TARGET_REPO}? Nothing is written to a board. [y/N] "
    if not _confirm(prompt, assume_yes, ask):
        print("Not copied. Nothing was changed.")
        return 1
    for line in apply(workspace, work):
        print(line)
    return 1 if work.refused else 0


def offer_after_update(workspace: Path, project: str, ask: Callable[[str], str] | None = None) -> int | None:
    """At the end of an update of the tool head repository: the offer, when the option is on. ``None`` when it does not apply (another project, option off)."""
    if project != SOURCE_REPO or not enabled():
        return None
    print("\nThe option to bring the firmware to the Flasher is on.")
    return run(workspace, ask=ask)


def cmd_sync(args: argparse.Namespace, ask: Callable[[str], str] | None = None) -> int:
    from .main import default_workspace_root  # imported late: main imports this module through flasher_handoff

    option = getattr(args, "option", None)
    if option:
        settings.save_settings(**{SETTING: option == "on"})
        print(f"The offer to bring the firmware to the Flasher after an update of {SOURCE_REPO} is now {option.upper()} (it is always a question; off is the default).")
        return 0
    workspace = Path(args.workspace).resolve() if getattr(args, "workspace", None) else default_workspace_root()
    return run(workspace, assume_yes=bool(args.yes), dry_run=bool(args.dry_run), ask=ask)
