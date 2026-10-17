# =============================================================================
# URTC-UPDATER - Comparing a checkout with its remote by commit: commits.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""Detects new commits that do not come with a version bump.

In this ecosystem the version number only moves when a project is built for
release, so a fix pushed without a build leaves the manifest version equal on
both sides. Comparing versions alone then reports "up to date" forever. One
cheap ``git ls-remote`` per installed project answers the other question:
does the remote branch point at a commit this checkout does not have?
"""
from __future__ import annotations

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

#: Same as the checkout: there is new work on the remote.
SAME = "same"
#: The remote HEAD is a commit this checkout does not contain.
NEW_COMMITS = "new_commits"
#: This checkout has commits the remote does not (unpushed work).
AHEAD = "ahead"
#: One side could not be read (no network, no remote, not a git checkout).
UNKNOWN = "unknown"

_TIMEOUT_S = 30


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    kwargs: dict[str, object] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        return subprocess.run(
            ["git", *args], cwd=str(path), check=False, capture_output=True,
            text=True, timeout=_TIMEOUT_S, env=env, **kwargs,  # type: ignore[arg-type]
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def local_head(path: Path) -> str | None:
    """The commit the checkout is at, or None when it cannot be read."""
    result = _git(path, "rev-parse", "HEAD")
    if result is None or result.returncode != 0:
        return None
    return result.stdout.strip() or None


def remote_head(path: Path, remote: str = "origin") -> str | None:
    """The commit the remote's HEAD points at (one ``git ls-remote``; nothing
    is downloaded and the checkout is not touched), or None when the remote
    cannot be reached."""
    result = _git(path, "ls-remote", remote, "HEAD")
    if result is None or result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.strip() == "HEAD" and sha.strip():
            return sha.strip()
    return None


def commit_state(path: Path) -> str:
    """SAME, NEW_COMMITS, AHEAD or UNKNOWN for the checkout at `path`."""
    local = local_head(path)
    remote = remote_head(path)
    if local is None or remote is None:
        return UNKNOWN
    if local == remote:
        return SAME
    known = _git(path, "cat-file", "-e", f"{remote}^{{commit}}")
    if known is None:
        return UNKNOWN
    if known.returncode != 0:
        # The remote commit is not in this checkout's history at all.
        return NEW_COMMITS
    contained = _git(path, "merge-base", "--is-ancestor", remote, local)
    if contained is None:
        return UNKNOWN
    return AHEAD if contained.returncode == 0 else NEW_COMMITS


def commit_states(paths: dict[str, Path], *, workers: int = 8) -> dict[str, str]:
    """`commit_state` for several checkouts at once, keyed like `paths`."""
    if not paths:
        return {}
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="urtc-commits") as pool:
        futures = {name: pool.submit(commit_state, path) for name, path in paths.items()}
        return {name: future.result() for name, future in futures.items()}
