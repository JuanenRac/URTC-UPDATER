# =============================================================================
# URTC-UPDATER - tests/test_evidence_fuzz.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The evidence chain over generated histories (a fixed seed, so a failure repeats): an intact chain always verifies, and removing, editing, reordering or adding a line is always found."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from urtc_updater.evidence import EVIDENCE_DIRECTORY, EVIDENCE_FILE, read_attempts, record_attempt, verify_chain

SEED = 20261112


def _history(workspace: Path, rng: random.Random, count: int) -> Path:
    path = None
    for i in range(count):
        path = record_attempt(workspace, project=rng.choice(["URTC", "URTC-FLASHER", "URTC-TESTER"]), before={"version": f"0.{i}.0", "commit": "a" * 40},
                              after={"version": f"0.{i + 1}.0", "commit": "b" * 40}, ok=rng.random() < 0.7, message="x" * rng.randrange(0, 700))
    assert path is not None
    return path


def _lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize("seed", range(12))
def test_an_intact_history_of_any_length_verifies_and_chains_every_line_to_the_one_before(tmp_path, seed):
    rng = random.Random(SEED + seed)
    count = rng.randrange(1, 15)
    path = _history(tmp_path, rng, count)
    assert verify_chain(tmp_path) == []
    attempts = read_attempts(tmp_path)
    assert len(attempts) == count and attempts[0]["previousHash"] == ""
    for before, after in zip(attempts, attempts[1:]):
        assert after["previousHash"] == before["hash"]
    assert all(len(attempt["message"]) <= 500 for attempt in attempts)
    assert path == tmp_path / EVIDENCE_DIRECTORY / EVIDENCE_FILE


@pytest.mark.parametrize("seed", range(12))
def test_removing_a_line_from_the_middle_is_always_found(tmp_path, seed):
    rng = random.Random(SEED + seed)
    path = _history(tmp_path, rng, rng.randrange(3, 12))
    lines = _lines(path)
    gone = rng.randrange(1, len(lines) - 1) if len(lines) > 2 else 1
    del lines[gone]
    _write(path, lines)
    assert any("removed, added or reordered" in problem for problem in verify_chain(tmp_path))


@pytest.mark.parametrize("seed", range(12))
def test_editing_any_field_of_any_line_is_found_on_that_line(tmp_path, seed):
    rng = random.Random(SEED + seed)
    path = _history(tmp_path, rng, rng.randrange(2, 10))
    lines = _lines(path)
    target = rng.randrange(len(lines))
    doc = json.loads(lines[target])
    field = rng.choice([key for key in doc if key not in ("hash", "previousHash")])
    doc[field] = "tampered" if doc[field] != "tampered" else "other"
    lines[target] = json.dumps(doc, sort_keys=True)
    _write(path, lines)
    problems = verify_chain(tmp_path)
    assert any(problem.startswith(f"line {target + 1}:") and "edited" in problem for problem in problems)


@pytest.mark.parametrize("seed", range(12))
def test_swapping_two_neighbouring_lines_is_always_found(tmp_path, seed):
    rng = random.Random(SEED + seed)
    path = _history(tmp_path, rng, rng.randrange(3, 10))
    lines = _lines(path)
    at = rng.randrange(len(lines) - 1)
    lines[at], lines[at + 1] = lines[at + 1], lines[at]
    _write(path, lines)
    assert verify_chain(tmp_path) != []


def test_a_line_added_with_a_made_up_chain_is_found(tmp_path):
    rng = random.Random(SEED)
    path = _history(tmp_path, rng, 4)
    lines = _lines(path)
    forged = json.loads(lines[-1])
    forged["previousHash"] = "0" * 64
    forged["project"] = "forged"
    lines.append(json.dumps(forged, sort_keys=True))
    _write(path, lines)
    assert verify_chain(tmp_path) != []


def test_text_that_is_not_json_in_the_middle_is_reported_and_the_chain_goes_on(tmp_path):
    rng = random.Random(SEED)
    path = _history(tmp_path, rng, 3)
    lines = _lines(path)
    lines.insert(1, "this is not json")
    _write(path, lines)
    problems = verify_chain(tmp_path)
    assert any("line 2: not valid JSON" in problem for problem in problems)


def test_lines_written_before_the_chain_existed_are_accepted_and_the_chain_starts_after_them(tmp_path):
    directory = tmp_path / EVIDENCE_DIRECTORY
    directory.mkdir(parents=True)
    old = [json.dumps({"timestamp": "2020-01-01T00:00:00+00:00", "project": "OLD", "ok": True, "message": "before the chain"}) for _ in range(3)]
    _write(directory / EVIDENCE_FILE, old)
    assert verify_chain(tmp_path) == []
    record_attempt(tmp_path, project="URTC", before={}, after={}, ok=True, message="first chained")
    record_attempt(tmp_path, project="URTC", before={}, after={}, ok=False, message="second chained")
    assert verify_chain(tmp_path) == []
    lines = _lines(directory / EVIDENCE_FILE)
    lines.insert(4, json.dumps({"project": "no hash inside the chain"}))
    _write(directory / EVIDENCE_FILE, lines)
    assert any("missing hash" in problem for problem in verify_chain(tmp_path))


def test_no_file_and_an_empty_file_have_nothing_to_report(tmp_path):
    assert verify_chain(tmp_path) == [] and read_attempts(tmp_path) == []
    directory = tmp_path / EVIDENCE_DIRECTORY
    directory.mkdir(parents=True)
    (directory / EVIDENCE_FILE).write_text("\n\n", encoding="utf-8")
    assert verify_chain(tmp_path) == [] and read_attempts(tmp_path) == []
