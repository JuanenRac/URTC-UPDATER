# Security Policy 🔒 (URTC-UPDATER)

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x  | ✅ Yes             |

## Reporting a Vulnerability

**CRITICAL: Do not report safety-critical vulnerabilities through public GitHub issues.**

This tool downloads repositories from GitHub, runs their `build-test` script in a staging clone and replaces a local checkout. What a report here can be about:

1. **A way to make it run or install something that was not asked for**, for example a path that escapes the workspace, a promotion of a staging clone that failed its build, or an update of a checkout that has local changes.
2. **A way to bypass the signature policy** (`signature_policy`, `require_signed_commits`) or to forge an entry of the evidence log.
3. **A secret or private detail** that reached a log, a message or a public file.

How to report:

1. **Email**: send a detailed report to `electrohobby3d@gmail.com`.
2. **Response**: initial acknowledgment within 48 hours.

We follow a coordinated disclosure policy. What the tool does and does not verify is described in its README and in the security baseline and threat model of URTC-DOCS.
