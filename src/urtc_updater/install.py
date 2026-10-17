# =============================================================================
# URTC-UPDATER - Clone/pull + delegate to each project's own build
# script: install.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
#
# Deliberately does NOT reimplement per-stack build logic (npm/cargo/go/
# gradlew/flutter/pip, 7 different toolchains across the ecosystem). Every
# project carries the common non-versioning build-test.sh/.bat entry point.
# It delegates to its own stack-aware check without incrementing a manifest or
# CHANGELOG, so fleet maintenance cannot manufacture a release merely by
# refreshing a checkout. Versioned build scripts remain an explicit human
# release action and are never selected here. The shared build-test entry point
# already knows its own real
# dependencies, venv/toolchain setup, and quirks (HYDRA-UMC-TELEMETRY-
# COLLECTOR/HYDRA-UMC-TOOL-CLI's module root being src/, not the repo
# root, for instance). Reimplementing that here would mean two places that
# both claim to know how to build a given project, guaranteed to drift.
# This module's own job ends at "clone/pull the source, then run whichever
# build script this specific checkout actually has."
# =============================================================================
from __future__ import annotations

import re
import stat
import sys
import subprocess
import os
import time
from contextlib import contextmanager
from shutil import copy2, copytree, rmtree
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator
from uuid import uuid4

from .evidence import installed_state, record_attempt
from .messages import coded
from .project_manifest import ManifestValidationError, ProjectManifest, parse_manifest
from .registry import ProjectEntry, github_repo_url
from .signature import current_policy, unsigned_reason, verify_revision

# P01/the durable version of this module's own in-process
# self-heal for the narrow gap between the 2 promotion renames below (see
# clone_or_pull's own docstring) - HYDRA-UMC-SDK's promotion_journal
# module, shared with HYDRA-UMC-OPS-AGENT's own canary_deploy.py, exactly
# as that fix's own comment called for. Optional (see pyproject.toml's
# own "durable-journal" extra) so this project's safety-critical update
# core stays usable with zero external dependencies - the SAME
# stdlib-only-by-default / opt-in-extra shape this module's own PySide6
# GUI dependency already established. Without it installed, promotion
# still works exactly as before (the in-process self-heal already in
# clone_or_pull), just without surviving a full process crash.
#
# P01/the same optional package also carries check_service_health -
# when a project's own manifest declares a real service_port +
# service_health_path, a promotion is not reported as a real success
# until that real endpoint answers healthy (see _health_check_url_for()
# and clone_or_pull's own promotion step below), and a crash between
# promoting and checking is itself recoverable via
# recover_interrupted_promotions() (the pending check runs for real on
# the next call, never repeating the build).
try:
    from hydra_umc_sdk.promotion_journal import PromotionJournal, PromotionPhase
    from hydra_umc_sdk.promotion_journal import check_service_health as _check_service_health
    from hydra_umc_sdk.promotion_journal import recover as _recover_promotions
    _HAS_DURABLE_JOURNAL = True
except ImportError:
    _HAS_DURABLE_JOURNAL = False

# One journal file per workspace, not per project - a single small JSON
# file covers however many projects this workspace ever promotes,
# consistent with PromotionJournal's own "proportionate for a handful of
# records" design.
_JOURNAL_FILENAME = ".urtc_updater_promotion_journal.json"


def _health_check_url_for(entry: ProjectEntry) -> str | None:
    """this project's own real 'servicio comprobado' target - only ever built when
    the project's own manifest declares BOTH `service_port` and
    `service_health_path` (see ProjectEntry's own field comments); either
    alone declares nothing checkable. Always `127.0.0.1`: this checks
    whatever is listening on THIS host, immediately after THIS host's own
    checkout was just promoted - never a remote address a manifest could
    otherwise smuggle in. A project whose real runtime lives elsewhere
    (e.g. deployed separately to /opt/hydra-umc/<svc> and restarted by
    HYDRA-UMC-OS's own provisioning scripts, not served directly from this
    checkout) simply should not declare `service_health_path` in a context
    where checking it here wouldn't mean anything - that is the project's
    own manifest to author, not a judgment call this function makes."""
    if entry.service_port is None or not entry.service_health_path:
        return None
    return f"http://127.0.0.1:{entry.service_port}{entry.service_health_path}"


def recover_interrupted_promotions(workspace_root: Path) -> list[str]:
    """Heals any promotion this updater itself started and never finished
    - a real process crash, `kill -9`, power loss, or a reboot exactly
    between the 2 renames in clone_or_pull's own promotion step. Called
    once at the start of install_or_update() (every real entry point -
    CLI, Tkinter GUI, Qt GUI - funnels through it), so a genuinely
    interrupted prior run is healed before another update ever proceeds.

    Returns the human-readable actions recover() took (empty if nothing
    was pending, OR if hydra-umc-sdk itself isn't installed - see this
    module's own header comment for why that is a real, honest no-op
    rather than an error)."""
    if not _HAS_DURABLE_JOURNAL:
        return []
    journal = PromotionJournal(workspace_root / _JOURNAL_FILENAME)
    return _recover_promotions(journal)


# Checked in this order - the first one that exists in the checkout is the
# one actually run. Covers every real name used across the 44 projects
# (see this module's own header comment) without needing a per-project
# override in registry.py for something this mechanical.
BUILD_TEST_SCRIPT_POSIX = "build-test.sh"
BUILD_TEST_SCRIPT_WINDOWS = "build-test.bat"

# The GUI consumes these events to show the same real work that the CLI does.
# A callback is deliberately optional: command-line users retain normal child
# process output, while the GUI captures it so Windows never needs a second
# terminal window merely to show a project's build output.
ProgressCallback = Callable[[str, str], None]


@dataclass
class InstallResult:
    ok: bool
    message: str
    output: str = ""


def _run(
    cmd: list[str], cwd: Path, *, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    kwargs: dict[str, object] = {"cwd": str(cwd), "check": False}
    if capture_output:
        kwargs.update({"capture_output": True, "text": True})
    # The GUI is started with pythonw on Windows. Do not let git or a child
    # build script create a surprise console while its output is captured for
    # the in-window checkpoint log.
    if capture_output and os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        # Ecosystem .bat files deliberately finish with `pause` when an
        # operator double-clicks them.  In the GUI they run as a child with
        # captured evidence instead, so provide one harmless newline and do
        # not leave a hidden child waiting forever for a keypress.
        kwargs["input"] = "\n"
    try:
        return subprocess.run(cmd, **kwargs)  # type: ignore[arg-type]
    except FileNotFoundError as exc:
        raise InstallError(coded("tool_missing", tool=cmd[0], error=str(exc))) from exc


def _rmtree_best_effort(path: Path) -> None:
    """Removes a staging directory this module created and no longer
    needs, tolerating a Windows-specific rough edge: a child process (git,
    or a project's own build-test.sh/.bat) can leave a file handle open
    for a brief moment even after that process has already exited,
    turning an immediate rmtree into a spurious PermissionError. Retries
    a few times with a short pause instead of either raising (this is
    always best-effort cleanup of OUR OWN temporary directory, never
    something that should fail the caller's own real result) or silently
    giving up on the very first attempt."""
    def _writable_and_again(function, target, *_error):
        # git writes its pack files read-only: on Windows deleting them fails until the flag is cleared, and a refused or failed candidate was left behind as a directory
        try:
            os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
            function(target)
        except OSError:
            pass

    for attempt in range(5):
        try:
            if sys.version_info >= (3, 12):
                rmtree(path, onexc=_writable_and_again)
            else:
                rmtree(path, onerror=_writable_and_again)
            if not path.exists():
                return
            raise OSError(f"{path} could not be removed")
        except FileNotFoundError:
            return
        except OSError:
            if attempt == 4:
                return
            time.sleep(0.2)


def _checkpoint(progress: ProgressCallback | None, phase: str, code: str, **params: object) -> None:
    if progress is not None:
        progress(phase, coded(code, **params))


def _warn_if_unsigned(progress: ProgressCallback | None, repo: Path, revision: str, policy) -> None:   # noqa: ANN001 - SignaturePolicy
    """In the default (warn) mode an unsigned revision is installed, and the steps of the window and of the command line say that it is not signed."""
    if policy.required:
        return
    reason = unsigned_reason(repo, revision, policy)
    if reason is not None:
        _checkpoint(progress, "validation", "cp_unsigned_warning", commit=revision[:12], reason=reason)


# well-known
# build-artifact directory names, never carried over by
# _carry_over_local_data() below even though git genuinely considers
# them untracked/ignored - always safe to regenerate, and carrying them
# over would risk a large, slow copy that also contaminates the staging
# clone's own freshly-verified build with stale artifacts. Same real
# convention this ecosystem's own generic tools/build_test.py already
# excludes when walking a checkout.
_NEVER_CARRIED_OVER_DIR_NAMES = {
    ".git", "node_modules", "dist", "build", "target", ".venv", "venv",
    "__pycache__", ".next", ".cache", ".pytest_cache", ".mypy_cache",
}


def _real_untracked_paths(path: Path) -> list[str]:
    """Returns every real path (relative to `path`) this checkout's own
    git considers untracked OR ignored (`git status`'s own `??`/`!!`
    codes) - the exact real local-data shape needs carried over
    into a staging clone, which `git clone --local` never copies (it
    only ever copies the committed object database). Deliberately never
    includes a modified TRACKED file - a genuinely dirty working tree on
    a tracked file already fails clone_or_pull's own `git merge
    --ff-only` step separately, a different real problem this is not
    trying to solve."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--ignored", "-z"],
        cwd=str(path), check=False, capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    paths: list[str] = []
    for entry in result.stdout.split("\0"):
        if len(entry) < 4:
            continue
        status_code, rel_path = entry[:2], entry[3:]
        if status_code in ("??", "!!"):
            paths.append(rel_path)
    return paths


class DirtyCheckError(RuntimeError):
    """(shared with HYDRA-UMC-OPS-AGENT's own sibling helper): `git
    status` itself failed to run against a checkout (not a git
    repository, git missing from PATH, a permissions/IO error, ...) -
    see `_tracked_dirty_paths()`'s own docstring for why this must never
    be read as "no dirty files found". Nothing was touched."""

    def __init__(self, message: str, *, exit_code: int = 0, detail: str = "") -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.detail = detail


def _tracked_dirty_paths(path: Path) -> list[str]:
    """Returns every real path (relative to `path`) this checkout's own
    git considers a TRACKED file with a real uncommitted change - staged
    or not (`git status --porcelain`'s own status codes other than
    `??`/`!!`, which _real_untracked_paths() already owns).

    this
    module's own docstring used to claim "a real local edit... fails
    loudly with git's own error instead of being silently discarded" -
    true only for the older verify_build=False in-place `git merge
    --ff-only` path. Once moved the default (verify_build=True)
    flow to an isolated staging clone, that claim silently stopped being
    true: `git clone --local` only ever copies the COMMITTED object
    database, so a real uncommitted edit to an already-tracked file
    lives ONLY in `path`'s own working tree and is invisible to the
    fresh, clean staging clone - its own `git merge --ff-only` always
    succeeds (nothing there conflicts), the build succeeds, and
    promotion renames the dirty original aside to `.backup`, so the
    real edit survives only there while this function's own caller
    still reports `ok=True`. Checked explicitly, upfront, so this can
    fail loudly again before any staging work happens at all - matching
    what the docstring already promised.

    (P0, shared with OPS-AGENT's own sibling helper): a `git
    status` that fails to even RUN (returncode != 0) used to be treated
    exactly like "ran fine, found nothing dirty" - the one real
    uncommitted edit this function exists to catch became invisible the
    moment the check itself broke. Raises DirtyCheckError instead: not
    being able to verify clean is not the same as clean."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z"],
        cwd=str(path), check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise DirtyCheckError(
            f"could not verify {path} has no uncommitted changes - `git status` itself failed "
            f"(exit {result.returncode}): {result.stderr.strip() or '(no stderr)'}",
            exit_code=result.returncode,
            detail=result.stderr.strip() or "(no stderr)",
        )
    if not result.stdout:
        return []
    paths: list[str] = []
    for entry_text in result.stdout.split("\0"):
        if len(entry_text) < 4:
            continue
        status_code, rel_path = entry_text[:2], entry_text[3:]
        if status_code in ("??", "!!"):
            continue  # real untracked/ignored data - _carry_over_local_data()'s own concern, not a rejection reason
        paths.append(rel_path)
    return paths


def _carry_over_local_data(old_path: Path, staging_path: Path, *, progress: ProgressCallback | None = None) -> None:
    """Copies every real untracked/ignored file or directory from
    `old_path` into `staging_path` before the candidate is built or
    promoted.

    a real
    project's own operational data living inside its checkout (`data/
    settings.json`, `data/users.json`, a real sqlite file, TLS material a
    project generated for itself, ...) is exactly the shape of file `git
    clone --local` never copies at all - it only ever copies the
    committed object database. Reproduced with a real untracked file
    dropped into a real git checkout before an update: the promoted
    checkout was missing it entirely afterward, while the (kept, never
    deleted) `.backup` checkout still had it - a real, silent data loss
    on every update of a project that keeps any real local state inside
    its own checkout, which describes most services in this ecosystem
    (see this module's own header comment on why relocating that data
    outside every checkout entirely is real, separate, future work this
    fix does not attempt)."""
    carried = 0
    for rel_path in _real_untracked_paths(old_path):
        if any(part in _NEVER_CARRIED_OVER_DIR_NAMES for part in rel_path.replace("\\", "/").split("/")):
            continue
        source = old_path / rel_path
        if not source.exists():
            continue  # a real race (removed between `git status` and now) - nothing left to carry
        destination = staging_path / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            copytree(source, destination, dirs_exist_ok=True, symlinks=True)
        else:
            copy2(source, destination)
        carried += 1
    if carried:
        _checkpoint(progress, "validation", "cp_carried", count=carried)


def _validated_manifest_text(text: str, entry: ProjectEntry) -> ProjectManifest:
    """Parse the repository-owned manifest used as an update precondition.

    The updater never treats a Git revision as deployable merely because it
    can be fetched. It must still identify itself as the project selected by
    the operator and retain a valid public manifest.
    """
    return parse_manifest(text, expected_name=entry.name)


def _version_tuple(manifest: ProjectManifest) -> tuple[int, int, int, int]:
    parts = [int(part) for part in manifest.version.split(".")]
    parts += [0] * (4 - len(parts))  # a missing fourth component compares as 0
    return tuple(parts)  # type: ignore[return-value]


def _manifest_from_revision(path: Path, revision: str, entry: ProjectEntry) -> ProjectManifest:
    """Read a manifest from Git without modifying the working tree."""
    result = subprocess.run(
        ["git", "show", f"{revision}:urtc.project.json"],
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ManifestValidationError("candidate revision has no readable urtc.project.json")
    return _validated_manifest_text(result.stdout, entry)


def clone_or_pull(
    entry: ProjectEntry,
    workspace_root: Path,
    *,
    verify_build: bool = True,
    progress: ProgressCallback | None = None,
) -> InstallResult:
    """git clone if this project isn't checked out yet under
    workspace_root, otherwise `git -C <path> fetch` followed by a real
    `git merge --ff-only FETCH_HEAD` - never a force-push-style reset.
    Before that fast-forward, the updater validates the fetched revision's
    repository-owned manifest and rejects a lower version, so an update
    cannot silently become a rollback. A real local edit a developer made
    (this tool is meant to also run on a dev machine, not only the real
    CM5) fails loudly instead of being silently discarded - explicitly
    checked upfront (see _tracked_dirty_paths()'s own docstring for why
    this can no longer be left to git's own `merge --ff-only` error:
    that used to be true, but stopped being true the moment verify_build
    defaulted to the isolated staging-clone flow below, ).

    (P1):
    updating an EXISTING checkout used to merge the candidate straight
    into `path`, then leave building it to a separate step
    (install_or_update's own run_build_script call) - a build failure
    there left new sources merged into `path` sitting next to the
    PREVIOUS build's artifacts, an inconsistent install with no rollback.
    With verify_build=True (the default), the candidate is instead
    cloned+merged+built in a fully independent staging clone FIRST -
    `path` is never touched at all until that build actually succeeds -
    then promoted into place via two back-to-back directory renames
    (each individually atomic on the same filesystem; the previous
    installation is kept, not deleted, at `<name>.backup`, so an
    operator can restore it by hand if the new version misbehaves
    despite building fine). A build failure - or a crash, full disk, or
    diverged/dirty checkout at any point before that final promotion -
    leaves `path` completely untouched and still the operative
    installation. verify_build=False skips all of this and restores the
    exact old in-place-merge behavior, for a caller that intentionally
    doesn't want a build (matching install_or_update's own `build=False`
    path)."""
    path = workspace_root / entry.name
    _checkpoint(progress, "preflight", "cp_workspace")
    if not path.exists():
        # Clone to a sibling staging path first.  A failed network transfer or
        # malformed remote must not leave a partial directory that the next
        # operator run mistakes for a real installation.  rename() is atomic
        # inside workspace_root and we never remove a path we did not create.
        staging_path = workspace_root / f".{entry.name}.clone-{uuid4().hex}"
        _checkpoint(progress, "source", "cp_clone_staging")
        result = _run(
            ["git", "clone", github_repo_url(entry), str(staging_path)],
            cwd=workspace_root,
            capture_output=progress is not None,
        )
        if result.returncode != 0:
            _rmtree_best_effort(staging_path)
            return InstallResult(False, coded("clone_failed", code=result.returncode), _command_output(result))
        policy = current_policy()
        refused = verify_revision(staging_path, "HEAD", policy)
        if refused:
            _rmtree_best_effort(staging_path)
            return InstallResult(False, coded("clone_refused_signature", reason=refused))
        _warn_if_unsigned(progress, staging_path, "HEAD", policy)
        try:
            _checkpoint(progress, "validation", "cp_validate_fetched")
            _manifest_from_revision(staging_path, "HEAD", entry)
        except ManifestValidationError as exc:
            _rmtree_best_effort(staging_path)
            return InstallResult(False, coded("clone_manifest_invalid", reason=str(exc)))
        if path.exists():
            _rmtree_best_effort(staging_path)
            return InstallResult(False, coded("path_appeared", path=str(path)))
        staging_path.replace(path)
        _checkpoint(progress, "validation", "cp_clone_promoted")
        return InstallResult(True, coded("cloned", path=str(path)))

    if not (path / ".git").is_dir():
        return InstallResult(False, coded("not_git", path=str(path)))

    try:
        _checkpoint(progress, "preflight", "cp_validate_installed")
        installed = _manifest_from_revision(path, "HEAD", entry)
    except ManifestValidationError as exc:
        return InstallResult(False, coded("installed_manifest_invalid", reason=str(exc)))

    # refuse upfront, before any fetch/staging work, if a real
    # tracked file has a genuine uncommitted edit - see
    # _tracked_dirty_paths()'s own docstring for exactly why the
    # staging-clone flow below can no longer be trusted to catch this
    # itself. Applies to both verify_build values - a caller intending
    # the older in-place-merge path (verify_build=False) never wanted
    # a real local edit silently discarded either.
    try:
        dirty = _tracked_dirty_paths(path)
    except DirtyCheckError as exc:
        return InstallResult(False, coded("dirty_check_failed", path=str(path), code=exc.exit_code, detail=exc.detail))
    if dirty:
        preview = ", ".join(dirty[:5]) + (f" (+{len(dirty) - 5} more)" if len(dirty) > 5 else "")
        return InstallResult(False, coded("dirty", path=str(path), preview=preview))

    # Fetch first and inspect FETCH_HEAD before changing the operator's
    # working tree. This prevents a malformed or older remote manifest from
    # becoming an installed downgrade merely because Git can fast-forward it.
    _checkpoint(progress, "source", "cp_fetching")
    result = _run(
        ["git", "fetch", "--quiet", "origin", "HEAD"],
        cwd=path,
        capture_output=progress is not None,
    )
    if result.returncode != 0:
        return InstallResult(False, coded("fetch_failed", code=result.returncode), _command_output(result))
    # Resolve the fetched commit exactly once and use that SHA for every
    # later step (signature, manifest, merge): the name FETCH_HEAD is a
    # shared file another process could rewrite between two reads.
    resolved = subprocess.run(
        ["git", "rev-parse", "FETCH_HEAD"], cwd=str(path), check=False, capture_output=True, text=True
    )
    candidate_sha = resolved.stdout.strip() if resolved.returncode == 0 else ""
    if not candidate_sha:
        return InstallResult(False, coded("unresolved", path=str(path)))
    policy = current_policy()
    refused = verify_revision(path, candidate_sha, policy)
    if refused:
        return InstallResult(False, coded("remote_refused_signature", reason=refused))
    _warn_if_unsigned(progress, path, candidate_sha, policy)
    try:
        _checkpoint(progress, "validation", "cp_check_candidate")
        candidate = _manifest_from_revision(path, candidate_sha, entry)
    except ManifestValidationError as exc:
        return InstallResult(False, coded("remote_manifest_invalid", reason=str(exc)))
    if _version_tuple(candidate) < _version_tuple(installed):
        return InstallResult(False, coded("anti_rollback", candidate=candidate.version, installed=installed.version))

    if not verify_build:
        _checkpoint(progress, "validation", "cp_merge_in_place")
        result = _run(
            ["git", "merge", "--ff-only", candidate_sha],
            cwd=path,
            capture_output=progress is not None,
        )
        if result.returncode != 0:
            return InstallResult(False, coded("merge_failed", code=result.returncode), _command_output(result))
        return InstallResult(True, coded("pulled", path=str(path)))

    # prove the candidate actually builds in a fully independent
    # staging clone BEFORE touching `path` at all - see this function's
    # own docstring. Resolved as a real SHA (not the name "FETCH_HEAD",
    # which means something different in every repo) BEFORE staging even
    # exists: `path`'s FETCH_HEAD already names this exact commit, and
    # `git clone --local` below copies `path`'s whole object database, so
    # that commit is already a real, present object in the staging clone
    # even though nothing there points to it yet - no second fetch
    # needed, and no dependency on staging's own "origin" (which `git
    # clone` would otherwise point at `path` itself, not path's real
    # upstream - fetching "origin" there would silently fetch nothing
    # new and validate the WRONG, stale candidate).
    staging_path = workspace_root / f".{entry.name}.update-{uuid4().hex}"
    _checkpoint(progress, "source", "cp_clone_for_verify")
    # --no-hardlinks: a plain `git clone --local` hardlinks object files
    # from `path` on the same volume by default - real, reproducible
    # testing on Windows found that a build script running INSIDE the
    # staging clone can leave those hardlinked objects genuinely
    # undeletable afterward (WinError 5, not a transient lock - retrying
    # does not help), silently leaving an orphaned `.{name}.update-*`
    # directory behind in workspace_root forever. A full copy costs a
    # little more local disk I/O (still no network - this is a same-
    # filesystem clone either way) in exchange for staging actually being
    # a fully independent directory that can always be cleaned up.
    result = _run(
        ["git", "clone", "--local", "--no-hardlinks", str(path), str(staging_path)],
        cwd=workspace_root,
        capture_output=progress is not None,
    )
    if result.returncode != 0:
        _rmtree_best_effort(staging_path)
        return InstallResult(False, coded("staging_clone_failed", code=result.returncode, path=str(path)), _command_output(result))

    # `git
    # clone --local` above points the new clone's own `origin` remote at
    # the LOCAL SOURCE PATH it was cloned from (`path`, the installation
    # about to be renamed aside) - never at this project's real GitHub
    # upstream. Left uncorrected, the checkout this staging clone becomes
    # once promoted below would have `origin` pointing at itself, so
    # every FUTURE `git fetch origin` here would fetch nothing new,
    # silently and permanently stopping this checkout from ever
    # discovering a real update again. Reset to the real upstream
    # immediately, before build/promotion, so staging is a faithful
    # preview of the checkout it is about to become in every respect,
    # not just source content.
    real_origin_url = github_repo_url(entry)
    result = _run(["git", "remote", "set-url", "origin", real_origin_url], cwd=staging_path, capture_output=progress is not None)
    if result.returncode != 0:
        _rmtree_best_effort(staging_path)
        return InstallResult(False, coded("remote_restore_failed", code=result.returncode, path=str(path)), _command_output(result))

    # carry
    # over the installed checkout's own real local data BEFORE building/
    # promoting - see _carry_over_local_data()'s own docstring for the
    # real gap this closes. Done before the build below (not merely
    # before promotion) so a build-test script that reads this project's
    # own real local files during verification sees the same real data
    # the promoted checkout will actually run against.
    _carry_over_local_data(path, staging_path, progress=progress)

    _checkpoint(progress, "validation", "cp_merge_staging")
    result = _run(["git", "merge", "--ff-only", candidate_sha], cwd=staging_path, capture_output=progress is not None)
    if result.returncode != 0:
        _rmtree_best_effort(staging_path)
        return InstallResult(False, coded("staging_merge_failed", code=result.returncode, path=str(path)), _command_output(result))

    _checkpoint(progress, "build", "cp_build_isolated")
    build_result = _run_build_script_at(staging_path, progress=progress)
    if not build_result.ok:
        _rmtree_best_effort(staging_path)
        return InstallResult(False, coded("candidate_build_failed", path=str(path), detail=build_result.message), build_result.output)

    # The one real promotion step: swap the previous installation aside
    # (kept, never deleted - see this function's own docstring) and move
    # the proven-buildable staging clone into its place. Both are plain
    # directory renames on the same filesystem/volume, so each one
    # individually is atomic; the only remaining unsafe window is the
    # brief gap between these two renames (a crash exactly there would
    # leave `path` genuinely missing) - vastly narrower than before,
    # where the unsafe window spanned the entire build.
    #
    # (P1; honest,
    # bounded mitigation, not the full transactional journal/rollback
    # the finding's own acceptance criteria describes - that needs
    # designing once, shared with HYDRA-UMC-OPS-AGENT's own
    # canary_deploy.py, as real, separate future work): two real gaps
    # existed here. First, `backup_path` reused the SAME fixed name
    # every promotion (`rmtree(backup_path, ...)` right before renaming
    # into it) - a second install after a first one already failed
    # partway would silently delete the ONLY recoverable copy of the
    # previous installation before even attempting the new promotion.
    # Now unique per attempt (`.backup-<uuid>`, matching OPS-AGENT's own
    # fix), never overwriting an earlier backup. Second, a crash or
    # exception in the narrow gap between the two renames used to leave
    # NO active checkout at `path` at all, with no attempt to recover -
    # now a best-effort self-heal: if the second rename fails, this
    # immediately tries to rename the backup back to `path` so a real
    # installation still exists, rather than silently leaving neither a
    # live checkout nor a clear indication of which path holds the real
    # one.
    backup_path = workspace_root / f"{entry.name}.backup-{uuid4().hex[:8]}"
    # P01/a durable journal entry, written to disk BEFORE the
    # first real rename, so recover_interrupted_promotions() can heal
    # this promotion even if the process itself dies right here - the
    # in-process self-heal below still runs unconditionally either way,
    # this is additive, never a replacement for it. journal is None
    # (never referenced past this point) when hydra-umc-sdk isn't
    # installed - see this module's own header comment.
    health_check_url = _health_check_url_for(entry)
    journal = PromotionJournal(workspace_root / _JOURNAL_FILENAME) if _HAS_DURABLE_JOURNAL else None
    promotion_id = journal.begin(entry.name, path, staging_path, backup_path, health_check_url=health_check_url).promotion_id if journal else None
    _checkpoint(progress, "validation", "cp_promoting")
    try:
        path.rename(backup_path)
    except OSError as exc:
        # Something has a file of the installation open (the tool running, a terminal inside the folder, an editor): nothing was changed and the candidate is thrown away.
        _rmtree_best_effort(staging_path)
        return InstallResult(False, coded("set_aside_failed", path=str(path), error=str(exc)), build_result.output)
    try:
        # The folder keeps the modification time of the files inside it; the
        # retention rule orders backups by when they were made.
        os.utime(backup_path, None)
    except OSError:
        pass
    if journal:
        journal.advance(promotion_id, PromotionPhase.BACKED_UP)
    try:
        staging_path.rename(path)
    except OSError as exc:
        try:
            backup_path.rename(path)
        except OSError:
            return InstallResult(False, coded("promotion_double_failure", path=str(path), backup=str(backup_path), error=str(exc)), build_result.output)
        if journal:
            # The in-process self-heal above already fully resolved this -
            # nothing left for a later recover_interrupted_promotions()
            # call to do.
            journal.complete(promotion_id)
        return InstallResult(False, coded("promotion_restored", error=str(exc), path=str(path), staging=str(staging_path)), build_result.output)
    if journal:
        journal.advance(promotion_id, PromotionPhase.PROMOTED)
    sha_label = candidate_sha[:12]
    # a promotion that finishes its 2 renames is not yet a HEALTHY
    # promotion when the project itself declares a real health endpoint -
    # check it for real before ever calling this a success, rather than
    # treating "the files moved" as the whole postcondition. Skipped
    # entirely (same as before this feature existed) when the project
    # declares no health endpoint, or the optional durable-journal
    # dependency isn't installed at all (no journal to even record the
    # check against - see this module's own header comment).
    if journal and health_check_url:
        healthy, reason = _check_service_health(health_check_url)
        if not healthy:
            return InstallResult(
                False,
                coded("health_failed", path=str(path), version=candidate.version, commit=sha_label, url=health_check_url, reason=str(reason)),
                build_result.output,
            )
        journal.complete(promotion_id)
        return InstallResult(
            True,
            coded("updated_health", path=str(path), version=candidate.version, commit=sha_label, reason=str(reason), backup=str(backup_path)),
            build_result.output,
        )
    if journal:
        journal.complete(promotion_id)
    return InstallResult(
        True,
        coded("updated", path=str(path), version=candidate.version, commit=sha_label, backup=str(backup_path)),
        build_result.output,
    )


def find_build_test_script(path: Path) -> Path | None:
    import os
    name = BUILD_TEST_SCRIPT_WINDOWS if os.name == "nt" else BUILD_TEST_SCRIPT_POSIX
    candidate = path / name
    return candidate if candidate.is_file() else None


def run_build_script(
    entry: ProjectEntry,
    workspace_root: Path,
    *,
    progress: ProgressCallback | None = None,
) -> InstallResult:
    return _run_build_script_at(workspace_root / entry.name, progress=progress)


def _run_build_script_at(path: Path, *, progress: ProgressCallback | None = None) -> InstallResult:
    """The real work behind run_build_script(), taking an explicit path
    instead of deriving one from workspace_root/entry.name - shared with
    clone_or_pull's own staging-clone build verification, which
    needs to build a candidate sitting in a temporary staging directory,
    not (yet) the real installed checkout."""
    script = find_build_test_script(path)
    if script is None:
        return InstallResult(False, coded("no_build_script", path=str(path)))

    if os.name == "nt":
        cmd = ["cmd", "/c", str(script)]
    else:
        cmd = ["bash", str(script)]

    _checkpoint(progress, "build", "cp_run_script", script=script.name)
    result = _run(cmd, cwd=path, capture_output=progress is not None)
    if result.returncode != 0:
        return InstallResult(False, coded("script_failed", script=script.name, code=result.returncode), _command_output(result))
    return InstallResult(True, coded("script_ok", script=script.name), _command_output(result))


class InstallError(Exception):
    """A failure that has a message for the person (a command that cannot be started, say), not a bug."""


_LOCK_DIRECTORY = ".urtc-updater"
_LOCK_FILENAME = "lock"


@contextmanager
def workspace_lock(workspace_root: Path) -> Iterator[None]:
    """Holds an exclusive, operating-system level lock on the workspace for
    the duration of one install or update, so two instances (a window and a
    command line run, or two windows) can never work on the same checkout at
    once. The lock is released by the operating system if the process dies,
    so a crash never leaves a stale lock behind. Raises InstallError when
    another instance holds it."""
    directory = workspace_root / _LOCK_DIRECTORY
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handle = open(directory / _LOCK_FILENAME, "a+b")
    except OSError as exc:
        raise InstallError(coded("lock_create_failed", path=str(directory), error=str(exc))) from exc
    busy = InstallError(coded("lock_busy"))
    try:
        # A few short retries: the operating system may take a moment to
        # release a lock whose previous holder has only just finished.
        for attempt in range(6):
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if attempt == 5:
                    raise busy from None
                time.sleep(0.1)
        try:
            yield
        finally:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        handle.close()


def is_running_checkout(path: Path) -> bool:
    """True when `path` is the checkout this very program is running from.
    Replacing it while it runs cannot work (on Windows its files are open,
    and its environment would be swapped underneath it)."""
    try:
        running = Path(__file__).resolve()
        return running.is_relative_to(path.resolve())
    except (OSError, ValueError):
        return False


def install_or_update(
    entry: ProjectEntry,
    workspace_root: Path,
    *,
    build: bool = True,
    progress: ProgressCallback | None = None,
) -> list[InstallResult]:
    """The same flow, with nothing escaping: any failure is a result with its message. The window runs this in a thread, and an exception that left it would never emit its
    result - the buttons stayed disabled for ever and nothing was written down."""
    try:
        return _install_or_update(entry, workspace_root, build=build, progress=progress)
    except InstallError as exc:
        return [InstallResult(False, exc.args[0] if exc.args else str(exc))]
    except Exception as exc:  # noqa: BLE001 - the whole point is that nothing gets out
        import logging
        import traceback
        logging.getLogger("urtc_updater.gui").error("unexpected error installing %s: %s", entry.name, traceback.format_exc())
        return [InstallResult(False, coded("unexpected", error=str(exc)), traceback.format_exc())]


def _install_or_update(
    entry: ProjectEntry,
    workspace_root: Path,
    *,
    build: bool = True,
    progress: ProgressCallback | None = None,
) -> list[InstallResult]:
    """The full manual install/update flow for ONE project - never called
    for more than one project per invocation (see cli.py's own `install`/
    `update` subcommands, which always take an explicit project name, and
    this project's own README for why that is a deliberate, non-optional
    design choice: explicit operator approval keeps deployment safe).

    updating an EXISTING checkout now builds/verifies the
    candidate itself, inside clone_or_pull's own staging clone, BEFORE
    ever promoting it into the real installation - see that function's
    own docstring. A brand-new clone has no previous installation to
    protect, so it still gets its separate run_build_script call here,
    exactly as before.

    P01: heals any promotion a PREVIOUS run of this updater started and
    never finished (a real process crash exactly between clone_or_pull's
    own 2 promotion renames) before this run's own work begins - see
    recover_interrupted_promotions()'s own doc comment. A genuine no-op
    when nothing was pending, or when hydra-umc-sdk isn't installed."""
    if is_running_checkout(workspace_root / entry.name):
        return [InstallResult(False, coded("running_checkout", name=entry.name))]
    with workspace_lock(workspace_root):
        return _install_or_update_locked(entry, workspace_root, build=build, progress=progress)


def _install_or_update_locked(
    entry: ProjectEntry,
    workspace_root: Path,
    *,
    build: bool,
    progress: ProgressCallback | None,
) -> list[InstallResult]:
    recover_interrupted_promotions(workspace_root)
    was_existing_checkout = (workspace_root / entry.name / ".git").is_dir()
    before = installed_state(workspace_root / entry.name)
    leftovers_before = set(_orphan_staging(workspace_root, entry.name))
    try:
        results = [clone_or_pull(entry, workspace_root, verify_build=build, progress=progress)]
    except BaseException:
        # An exception that escapes mid-flow must not strand its hidden
        # staging folder in the workspace.
        for stray in _orphan_staging(workspace_root, entry.name):
            if stray not in leftovers_before:
                _rmtree_best_effort(stray)
        raise
    if results[0].ok and build and not was_existing_checkout:
        results.append(run_build_script(entry, workspace_root, progress=progress))
    elif results[0].ok and build:
        _checkpoint(progress, "build", "cp_build_already")
    elif results[0].ok:
        _checkpoint(progress, "build", "cp_build_skipped")
    record_attempt(
        workspace_root,
        project=entry.name,
        before=before,
        after=installed_state(workspace_root / entry.name),
        ok=all(r.ok for r in results),
        message="; ".join(r.message for r in results),
    )
    if was_existing_checkout and all(r.ok for r in results):
        try:
            prune_backups(workspace_root, backups_to_keep(), name=entry.name)
        except OSError:
            pass  # retention is housekeeping; it never turns a good update into a failure
    return results


def _command_output(result: subprocess.CompletedProcess[str]) -> str:
    """Return compact child evidence when a GUI captured it.

    The full command output remains available in the process result while the
    desktop surface keeps a bounded, readable activity trace instead of
    attempting to render an unbounded compiler log.
    """
    return "\n".join(part for part in (result.stdout, result.stderr) if part).strip()


# ---------------------------------------------------------------------------
# Kept previous installations: listing, retention, cleaning and restoring
# ---------------------------------------------------------------------------

#: How many previous installations of one project are kept after an update.
DEFAULT_BACKUPS_TO_KEEP = 2

_BACKUP_FOLDER = re.compile(r"^(?P<name>.+)\.backup-[0-9a-f]{8}$")
_STAGING_FOLDER = re.compile(r"^\.(?P<name>.+)\.(?:update|clone)-[0-9a-f]{32}$")


def backups_to_keep() -> int:
    """The retention count: the `backups_to_keep` setting when it is a whole
    number of at least zero, otherwise the default."""
    from .settings import load_settings

    value = load_settings().get("backups_to_keep")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return DEFAULT_BACKUPS_TO_KEEP


def list_backups(workspace_root: Path, name: str | None = None) -> dict[str, list[Path]]:
    """Kept previous installations by project name, newest first."""
    found: dict[str, list[Path]] = {}
    if not workspace_root.is_dir():
        return found
    for folder in workspace_root.iterdir():
        match = _BACKUP_FOLDER.match(folder.name)
        if match is None or not folder.is_dir():
            continue
        if name is not None and match.group("name") != name:
            continue
        found.setdefault(match.group("name"), []).append(folder)

    def age(folder: Path) -> tuple[float, str]:
        try:
            return (folder.stat().st_mtime, folder.name)
        except OSError:
            return (0.0, folder.name)

    for folders in found.values():
        folders.sort(key=age, reverse=True)
    return found


def _orphan_staging(workspace_root: Path, name: str | None = None) -> list[Path]:
    """Hidden staging folders (`.NAME.update-...`, `.NAME.clone-...`)."""
    if not workspace_root.is_dir():
        return []
    found = []
    for folder in workspace_root.iterdir():
        match = _STAGING_FOLDER.match(folder.name)
        if match is not None and folder.is_dir() and (name is None or match.group("name") == name):
            found.append(folder)
    return sorted(found)


def prune_backups(
    workspace_root: Path,
    keep: int = DEFAULT_BACKUPS_TO_KEEP,
    *,
    name: str | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Removes every kept previous installation beyond the newest `keep` of
    each project (only that project when `name` is given). Returns the
    folders removed - or, with `dry_run`, the ones that would be."""
    removed: list[Path] = []
    for folders in list_backups(workspace_root, name).values():
        for folder in folders[max(keep, 0):]:
            if not dry_run:
                _rmtree_best_effort(folder)
                if folder.exists():
                    continue
            removed.append(folder)
    return removed


@dataclass
class CleanReport:
    backups: list[Path]
    staging: list[Path]


def clean_workspace(workspace_root: Path, *, keep: int = 0, dry_run: bool = False) -> CleanReport:
    """The "clean backups" operation: holds the workspace lock (so it can
    never run under another install), first heals any promotion that was
    interrupted, then removes old backups beyond `keep` per project and every
    hidden staging folder left behind by a run that died."""
    with workspace_lock(workspace_root):
        recover_interrupted_promotions(workspace_root)
        backups = prune_backups(workspace_root, keep, dry_run=dry_run)
        staging = _orphan_staging(workspace_root)
        if not dry_run:
            for folder in staging:
                _rmtree_best_effort(folder)
            staging = [folder for folder in staging if not folder.exists()]
        return CleanReport(backups, staging)


def restore_backup(name: str, workspace_root: Path, *, backup: str | None = None) -> InstallResult:
    """Puts a kept previous installation back in place, with the same
    guarantees as an update: the installation being replaced is itself kept
    (as a new backup, so the swap can be undone), nothing is deleted, and a
    failure between the two renames puts the original back."""
    try:
        with workspace_lock(workspace_root):
            return _restore_backup_locked(name, workspace_root, backup)
    except InstallError as exc:
        return InstallResult(False, exc.args[0] if exc.args else str(exc))


def _restore_backup_locked(name: str, workspace_root: Path, backup: str | None) -> InstallResult:
    path = workspace_root / name
    if is_running_checkout(path):
        return InstallResult(False, coded("running_checkout", name=name))
    recover_interrupted_promotions(workspace_root)
    available = list_backups(workspace_root, name).get(name, [])
    if backup is not None:
        available = [folder for folder in available if folder.name == backup]
    if not available:
        return InstallResult(False, f"no kept previous installation of {name} to restore" + (f" named {backup}" if backup else ""))
    chosen = available[0]
    manifest_file = chosen / "urtc.project.json"
    try:
        restored = parse_manifest(manifest_file.read_text(encoding="utf-8"), expected_name=name)
    except (OSError, ManifestValidationError) as exc:
        return InstallResult(False, f"{chosen.name} is not a usable installation of {name}: {exc}")
    before = installed_state(path)
    set_aside: Path | None = None
    if path.exists():
        set_aside = workspace_root / f"{name}.backup-{uuid4().hex[:8]}"
        try:
            path.rename(set_aside)
        except OSError as exc:
            return InstallResult(False, f"the installation at {path} could not be set aside (is it open in a running program or a terminal?): {exc}")
        try:
            os.utime(set_aside, None)
        except OSError:
            pass
    try:
        chosen.rename(path)
    except OSError as exc:
        if set_aside is not None:
            try:
                set_aside.rename(path)
            except OSError:
                return InstallResult(False, f"restoring failed AND putting {path} back also failed; the installation that was in place is at {set_aside}: {exc}")
        return InstallResult(False, f"could not restore {chosen.name} ({exc}); {path} was left as it was")
    message = f"Restored {path} to v{restored.version} from {chosen.name}" + (
        f"; the installation that was in place is kept at {set_aside}" if set_aside is not None else ""
    )
    record_attempt(
        workspace_root, project=name, before=before, after=installed_state(path), ok=True, message=message,
    )
    return InstallResult(True, message)


# ---------------------------------------------------------------------------
# What an update would change, before it is approved
# ---------------------------------------------------------------------------

#: Paths whose changes matter most before approving an update: what gets run.
_BUILD_PATHSPECS = ("build-test.*", "build*.sh", "build*.bat", "tools", "scripts")


@dataclass
class UpdatePreview:
    commit: str
    author: str
    version: str
    installed_version: str
    #: "not required", "accepted" or the reason the policy refuses the commit.
    signature: str
    #: Changed files among the build and tool scripts the update would run.
    changed_scripts: list[str]
    diffstat: str


def preview_update(entry: ProjectEntry, workspace_root: Path) -> UpdatePreview:
    """Fetches the candidate commit and describes it - author, signature
    state and the build or tool scripts it changes - without modifying the
    checkout. Raises InstallError when it cannot."""
    path = workspace_root / entry.name
    if not (path / ".git").is_dir():
        raise InstallError(coded("not_git", path=str(path)))
    with workspace_lock(workspace_root):
        try:
            installed = _manifest_from_revision(path, "HEAD", entry)
        except ManifestValidationError as exc:
            raise InstallError(coded("installed_manifest_invalid", reason=str(exc))) from exc
        fetched = _run(["git", "fetch", "--quiet", "origin", "HEAD"], cwd=path, capture_output=True)
        if fetched.returncode != 0:
            raise InstallError(coded("fetch_failed", code=fetched.returncode))
        resolved = subprocess.run(["git", "rev-parse", "FETCH_HEAD"], cwd=str(path), check=False, capture_output=True, text=True)
        sha = resolved.stdout.strip() if resolved.returncode == 0 else ""
        if not sha:
            raise InstallError(coded("unresolved", path=str(path)))
        try:
            candidate = _manifest_from_revision(path, sha, entry)
        except ManifestValidationError as exc:
            raise InstallError(coded("remote_manifest_invalid", reason=str(exc))) from exc
        policy = current_policy()
        refusal = verify_revision(path, sha, policy)
        signature = refusal if refusal else ("accepted" if policy.required else "not required")
        author = subprocess.run(
            ["git", "log", "-1", "--format=%an <%ae>", sha], cwd=str(path), check=False, capture_output=True, text=True
        ).stdout.strip()
        names = subprocess.run(
            ["git", "diff", "--name-only", f"HEAD..{sha}", "--", *_BUILD_PATHSPECS],
            cwd=str(path), check=False, capture_output=True, text=True,
        ).stdout.split()
        stat_text = subprocess.run(
            ["git", "diff", "--stat", f"HEAD..{sha}", "--", *_BUILD_PATHSPECS],
            cwd=str(path), check=False, capture_output=True, text=True,
        ).stdout.strip()
    return UpdatePreview(sha, author, candidate.version, installed.version, signature, names, stat_text)
