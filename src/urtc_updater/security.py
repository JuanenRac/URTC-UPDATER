# =============================================================================
# URTC-UPDATER - Security options of an install or update: security.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The two protections an install or update can ask for, and how to change them.

An install or update runs the build check of the candidate (``build-test.sh`` or
``.bat`` and what it calls) with the permissions of the person who runs the
updater. Two options decide how much is trusted before that happens. Both are
**off by default** - the behaviour of the tool is the same unless one is turned
on - and both can be turned on and off from the settings window, the settings
file, the environment and the command line:

``require signed commits``
    The candidate commit must carry a valid GPG or SSH signature before its
    manifest is read or anything in it is built (see ``signature.py``).
    Settings: ``signature_policy: "require"`` or ``require_signed_commits: true``.
    Environment: ``URTC_UPDATER_REQUIRE_SIGNED=1`` (``0`` turns it off).
    Command line: ``--require-signed`` / ``--no-require-signed``.

``confirm before the build check``
    The candidate is fetched and checked, and then the person is shown the
    project, the commit, its author, its signature and the build or tool scripts
    that changed, and asked before any of that is run. Without an answer (no
    window, no terminal) nothing is run.
    Settings: ``confirm_before_build: true``.
    Environment: ``URTC_UPDATER_CONFIRM_BUILD=1`` (``0`` turns it off).
    Command line: ``--confirm-build`` / ``--no-confirm-build``; ``--yes`` (or
    ``URTC_UPDATER_ASSUME_YES=1``) answers yes without asking, for scripts.

The environment and the command line win over the saved settings, so a script or
a single run can change a protection without touching the settings file. When a
run turns off a protection that the saved settings have on, the tool says so
(:func:`lowering_warnings`), and the settings window and the ``security``
command ask before saving a lower level.
"""
from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from . import settings
from .messages import CodedText, coded

ENV_REQUIRE_SIGNED = "URTC_UPDATER_REQUIRE_SIGNED"
ENV_CONFIRM_BUILD = "URTC_UPDATER_CONFIRM_BUILD"
ENV_ASSUME_YES = "URTC_UPDATER_ASSUME_YES"

SETTING_CONFIRM_BUILD = "confirm_before_build"


def _env_flag(name: str) -> bool | None:
    value = os.environ.get(name, "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return None


def saved_require_signed() -> bool:
    """What the settings file asks for. A settings file that exists but cannot be read counts as "required": the safe side, until it is fixed or removed."""
    if settings.settings_state() == "corrupt":
        return True
    data = settings.load_settings()
    return data.get("signature_policy") == "require" or data.get("require_signed_commits") is True


def saved_confirm_build() -> bool:
    return settings.load_settings().get(SETTING_CONFIRM_BUILD) is True


def effective_require_signed() -> bool:
    override = _env_flag(ENV_REQUIRE_SIGNED)
    return override if override is not None else saved_require_signed()


def effective_confirm_build() -> bool:
    override = _env_flag(ENV_CONFIRM_BUILD)
    return override if override is not None else saved_confirm_build()


def assume_yes() -> bool:
    return _env_flag(ENV_ASSUME_YES) is True


def lowering_warnings() -> list[CodedText]:
    """The protections that the saved settings have on and that this run turns off (through the environment or the command line)."""
    found: list[CodedText] = []
    if saved_require_signed() and not effective_require_signed():
        found.append(coded("security_lowered_signed"))
    if saved_confirm_build() and not effective_confirm_build():
        found.append(coded("security_lowered_confirm"))
    return found


def lowering_of_change(*, require_signed: bool, confirm_build: bool) -> list[CodedText]:
    """The protections that saving these values would turn off compared with the saved settings (what the settings window asks about)."""
    found: list[CodedText] = []
    if saved_require_signed() and not require_signed:
        found.append(coded("security_lowered_signed"))
    if saved_confirm_build() and not confirm_build:
        found.append(coded("security_lowered_confirm"))
    return found


def save_security(*, require_signed: bool, confirm_build: bool) -> None:
    """Writes both options to the settings file. ``signature_policy`` is the name the signature module reads; the older ``require_signed_commits`` key is dropped so the two cannot disagree."""
    data = settings.load_settings()
    data.pop("require_signed_commits", None)
    data["signature_policy"] = "require" if require_signed else "warn"
    data[SETTING_CONFIRM_BUILD] = bool(confirm_build)
    settings.replace_settings(data)


# ---------------------------------------------------------------------------
# Asking before the build check
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BuildRequest:
    """What the person is shown before the build check of a candidate runs."""

    project: str
    script: str
    commit: str
    author: str
    signature: str
    changed_scripts: tuple[str, ...]


ConfirmFunction = Callable[[BuildRequest], bool]

_confirmer: ConfirmFunction | None = None


def set_confirmer(function: ConfirmFunction | None) -> None:
    """The function that asks the person (the window, or the terminal). None means there is nobody to ask."""
    global _confirmer
    _confirmer = function


@contextmanager
def confirmer(function: ConfirmFunction | None) -> Iterator[None]:
    global _confirmer
    previous = _confirmer
    _confirmer = function
    try:
        yield
    finally:
        _confirmer = previous


@dataclass(frozen=True)
class BuildDecision:
    allowed: bool
    #: "not asked" (the option is off), "assumed" (yes without asking), "confirmed", "declined" or "nobody to ask".
    how: str


def decide_build(request: BuildRequest) -> BuildDecision:
    """Whether the build check of the candidate may run. With the option off the answer is always yes and nobody is asked."""
    if not effective_confirm_build():
        return BuildDecision(True, "not asked")
    if assume_yes():
        return BuildDecision(True, "assumed")
    if _confirmer is None:
        return BuildDecision(False, "nobody to ask")
    answer = bool(_confirmer(request))
    return BuildDecision(answer, "confirmed" if answer else "declined")
