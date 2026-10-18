# =============================================================================
# URTC-UPDATER - tests/test_github_fetch_errors.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Reading one project's remote version: every way the request can fail is
reported on that project alone, never raised, and the scan of the whole
family goes on. The network layer is replaced by a function that answers per
address, so nothing leaves the machine."""
from __future__ import annotations

import email.message
import json
import urllib.error

import pytest

from urtc_updater import github_client
from urtc_updater.github_client import _fetch_one, fetch_all
from urtc_updater.registry import ProjectEntry

ENTRY = ProjectEntry("URTC-EXAMPLE", "python", "pyproject.toml", r"^version\s*=\s*\"(\d+)\.(\d+)\.(\d+)\"")


def _manifest(name="URTC-EXAMPLE", version="1.2.3"):
    return json.dumps({
        "schema_version": "1.0", "ecosystem": "URTC", "name": name, "version": version, "role": "tool", "stack": "python",
        "technologies": ["Python"], "deployment_target": "cm5", "maturity": "functional", "family": "Example",
        "parent": None, "native_version": {"file": "pyproject.toml", "pattern": "^version\\s*=\\s*\"(\\d+)\\.(\\d+)\\.(\\d+)\""},
        "build": "python -m build", "notes": "Fixture.",
    }).encode("utf-8")


def _http_error(code):
    return urllib.error.HTTPError("http://example.invalid/", code, "error", email.message.Message(), None)


def _serve(monkeypatch, answers):
    """answers: callable(url) -> bytes, or an exception to raise."""
    calls = []

    def opener(request, timeout=None):
        calls.append(request.full_url)
        answer = answers(request.full_url)
        if isinstance(answer, BaseException):
            raise answer
        return answer
    monkeypatch.setattr(github_client, "_urlopen_with_retries", opener)
    return calls


def test_a_valid_manifest_gives_the_remote_version(monkeypatch):
    _serve(monkeypatch, lambda url: _manifest(version="1.2.3"))
    status = _fetch_one(ENTRY)
    assert status.error is None and str(status.version) == "1.2.3"


def test_a_manifest_that_names_another_project_is_rejected(monkeypatch):
    _serve(monkeypatch, lambda url: _manifest(name="SOMETHING-ELSE"))
    status = _fetch_one(ENTRY)
    assert status.version is None and "invalid project manifest" in status.error


def test_text_that_is_not_a_manifest_is_rejected(monkeypatch):
    _serve(monkeypatch, lambda url: b"<html>not json</html>")
    status = _fetch_one(ENTRY)
    assert status.version is None and "invalid project manifest" in status.error


def test_a_missing_manifest_falls_back_to_the_native_version_file(monkeypatch):
    urls = []

    def answers(url):
        urls.append(url)
        return _http_error(404) if len(urls) == 1 else b'version = "4.5.6"\n'
    _serve(monkeypatch, answers)
    status = _fetch_one(ENTRY)
    assert status.error is None and str(status.version) == "4.5.6"
    assert len(urls) == 2 and urls[0] != urls[1]


def test_a_missing_manifest_and_native_file_reports_the_404(monkeypatch):
    _serve(monkeypatch, lambda url: _http_error(404))
    status = _fetch_one(ENTRY)
    assert status.version is None and status.http_status == 404 and status.error


def test_a_native_file_without_a_version_line_reports_the_404(monkeypatch):
    urls = []

    def answers(url):
        urls.append(url)
        return _http_error(404) if len(urls) == 1 else b"nothing useful here\n"
    _serve(monkeypatch, answers)
    status = _fetch_one(ENTRY)
    assert status.version is None and status.http_status == 404


def test_a_network_failure_while_reading_the_native_file_reports_the_404(monkeypatch):
    urls = []

    def answers(url):
        urls.append(url)
        return _http_error(404) if len(urls) == 1 else urllib.error.URLError("offline")
    _serve(monkeypatch, answers)
    status = _fetch_one(ENTRY)
    assert status.version is None and status.http_status == 404


@pytest.mark.parametrize("code", [403, 429, 500, 503])
def test_other_http_errors_keep_their_status(monkeypatch, code):
    _serve(monkeypatch, lambda url: _http_error(code))
    status = _fetch_one(ENTRY)
    assert status.version is None and status.http_status == code and status.error


def test_a_dns_or_connection_failure_is_a_network_error(monkeypatch):
    _serve(monkeypatch, lambda url: urllib.error.URLError("name not resolved"))
    status = _fetch_one(ENTRY)
    assert status.version is None and status.error.startswith("network error") and "name not resolved" in status.error


@pytest.mark.parametrize("failure", [TimeoutError(), TimeoutError("slow")])
def test_a_timeout_says_so(monkeypatch, failure):
    _serve(monkeypatch, lambda url: failure)
    status = _fetch_one(ENTRY)
    assert status.version is None and "timed out" in status.error


def test_an_operating_system_error_is_reported(monkeypatch):
    _serve(monkeypatch, lambda url: ConnectionResetError("reset by peer"))
    status = _fetch_one(ENTRY)
    assert status.version is None and "OS/network error" in status.error


def test_an_unexpected_exception_is_reported_not_raised(monkeypatch):
    _serve(monkeypatch, lambda url: RuntimeError("bug in the opener"))
    status = _fetch_one(ENTRY)
    assert status.version is None and "unexpected error: RuntimeError" in status.error


def test_the_family_scan_survives_one_failing_project_and_reports_progress(monkeypatch):
    entries = [ProjectEntry(f"URTC-P{i}", "python", "pyproject.toml", ENTRY.pattern) for i in range(4)]

    def fake_fetch(entry):
        if entry.name == "URTC-P2":
            raise RuntimeError("worker blew up")
        return github_client.RemoteStatus(entry=entry, version=None, error=None, url="u")
    monkeypatch.setattr(github_client, "_fetch_one", fake_fetch)
    progress = []
    results = fetch_all(entries, progress=lambda done, total: progress.append((done, total)))
    assert set(results) == {entry.name for entry in entries}
    assert "worker failure: RuntimeError: worker blew up" in results["URTC-P2"].error
    assert results["URTC-P0"].error is None
    assert sorted(progress) == [(1, 4), (2, 4), (3, 4), (4, 4)]


def test_an_empty_scan_returns_nothing_without_starting_workers(monkeypatch):
    monkeypatch.setattr(github_client, "_fetch_one", lambda entry: pytest.fail("no project, no request"))
    assert fetch_all([]) == {}
