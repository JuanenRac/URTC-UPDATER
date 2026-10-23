# =============================================================================
# URTC-UPDATER - GUI translations: i18n.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
#
# Real, complete translations (not machine-generated placeholders) for the
# windowed GUI's own UI chrome and closed vocabulary (maturity/role/deploy
# labels, install-state labels), in the same 8 languages this ecosystem's
# own READMEs and JuanenRac/scripts/generate_dashboard.py's own dashboard
# already ship. Deliberately does NOT translate project names, family
# names, or the free-text `notes`/`tech` content that comes straight from
# registry.py - same reasoning as the dashboard's own TRANSLATIONS module
# docstring: that content is real engineering documentation with
# registry.py as its single source of truth, and maintaining 7 parallel
# copies of it would stop it being that.
#
# `--cli` mode (main.py) is intentionally NOT translated - it's meant to
# be scripted/piped, where a stable, English, greppable output matters
# more than localization; only the windowed GUI (the default way this
# tool runs) gets real language support.
# =============================================================================
from __future__ import annotations

import locale

from . import settings
from .translations_data import TRANSLATIONS

#: (code, native display name with flag) - same order shown in the
#: language combobox, same codes the dashboard and every README already
#: use across this ecosystem.
LANGUAGES: list[tuple[str, str]] = [
    ("en", "🇺🇸 English"),
    ("es", "🇪🇸 Español"),
    ("fr", "🇫🇷 Français"),
    ("it", "🇮🇹 Italiano"),
    ("de", "🇩🇪 Deutsch"),
    ("zh", "🇨🇳 简体中文"),
    ("ja", "🇯🇵 日本語"),
    ("pt", "🇵🇹 Português"),
]

_LANG_CODES = {code for code, _ in LANGUAGES}


def resolve_initial_lang() -> str:
    """Real preference resolution, same precedence order as the
    dashboard's own resolveInitialLang(): a previously saved choice on
    this machine, then the OS's own configured locale, then English.

    The saved choice now lives in `settings.py`'s own shared
    `~/.urtc_updater_settings.json` (alongside the real remembered
    workspace root) rather than this module's own separate file - a
    language already saved in the OLD `~/.urtc_updater_lang.json`
    is still honored via `settings.get_saved_lang()`'s own migration
    path, so upgrading never silently resets an already-configured
    language back to the OS locale.
    """
    saved = settings.get_saved_lang()
    if saved in _LANG_CODES:
        return saved

    try:
        # locale.getlocale() (not the deprecated getdefaultlocale()) -
        # returns e.g. ("es_ES", "UTF-8") or (None, None) if unset/unknown.
        detected, _encoding = locale.getlocale()
    except (ValueError, TypeError):
        detected = None

    if detected:
        short = detected[:2].lower()
        if short in _LANG_CODES:
            return short

    return "en"


def save_lang_preference(lang: str) -> None:
    """Best-effort persistence into the shared settings file - see
    `settings.save_lang()`'s own docstring for the non-fatal-on-failure
    guarantee this keeps."""
    settings.save_lang(lang)


# =============================================================================
# Translations
#
# The texts of the window, in the eight languages, are written once in the catalog of URTC-COMMON (spec/i18n/catalog/updater.json) and generated into
# translations_data.py (tools/i18n_generate.py sync URTC-UPDATER); edit the catalog, not that file.
# =============================================================================


def t(lang: str, key: str, **kwargs: object) -> str:
    """Real translation lookup with real `{placeholder}` substitution
    (str.format, not a template engine) - falls back to English on an
    unknown language, and to the key itself (never a crash) on an
    unknown key, the same defensive spirit as the dashboard's own
    `dict[key] !== undefined` checks."""
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    template = table.get(key, TRANSLATIONS["en"].get(key, key))
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
