# =============================================================================
# URTC-UPDATER - Entry point: main.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
#
# Runs on the user's own Windows/Linux/macOS dev machine, or anywhere else
# with the same ecosystem checkout layout - every project as a sibling
# directory under one workspace root, same assumption URTC-FLASHER/
# URTC-TESTER's own build scripts already make.
#
# Bare invocation (no arguments, or double-clicked) launches the QML desktop
# GUI (qt_gui.py, PySide6/Qt Quick).  The old Tkinter shell stays as a
# compatibility fallback only when
# the optional GUI package was not installed. `--cli` switches to the
# headless argparse CLI below, with three subcommands:
#   status              - what's installed, what version, what's on GitHub
#   install <project>   - clone + build ONE project that isn't installed yet
#   update  <project>   - pull + rebuild ONE project that IS installed
# install/update are deliberately separate from status and always take an
# explicit project name - there is no "update everything" - see
# install.py's own header comment for why. Four more commands never change a
# project's code on their own: `check` (notify only), `clean-backups`,
# `restore-backup` and `evidence`.
#
# GUI imports are only attempted after --cli has been ruled out.  A genuinely
# headless CM5 therefore never needs Qt, tkinter or a display to run
# `urtc-updater --cli status`.
# =============================================================================
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, commits, compat_view, flasher_handoff, package, profiles, security, settings
from .detect import LocalStatus, discover_workspace
from .evidence import export_common, export_evidence, verify_chain
from .github_client import RemoteStatus, discover_remote_projects, fetch_all
from .install import (
    InstallError,
    clean_workspace,
    install_or_update,
    list_backups,
    preview_update,
    restore_backup,
)
from .notify import send_notification


def default_workspace_root() -> Path:
    """This project's own parent directory - correct as long as
    URTC-UPDATER itself was checked out the same way every other
    ecosystem project is (a sibling of the other 55 under one common
    parent) - the standard layout this whole tool assumes throughout.
    Always overridable with --workspace for anything else (a CM5 install
    under a different path, a CI checkout, ...)."""
    candidate = Path(__file__).resolve().parents[3]
    # Only a source checkout (src/urtc_updater/ inside a folder holding this
    # project's own manifest) has the sibling layout; installed as a normal
    # package the parents point into the Python installation, which must
    # never be used as a workspace.
    if (Path(__file__).resolve().parents[2] / "urtc.project.json").is_file():
        return candidate
    return Path.cwd()


def resolve_workspace_root() -> Path:
    """Real user request: the GUI's "Browse" used to reset back to
    `default_workspace_root()` on every single launch, with no way to
    remember a different one. Prefers a previously chosen, still-real
    directory (`settings.get_saved_workspace_root()` already refuses a
    saved path that no longer exists) over the parent-directory
    heuristic - used only by the GUI launch paths below; `--cli`
    subcommands keep resolving `default_workspace_root()` directly so a
    script's own behavior never depends on a GUI preference saved on the
    same machine.
    """
    return settings.get_saved_workspace_root() or default_workspace_root()


#: Exit code of `check` when something can be updated (0: nothing to do).
EXIT_UPDATES_AVAILABLE = 10


def _same_version(local: LocalStatus, remote: RemoteStatus | None) -> bool:
    return (
        local.installed and local.version is not None and remote is not None and remote.version is not None
        and not local.version < remote.version and not remote.version < local.version
    )


def _commit_states(locals_: list[LocalStatus], remotes: dict[str, RemoteStatus]) -> dict[str, str]:
    """For every installed project whose version equals GitHub's, whether
    the remote has commits the checkout does not (one `git ls-remote` each)."""
    same = {
        ls.entry.name: ls.path for ls in locals_ if _same_version(ls, remotes.get(ls.entry.name))
    }
    return commits.commit_states(same)


def _state_label(local: LocalStatus, remote: RemoteStatus | None, commit: str | None = None) -> str:
    if not local.installed:
        return "not installed"
    if local.version is None:
        return "unknown (local)"
    if remote is None:
        return "installed (not checked)"
    if remote.version is None:
        return f"installed, GitHub unknown ({remote.error})"
    if local.version < remote.version:
        return "OUTDATED"
    if remote.version < local.version:
        return "ahead of GitHub"
    if commit == commits.NEW_COMMITS:
        return "NEW COMMITS"
    return "up to date"


def cmd_status(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    # Real bug fixed here, found while adding --json: this line (and the
    # --offline notice below) printed to stdout unconditionally, ahead of
    # everything else - the exact opposite of what --json promises a
    # script piping this output into `json.loads()`. Every diagnostic
    # stdout print in this function is now gated on `not args.json`;
    # informational GitHub-check messages already went to stderr, so
    # those needed no change.
    if not args.json:
        print(f"Workspace root: {workspace_root}")
    local_discovery = discover_workspace(workspace_root)
    local_by_name = {status.entry.name: status for status in local_discovery.projects}

    remotes: dict[str, RemoteStatus] = {}
    if not args.offline:
        print("Checking GitHub repository manifests...", file=sys.stderr)
        try:
            remote_discovery = discover_remote_projects()
            remotes = {status.entry.name: status for status in remote_discovery.projects}
            for error in remote_discovery.errors:
                print(f"WARNING: {error}", file=sys.stderr)
        except RuntimeError as exc:
            # Public GitHub API quotas can be exhausted on a developer PC.
            # Raw version reads still let an existing local workspace report
            # updates; automatic discovery resumes when a token is available.
            print(f"WARNING: remote discovery unavailable: {exc}", file=sys.stderr)
            remotes = fetch_all([status.entry for status in local_discovery.projects])
    elif not args.json:
        print("(--offline: not checking GitHub - showing local state only)")

    entries = {name: status.entry for name, status in local_by_name.items()}
    entries.update({name: status.entry for name, status in remotes.items()})
    try:
        profile = profiles.load_profile(getattr(args, "profile", None))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if profile is not None:
        entries = {name: entry for name, entry in entries.items() if profile.allows(name)}
    locals_ = [
        local_by_name.get(
            name,
            LocalStatus(entry=entry, path=workspace_root / name, installed=False, version=None),
        )
        for name, entry in sorted(entries.items(), key=lambda item: item[0].casefold())
    ]
    commit_map = {} if args.offline else _commit_states(locals_, remotes)

    if args.json:
        # Real, scripting-friendly shape - every field the human-readable
        # table below also shows, plus the real local checkout path (not
        # printed by the table at all) - never a second, independently-
        # drifting summary of the same discovery data.
        payload = {
            "workspace_root": str(workspace_root),
            "offline": bool(args.offline),
            "projects": [
                {
                    "name": ls.entry.name,
                    "maturity": ls.entry.maturity,
                    "role": ls.entry.role,
                    "stack": ls.entry.stack,
                    "installed": ls.installed,
                    "path": str(ls.path),
                    "local_version": str(ls.version) if ls.version else None,
                    "github_version": str(remotes[ls.entry.name].version) if ls.entry.name in remotes and remotes[ls.entry.name].version else None,
                    "state": _state_label(ls, remotes.get(ls.entry.name), commit_map.get(ls.entry.name)),
                    "commit_state": commit_map.get(ls.entry.name),
                    "deployment_target": ls.entry.deploy,
                    "components": [
                        {"name": c.name, "kind": c.kind, "version": c.version, "target": c.target}
                        for c in (remotes[ls.entry.name].entry.components if ls.entry.name in remotes else ls.entry.components)
                    ],
                }
                for ls in locals_
            ],
        }
        installed_count = sum(1 for ls in locals_ if ls.installed)
        outdated_count = sum(1 for ls in locals_ if _state_label(ls, remotes.get(ls.entry.name)) == "OUTDATED")
        payload["installed_count"] = installed_count
        payload["outdated_count"] = outdated_count
        payload["new_commits_count"] = sum(1 for state in commit_map.values() if state == commits.NEW_COMMITS)
        payload["total"] = len(locals_)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    name_w = max((len(p.name) for p in entries.values()), default=7) + 2
    # Dynamic like name_w above - a fixed width silently ran stack values
    # like "python-qtquick" (14 chars) straight into the LOCAL column with
    # no separating space the moment a stack name grew past the old fixed 12.
    stack_w = max((len(p.stack) for p in entries.values()), default=5) + 2
    header = f"{'PROJECT':<{name_w}}{'MATURITY':<13}{'ROLE':<10}{'STACK':<{stack_w}}{'LOCAL':<10}{'GITHUB':<10}{'STATE'}"
    print(header)
    print("-" * len(header))

    outdated = 0
    new_commits = 0
    for ls in locals_:
        remote = remotes.get(ls.entry.name)
        local_v = str(ls.version) if ls.version else ("-" if not ls.installed else "?")
        remote_v = str(remote.version) if remote and remote.version else ("-" if args.offline else "?")
        state = _state_label(ls, remote, commit_map.get(ls.entry.name))
        if state == "OUTDATED":
            outdated += 1
        elif state == "NEW COMMITS":
            new_commits += 1
        print(
            f"{ls.entry.name:<{name_w}}{ls.entry.maturity:<13}{ls.entry.role:<10}"
            f"{ls.entry.stack:<{stack_w}}{local_v:<10}{remote_v:<10}{state}"
        )

    print()
    installed_count = sum(1 for ls in locals_ if ls.installed)
    summary = f"{installed_count}/{len(locals_)} installed, {outdated} outdated"
    if new_commits:
        summary += f", {new_commits} with new commits at the same version"
    print(summary + (" (GitHub not checked)" if args.offline else ""))
    if outdated or new_commits:
        print("Run `urtc-updater update <project>` to update one by hand - never automatic, see this tool's own README.")
    if args.notes:
        print("\nNotes (what's actually real per project, from its own manifest):")
        for ls in locals_:
            entry = ls.entry
            parent_suffix = f" (child of {entry.parent})" if entry.parent else ""
            print(f"\n{entry.name} [{entry.family}{parent_suffix}]")
            print(f"  {entry.notes or '(no notes recorded for this project yet)'}")
            if entry.tech:
                print(f"  Tech: {', '.join(entry.tech)}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Notify-only: reports what could be updated, changes nothing. Exits
    EXIT_UPDATES_AVAILABLE when something can be, so a scheduled task can act
    on the code; with --notify it also shows a desktop notification."""
    workspace_root = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    local_discovery = discover_workspace(workspace_root)
    installed = [status for status in local_discovery.projects if status.installed]
    try:
        profile = profiles.load_profile(getattr(args, "profile", None))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if profile is not None:
        installed = [status for status in installed if profile.allows(status.entry.name)]
    remotes = fetch_all([status.entry for status in installed])
    pending: list[str] = []
    for status in installed:
        remote = remotes.get(status.entry.name)
        if remote is not None and remote.version is not None and status.version is not None and status.version < remote.version:
            pending.append(f"{status.entry.name} {status.version} -> {remote.version}")
    commit_map = _commit_states(installed, remotes)
    pending += [
        f"{name} (new commits at the same version)"
        for name, state in sorted(commit_map.items()) if state == commits.NEW_COMMITS
    ]
    if not pending:
        if not args.quiet:
            print("Everything checked is up to date.")
        return 0
    print("Updates available (nothing was changed):")
    for item in pending:
        print(f"  {item}")
    if args.notify:
        shown = send_notification("URTC updates available", "; ".join(pending[:5]) + (f" (+{len(pending) - 5} more)" if len(pending) > 5 else ""))
        if not shown:
            print("(no desktop notification could be shown on this system)", file=sys.stderr)
    return EXIT_UPDATES_AVAILABLE


def cmd_clean_backups(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    try:
        report = clean_workspace(workspace_root, keep=args.keep, dry_run=args.dry_run)
    except InstallError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    verb = "Would remove" if args.dry_run else "Removed"
    for folder in report.backups + report.staging:
        print(f"{verb} {folder}")
    print(f"{verb} {len(report.backups)} previous installation(s) and {len(report.staging)} leftover staging folder(s); kept the newest {args.keep} per project.")
    return 0


def cmd_restore_backup(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    if args.list:
        found = list_backups(workspace_root, args.project)
        for folder in found.get(args.project, []):
            print(folder.name)
        return 0
    result = restore_backup(args.project, workspace_root, backup=args.backup)
    print(("OK  " if result.ok else "FAIL ") + result.message)
    return 0 if result.ok else 1


def _evidence_history(folder: str, as_json: bool) -> int:
    """The ``urtc-evidence/1`` records of a folder (the ones the flasher, the tester and this tool write), newest first, each one checked. Reads only."""
    from .urtc_pkg import evidence_history

    try:
        entries = evidence_history.select(evidence_history.load_folder(folder))
    except FileNotFoundError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    print(evidence_history.to_json(entries).rstrip("\n") if as_json else evidence_history.to_text(entries))
    return 1 if any(not entry.valid for entry in entries) else 0


def cmd_evidence(args: argparse.Namespace) -> int:
    if getattr(args, "history", None):
        return _evidence_history(args.history, bool(getattr(args, "json", False)))
    workspace_root = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    problems = verify_chain(workspace_root)
    if args.export:
        destination = export_evidence(workspace_root, Path(args.export))
        print(f"Evidence exported to {destination}")
    if args.export_common:
        written, skipped = export_common(workspace_root, Path(args.export_common))
        print(f"{written} record(s) in the urtc-evidence/1 shape written to {args.export_common}" + (f" ({skipped} line(s) left out: they do not fit the shape)" if skipped else ""))
    for problem in problems:
        print(f"PROBLEM {problem}", file=sys.stderr)
    if not problems:
        print("Evidence chain intact.")
    return 1 if problems else 0


def _terminal_confirmer(request: security.BuildRequest) -> bool:
    """Asks in the terminal before the build check of a candidate runs. Without a terminal there is nobody to ask: the answer is no."""
    if not sys.stdin.isatty():
        return False
    print(f"About to run {request.script} of {request.project} with your permissions.", file=sys.stderr)
    print(f"  Commit:    {request.commit}", file=sys.stderr)
    print(f"  Author:    {request.author or 'unknown'}", file=sys.stderr)
    print(f"  Signature: {request.signature}", file=sys.stderr)
    changed = ", ".join(request.changed_scripts) if request.changed_scripts else "none"
    print(f"  Build and tool files that changed: {changed}", file=sys.stderr)
    try:
        answer = input("Run the build check? [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}


def _apply_security_arguments(args: argparse.Namespace) -> None:
    """Turns the security flags of the command line into the environment variables the rest of the tool reads, installs the terminal question and says so when a flag turns
    off a protection that the saved settings have on."""
    for flag, variable in (("require_signed", security.ENV_REQUIRE_SIGNED), ("confirm_build", security.ENV_CONFIRM_BUILD)):
        value = getattr(args, flag, None)
        if value is not None:
            os.environ[variable] = "1" if value else "0"
    if getattr(args, "yes", False):
        os.environ[security.ENV_ASSUME_YES] = "1"
    security.set_confirmer(_terminal_confirmer)
    for warning in security.lowering_warnings():
        print(str(warning), file=sys.stderr)


def _on_off(value: bool) -> str:
    return "on" if value else "off"


def cmd_security(args: argparse.Namespace) -> int:
    """Shows the two security options, or changes them in the settings file. Turning one off asks first (or needs --yes)."""
    saved_signed, saved_confirm = security.saved_require_signed(), security.saved_confirm_build()
    new_signed = saved_signed if args.require_signed is None else args.require_signed == "on"
    new_confirm = saved_confirm if args.confirm_build is None else args.confirm_build == "on"
    if args.require_signed is None and args.confirm_build is None:
        state = settings.settings_state()
        print(f"Require signed commits:           {_on_off(saved_signed)} (saved)  {_on_off(security.effective_require_signed())} (in force now)")
        print(f"Ask before the build check:       {_on_off(saved_confirm)} (saved)  {_on_off(security.effective_confirm_build())} (in force now)")
        if state == "corrupt":
            print(f"The settings file {settings.SETTINGS_PATH} cannot be read: signatures are required until it is fixed or removed.", file=sys.stderr)
        print("Both are off by default. Environment: URTC_UPDATER_REQUIRE_SIGNED, URTC_UPDATER_CONFIRM_BUILD (1 or 0).")
        return 0
    lowering = security.lowering_of_change(require_signed=new_signed, confirm_build=new_confirm)
    if lowering:
        for warning in lowering:
            print(str(warning), file=sys.stderr)
        print("Turning a protection off means updates run code from the repositories with fewer checks.", file=sys.stderr)
        if not args.yes:
            if not sys.stdin.isatty():
                print("Not changed: confirm in a terminal, or repeat the command with --yes.", file=sys.stderr)
                return 1
            if input("Turn it off anyway? [y/N] ").strip().lower() not in {"y", "yes"}:
                print("Not changed.")
                return 1
    security.save_security(require_signed=new_signed, confirm_build=new_confirm)
    print(f"Saved: signed commits {_on_off(new_signed)}, ask before the build check {_on_off(new_confirm)}.")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    return _install_or_update(args, expect_installed=False)


def cmd_update(args: argparse.Namespace) -> int:
    return _install_or_update(args, expect_installed=True)


def _install_or_update(args: argparse.Namespace, *, expect_installed: bool) -> int:
    if getattr(args, "accept_unavailable_validation", False):
        # An explicit, per-run opt-in: the install still refuses by default.
        os.environ["URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION"] = "1"
    _apply_security_arguments(args)
    workspace_root = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    local_discovery = discover_workspace(workspace_root)
    local_by_name = {status.entry.name: status.entry for status in local_discovery.projects}
    entry = local_by_name.get(args.project)

    # GitHub discovery makes a just-added manifest project installable without
    # an updater release or a hard-coded registry row.
    if entry is None or not expect_installed:
        try:
            remote_discovery = discover_remote_projects()
        except RuntimeError as exc:
            print(f"Unable to discover GitHub projects: {exc}", file=sys.stderr)
            return 1
        remote_by_name = {status.entry.name: status.entry for status in remote_discovery.projects}
        entry = remote_by_name.get(args.project, entry)

    if entry is None:
        print(f"Unknown ecosystem project: {args.project!r}", file=sys.stderr)
        print("The project must expose a valid urtc.project.json on GitHub.", file=sys.stderr)
        return 1

    try:
        profile = profiles.load_profile(getattr(args, "profile", None))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if profile is not None and not profile.allows(entry.name):
        print(f"{entry.name} is not part of the {profile.name!r} profile.", file=sys.stderr)
        return 1

    path = workspace_root / entry.name
    already_installed = path.is_dir()
    if expect_installed and not already_installed:
        print(f"{entry.name} isn't installed yet at {path} - use `install`, not `update`, the first time.", file=sys.stderr)
        return 1
    if not expect_installed and already_installed:
        print(f"{entry.name} already exists at {path} - use `update`, not `install`, for an existing checkout.", file=sys.stderr)
        return 1

    if expect_installed and getattr(args, "preview", False):
        try:
            preview = preview_update(entry, workspace_root)
        except InstallError as exc:
            print(f"FAIL {exc.args[0] if exc.args else exc}", file=sys.stderr)
            return 1
        print(f"Candidate commit: {preview.commit}")
        print(f"Author:           {preview.author}")
        print(f"Version:          {preview.installed_version} -> {preview.version}")
        print(f"Signature:        {preview.signature}")
        if preview.changed_scripts:
            print("Build/tool files changed since the installed commit:")
            for name in preview.changed_scripts:
                print(f"  {name}")
        else:
            print("Build/tool files changed since the installed commit: none")
        print("Nothing was changed. Run the same command without --preview to apply it.")
        return 0

    if entry.note:
        print(f"Note: {entry.note}")
    print(f"{'Updating' if expect_installed else 'Installing'} {entry.name} into {workspace_root} ...")

    results = install_or_update(entry, workspace_root, build=not args.no_build)
    ok = all(r.ok for r in results)
    for r in results:
        print(("OK  " if r.ok else "FAIL ") + r.message)
    return 0 if ok else 1


def _add_security_arguments(subparser: argparse.ArgumentParser) -> None:
    group = subparser.add_mutually_exclusive_group()
    group.add_argument("--require-signed", dest="require_signed", action="store_true", default=None,
                       help="Refuse a candidate commit that has no valid GPG or SSH signature (also URTC_UPDATER_REQUIRE_SIGNED=1 or the saved setting).")
    group.add_argument("--no-require-signed", dest="require_signed", action="store_false",
                       help="Do not require signed commits in this run (a warning is shown when the saved setting requires them).")
    other = subparser.add_mutually_exclusive_group()
    other.add_argument("--confirm-build", dest="confirm_build", action="store_true", default=None,
                       help="Ask before the build check of the candidate runs, showing its commit, author, signature and changed build files (also URTC_UPDATER_CONFIRM_BUILD=1 or the saved setting).")
    other.add_argument("--no-confirm-build", dest="confirm_build", action="store_false",
                       help="Do not ask before the build check in this run (a warning is shown when the saved setting asks).")
    subparser.add_argument("--yes", "-y", action="store_true", help="Answer yes to the question before the build check without asking, for scripts.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urtc-updater --cli",
        description="Detects, installs, and manually updates the URTC ecosystem's own repositories on this machine.",
    )
    parser.add_argument("--version", action="version", version=f"urtc-updater {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    status_p = subparsers.add_parser("status", help="Show what's installed, its version, and the latest GitHub version of every project.")
    status_p.add_argument("--workspace", help="Workspace root to scan (default: this tool's own parent directory).")
    status_p.add_argument("--offline", action="store_true", help="Skip the GitHub check - local state only.")
    status_p.add_argument("--notes", action="store_true", help="Also print each project's real notes (family/parent, what's actually implemented, tech) below the table.")
    status_p.add_argument("--json", action="store_true", help="Machine-readable JSON instead of the human-readable table (ignores --notes).")
    status_p.add_argument("--profile", help="Only the projects of this station profile (default: the profile selected in the settings).")
    status_p.set_defaults(func=cmd_status)

    install_p = subparsers.add_parser("install", help="Clone and build ONE project that isn't installed yet.")
    install_p.add_argument("project", help="Exact project name (see `status` for the full list).")
    install_p.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    install_p.add_argument("--no-build", action="store_true", help="Clone only - skip running the project's own build script.")
    install_p.add_argument("--profile", help="Refuse a project outside this station profile.")
    install_p.add_argument(
        "--accept-unavailable-validation", action="store_true",
        help="Go on when the project's build check says it cannot validate here (a missing tool). Without this flag such an install is refused.",
    )
    _add_security_arguments(install_p)
    install_p.set_defaults(func=cmd_install)

    update_p = subparsers.add_parser("update", help="Pull and rebuild ONE project that's already installed.")
    update_p.add_argument("project", help="Exact project name (see `status` for the full list).")
    update_p.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    update_p.add_argument("--no-build", action="store_true", help="Pull only - skip running the project's own build script.")
    update_p.add_argument("--profile", help="Refuse a project outside this station profile.")
    update_p.add_argument(
        "--preview", action="store_true",
        help="Show the candidate commit, its author, signature state and the build/tool files it changes, then stop without updating.",
    )
    update_p.add_argument(
        "--accept-unavailable-validation", action="store_true",
        help="Go on when the project's build check says it cannot validate here (a missing tool). Without this flag such an install is refused.",
    )
    _add_security_arguments(update_p)
    update_p.set_defaults(func=cmd_update)

    check_p = subparsers.add_parser(
        "check", help="Notify only: list what could be updated and change nothing (exit code 10 when something can).",
    )
    check_p.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    check_p.add_argument("--notify", action="store_true", help="Also show a desktop notification when updates are available.")
    check_p.add_argument("--quiet", action="store_true", help="Print nothing when everything is up to date.")
    check_p.add_argument("--profile", help="Only the projects of this station profile.")
    check_p.set_defaults(func=cmd_check)

    clean_p = subparsers.add_parser(
        "clean-backups", help="Remove kept previous installations (and leftover staging folders) beyond the newest N per project.",
    )
    clean_p.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    clean_p.add_argument("--keep", type=int, default=0, help="Previous installations to keep per project (default: 0).")
    clean_p.add_argument("--dry-run", action="store_true", help="Only list what would be removed.")
    clean_p.set_defaults(func=cmd_clean_backups)

    restore_p = subparsers.add_parser(
        "restore-backup", help="Put the newest kept previous installation of ONE project back in place (the current one is kept too).",
    )
    restore_p.add_argument("project", help="Exact project name.")
    restore_p.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    restore_p.add_argument("--backup", help="Folder name of the backup to restore (default: the newest).")
    restore_p.add_argument("--list", action="store_true", help="Only list the kept previous installations of the project.")
    restore_p.set_defaults(func=cmd_restore_backup)

    security_p = subparsers.add_parser(
        "security",
        help="Show or change the security options: require signed commits, ask before the build check (both off by default; turning one off asks first).",
    )
    security_p.add_argument("--require-signed", choices=["on", "off"], help="Save whether a candidate commit must carry a valid signature.")
    security_p.add_argument("--confirm-build", choices=["on", "off"], help="Save whether to ask before the build check of a candidate runs.")
    security_p.add_argument("--yes", "-y", action="store_true", help="Do not ask before saving a lower level.")
    security_p.set_defaults(func=cmd_security)

    evidence_p = subparsers.add_parser("evidence", help="Verify the hash chain of the evidence log, optionally exporting it as one JSON file.")
    evidence_p.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    evidence_p.add_argument("--export", metavar="FILE", help="Write the entries and the verification result to FILE.")
    evidence_p.add_argument("--export-common", metavar="FILE", help="Write the attempts as urtc-evidence/1 records (one JSON document per line), the shape the flasher and the tester use.")
    evidence_p.add_argument("--history", metavar="FOLDER", help="List the urtc-evidence/1 records of FOLDER (flasher, tester and updater alike), newest first, checking each one: "
                                                               "a record edited after it was written is listed as NOT VALID and the exit status is 1. Reads only.")
    evidence_p.add_argument("--json", action="store_true", help="With --history: print the list with its summary as one JSON document.")
    evidence_p.set_defaults(func=cmd_evidence)

    package.add_parser(subparsers)
    flasher_handoff.add_parser(subparsers)
    compat_view.add_parser(subparsers)

    return parser


def main() -> int:
    if "--cli" not in sys.argv:
        try:
            from .qt_gui import launch_qt_gui
        except ImportError:
            # A checkout can still run its original dependency-free desktop
            # shell before `pip install -e '.[gui]'` has been performed. This
            # is a compatibility bridge, not the preferred visual path.
            try:
                from .gui import launch_gui
            except ImportError:
                print("The Qt Quick GUI is not installed and tkinter is unavailable. "
                      "Use `--cli` on a headless system, or run the project build "
                      "to install the optional PySide6 GUI runtime.", file=sys.stderr)
                return 2
            else:
                print("Qt Quick GUI runtime is not installed; starting the legacy "
                      "Tkinter fallback. Run build.bat/build.sh to enable the new "
                      "visual desktop interface.", file=sys.stderr)
                return launch_gui(resolve_workspace_root())
        else:
            return launch_qt_gui(resolve_workspace_root())

    argv = [a for a in sys.argv[1:] if a != "--cli"]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
