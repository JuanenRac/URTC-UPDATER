# =============================================================================
# URTC-UPDATER - tests/test_messages.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0 - see LICENSE
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
