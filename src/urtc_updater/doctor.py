# =============================================================================
# URTC-UPDATER - The doctor: what this computer has for the family, and what is next to this program: doctor.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""One report on this computer for the URTC family.

    urtc-updater --cli doctor                # the tools, the serial ports that could be an SLCAN adapter, the projects and the firmware of the Flasher
    urtc-updater --cli doctor --probe        # also ask each candidate adapter (and each virtual board of URTC_VIRTUAL_PORT) for its version
    urtc-updater --cli doctor --json         # the same as data

It reads. A serial port is opened only with ``--probe`` (or the button of the window), and then the only thing sent is the version query of the SLCAN text
protocol: the channel is not opened and no frame goes to the bus. What it looks for (the USB identifiers of adapters, the words of their descriptions, the
speed and the time of the query, the names of the programs) is in ``doctor.json``, not in this code. Exit status: 0 when nothing is missing that the family
needs, 1 when something it needs is (git), 2 when the workspace cannot be read.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import doctor_texts, firmware_sync
from .compat_view import compat_matrix_path
from .urtc_pkg import compat

OK, WARN, FAIL, INFO = "ok", "warn", "fail", "info"
SECTION_MACHINE, SECTION_ADAPTERS, SECTION_PROJECTS, SECTION_SYNC = "machine", "adapters", "projects", "sync"
CONFIG = Path(__file__).resolve().parent / "doctor.json"


@dataclass(frozen=True)
class Check:
    section: str
    state: str
    key: str
    values: dict[str, Any] = field(default_factory=dict)

    def text(self, language: str) -> str:
        return doctor_texts.text(language, self.key, **self.values)


def load_config(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------------------------------
# the tools of the machine
# ---------------------------------------------------------------------------------------------------------------------
def _first_line(output: str) -> str:
    for line in output.splitlines():
        if line.strip():
            return line.strip()[:120]
    return "?"


def program_version(name: str, config: dict, *, which: Callable[[str], str | None], run: Callable[..., Any]) -> str | None:
    """The first line of ``name --version``, or None when the program is not found. A program that does not answer in time is found, with an unknown version."""
    found = which(name)
    if found is None:
        return None
    try:
        done = run([found, "--version"], capture_output=True, text=True, timeout=float(config["tools"]["version_timeout_seconds"]), check=False)
    except (OSError, subprocess.SubprocessError):
        return "?"
    return _first_line((done.stdout or "") + (done.stderr or "")) if done.returncode == 0 else "?"


def module_version(name: str, distribution: str, *, find_spec: Callable[[str], Any]) -> str | None:
    try:
        if find_spec(name) is None:
            return None
    except (ImportError, ValueError):
        return None
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "?"


def check_machine(config: dict, *, which: Callable[[str], str | None] = shutil.which, run: Callable[..., Any] = subprocess.run,
                  find_spec: Callable[[str], Any] = importlib.util.find_spec, python_version: str | None = None) -> list[Check]:
    checks = [Check(SECTION_MACHINE, INFO, "python", {"version": python_version or sys.version.split()[0]})]
    tools = config["tools"]
    # (config key, check key prefix, state when missing)
    for group, prefix, missing_state in (("git", "git", FAIL), ("toolchain", "toolchain", WARN), ("host_compiler", "hostcc", INFO), ("node", "node", INFO)):
        version = None
        for name in tools[group]:
            version = program_version(name, config, which=which, run=run)
            if version is not None:
                break
        checks.append(Check(SECTION_MACHINE, OK, f"{prefix}_ok", {"version": version}) if version is not None else Check(SECTION_MACHINE, missing_state, f"{prefix}_missing"))
    for module, distribution, prefix, missing_state in (("PySide6", "PySide6", "pyside", WARN), ("serial", "pyserial", "pyserial", WARN)):
        version = module_version(module, distribution, find_spec=find_spec)
        checks.append(Check(SECTION_MACHINE, OK, f"{prefix}_ok", {"version": version}) if version is not None else Check(SECTION_MACHINE, missing_state, f"{prefix}_missing"))
    return checks


# ---------------------------------------------------------------------------------------------------------------------
# the adapters
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Port:
    device: str
    description: str
    vid: int | None = None
    pid: int | None = None


def serial_ports() -> list[Port]:
    """The serial ports the system lists (pyserial). Nothing is opened. Empty when pyserial is not installed."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return [Port(item.device, item.description or "", item.vid, item.pid) for item in list_ports.comports()]


def classify_port(port: Port, config: dict) -> str | None:
    """The reason this port could be an SLCAN adapter (the name of its USB identifier, or the word of its description that gave it away), else None."""
    for entry in config["usb_ids"]:
        if port.vid is not None and port.pid is not None and (port.vid, port.pid) == (int(entry["vid"], 16), int(entry["pid"], 16)):
            return entry["name"]
    lowered = port.description.lower()
    for word in config["keywords"]:
        if word in lowered:
            return word
    return None


def probe_serial(port: Port, config: dict, *, opener: Callable[..., Any] | None = None) -> tuple[str, str]:
    """Ask the port for its version: ('answer', text), ('silent', '') or ('busy', ''). Only the version query is written; the channel is not opened."""
    settings = config["probe"]
    if opener is None:
        try:
            import serial
        except ImportError:
            return "busy", ""
        opener = serial.Serial
    try:
        handle = opener(port.device, int(settings["baudrate"]), timeout=float(settings["timeout_seconds"]), write_timeout=float(settings["timeout_seconds"]))
    except (OSError, ValueError):
        return "busy", ""
    except Exception:   # pyserial raises its own exception type for a port that is in use
        return "busy", ""
    try:
        try:
            handle.reset_input_buffer()
            handle.write(settings["query"].encode("ascii"))
            raw = handle.read(16)
        except Exception:
            return "silent", ""
    finally:
        try:
            handle.close()
        except Exception:
            pass
    answer = raw.decode("ascii", "replace").strip("\r\x07 \n")
    return ("answer", answer) if answer.startswith(settings["answer_prefix"]) and len(answer) >= 2 else ("silent", "")


def probe_virtual(url: str, config: dict, *, connect: Callable[..., Any] = socket.create_connection) -> tuple[str, str]:
    """The same query to a virtual board named by a ``socket://host:port`` URL."""
    settings = config["probe"]
    host, _, port = url[len("socket://"):].partition(":")
    try:
        with connect((host, int(port)), timeout=float(settings["timeout_seconds"]) * 3) as stream:
            stream.settimeout(float(settings["timeout_seconds"]) * 3)
            stream.sendall(settings["query"].encode("ascii"))
            raw = stream.recv(16)
    except (OSError, ValueError):
        return "silent", ""
    answer = raw.decode("ascii", "replace").strip("\r\x07 \n")
    return ("answer", answer) if answer.startswith(settings["answer_prefix"]) and len(answer) >= 2 else ("silent", "")


def virtual_urls(environ: dict[str, str] | os._Environ[str] = os.environ) -> list[str]:
    return [item.strip() for item in environ.get("URTC_VIRTUAL_PORT", "").split(",") if item.strip().startswith("socket://")]


def check_adapters(config: dict, *, probe: bool = False, ports: Callable[[], list[Port]] = serial_ports, environ: dict[str, str] | os._Environ[str] = os.environ,
                   serial_probe: Callable[..., tuple[str, str]] = probe_serial, virtual_probe: Callable[..., tuple[str, str]] = probe_virtual) -> list[Check]:
    checks: list[Check] = []
    candidates: list[Port] = []
    for port in ports():
        reason = classify_port(port, config)
        if reason is None:
            checks.append(Check(SECTION_ADAPTERS, INFO, "adapter_other", {"port": port.device, "description": port.description or "-"}))
        else:
            candidates.append(port)
            checks.append(Check(SECTION_ADAPTERS, OK, "adapter_found", {"port": port.device, "description": port.description or reason}))
    if not candidates:
        checks.insert(0, Check(SECTION_ADAPTERS, WARN, "adapters_none"))
    urls = virtual_urls(environ)
    if probe:
        for port in candidates:
            result, answer = serial_probe(port, config)
            key, state = {"answer": ("probe_answer", OK), "silent": ("probe_silent", WARN), "busy": ("probe_busy", WARN)}[result]
            checks.append(Check(SECTION_ADAPTERS, state, key, {"port": port.device, "answer": answer}))
        for url in urls:
            result, answer = virtual_probe(url, config)
            checks.append(Check(SECTION_ADAPTERS, OK if result == "answer" else WARN, "virtual_up" if result == "answer" else "virtual_down", {"url": url, "answer": answer}))
    else:
        for url in urls:
            checks.append(Check(SECTION_ADAPTERS, INFO, "virtual_listed", {"url": url}))
        if candidates or urls:
            checks.append(Check(SECTION_ADAPTERS, INFO, "probe_off"))
    return checks


# ---------------------------------------------------------------------------------------------------------------------
# the projects and the firmware of the Flasher
# ---------------------------------------------------------------------------------------------------------------------
def check_projects(workspace: Path, language: str) -> list[Check]:
    matrix = compat.load_matrix(compat_matrix_path())
    result = compat.report(matrix, workspace, language)
    rows = result["rows"]
    installed = [row for row in rows if row.state != compat.MISSING]
    checks: list[Check] = []
    if not installed:
        return [Check(SECTION_PROJECTS, WARN, "projects_none")]
    checks.append(Check(SECTION_PROJECTS, INFO, "projects", {"installed": len(installed), "total": len(rows)}))
    differing = [row for row in installed if row.state != compat.MATCH]
    checks.append(Check(SECTION_PROJECTS, WARN, "compat_differ", {"count": len(differing)}) if differing else Check(SECTION_PROJECTS, OK, "compat_ok"))
    for line in result["firmware"]:
        checks.append(Check(SECTION_PROJECTS, INFO, "firmware_line", {"line": line}))
    return checks


def check_sync(workspace: Path) -> list[Check]:
    checks = [Check(SECTION_SYNC, INFO, "sync_on" if firmware_sync.enabled() else "sync_off")]
    try:
        work = firmware_sync.plan(workspace)
    except (OSError, ValueError) as exc:
        return [*checks, Check(SECTION_SYNC, INFO, "sync_unavailable", {"reason": str(exc)})]
    if work.problems:
        checks.append(Check(SECTION_SYNC, INFO, "sync_unavailable", {"reason": "; ".join(work.problems)}))
    elif work.copies:
        checks.append(Check(SECTION_SYNC, WARN, "sync_pending", {"count": len(work.copies)}))
    else:
        checks.append(Check(SECTION_SYNC, OK, "sync_current"))
    return checks


def run_doctor(workspace: Path, language: str = "english", *, probe: bool = False, config: dict | None = None) -> list[Check]:
    config = config or load_config()
    return [*check_machine(config), *check_adapters(config, probe=probe), *check_projects(workspace, language), *check_sync(workspace)]


# ---------------------------------------------------------------------------------------------------------------------
# the command
# ---------------------------------------------------------------------------------------------------------------------
def exit_status(checks: list[Check]) -> int:
    return 1 if any(check.state == FAIL for check in checks) else 0


def render(checks: list[Check], language: str) -> str:
    out: list[str] = []
    for section in (SECTION_MACHINE, SECTION_ADAPTERS, SECTION_PROJECTS, SECTION_SYNC):
        rows = [check for check in checks if check.section == section]
        if not rows:
            continue
        out.append(doctor_texts.text(language, f"section_{section}") + ":")
        for check in rows:
            out.append(f"  [{doctor_texts.text(language, 'state_' + check.state)}] {check.text(language)}")
    return "\n".join(out)


def cmd_doctor(args: argparse.Namespace) -> int:
    from .main import default_workspace_root  # imported late: main imports this module

    workspace = Path(args.workspace).resolve() if args.workspace else default_workspace_root()
    if not workspace.is_dir():
        print(f"workspace does not exist: {workspace}", file=sys.stderr)
        return 2
    try:
        checks = run_doctor(workspace, args.language, probe=bool(args.probe))
    except (OSError, ValueError) as exc:
        print(f"the doctor cannot read what it needs: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"workspace": str(workspace), "checks": [{"section": c.section, "state": c.state, "key": c.key, "values": c.values, "text": c.text(args.language)} for c in checks]},
                         indent=2, ensure_ascii=False))
    else:
        print(doctor_texts.text(args.language, "title"))
        print(render(checks, args.language))
    return exit_status(checks)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("doctor", help="Report the tools of this computer, the SLCAN adapters it can see, the installed projects and the firmware of the Flasher (read-only).")
    parser.add_argument("--workspace", help="Workspace root (default: this tool's own parent directory).")
    parser.add_argument("--probe", action="store_true", help="Open each candidate adapter and each virtual board and ask for its version (the only thing sent; no frame goes to the bus).")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON.")
    parser.add_argument("--language", default="english", choices=doctor_texts.LANGUAGES, help="Language of the report (default: english).")
    parser.set_defaults(func=cmd_doctor)
