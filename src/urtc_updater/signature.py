# =============================================================================
# URTC-UPDATER - Optional commit-signature policy: signature.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Commit-signature policy: warn by default, require on request.

By default the updater trusts whatever the GitHub remote serves (a
compromised account or repository could push a commit that this tool would
then build and run). The policy decides what happens with a revision that
carries no valid GPG or SSH signature (`git verify-commit`):

* `warn` (the default): the install or update goes ahead, and the window and
  the command line state in the steps that the revision is not signed.
* `require`: the candidate revision - the fresh clone's HEAD, or the fetched
  FETCH_HEAD of an update - must carry a valid signature BEFORE its manifest
  is read or anything in it is built. A refused candidate leaves the
  installed checkout untouched.

A settings file that exists but cannot be read counts as "required" (the safe side)
until it is fixed or removed; the environment variable can still say otherwise.
The other protection, confirming before the build check, is in `security.py`.

Require signatures in `~/.urtc_updater_settings.json`:

    {"signature_policy": "require",
     "require_signed_commits": true,
     "allowed_signers_file": "/home/me/.config/urtc/allowed_signers"}

or with the environment variable `URTC_UPDATER_REQUIRE_SIGNED=1` (and
`URTC_UPDATER_ALLOWED_SIGNERS=<file>`). `allowed_signers_file` is the
OpenSSH allowed-signers file used for SSH-signed commits; GPG-signed
commits are checked against the user's own GPG keyring.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import security
from .settings import load_settings, settings_state


@dataclass(frozen=True)
class SignaturePolicy:
    required: bool = False
    allowed_signers_file: str | None = None
    #: True when the settings file exists but cannot be read: signatures are then required (unless the environment says otherwise) until it is fixed or removed.
    settings_unreadable: bool = False

    @property
    def mode(self) -> str:
        """"require" refuses an unsigned revision, "warn" (the default) installs it and says so."""
        return "require" if self.required else "warn"


def current_policy() -> SignaturePolicy:
    """The policy in force: the environment variables win over the saved
    settings, so a CI job or a one-off run can require signatures without
    touching the user's settings file."""
    saved = load_settings()
    unreadable = settings_state() == "corrupt"
    required = security.effective_require_signed()
    signers = os.environ.get("URTC_UPDATER_ALLOWED_SIGNERS") or saved.get("allowed_signers_file")
    return SignaturePolicy(required, signers if isinstance(signers, str) and signers else None, unreadable and required)


def unsigned_reason(repo: Path, revision: str, policy: SignaturePolicy) -> str | None:
    """None when `revision` carries a signature that verifies, otherwise why it does not (not signed, signed by a key that is not trusted, or git could not check).
    It does not depend on the policy mode: the warning of the default mode and the refusal of the strict one are built from it."""
    cmd = ["git"]
    if policy.allowed_signers_file:
        if not Path(policy.allowed_signers_file).is_file():
            return f"allowed signers file {policy.allowed_signers_file} does not exist"
        cmd += ["-c", f"gpg.ssh.allowedSignersFile={policy.allowed_signers_file}"]
    cmd += ["verify-commit", revision]
    try:
        result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"could not run git verify-commit: {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return "candidate commit is not signed by a trusted key" + (f" ({detail[-1]})" if detail else "")
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
