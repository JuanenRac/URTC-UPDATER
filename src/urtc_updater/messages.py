# =============================================================================
# URTC-UPDATER - Translatable install/update messages: messages.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Messages that carry a code and parameters next to their English text.

The install and update flow reports what it is doing (checkpoints) and how it
ended (results) as plain strings, so the command line and the logs keep
working unchanged. Each of those strings is a ``CodedText``: a ``str`` holding
the English text that also remembers its message code and parameters. The
window calls ``localize()`` to render the same message in the language of the
interface; the translations live in ``i18n.py`` under the key ``inst_<code>``.
"""
from __future__ import annotations

from . import i18n


class CodedText(str):
    """The English text of a message, plus the code and parameters it came from."""

    code: str
    params: dict[str, object]

    def __new__(cls, code: str, params: dict[str, object]) -> "CodedText":
        text = i18n.t("en", f"inst_{code}", **params)
        obj = super().__new__(cls, text)
        obj.code = code
        obj.params = params
        return obj


def coded(code: str, /, **params: object) -> CodedText:
    return CodedText(code, params)


def localize(lang: str, text: object) -> str:
    """The message in `lang` when it is a coded one; any other text unchanged.
    A parameter that is itself a coded message (a nested failure) is
    translated too."""
    if not isinstance(text, CodedText):
        return str(text)
    params = {
        key: localize(lang, value) if isinstance(value, CodedText) else value
        for key, value in text.params.items()
    }
    return i18n.t(lang, f"inst_{text.code}", **params)
