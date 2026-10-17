# =============================================================================
# URTC-UPDATER - Station profiles: profiles.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Named station profiles: which projects a machine installs and whether
batches are allowed on it.

A profile lives in the settings file (``~/.urtc_updater_settings.json``):

    {"profiles": {"firmware-bench": {"projects": ["URTC", "URTC-FLASHER"],
                                     "allow_batch": false}},
     "profile": "firmware-bench"}

``projects`` lists the project names the profile covers; an empty or missing
list means every project. ``allow_batch`` (default true) says whether the
install-all and update-all actions are offered. The profile in use is the one
named by ``--profile`` on the command line, otherwise the settings' ``profile``.
"""
from __future__ import annotations

from dataclasses import dataclass

from .settings import load_settings


@dataclass(frozen=True)
class Profile:
    name: str
    projects: tuple[str, ...] = ()
    allow_batch: bool = True

    def allows(self, project: str) -> bool:
        return not self.projects or project in self.projects


def load_profile(name: str | None = None) -> Profile | None:
    """The requested profile (or the one selected in the settings), or None
    when no profile is in use. Raises ValueError for a name that is not
    defined, so a typo never silently means "no restriction"."""
    settings = load_settings()
    wanted = name if name is not None else settings.get("profile")
    if not isinstance(wanted, str) or not wanted:
        return None
    definitions = settings.get("profiles")
    definition = definitions.get(wanted) if isinstance(definitions, dict) else None
    if not isinstance(definition, dict):
        raise ValueError(f"profile {wanted!r} is not defined in the settings file")
    projects = definition.get("projects")
    listed = tuple(item for item in projects if isinstance(item, str)) if isinstance(projects, list) else ()
    return Profile(wanted, listed, definition.get("allow_batch") is not False)
