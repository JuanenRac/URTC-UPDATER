# =============================================================================
# URTC-COMMON - src/urtc_common/compat.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The compatibility matrix against what is installed: which program is at the version the release was made with, which is older or newer,
and whether the firmware that the flasher and the web studio carry is the firmware of the tool head repository.

``compat.json`` (generated from ``spec/versions.json``) records, for one release of the family, the version of every project, the
version of the protocol they speak and the copy of the shared code each carries. This module only compares: it reads folders and
manifests when asked to (``installed_versions``) but never writes, never starts a program and never asks the network. A project that is
not installed is "missing" and one whose version cannot be read is "unknown"; neither is ever shown as a match.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import firmware_names

MATCH, NEWER, OLDER, MISSING, UNKNOWN = "match", "newer", "older", "missing", "unknown"
STATES = (MATCH, NEWER, OLDER, MISSING, UNKNOWN)
#: where each program keeps the firmware images it carries, relative to its repository
BUNDLED_FOLDERS = {"URTC-FLASHER": "firmware", "URTC-WEB-STUDIO": "public/firmware"}


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """``"0.4.1"`` or ``"0.8.0.2"`` as a tuple; ``None`` when it is not a dotted number."""
    if not text or not re.fullmatch(r"\d+(\.\d+){1,3}", text.strip()):
        return None
    return tuple(int(part) for part in text.strip().split("."))


def _order(found: tuple[int, ...], wanted: tuple[int, ...]) -> str:
    width = max(len(found), len(wanted))
    a, b = found + (0,) * (width - len(found)), wanted + (0,) * (width - len(wanted))
    return MATCH if a == b else (NEWER if a > b else OLDER)


@dataclass(frozen=True)
class Row:
    repo: str
    title: str
    kind: str
    expected: str
    found: str | None
    state: str
    common_expected: str | None
    common_found: str | None
    common_state: str


def load_matrix(source: dict | str | Path) -> dict:
    """The matrix as a dictionary, checked: a format, a protocol version and a list of projects with a repository and a version each."""
    data = source if isinstance(source, dict) else json.loads(Path(source).read_text(encoding="utf-8"))
    if data.get("format") != 1 or not isinstance(data.get("protocol_version"), int) or not isinstance(data.get("projects"), list):
        raise ValueError("not a compatibility matrix (expected format 1, a protocol_version and a list of projects)")
    for item in data["projects"]:
        if not isinstance(item, dict) or not isinstance(item.get("repo"), str) or parse_version(item.get("version")) is None:
            raise ValueError(f"a project of the matrix has no repository or no valid version: {item!r}")
    return data


def compare(matrix: dict, installed: dict[str, str | None], carried_common: dict[str, str | None] | None = None) -> list[Row]:
    """One row per project of the matrix. ``installed`` maps a repository name to the version found there (``None``: present but unreadable;
    absent from the mapping: not installed). ``carried_common`` maps it to the version of URTC-COMMON its copy was made from."""
    carried_common = carried_common or {}
    rows = []
    for item in matrix["projects"]:
        repo, expected = item["repo"], item["version"]
        if repo not in installed:
            state, found = MISSING, None
        else:
            found = installed[repo]
            wanted, have = parse_version(expected), parse_version(found)
            state = UNKNOWN if have is None or wanted is None else _order(have, wanted)
        common_expected = item.get("common")
        common_found = carried_common.get(repo)
        if repo not in installed:
            common_state = MISSING
        elif common_expected is None:
            common_state = MATCH  # the project carries no copy, so there is nothing to compare
        else:
            wanted_c, have_c = parse_version(common_expected), parse_version(common_found)
            common_state = UNKNOWN if have_c is None or wanted_c is None else _order(have_c, wanted_c)
        rows.append(Row(repo, item.get("title", repo), item.get("kind", ""), expected, found, state, common_expected, common_found, common_state))
    return rows


def installed_versions(workspace: Path) -> tuple[dict[str, str | None], dict[str, str | None]]:
    """Read the versions in the folders next to each other: the manifest version of each repository of the matrix that is present, and the
    version of URTC-COMMON that its ``urtc_common.lock.json`` records (the first one found)."""
    versions: dict[str, str | None] = {}
    carried: dict[str, str | None] = {}
    if not workspace.is_dir():
        return versions, carried
    for folder in sorted(workspace.iterdir(), key=lambda p: p.name.casefold()):
        manifest = folder / "urtc.project.json"
        if not folder.is_dir() or folder.name.startswith(".") or not manifest.is_file():
            continue
        try:
            versions[folder.name] = str(json.loads(manifest.read_text(encoding="utf-8")).get("version"))
        except (OSError, ValueError):
            versions[folder.name] = None
        for lock in sorted(folder.rglob("urtc_common.lock.json")):
            if any(part in {"node_modules", ".git", "dist", "build", "__pycache__", ".venv"} for part in lock.parts):
                continue
            try:
                carried[folder.name] = json.loads(lock.read_text(encoding="utf-8")).get("urtc_common_version")
            except (OSError, ValueError):
                carried[folder.name] = None
            break
    return versions, carried


def bundled_firmware(workspace: Path) -> dict[str, str | None]:
    """The newest main application firmware each program carries (``None`` when its folder holds none); programs that are not installed are left out."""
    result: dict[str, str | None] = {}
    for repo, folder in BUNDLED_FOLDERS.items():
        base = workspace / repo
        if not base.is_dir():
            continue
        images = sorted((base / folder).iterdir()) if (base / folder).is_dir() else []
        found = [parsed for item in images if (name := firmware_names.parse_image_name(item.name)) and name[:2] == ("MAIN", "FIRMWARE") and (parsed := parse_version(name[2]))]
        result[repo] = ".".join(str(n) for n in max(found)) if found else None
    return result


def main_firmware_version(matrix: dict) -> str | None:
    """The main application firmware version the matrix was made with (the component of the tool head repository), else its own version."""
    for item in matrix["projects"]:
        if item["repo"] == "URTC":
            for component in item.get("components", []):
                if component.get("name") == "URTC_MAIN_FIRMWARE":
                    return component["version"]
            return item["version"]
    return None


def firmware_findings(expected: str | None, installed_head: str | None, bundled: dict[str, str | None]) -> list[tuple[str, str, str | None, str | None]]:
    """Where the firmware a program carries is not the firmware of the tool head repository: ``(repo, state, carried, wanted)``.

    ``wanted`` is the version installed in the tool head repository when it is present (what an update would bring), else the matrix's.
    Programs that carry the wanted version are not listed."""
    wanted = installed_head or expected
    findings = []
    for repo, carried in sorted(bundled.items()):
        have, want = parse_version(carried), parse_version(wanted)
        if want is None:
            continue
        state = UNKNOWN if have is None else _order(have, want)
        if state != MATCH:
            findings.append((repo, state, carried, wanted))
    return findings


def protocol_note(matrix: dict, other_protocol: int | None) -> str | None:
    """A sentence when another source speaks a different protocol version than the matrix; ``None`` otherwise."""
    if other_protocol is None or other_protocol == matrix["protocol_version"]:
        return None
    return f"protocol version {other_protocol} differs from the matrix ({matrix['protocol_version']})"


def summary(rows: list[Row]) -> dict[str, int]:
    return {state: sum(1 for row in rows if row.state == state) for state in STATES}


STRINGS: dict[str, dict[str, str]] = {
    "english": {
        "title": "Compatibility", "intro": "Compared with the release matrix: protocol {protocol}. Nothing here changes anything.",
        "project": "Project", "expected": "Release", "found": "Installed", "state": "State", "common": "Shared code",
        "match": "as released", "newer": "newer than the release", "older": "older than the release", "missing": "not installed", "unknown": "version unknown",
        "firmware": "Firmware carried by the programs", "firmware_ok": "The programs carry the firmware of the release ({version}).",
        "firmware_older": "{repo} carries firmware {carried}; the tool head repository is at {wanted}. Update it before flashing.",
        "firmware_newer": "{repo} carries firmware {carried}, newer than {wanted}.",
        "firmware_unknown": "{repo} carries no readable main firmware image.", "none_installed": "None of the projects of the release is installed here.", "close": "Close",
    },
    "spanish": {
        "title": "Compatibilidad", "intro": "Comparado con la matriz de la versión publicada: protocolo {protocol}. Nada de aquí cambia nada.",
        "project": "Proyecto", "expected": "Publicada", "found": "Instalada", "state": "Estado", "common": "Código compartido",
        "match": "como la publicada", "newer": "más nueva que la publicada", "older": "más antigua que la publicada", "missing": "no instalado", "unknown": "versión desconocida",
        "firmware": "Firmware que llevan los programas", "firmware_ok": "Los programas llevan el firmware de la versión publicada ({version}).",
        "firmware_older": "{repo} lleva el firmware {carried}; el repositorio del cabezal está en {wanted}. Actualízalo antes de flashear.",
        "firmware_newer": "{repo} lleva el firmware {carried}, más nuevo que {wanted}.",
        "firmware_unknown": "{repo} no lleva ninguna imagen de firmware principal legible.", "none_installed": "Aquí no hay instalado ningún proyecto de la versión publicada.", "close": "Cerrar",
    },
    "italian": {
        "title": "Compatibilità", "intro": "Confrontato con la matrice della release: protocollo {protocol}. Niente qui modifica nulla.",
        "project": "Progetto", "expected": "Release", "found": "Installata", "state": "Stato", "common": "Codice condiviso",
        "match": "come la release", "newer": "più recente della release", "older": "più vecchia della release", "missing": "non installato", "unknown": "versione sconosciuta",
        "firmware": "Firmware incluso nei programmi", "firmware_ok": "I programmi includono il firmware della release ({version}).",
        "firmware_older": "{repo} include il firmware {carried}; il repository della testa è alla {wanted}. Aggiornalo prima di programmare.",
        "firmware_newer": "{repo} include il firmware {carried}, più recente di {wanted}.",
        "firmware_unknown": "{repo} non include nessuna immagine di firmware principale leggibile.", "none_installed": "Qui non è installato nessun progetto della release.", "close": "Chiudi",
    },
    "french": {
        "title": "Compatibilité", "intro": "Comparé à la matrice de la version publiée : protocole {protocol}. Rien ici ne modifie quoi que ce soit.",
        "project": "Projet", "expected": "Publiée", "found": "Installée", "state": "État", "common": "Code partagé",
        "match": "comme la version publiée", "newer": "plus récente que la version publiée", "older": "plus ancienne que la version publiée", "missing": "non installé", "unknown": "version inconnue",
        "firmware": "Firmware embarqué par les programmes", "firmware_ok": "Les programmes embarquent le firmware de la version publiée ({version}).",
        "firmware_older": "{repo} embarque le firmware {carried} ; le dépôt de la tête est à {wanted}. Mettez-le à jour avant de flasher.",
        "firmware_newer": "{repo} embarque le firmware {carried}, plus récent que {wanted}.",
        "firmware_unknown": "{repo} n'embarque aucune image de firmware principale lisible.", "none_installed": "Aucun projet de la version publiée n'est installé ici.", "close": "Fermer",
    },
    "german": {
        "title": "Kompatibilität", "intro": "Verglichen mit der Matrix der Veröffentlichung: Protokoll {protocol}. Hier wird nichts verändert.",
        "project": "Projekt", "expected": "Veröffentlicht", "found": "Installiert", "state": "Status", "common": "Gemeinsamer Code",
        "match": "wie veröffentlicht", "newer": "neuer als die Veröffentlichung", "older": "älter als die Veröffentlichung", "missing": "nicht installiert", "unknown": "Version unbekannt",
        "firmware": "Von den Programmen mitgelieferte Firmware", "firmware_ok": "Die Programme enthalten die Firmware der Veröffentlichung ({version}).",
        "firmware_older": "{repo} enthält die Firmware {carried}; das Werkzeugkopf-Repository steht bei {wanted}. Vor dem Flashen aktualisieren.",
        "firmware_newer": "{repo} enthält die Firmware {carried}, neuer als {wanted}.",
        "firmware_unknown": "{repo} enthält kein lesbares Hauptfirmware-Image.", "none_installed": "Hier ist kein Projekt der Veröffentlichung installiert.", "close": "Schließen",
    },
    "chinese": {
        "title": "兼容性", "intro": "与发布版本的矩阵对比：协议 {protocol}。此处不会更改任何内容。",
        "project": "项目", "expected": "发布版本", "found": "已安装", "state": "状态", "common": "共享代码",
        "match": "与发布版本一致", "newer": "比发布版本新", "older": "比发布版本旧", "missing": "未安装", "unknown": "版本未知",
        "firmware": "程序自带的固件", "firmware_ok": "程序自带的固件与发布版本一致（{version}）。",
        "firmware_older": "{repo} 自带固件 {carried}；工具头仓库为 {wanted}。刷写前请先更新。",
        "firmware_newer": "{repo} 自带固件 {carried}，比 {wanted} 新。",
        "firmware_unknown": "{repo} 没有可读取的主固件镜像。", "none_installed": "此处没有安装发布版本中的任何项目。", "close": "关闭",
    },
    "japanese": {
        "title": "互換性", "intro": "リリースの対応表と比較しています（プロトコル {protocol}）。ここでは何も変更されません。",
        "project": "プロジェクト", "expected": "リリース", "found": "インストール済み", "state": "状態", "common": "共有コード",
        "match": "リリースと同じ", "newer": "リリースより新しい", "older": "リリースより古い", "missing": "未インストール", "unknown": "バージョン不明",
        "firmware": "各プログラムに同梱のファームウェア", "firmware_ok": "各プログラムはリリースのファームウェア（{version}）を同梱しています。",
        "firmware_older": "{repo} はファームウェア {carried} を同梱していますが、ツールヘッドのリポジトリは {wanted} です。書き込み前に更新してください。",
        "firmware_newer": "{repo} が同梱するファームウェア {carried} は {wanted} より新しいです。",
        "firmware_unknown": "{repo} には読み取れるメインのファームウェアイメージがありません。", "none_installed": "リリースのプロジェクトはここにインストールされていません。", "close": "閉じる",
    },
    "portuguese": {
        "title": "Compatibilidade", "intro": "Comparado com a matriz da versão publicada: protocolo {protocol}. Nada aqui altera o que quer que seja.",
        "project": "Projeto", "expected": "Publicada", "found": "Instalada", "state": "Estado", "common": "Código partilhado",
        "match": "como a publicada", "newer": "mais recente do que a publicada", "older": "mais antiga do que a publicada", "missing": "não instalado", "unknown": "versão desconhecida",
        "firmware": "Firmware que os programas incluem", "firmware_ok": "Os programas incluem o firmware da versão publicada ({version}).",
        "firmware_older": "{repo} inclui o firmware {carried}; o repositório da cabeça está na {wanted}. Atualize-o antes de gravar.",
        "firmware_newer": "{repo} inclui o firmware {carried}, mais recente do que {wanted}.",
        "firmware_unknown": "{repo} não inclui nenhuma imagem de firmware principal legível.", "none_installed": "Aqui não está instalado nenhum projeto da versão publicada.", "close": "Fechar",
    },
}
LANGUAGES = tuple(STRINGS)


def text(language: str, key: str, **values: object) -> str:
    table = STRINGS.get(language) or STRINGS["english"]
    return (table.get(key) or STRINGS["english"][key]).format(**values)


def report(matrix: dict, workspace: Path, language: str = "english") -> dict:
    """Everything the window and the command line show, as plain data: the rows, the firmware lines and the counts."""
    installed, carried = installed_versions(workspace)
    rows = compare(matrix, installed, carried)
    bundled = bundled_firmware(workspace)
    expected = main_firmware_version(matrix)
    head = installed.get("URTC")
    findings = firmware_findings(expected, None if head is None else _component_main(workspace) or head, bundled)
    lines = []
    for repo, state, have, want in findings:
        lines.append(text(language, f"firmware_{state}", repo=repo, carried=have or "-", wanted=want or "-"))
    if not findings and bundled and expected:
        lines.append(text(language, "firmware_ok", version=expected))
    return {"protocol": matrix["protocol_version"], "rows": rows, "firmware": lines, "findings": findings, "counts": summary(rows),
            "any_installed": any(row.state != MISSING for row in rows)}


def _component_main(workspace: Path) -> str | None:
    """The main application firmware version the tool head repository declares in its own manifest (``None`` when it declares no component)."""
    try:
        data = json.loads((workspace / "URTC" / "urtc.project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for component in data.get("components", []):
        if component.get("name") == "URTC_MAIN_FIRMWARE":
            return str(component.get("version"))
    return None
