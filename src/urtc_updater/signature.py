# =============================================================================
# URTC-UPDATER - Optional commit-signature policy: signature.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Commit-signature policy: `warn` or `require`.

The policy object itself starts as `warn`, but the updater asks for `require` unless the saved setting (`security.saved_require_signed`) says otherwise, so a fresh install
requires a signature.

By default the updater trusts whatever the GitHub remote serves (a
compromised account or repository could push a commit that this tool would
then build and run). The policy decides what happens with a revision that
carries no valid GPG or SSH signature (`git verify-commit`):

* `warn`: the install or update goes ahead, and the window and
  the command line state in the steps that the revision is not signed.
* `require` (what a fresh install uses): the candidate revision - the fresh clone's HEAD, or the fetched
  FETCH_HEAD of an update - must carry a valid signature BEFORE its manifest
  is read or anything in it is built. A refused candidate leaves the
  installed checkout untouched. A GPG signature counts when it is good for any key in the keyring of the person who runs the updater (`git verify-commit` does not
  pin the maintainer's key); for SSH signatures `allowed_signers_file` limits which keys are trusted.

`trusted_signers` (optional, empty by default) pins who may have signed. It is a list of key fingerprints: GPG fingerprints (40 or 64 hex digits, spaces
allowed; the signing key or its primary key) and SSH key fingerprints (`SHA256:...`, as `ssh-keygen -lf key.pub` prints them). With a list, a revision counts as
signed only when `git verify-commit` accepts it AND its signer is in the list. An entry that is not a fingerprint matches nothing, so a typing mistake refuses
instead of letting everything through.

A settings file that exists but cannot be read counts as "required" (the safe side)
until it is fixed or removed; the environment variable can still say otherwise.
The other protection, confirming before the build check, is in `security.py`.

Require signatures in `~/.urtc_updater_settings.json`:

    {"signature_policy": "require",
     "require_signed_commits": true,
     "allowed_signers_file": "/home/me/.config/urtc/allowed_signers"}

or with the environment variable `URTC_UPDATER_REQUIRE_SIGNED=1` (and
`URTC_UPDATER_ALLOWED_SIGNERS=<file>`, `URTC_UPDATER_TRUSTED_SIGNERS=<fingerprint>,<fingerprint>`). `allowed_signers_file` is the
OpenSSH allowed-signers file used for SSH-signed commits; GPG-signed
commits are checked against the user's own GPG keyring.
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import security
from .settings import load_settings, settings_state
from .updater_core import PROFILE as _PROFILE

SETTING_TRUSTED_SIGNERS = "trusted_signers"
#: What an unusable setting turns into: an entry that no signer can match.
_NOBODY = "(not a fingerprint)"
_GPG_FINGERPRINT = re.compile(r"[0-9A-F]{40}|[0-9A-F]{64}")
_SSH_FINGERPRINT = re.compile(r"SHA256:[A-Za-z0-9+/]{43}")
_SSH_GOOD = re.compile(r'Good "git" signature (?:for .+ )?with \S+ key (SHA256:[A-Za-z0-9+/]{43})')


def _fingerprint(entry: object) -> str:
    """One entry of the list in its comparable form: GPG fingerprints without spaces and in upper case, SSH fingerprints as written."""
    if not isinstance(entry, str):
        return _NOBODY
    text = entry.strip()
    if text.upper().startswith("SHA256:"):
        text = "SHA256:" + text[7:].rstrip("=")
        return text if _SSH_FINGERPRINT.fullmatch(text) else _NOBODY
    text = "".join(text.split()).upper()
    return text if _GPG_FINGERPRINT.fullmatch(text) else _NOBODY


def parse_trusted_signers(value: object) -> tuple[str, ...]:
    """The list of the settings file (a list, or a text with commas or semicolons). Nothing set gives an empty tuple: any signer `git verify-commit` accepts."""
    if value is None:
        return ()
    if isinstance(value, str):
        entries: list[object] = [part for part in re.split(r"[,;]", value) if part.strip()]
    elif isinstance(value, list):
        entries = value
    else:
        entries = [value]
    return tuple(_fingerprint(entry) for entry in entries)


def signer_fingerprints(output: str) -> set[str]:
    """The fingerprints of the key that made a signature, from the output of `git verify-commit --raw` (GPG status lines, or the line of ssh-keygen)."""
    found: set[str] = set()
    for line in output.splitlines():
        parts = line.split()
        if parts[:2] == ["[GNUPG:]", "VALIDSIG"] and len(parts) > 2:
            found.add(parts[2].upper())
            if len(parts) > 11:
                found.add(parts[11].upper())   # the primary key of a signing subkey
            continue
        match = _SSH_GOOD.fullmatch(line.strip())
        if match:
            found.add(match.group(1))
    return found


@dataclass(frozen=True)
class SignaturePolicy:
    required: bool = False
    allowed_signers_file: str | None = None
    #: True when the settings file exists but cannot be read: signatures are then required (unless the environment says otherwise) until it is fixed or removed.
    settings_unreadable: bool = False
    #: Fingerprints that may have signed; empty: any signature that `git verify-commit` accepts.
    trusted_signers: tuple[str, ...] = ()

    @property
    def mode(self) -> str:
        """"require" refuses an unsigned revision, "warn" installs it and says so. The updater itself starts in "require" (see `security.saved_require_signed`)."""
        return "require" if self.required else "warn"


def current_policy() -> SignaturePolicy:
    """The policy in force: the environment variables win over the saved
    settings, so a CI job or a one-off run can require signatures without
    touching the user's settings file."""
    saved = load_settings()
    unreadable = settings_state() == "corrupt"
    required = security.effective_require_signed()
    signers = os.environ.get(_PROFILE.env_name("ALLOWED_SIGNERS")) or saved.get("allowed_signers_file")
    pinned = os.environ.get(_PROFILE.env_name("TRUSTED_SIGNERS")) or saved.get(SETTING_TRUSTED_SIGNERS)
    return SignaturePolicy(required, signers if isinstance(signers, str) and signers else None, unreadable and required, parse_trusted_signers(pinned))


def unsigned_reason(repo: Path, revision: str, policy: SignaturePolicy) -> str | None:
    """None when `revision` carries a signature that verifies (and, with `trusted_signers`, was made by one of them), otherwise why it does not (not signed, signed by a key that is not trusted, or git could not check).
    It does not depend on the policy mode: the warning of the default mode and the refusal of the strict one are built from it."""
    cmd = ["git"]
    if policy.allowed_signers_file:
        if not Path(policy.allowed_signers_file).is_file():
            return f"allowed signers file {policy.allowed_signers_file} does not exist"
        cmd += ["-c", f"gpg.ssh.allowedSignersFile={policy.allowed_signers_file}"]
    cmd += ["verify-commit"]
    if policy.trusted_signers:
        cmd.append("--raw")
    cmd.append(revision)
    try:
        result = subprocess.run(cmd, cwd=repo, capture_output=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"could not run git verify-commit: {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return "candidate commit is not signed by a trusted key" + (f" ({detail[-1]})" if detail else "")
    if policy.trusted_signers:
        signers = signer_fingerprints((result.stderr or "") + "\n" + (result.stdout or ""))
        if not signers.intersection(policy.trusted_signers):
            return "candidate commit is not signed by a key listed in trusted_signers" + (f" (signed by {', '.join(sorted(signers))})" if signers else "")
    return None


def verify_revision(repo: Path, revision: str, policy: SignaturePolicy) -> str | None:
    """None when `revision` is acceptable under `policy`, otherwise the reason it is refused. Only the strict mode refuses; the default mode accepts everything (the caller
    asks `unsigned_reason` to warn)."""
    if not policy.required:
        return None
    reason = unsigned_reason(repo, revision, policy)
    if reason is not None and policy.settings_unreadable:
        reason += " (the settings file could not be read, so signatures are required until it is fixed or removed)"
    return reason
