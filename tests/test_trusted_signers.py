# =============================================================================
# URTC-UPDATER - tests/test_trusted_signers.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The optional list of accepted signers: without it nothing changes; with it a good signature of a key that is not listed is refused."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from urtc_updater import signature
from urtc_updater.signature import SignaturePolicy, current_policy, parse_trusted_signers, signer_fingerprints, unsigned_reason, verify_revision
from test_signature import _remote_with_one_commit, _signing_key, git, needs_ssh_keygen

SUBKEY = "A" * 40
PRIMARY = "B" * 40
GPG_RAW = (
    "[GNUPG:] NEWSIG\n"
    f"[GNUPG:] GOODSIG {SUBKEY[-16:]} Contract <contract@example.invalid>\n"
    f"[GNUPG:] VALIDSIG {SUBKEY} 2000-01-01 946684800 0 4 0 22 10 00 {PRIMARY}\n"
)


def _git_says(monkeypatch, *, code: int, raw: str) -> list[list[str]]:
    calls: list[list[str]] = []

    def run(cmd, **_kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, code, "", raw)

    monkeypatch.setattr(signature.subprocess, "run", run)
    return calls


def test_no_list_keeps_the_previous_command_and_answer(monkeypatch, tmp_path: Path):
    calls = _git_says(monkeypatch, code=0, raw="")
    assert verify_revision(tmp_path, "HEAD", SignaturePolicy(True)) is None
    assert calls == [["git", "verify-commit", "HEAD"]]


@pytest.mark.parametrize("listed", [SUBKEY, PRIMARY])
def test_a_listed_gpg_signing_or_primary_key_is_accepted(monkeypatch, tmp_path: Path, listed: str):
    calls = _git_says(monkeypatch, code=0, raw=GPG_RAW)
    assert verify_revision(tmp_path, "HEAD", SignaturePolicy(True, trusted_signers=(listed,))) is None
    assert calls == [["git", "verify-commit", "--raw", "HEAD"]]


def test_a_good_signature_of_a_key_that_is_not_listed_is_refused(monkeypatch, tmp_path: Path):
    _git_says(monkeypatch, code=0, raw=GPG_RAW)
    reason = verify_revision(tmp_path, "HEAD", SignaturePolicy(True, trusted_signers=("C" * 40,)))
    assert reason and "trusted_signers" in reason and SUBKEY in reason


def test_a_listed_key_does_not_rescue_a_signature_git_refuses(monkeypatch, tmp_path: Path):
    _git_says(monkeypatch, code=1, raw=GPG_RAW)
    assert verify_revision(tmp_path, "HEAD", SignaturePolicy(True, trusted_signers=(SUBKEY,))) is not None


def test_accepted_by_git_without_a_readable_signer_is_refused(monkeypatch, tmp_path: Path):
    _git_says(monkeypatch, code=0, raw="something else\n")
    assert unsigned_reason(tmp_path, "HEAD", SignaturePolicy(True, trusted_signers=(SUBKEY,))) is not None


def test_the_warning_mode_reports_the_signer_but_accepts(monkeypatch, tmp_path: Path):
    _git_says(monkeypatch, code=0, raw=GPG_RAW)
    policy = SignaturePolicy(False, trusted_signers=("C" * 40,))
    assert unsigned_reason(tmp_path, "HEAD", policy) is not None
    assert verify_revision(tmp_path, "HEAD", policy) is None


def test_entries_are_normalised_and_a_mistake_matches_nobody():
    spaced = " ".join(["aaaa"] * 10)
    assert parse_trusted_signers([spaced]) == (SUBKEY,)
    assert parse_trusted_signers(f"{SUBKEY}; {PRIMARY}") == (SUBKEY, PRIMARY)
    assert parse_trusted_signers(None) == ()
    assert parse_trusted_signers([]) == ()
    for wrong in (["abc"], [42], 7, {"a": 1}, ["SHA256:short"]):
        parsed = parse_trusted_signers(wrong)
        assert parsed and not set(parsed) & signer_fingerprints(GPG_RAW)


def test_the_environment_wins_over_the_settings_file(monkeypatch):
    monkeypatch.setattr(signature, "load_settings", lambda: {"trusted_signers": [PRIMARY]})
    monkeypatch.delenv("URTC_UPDATER_TRUSTED_SIGNERS", raising=False)
    assert current_policy().trusted_signers == (PRIMARY,)
    monkeypatch.setenv("URTC_UPDATER_TRUSTED_SIGNERS", SUBKEY)
    assert current_policy().trusted_signers == (SUBKEY,)


@needs_ssh_keygen
def test_a_real_ssh_signature_is_matched_by_its_key_fingerprint(tmp_path: Path):
    key, allowed = _signing_key(tmp_path)
    remote = _remote_with_one_commit(tmp_path, signing_key=key)
    local = tmp_path / "local"
    git("clone", str(remote), str(local), cwd=tmp_path)
    printed = subprocess.check_output(["ssh-keygen", "-lf", str(key) + ".pub"], text=True)
    fingerprint = printed.split()[1]
    assert verify_revision(local, "HEAD", SignaturePolicy(True, str(allowed), trusted_signers=parse_trusted_signers([fingerprint]))) is None
    other = "SHA256:" + "A" * 43
    reason = verify_revision(local, "HEAD", SignaturePolicy(True, str(allowed), trusted_signers=(other,)))
    assert reason and "trusted_signers" in reason and fingerprint in reason
