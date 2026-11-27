# =============================================================================
# URTC-UPDATER - tests/test_cuts_and_encodings.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Names and texts outside ASCII, files saved in another encoding and downloads cut in the middle. The git repositories are
real local ones; the network is replaced by functions, so nothing leaves the machine."""
from __future__ import annotations

import http.client
import io
import json
import urllib.error

import pytest
from repo_helpers import NAME, entry, git, make_remote, manifest_text

from urtc_updater import detect, evidence, github_client, settings
from urtc_updater.install import clone_or_pull


def test_local_files_with_names_outside_ascii_survive_an_update(tmp_path):
    remote = make_remote(tmp_path)
    kept = {"configuración.json": "{}", "datos/mediciones_ñ.csv": "1;2", "ログ.txt": "x"}
    for name, content in kept.items():
        target = remote.checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    remote.push("1.1.0", "second")
    result = clone_or_pull(entry(), remote.workspace)
    assert result.ok, result.message
    for name, content in kept.items():
        assert (remote.checkout / name).read_text(encoding="utf-8") == content, name


def test_a_manifest_with_text_outside_ascii_is_read_from_git(tmp_path):
    remote = make_remote(tmp_path)
    data = json.loads(manifest_text("1.1.0"))
    data["notes"] = "Notas: señal, Ü, 日本語の説明, 中文说明, ”quoted” – ok"   # bytes that cp1252 has no character for
    (remote.seed / "urtc.project.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    git("commit", "-q", "-am", "notas con señal ”日本”", cwd=remote.seed)
    git("push", "-q", "origin", "HEAD", cwd=remote.seed)
    result = clone_or_pull(entry(), remote.workspace)
    assert result.ok, result.message


@pytest.mark.parametrize("raw", [
    '{"lang": "es"}'.encode("utf-16"),
    b'{"workspace_root": "C:\\\\proyectos\\\\se\xf1al"}',   # latin-1
    '{"nota": "日'.encode()[:-1],                            # cut inside a character
])
def test_a_settings_file_in_another_encoding_or_cut_never_raises(raw):
    settings.SETTINGS_PATH.write_bytes(raw)
    assert settings.load_settings() == {}
    assert settings.get_saved_lang() is None
    assert settings.settings_state() == "corrupt"
    settings.save_settings(lang="es")
    assert settings.SETTINGS_PATH.read_bytes() == raw   # left as it was, not overwritten


def test_a_settings_file_with_a_byte_order_mark_is_read():
    settings.SETTINGS_PATH.write_bytes(b'\xef\xbb\xbf{"lang": "es", "backups_to_keep": 3}')
    assert settings.load_settings()["backups_to_keep"] == 3
    assert settings.settings_state() == "ok"


def test_one_folder_with_an_unreadable_manifest_does_not_hide_the_others(tmp_path):
    good = tmp_path / NAME
    good.mkdir()
    (good / "urtc.project.json").write_text(manifest_text("1.0.0"), encoding="utf-8")
    bad = tmp_path / "URTC-LATIN"
    bad.mkdir()
    (bad / "urtc.project.json").write_bytes(b'{"notes": "se\xf1al"}')
    found = detect.discover_workspace(tmp_path)
    assert [status.entry.name for status in found.projects] == [NAME]
    assert len(found.errors) == 1 and "URTC-LATIN" in found.errors[0]


@pytest.mark.parametrize("raw", [b"[1, 2]", b'"text"', b"\xff\xfe{", b"{ cut"])
def test_the_installed_state_of_a_damaged_manifest_is_unknown(tmp_path, raw):
    (tmp_path / "urtc.project.json").write_bytes(raw)
    assert evidence.installed_state(tmp_path)["version"] is None


class CutAnswer(io.BytesIO):
    headers = None

    def read(self, *args):
        raise http.client.IncompleteRead(b"{", 100)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_a_download_cut_in_the_middle_is_asked_again():
    answers = [CutAnswer(), CutAnswer(), io.BytesIO(b"whole")]
    body = github_client._urlopen_with_retries(
        object(), timeout=1, max_attempts=3, opener=lambda request, timeout: answers.pop(0), sleep=lambda s: None)
    assert body == b"whole"


def _cut(monkeypatch, failing: str):
    def opener(request, *args, **kwargs):
        if failing in request.full_url:
            raise http.client.IncompleteRead(b"{", 100)
        raise urllib.error.HTTPError(request.full_url, 404, "not found", None, None)

    original = github_client._urlopen_with_retries
    monkeypatch.setattr(github_client, "_urlopen_with_retries", lambda request, **kw: original(request, opener=opener, sleep=lambda s: None, **kw))


def test_a_cut_repository_listing_is_a_message(monkeypatch):
    _cut(monkeypatch, "/users/")
    with pytest.raises(RuntimeError) as stop:
        github_client.discover_remote_projects("someone", token="")
    assert stop.value.args[0].code == "net_list_failed"


def test_a_cut_manifest_does_not_end_the_discovery_of_the_others(monkeypatch):
    listing = json.dumps([{"name": "URTC-CUT"}, {"name": NAME}]).encode()

    def answer(request, with_headers=False, **kwargs):
        if "/users/" in request.full_url:
            return (listing, None) if with_headers else listing
        if "URTC-CUT" in request.full_url:
            raise http.client.IncompleteRead(b"{", 100)
        return manifest_text("1.0.0").encode()

    monkeypatch.setattr(github_client, "_urlopen_with_retries", answer)
    found = github_client.discover_remote_projects("someone", token="")
    assert [status.entry.name for status in found.projects] == [NAME]
    assert len(found.errors) == 1 and "URTC-CUT" in found.errors[0]


def test_a_cut_listing_page_that_decodes_to_half_a_document_is_a_message(monkeypatch):
    monkeypatch.setattr(github_client, "_urlopen_with_retries", lambda request, with_headers=False, **kw: (b'[{"name": "URT', None))
    with pytest.raises(RuntimeError):
        github_client.discover_remote_projects("someone", token="")
