# =============================================================================
# URTC-UPDATER - Install a program from the signed package of a release: package.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The "package" way of installing a URTC program: the signed ``.zip`` / ``.tar.gz`` a release carries, instead of a clone and a build.

    urtc-updater --cli package list
    urtc-updater --cli package check urtc-flasher
    urtc-updater --cli package install urtc-flasher            # the latest release on GitHub
    urtc-updater --cli package install urtc-flasher --file urtc-flasher-0.5.0-windows-x64.zip   # a file on disk (no network)
    urtc-updater --cli package rollback urtc-flasher

The rules are the ones of the programs that update themselves (``urtc_pkg/self_update.py``, copied from URTC-COMMON): only a
strictly higher version, only the download hosts of GitHub, the announced size and SHA-256, the Ed25519 signature of the key of the
releases pinned here, a safe extraction, two releases kept and a rollback. Nothing is installed without asking: the command shows the
version and the notes and waits for a yes in the terminal (``--yes`` answers it, for scripts), and a package that fails any check is
deleted. The installed programs live under ``URTC_UPDATE_ROOT`` (or the data folder of the person), one folder per program, each with its
own ``releases/<version>/`` and ``current.txt``; the launcher of the program (``python -m urtc_updater.urtc_pkg.launcher ROOT``) starts the
current one and goes back to the previous release when a first start fails.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from . import settings
from .urtc_pkg import self_update as su
from .urtc_pkg import update_service as svc

KNOWN_APPS = ("urtc-flasher", "urtc-tester", "urtc-updater")
NOT_INSTALLED = "0.0.0"


def root_of(app: str) -> Path:
    return svc.default_root(app)


def installed_version(app: str) -> str:
    return su.current_version(root_of(app)) or NOT_INSTALLED


def make_service(app: str, fetch: Callable | None = None, busy: Callable | None = None) -> svc.UpdateService:
    """The service of one program, with the options saved in the settings of the updater (never-by-itself defaults)."""
    if app not in KNOWN_APPS:
        raise su.UpdateError("bad_app", f"{app} is not one of: {', '.join(KNOWN_APPS)}")
    policy = svc.policy_from(settings.load_settings())
    args = (app, installed_version(app), root_of(app), policy, svc.RELEASE_PUBLIC_KEY_HEX, svc.RELEASE_KEY_ID)
    if fetch is not None:
        return svc.UpdateService(*args, busy=busy, fetch=fetch)
    return svc.UpdateService(*args, busy=busy)


def _said(error: su.UpdateError) -> str:
    return f"{error.code}: {error}"


def _confirm(prompt: str, assume_yes: bool, ask: Callable[[str], str] | None = None) -> bool:
    if assume_yes:
        return True
    if ask is None:
        if not sys.stdin.isatty():
            print("Not installed: confirm in a terminal, or repeat the command with --yes.", file=sys.stderr)
            return False
        ask = input
    return ask(prompt).strip().lower() in {"y", "yes"}


def cmd_package(args: argparse.Namespace, fetch: Callable | None = None, ask: Callable[[str], str] | None = None) -> int:
    action = args.package_command
    try:
        if action == "list":
            for app in KNOWN_APPS:
                version = su.current_version(root_of(app))
                kept = ", ".join(su.installed_versions(root_of(app))) or "-"
                print(f"{app:14} {version or 'not installed':14} kept: {kept}   ({root_of(app)})")
            return 0
        service = make_service(args.app, fetch)
        if action == "rollback":
            print(f"{args.app}: current.txt now points to {service.rollback()}. The program starts it next time.")
            return 0
        if action == "check":
            offer = service.check()
            if offer is None:
                print(f"{args.app}: {service.installed} is the latest version with a package for this system.")
                return 0
            print(f"{args.app}: version {offer.version} is available (installed: {service.installed}).")
            return 10
        # install
        if args.file:
            prepared = service.prepare_local(args.file)
            print(f"{args.app}: {Path(args.file).name} checked (SHA-256 and signature).")
        else:
            offer = service.check()
            if offer is None:
                print(f"{args.app}: nothing newer than {service.installed} for this system.")
                return 0
            print(f"{args.app}: version {offer.version} is available (installed: {service.installed}).")
            if offer.notes.strip():
                print("What is new:\n" + "\n".join("  " + line for line in offer.notes.strip().splitlines()[:20]))
            prepared = service.prepare(offer, None)
            print(f"{args.app}: {prepared.path.name} downloaded and checked (SHA-256 and signature).")
        confirmed = _confirm(f"Install {args.app} {prepared.offer.version}? The previous version stays for a rollback. [y/N] ", args.yes, ask)
        if not confirmed:
            print("Not installed. Nothing was changed.")
            return 1
        service.install(prepared, confirmed=True)
        print(f"{args.app} {prepared.offer.version} installed in {service.root}. Start it with the launcher or from its folder.")
        return 0
    except su.UpdateError as error:
        print(f"PACKAGE=FAIL {_said(error)}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"PACKAGE=FAIL network_or_disk: {error}", file=sys.stderr)
        return 1


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Adds ``package`` and its four actions to the command line."""
    package_p = subparsers.add_parser("package", help="Install a program from the signed package of its release (list, check, install, rollback).")
    package_p.set_defaults(func=cmd_package)
    actions = package_p.add_subparsers(dest="package_command", required=True)
    actions.add_parser("list", help="Show the installed version and the kept releases of every program.")
    for name, text in (("check", "Ask GitHub once whether a newer package exists (exit code 10 when it does)."),
                       ("install", "Download, check and install the latest package, or the one in --file."),
                       ("rollback", "Point the program back to its previous release.")):
        action_p = actions.add_parser(name, help=text)
        action_p.add_argument("app", choices=KNOWN_APPS)
        if name == "install":
            action_p.add_argument("--file", help="A package on disk (its .sha256 and .sig next to it); no network is used.")
            action_p.add_argument("--yes", "-y", action="store_true", help="Answer the confirmation with yes (for scripts).")
