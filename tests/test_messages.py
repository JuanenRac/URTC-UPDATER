# =============================================================================
# URTC-UPDATER - tests/test_messages.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Install and update messages: codes plus parameters, translated in every language."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from repo_helpers import entry, make_remote

from urtc_updater import i18n, install
from urtc_updater.install import clone_or_pull, install_or_update
from urtc_updater.messages import CodedText, coded, localize

_PLACEHOLDER = re.compile(r"\{(\w+)\}")
_INSTALL_KEYS = sorted(key for key in i18n.TRANSLATIONS["en"] if key.startswith("inst_"))


def test_there_are_install_messages_and_every_language_has_them_all():
    assert len(_INSTALL_KEYS) >= 50
    for lang, table in i18n.TRANSLATIONS.items():
        missing = [key for key in _INSTALL_KEYS if key not in table]
        assert not missing, f"{lang} lacks {missing}"


@pytest.mark.parametrize("key", _INSTALL_KEYS)
def test_every_translation_keeps_the_placeholders_of_the_english_text(key):
    expected = set(_PLACEHOLDER.findall(i18n.TRANSLATIONS["en"][key]))
    for lang, table in i18n.TRANSLATIONS.items():
        assert set(_PLACEHOLDER.findall(table[key])) == expected, f"{lang}:{key}"


def test_the_languages_really_differ_from_english():
    for lang in ("es", "fr", "it", "de", "zh", "ja", "pt"):
        same = [key for key in _INSTALL_KEYS if i18n.TRANSLATIONS[lang][key] == i18n.TRANSLATIONS["en"][key]]
        assert len(same) <= 1, (lang, same)


def test_portuguese_is_the_european_variant():
    pt = i18n.TRANSLATIONS["pt"]
    text = " ".join(pt[key] for key in _INSTALL_KEYS)
    assert "ficheiro" in text and "A validar" in text and "A clonar" in text
    for brazilian in ("arquivo", "Validando", "Clonando", "você", "usuário"):
        assert brazilian not in text


def test_a_coded_message_is_english_text_that_remembers_its_code():
    message = coded("cloned", path="/w/URTC-X")
    assert isinstance(message, str) and message == "Cloned into /w/URTC-X"
    assert isinstance(message, CodedText) and message.code == "cloned" and message.params == {"path": "/w/URTC-X"}


def test_localize_renders_the_same_message_in_another_language():
    message = coded("cloned", path="/w/URTC-X")
    assert localize("es", message) == "Clonado en /w/URTC-X"
    assert localize("pt", message) == "Clonado para /w/URTC-X"
    assert localize("en", message) == "Cloned into /w/URTC-X"


def test_plain_text_passes_through_localize_unchanged():
    assert localize("ja", "already plain") == "already plain"


def test_a_nested_message_is_translated_too():
    inner = coded("script_failed", script="build-test.sh", code=3)
    outer = coded("candidate_build_failed", path="/w/X", detail=inner)
    assert "build-test.sh exited with code 3" in outer
    translated = localize("de", outer)
    assert "wurde mit Code 3 beendet" in translated and "exited" not in translated


def test_a_command_name_called_code_does_not_clash_with_the_message_code():
    assert coded("clone_failed", code=128) == "git clone failed (exit 128)"


def test_a_real_failed_clone_is_a_message_the_window_can_translate(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(tmp_path / "missing.git"))
    result = clone_or_pull(entry(), tmp_path)
    assert not result.ok and isinstance(result.message, CodedText) and result.message.code == "clone_failed"
    assert localize("pt", result.message).startswith("git clone falhou")


def test_checkpoints_reach_the_window_as_messages_with_codes(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path, clone=False)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    seen: list[tuple[str, object]] = []
    result = clone_or_pull(entry(), remote.workspace, progress=lambda phase, detail: seen.append((phase, detail)))
    assert result.ok, result.message
    assert [detail.code for _phase, detail in seen] == ["cp_workspace", "cp_clone_staging", "cp_unsigned_warning", "cp_validate_fetched", "cp_clone_promoted"]   # the fixture remote is unsigned: the default policy warns
    assert localize("es", seen[1][1]).startswith("Clonando el repositorio")
    assert localize("zh", seen[0][1]) == i18n.TRANSLATIONS["zh"]["inst_cp_workspace"]


def test_a_dirty_checkout_is_refused_with_a_translatable_message(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    (remote.checkout / "dirty.txt").write_text("x", encoding="utf-8")  # untracked: allowed
    (remote.checkout / "urtc.project.json").write_text("{}", encoding="utf-8")  # tracked and modified
    results = install_or_update(entry(), remote.workspace)
    (result,) = results
    assert not result.ok
    assert isinstance(result.message, CodedText)
    assert "uncommitted" in result.message
    assert "modifications non validées" in localize("fr", result.message)


def test_a_missing_git_is_reported_as_a_coded_result(tmp_path: Path, monkeypatch):
    def no_git(*_args, **_kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(install.subprocess, "run", no_git)
    (result,) = install_or_update(entry(), tmp_path)
    assert not result.ok
    assert isinstance(result.message, CodedText) and result.message.code == "tool_missing"
    assert "'git' was not found" in result.message and "'git' est introuvable" in localize("fr", result.message)


# --- the restore of a kept installation and the errors of the GitHub client carry codes too ---------------------------------------

def test_the_results_of_a_restore_are_messages_the_window_can_translate(tmp_path: Path):
    from urtc_updater.install import restore_backup

    nothing = restore_backup("URTC-EXAMPLE", tmp_path)
    assert isinstance(nothing.message, CodedText) and nothing.message.code == "restore_none"
    assert localize("es", nothing.message).startswith("no hay ninguna instalación anterior de URTC-EXAMPLE")
    named = restore_backup("URTC-EXAMPLE", tmp_path, backup="URTC-EXAMPLE.backup-ffffffff")
    assert isinstance(named.message, CodedText) and named.message.code == "restore_none_named"
    assert "URTC-EXAMPLE.backup-ffffffff" in localize("de", named.message)

    folder = tmp_path / "URTC-EXAMPLE.backup-00000001"
    folder.mkdir()
    (folder / "urtc.project.json").write_text("{}", encoding="utf-8")
    unusable = restore_backup("URTC-EXAMPLE", tmp_path)
    assert isinstance(unusable.message, CodedText) and unusable.message.code == "restore_unusable"
    assert localize("fr", unusable.message).startswith("URTC-EXAMPLE.backup-00000001 n'est pas une installation utilisable")


def test_a_restore_that_worked_says_where_the_replaced_installation_went(tmp_path: Path):
    from repo_helpers import manifest_text

    from urtc_updater.install import restore_backup
    from urtc_updater.project_manifest import MANIFEST_FILE

    manifest = manifest_text("1.0.0", "URTC-EXAMPLE")
    kept = tmp_path / "URTC-EXAMPLE.backup-00000001"
    kept.mkdir()
    (kept / MANIFEST_FILE).write_text(manifest, encoding="utf-8")
    result = restore_backup("URTC-EXAMPLE", tmp_path)
    assert result.ok and isinstance(result.message, CodedText) and result.message.code == "restored"
    assert localize("pt", result.message).startswith("Restaurado ")
    (tmp_path / "URTC-EXAMPLE.backup-00000002").mkdir()
    (tmp_path / "URTC-EXAMPLE.backup-00000002" / MANIFEST_FILE).write_text(manifest, encoding="utf-8")
    again = restore_backup("URTC-EXAMPLE", tmp_path)
    assert again.ok and again.message.code == "restored_kept" and "mantiene" not in localize("es", again.message)
    assert "se conserva en" in localize("es", again.message)


def test_the_errors_of_the_github_client_keep_their_code_through_an_exception():
    from urtc_updater import github_client

    try:
        raise RuntimeError(coded("net_list_failed", owner="JuanenRac", detail=coded("net_http", code=503)))
    except RuntimeError as exc:
        message = exc.args[0]
    assert str(message) == "unable to list GitHub repositories for JuanenRac: HTTP 503"
    assert localize("de", message) == "die GitHub-Repositories von JuanenRac konnten nicht aufgelistet werden: HTTP-Fehler 503"
    assert github_client.describe_http_error is not None


def test_a_rate_limit_is_described_in_the_language_of_the_window():
    import io
    import urllib.error

    from urtc_updater.github_client import describe_http_error

    error = urllib.error.HTTPError("https://api.github.com/x", 403, "Forbidden", {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"}, io.BytesIO(b""))  # type: ignore[arg-type]
    message = describe_http_error(error)
    assert isinstance(message, CodedText) and message.code == "net_rate_limited"
    assert message.startswith("rate limited by GitHub - resets at 2023-11-14T22:13:20")
    assert "GITHUB_TOKEN" in localize("it", message) and "GitHub" in localize("zh", message)
    other = describe_http_error(urllib.error.HTTPError("https://api.github.com/x", 500, "Server error", {}, io.BytesIO(b"")))  # type: ignore[arg-type]
    assert other == "HTTP 500" and isinstance(other, CodedText)
