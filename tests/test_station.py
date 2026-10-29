# =============================================================================
# URTC-UPDATER - tests/test_station.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Evidence hash chain and export, station profiles, the notify-only check,
desktop notifications, log rotation and the cached repository listing."""
from __future__ import annotations

import argparse
import http.server
import json
import os
import threading
import time
from pathlib import Path

import pytest
from repo_helpers import NAME, entry, make_remote

from urtc_updater import commits, github_client, profiles, settings
from urtc_updater import main as main_module
from urtc_updater.evidence import (
    EVIDENCE_DIRECTORY,
    EVIDENCE_FILE,
    export_evidence,
    read_attempts,
    record_attempt,
    verify_chain,
)
from urtc_updater.github_client import RemoteStatus
from urtc_updater.logs import prune_logs
from urtc_updater.notify import notification_command, send_notification
from urtc_updater.version_parse import Version


# --- evidence hash chain -----------------------------------------------------

def _record(workspace: Path, text: str) -> None:
    record_attempt(workspace, project="P", before={}, after={}, ok=True, message=text)


def _lines(workspace: Path) -> list[str]:
    return (workspace / EVIDENCE_DIRECTORY / EVIDENCE_FILE).read_text(encoding="utf-8").splitlines()


def _write_lines(workspace: Path, lines: list[str]) -> None:
    (workspace / EVIDENCE_DIRECTORY / EVIDENCE_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_each_line_carries_the_hash_of_the_one_before(tmp_path: Path):
    for text in ("one", "two", "three"):
        _record(tmp_path, text)
    attempts = read_attempts(tmp_path)
    assert attempts[0]["previousHash"] == ""
    assert attempts[1]["previousHash"] == attempts[0]["hash"]
    assert attempts[2]["previousHash"] == attempts[1]["hash"]
    assert len({a["hash"] for a in attempts}) == 3
    assert verify_chain(tmp_path) == []


def test_an_edited_line_is_detected(tmp_path: Path):
    for text in ("one", "two", "three"):
        _record(tmp_path, text)
    lines = _lines(tmp_path)
    lines[1] = lines[1].replace('"two"', '"changed"')
    _write_lines(tmp_path, lines)
    problems = verify_chain(tmp_path)
    assert any("line 2" in p and "edited" in p for p in problems)


def test_a_removed_line_is_detected(tmp_path: Path):
    for text in ("one", "two", "three"):
        _record(tmp_path, text)
    lines = _lines(tmp_path)
    del lines[1]
    _write_lines(tmp_path, lines)
    assert any("line 2" in p and "removed" in p for p in verify_chain(tmp_path))


def test_reordered_lines_are_detected(tmp_path: Path):
    for text in ("one", "two", "three"):
        _record(tmp_path, text)
    lines = _lines(tmp_path)
    lines[1], lines[2] = lines[2], lines[1]
    _write_lines(tmp_path, lines)
    assert verify_chain(tmp_path)


def test_lines_written_before_chaining_are_accepted_and_chained_after(tmp_path: Path):
    directory = tmp_path / EVIDENCE_DIRECTORY
    directory.mkdir()
    (directory / EVIDENCE_FILE).write_text(json.dumps({"project": "old", "ok": True}) + "\n", encoding="utf-8")
    assert verify_chain(tmp_path) == []
    _record(tmp_path, "new")
    _record(tmp_path, "newer")
    assert verify_chain(tmp_path) == []
    assert read_attempts(tmp_path)[1]["previousHash"] != ""


def test_a_line_without_a_hash_after_the_chain_started_is_a_problem(tmp_path: Path):
    _record(tmp_path, "one")
    lines = _lines(tmp_path)
    lines.append(json.dumps({"project": "sneaked in", "ok": True}))
    _write_lines(tmp_path, lines)
    assert any("missing hash" in p for p in verify_chain(tmp_path))


def test_no_evidence_file_is_not_a_problem(tmp_path: Path):
    assert verify_chain(tmp_path) == []


def test_the_export_holds_the_entries_and_the_verdict(tmp_path: Path):
    _record(tmp_path, "one")
    _record(tmp_path, "two")
    destination = export_evidence(tmp_path, tmp_path / "out" / "evidence.json")
    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["chainIntact"] is True and document["problems"] == []
    assert [e["message"] for e in document["entries"]] == ["one", "two"]
    lines = _lines(tmp_path)
    lines[0] = lines[0].replace('"one"', '"x"')
    _write_lines(tmp_path, lines)
    broken = json.loads(export_evidence(tmp_path, tmp_path / "again.json").read_text(encoding="utf-8"))
    assert broken["chainIntact"] is False and broken["problems"]


def test_the_evidence_command_exports_and_sets_the_exit_code(tmp_path: Path, capsys):
    _record(tmp_path, "one")
    args = argparse.Namespace(workspace=str(tmp_path), export=str(tmp_path / "e.json"), export_common=str(tmp_path / "common.jsonl"))
    assert main_module.cmd_evidence(args) == 0
    out = capsys.readouterr().out
    assert "Evidence chain intact." in out and (tmp_path / "e.json").is_file()
    assert "urtc-evidence/1" in out and (tmp_path / "common.jsonl").is_file()
    lines = _lines(tmp_path)
    lines[0] = lines[0].replace('"one"', '"x"')
    _write_lines(tmp_path, lines)
    assert main_module.cmd_evidence(argparse.Namespace(workspace=str(tmp_path), export=None, export_common=None)) == 1
    assert "PROBLEM" in capsys.readouterr().err


# --- profiles ----------------------------------------------------------------

def test_without_a_profile_nothing_is_restricted():
    assert profiles.load_profile() is None


def test_a_profile_lists_its_projects_and_batch_permission():
    settings.save_settings(profiles={"bench": {"projects": ["URTC", "URTC-FLASHER"], "allow_batch": False},
                                      "all": {}}, profile="bench")
    selected = profiles.load_profile()
    assert selected is not None and selected.name == "bench"
    assert selected.allows("URTC") and not selected.allows("URTC-TESTER")
    assert selected.allow_batch is False
    everything = profiles.load_profile("all")
    assert everything is not None and everything.allows("anything") and everything.allow_batch is True


def test_an_undefined_profile_is_an_error_not_no_restriction():
    settings.save_settings(profiles={"bench": {}})
    with pytest.raises(ValueError, match="not defined"):
        profiles.load_profile("benhc")


def test_status_only_lists_the_projects_of_the_profile(tmp_path: Path, capsys):
    for name in ("URTC-A", "URTC-B"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "urtc.project.json").write_text(
            json.dumps({**json.loads(_manifest(name))}), encoding="utf-8")
    settings.save_settings(profiles={"only-a": {"projects": ["URTC-A"]}})
    args = argparse.Namespace(workspace=str(tmp_path), offline=True, notes=False, json=True, profile="only-a")
    assert main_module.cmd_status(args) == 0
    names = [p["name"] for p in json.loads(capsys.readouterr().out)["projects"]]
    assert names == ["URTC-A"]


def _manifest(name: str) -> str:
    from repo_helpers import manifest_text

    return manifest_text("1.0.0", name)


def test_install_and_update_refuse_a_project_outside_the_profile(tmp_path: Path, capsys, monkeypatch):
    folder = tmp_path / "URTC-B"
    folder.mkdir()
    (folder / "urtc.project.json").write_text(_manifest("URTC-B"), encoding="utf-8")
    settings.save_settings(profiles={"only-a": {"projects": ["URTC-A"]}})
    called: list[object] = []
    monkeypatch.setattr(main_module, "install_or_update", lambda *a, **k: called.append(a) or [])
    args = argparse.Namespace(workspace=str(tmp_path), project="URTC-B", no_build=False, preview=False, profile="only-a")
    assert main_module.cmd_update(args) == 1
    assert "not part of the 'only-a' profile" in capsys.readouterr().err and not called
    args.profile = "missing"
    assert main_module.cmd_update(args) == 1
    assert "not defined" in capsys.readouterr().err


# --- notify-only check -------------------------------------------------------

def _check_args(workspace: Path, **overrides) -> argparse.Namespace:
    values = {"workspace": str(workspace), "notify": False, "quiet": False, "profile": None}
    values.update(overrides)
    return argparse.Namespace(**values)


def _remote_status(version: str) -> dict[str, RemoteStatus]:
    return {NAME: RemoteStatus(entry=entry(), version=Version.from_string(version))}


def test_check_exits_zero_and_says_so_when_everything_is_current(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(main_module, "fetch_all", lambda entries: _remote_status("1.0.0"))
    assert main_module.cmd_check(_check_args(remote.workspace)) == 0
    assert "up to date" in capsys.readouterr().out
    assert main_module.cmd_check(_check_args(remote.workspace, quiet=True)) == 0
    assert capsys.readouterr().out == ""


def test_check_lists_a_newer_version_and_changes_nothing(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    head = commits.local_head(remote.checkout)
    monkeypatch.setattr(main_module, "fetch_all", lambda entries: _remote_status("1.2.0"))
    assert main_module.cmd_check(_check_args(remote.workspace)) == main_module.EXIT_UPDATES_AVAILABLE == 10
    output = capsys.readouterr().out
    assert f"{NAME} 1.0.0 -> 1.2.0" in output and "nothing was changed" in output
    assert commits.local_head(remote.checkout) == head


def test_check_also_reports_new_commits_at_the_same_version(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    remote.push("1.0.0", "fix", {"fix.txt": "x\n"})
    monkeypatch.setattr(main_module, "fetch_all", lambda entries: _remote_status("1.0.0"))
    assert main_module.cmd_check(_check_args(remote.workspace)) == 10
    assert "new commits at the same version" in capsys.readouterr().out


def test_check_sends_a_notification_only_when_asked_and_only_when_there_is_something(tmp_path: Path, monkeypatch, capsys):
    remote = make_remote(tmp_path)
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(main_module, "send_notification", lambda title, body: sent.append((title, body)) or True)
    monkeypatch.setattr(main_module, "fetch_all", lambda entries: _remote_status("1.0.0"))
    main_module.cmd_check(_check_args(remote.workspace, notify=True))
    assert sent == []
    monkeypatch.setattr(main_module, "fetch_all", lambda entries: _remote_status("1.3.0"))
    main_module.cmd_check(_check_args(remote.workspace))
    assert sent == []
    main_module.cmd_check(_check_args(remote.workspace, notify=True))
    assert len(sent) == 1 and "1.0.0 -> 1.3.0" in sent[0][1]
    monkeypatch.setattr(main_module, "send_notification", lambda title, body: False)
    main_module.cmd_check(_check_args(remote.workspace, notify=True))
    assert "no desktop notification could be shown" in capsys.readouterr().err


def test_check_respects_a_profile(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    settings.save_settings(profiles={"elsewhere": {"projects": ["URTC-OTHER"]}})
    monkeypatch.setattr(main_module, "fetch_all", lambda entries: _remote_status("9.0.0"))
    assert main_module.cmd_check(_check_args(remote.workspace, profile="elsewhere")) == 0


# --- desktop notification ----------------------------------------------------

def test_the_notification_command_matches_each_system():
    assert notification_command("T", "B", "linux")[:1] == ["notify-send"]
    assert notification_command("T", "B", "darwin")[:2] == ["osascript", "-e"]
    windows = notification_command("It's", "B", "win32")
    assert windows[0] == "powershell" and "'It''s'" in windows[-1]
    assert notification_command("T", "B", "plan9") is None


def test_the_notification_quotes_its_text_on_macos():
    command = notification_command('say "hi"', 'a\\b', "darwin")
    assert '\\"hi\\"' in command[2] and "a\\\\b" in command[2]


def test_sending_runs_the_command_and_reports_failure_honestly():
    ran: list[list[str]] = []
    assert send_notification("T", "B", runner=lambda command, **kw: ran.append(command), platform="linux") is True
    assert ran == [["notify-send", "T", "B"]]

    def broken(command, **kw):
        raise FileNotFoundError("notify-send")

    assert send_notification("T", "B", runner=broken, platform="linux") is False
    assert send_notification("T", "B", runner=broken, platform="plan9") is False


# --- log rotation ------------------------------------------------------------

def test_old_log_files_are_removed_beyond_the_limit(tmp_path: Path):
    files = []
    for number in range(8):
        path = tmp_path / f"gui_2000010{number}_000000.log"
        path.write_text("x", encoding="utf-8")
        stamp = time.time() - (100 - number)
        os.utime(path, (stamp, stamp))
        files.append(path)
    other = tmp_path / "keep-me.txt"
    other.write_text("x", encoding="utf-8")
    removed = prune_logs(tmp_path, keep=3)
    assert sorted(removed) == sorted(files[:5])
    assert all(p.exists() for p in files[5:]) and other.exists()
    assert prune_logs(tmp_path, keep=3) == []
    assert prune_logs(tmp_path / "absent", keep=3) == []


# --- cached repository listing ----------------------------------------------

class _EtagHandler(http.server.BaseHTTPRequestHandler):
    listing = b"[]"
    etag = '"v1"'
    requests: list[tuple[str, str | None]] = []

    def log_message(self, format, *args):
        pass

    def do_GET(self) -> None:
        self.requests.append((self.path, self.headers.get("If-None-Match")))
        if self.path.startswith("/users/"):
            if self.headers.get("If-None-Match") == self.etag:
                self.send_response(304)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("ETag", self.etag)
            self.end_headers()
            self.wfile.write(self.listing)
            return
        if self.path == "/JuanenRac/URTC-EXAMPLE/main/urtc.project.json":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(_manifest(NAME).encode())
            return
        self.send_response(404)
        self.end_headers()


def _serve(handler):
    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_an_unchanged_listing_is_answered_from_the_cache_with_a_304(monkeypatch):
    handler = type("H", (_EtagHandler,), {
        "listing": json.dumps([{"name": NAME, "default_branch": "main"}]).encode(),
        "requests": [],
    })
    server = _serve(handler)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setattr(github_client, "GITHUB_API_BASE", base)
        monkeypatch.setattr(github_client, "GITHUB_RAW_BASE", base)
        first = github_client.discover_remote_projects()
        second = github_client.discover_remote_projects()
    finally:
        server.shutdown()
    assert [s.entry.name for s in first.projects] == [NAME] == [s.entry.name for s in second.projects]
    listing_requests = [r for r in handler.requests if r[0].startswith("/users/")]
    assert listing_requests[0][1] is None
    assert listing_requests[1][1] == '"v1"'  # the second run asked "has it changed?" and was told no
    assert github_client.REPO_LIST_CACHE_PATH.is_file()


def test_a_changed_listing_replaces_the_cache(monkeypatch):
    handler = type("H", (_EtagHandler,), {"listing": b"[]", "requests": []})
    server = _serve(handler)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setattr(github_client, "GITHUB_API_BASE", base)
        monkeypatch.setattr(github_client, "GITHUB_RAW_BASE", base)
        assert github_client.discover_remote_projects().projects == ()
        handler.listing = json.dumps([{"name": NAME, "default_branch": "main"}]).encode()
        handler.etag = '"v2"'
        assert [s.entry.name for s in github_client.discover_remote_projects().projects] == [NAME]
        assert [s.entry.name for s in github_client.discover_remote_projects().projects] == [NAME]
    finally:
        server.shutdown()
    cached = json.loads(github_client.REPO_LIST_CACHE_PATH.read_text(encoding="utf-8"))
    assert [value["etag"] for value in cached.values()] == ['"v2"']


def test_a_corrupt_cache_is_ignored(monkeypatch):
    github_client.REPO_LIST_CACHE_PATH.write_text("not json", encoding="utf-8")
    handler = type("H", (_EtagHandler,), {"listing": json.dumps([{"name": NAME}]).encode(), "requests": []})
    server = _serve(handler)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setattr(github_client, "GITHUB_API_BASE", base)
        monkeypatch.setattr(github_client, "GITHUB_RAW_BASE", base)
        assert [s.entry.name for s in github_client.discover_remote_projects().projects] == [NAME]
    finally:
        server.shutdown()
