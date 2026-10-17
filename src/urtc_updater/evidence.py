# =============================================================================
# URTC-UPDATER - src/urtc_updater/evidence.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
# =============================================================================
"""One line of evidence for every install or update attempt: which project,
what was installed before, what is installed now, at which commit, and
whether the attempt succeeded. Appended to a JSON-lines file in the
workspace, so a failed or interrupted attempt leaves a trace and a
successful one can be checked later. Recording never raises: a problem
writing the record must not turn a good update into a failed one.

Every line also carries the hash of the line before it and its own hash, so
the file can be exported and later checked for edited, removed or reordered
lines with `verify_chain()`."""
from __future__ import annotations

import getpass
import hashlib
import json
import logging
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__

EVIDENCE_DIRECTORY = ".urtc-updater"
EVIDENCE_FILE = "evidence.jsonl"


def _line_hash(previous_hash: str, line: dict[str, Any]) -> str:
    body = json.dumps({k: v for k, v in line.items() if k not in ("hash", "previousHash")}, sort_keys=True)
    return hashlib.sha256((previous_hash + body).encode("utf-8")).hexdigest()


def _last_hash(path: Path) -> str:
    """The hash the next line must chain to: the last line's own hash, or for
    a file written before lines were chained, the hash of that raw line."""
    try:
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return ""
    if not lines:
        return ""
    try:
        recorded = json.loads(lines[-1]).get("hash")
    except ValueError:
        recorded = None
    return recorded if isinstance(recorded, str) and recorded else hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()


def installed_state(project_path: Path) -> dict[str, str | None]:
    """The version and commit of what is installed at `project_path`, or None for each when unknown."""
    version = commit = None
    manifest = project_path / "urtc.project.json"
    try:
        version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        pass
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_path), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if completed.returncode == 0:
            commit = completed.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    return {"version": version, "commit": commit}


def _current_user() -> str:
    try:
        return getpass.getuser()
    except (OSError, KeyError, ImportError):
        return ""


def record_attempt(
    workspace_root: Path,
    *,
    project: str,
    before: dict[str, Any],
    after: dict[str, Any],
    ok: bool,
    message: str,
) -> Path | None:
    """Append one attempt to the evidence file; returns its path, or None if it could not be written."""
    line = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "updaterVersion": __version__,
        "host": platform.node(),
        "user": _current_user(),
        "project": project,
        "ok": ok,
        "versionBefore": before.get("version"),
        "commitBefore": before.get("commit"),
        "versionAfter": after.get("version"),
        "commitAfter": after.get("commit"),
        "message": message[:500],
    }
    try:
        directory = workspace_root / EVIDENCE_DIRECTORY
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / EVIDENCE_FILE
        line["previousHash"] = _last_hash(path)
        line["hash"] = _line_hash(line["previousHash"], line)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(line, sort_keys=True) + "\n")
        return path
    except OSError as error:
        # The attempt is still reported to the person; only the evidence file could not be written, and that is said instead of passing unnoticed.
        logging.getLogger(__name__).warning("the evidence of the attempt on %s could not be written: %s", project, error)
        return None


def read_attempts(workspace_root: Path) -> list[dict[str, Any]]:
    path = workspace_root / EVIDENCE_DIRECTORY / EVIDENCE_FILE
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return []


def verify_chain(workspace_root: Path) -> list[str]:
    """The problems found in the evidence file's hash chain (empty when it is
    intact). Lines written before chaining existed are accepted as they are;
    from the first chained line on, every line must carry the hash of the
    one before it and match its own content."""
    path = workspace_root / EVIDENCE_DIRECTORY / EVIDENCE_FILE
    try:
        raw_lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return []
    problems: list[str] = []
    previous = ""
    chained = False
    for number, raw in enumerate(raw_lines, start=1):
        try:
            line = json.loads(raw)
        except ValueError:
            problems.append(f"line {number}: not valid JSON")
            previous = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            continue
        recorded = line.get("hash")
        if not isinstance(recorded, str):
            if chained:
                problems.append(f"line {number}: missing hash")
            previous = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            continue
        chained = True
        if line.get("previousHash") != previous:
            problems.append(f"line {number}: does not follow the previous line (a line was removed, added or reordered)")
        if _line_hash(str(line.get("previousHash", "")), line) != recorded:
            problems.append(f"line {number}: content does not match its hash (edited)")
        previous = recorded
    return problems


def export_evidence(workspace_root: Path, destination: Path) -> Path:
    """Writes the evidence as one JSON document - the entries plus whether
    the chain verified - for keeping with a production record."""
    problems = verify_chain(workspace_root)
    document = {
        "exportedBy": f"urtc-updater {__version__}",
        "workspace": str(workspace_root),
        "chainIntact": not problems,
        "problems": problems,
        "entries": read_attempts(workspace_root),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination
