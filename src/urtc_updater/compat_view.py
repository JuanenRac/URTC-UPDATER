# =============================================================================
# URTC-UPDATER - Compatibility of what is installed: compat_view.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Compare the folders of the workspace with the compatibility matrix of the release this program carries.

    urtc-updater --cli compat                  # a table: each project as released, newer, older, not installed or unknown
    urtc-updater --cli compat --json           # the same as data

It reads manifests and file names and nothing else: it changes nothing, starts nothing and does not use the network. The exit code is 0
whatever the result (a different version is information, not an error); 2 only when the matrix or the workspace cannot be read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .urtc_pkg import compat


def compat_matrix_path() -> Path:
    """The matrix that travels with this program (copied from URTC-COMMON, never edited here)."""
    return Path(__file__).resolve().parent / "urtc_pkg" / "compat.json"


def cmd_compat(args: argparse.Namespace) -> int:
    from .main import default_workspace_root  # imported late: main imports this module

    workspace = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    if not workspace.is_dir():
        print(f"workspace does not exist: {workspace}", file=sys.stderr)
        return 2
    try:
        matrix = compat.load_matrix(compat_matrix_path())
    except (OSError, ValueError) as exc:
        print(f"the compatibility matrix cannot be read: {exc}", file=sys.stderr)
        return 2
    result = compat.report(matrix, workspace, args.language)
    if args.json:
        print(json.dumps({
            "protocol": result["protocol"], "counts": result["counts"], "firmware": result["firmware"],
            "projects": [{"repo": row.repo, "release": row.expected, "installed": row.found, "state": row.state,
                          "shared_code_release": row.common_expected, "shared_code_installed": row.common_found, "shared_code_state": row.common_state}
                         for row in result["rows"]],
        }, indent=2, ensure_ascii=False))
        return 0
    print(compat.text(args.language, "intro", protocol=result["protocol"]))
    if not result["any_installed"]:
        print(compat.text(args.language, "none_installed"))
    width = max(len(row.repo) for row in result["rows"]) + 2
    print(f"{compat.text(args.language, 'project'):<{width}}{compat.text(args.language, 'expected'):<12}{compat.text(args.language, 'found'):<12}{compat.text(args.language, 'state')}")
    for row in result["rows"]:
        print(f"{row.repo:<{width}}{row.expected:<12}{row.found or '-':<12}{compat.text(args.language, row.state)}")
    print()
    print(compat.text(args.language, "firmware") + ":")
    for line in result["firmware"] or ["-"]:
        print("  " + line)
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("compat", help="Compare the installed projects with the compatibility matrix of the release (read-only).")
    parser.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON.")
    parser.add_argument("--language", default="english", choices=compat.LANGUAGES, help="Language of the table (default: english).")
    parser.set_defaults(func=cmd_compat)
