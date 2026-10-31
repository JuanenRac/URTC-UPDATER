<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center">🇺🇸 <b>English</b> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 📦 Detect, Install, and Manually Update the Whole URTC Ecosystem

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="stdlib-only CLI core">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="PySide6 Qt Quick desktop GUI">
</p>

> **Visual desktop mode:** the default desktop interface is now built with
> **Qt Quick / QML** through the optional `PySide6` GUI runtime. The updater
> core and `--cli` mode remain stdlib-only for a headless machine.
>
> **Windows launch and update evidence:** double-click `run-gui.vbs` (or use
> bare `run.bat`) for the console-free desktop client. Its Safe Update panel
> shows real Preflight, Source refresh, Manifest validation, Build-test and
> Complete checkpoints with captured command evidence; `run.bat --cli ...`
> deliberately keeps a terminal for diagnostics.
> Install is available only for a missing checkout; Update only when GitHub is
> newer. During an approved action, checkpoints replace the selected-project
> controls and selecting another project restores them.
> **Install all missing** and **Update all outdated** are separately confirmed,
> sequential batch actions built from the same live state and safety path.

---

**Honesty check - what actually runs today:** **Maturity: established (one documented end-to-end run, not sustained use).** This project adapts HYDRA-UMC-UPDATER's own proven design (the same manifest discovery, atomic-by-verification staging-clone install/update and evidence log) to just the URTC ecosystem's repositories. It was run end to end against GitHub in an isolated workspace: a clean install and a later update of a real repository were cloned, built and promoted correctly, with the previous checkout kept as a backup. The discovery and version logic (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), the GitHub raw-content client with retry/backoff and a cached repository listing (`github_client.py`), the commit comparison (`commits.py`) and the clone-stage-verify-promote pipeline (`install.py`) are covered by tests (`python -m pytest`), including a local HTTP fixture server and real temporary git repositories with a local bare remote. The Qt bridge's own logic runs headless in the tests, and the window with its dialogs is loaded offscreen to check that it opens and answers; how it looks is checked by eye, not by a test. The 8-language coverage of `i18n.py` is enforced by test for keys and placeholders, not for translation quality. See `CHANGELOG.md` for exactly what has shipped so far.

---

> **Safety and security status:** this ecosystem is not a certified safety system, and no populated URTC board exists yet. The bootloaders check firmware images with CRC32 and a shared-key HMAC-SHA256, not with an asymmetric signature (planned); the published application images are signed with the public development key (`signing_key_kind: dev`), so anyone can produce an image the bootloader accepts; nothing has been transmitted to a real board. Read the [security baseline](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) and the [threat model](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md) before relying on any statement here for the safety of a person.

## 📋 At a glance

| | |
|---|---|
| Version | `0.2.0` |
| Maturity | Established |
| Tests | 482 (`python -m pytest`) |
| Stack | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Target | The PC of the person using it |
| On real hardware | Not applicable: nothing here runs on hardware |

**Jump to:** [Overview](#-overview) · [Architecture](#-architecture) · [Security](#-security--safety) · [Interfaces](#-interfaces) · [Quick start](#-quick-start) · [Testing](#-testing) · [Troubleshooting](#-troubleshooting) · [Structure](#-repository-structure) · [Related](#-related-projects)

<!-- urtc-section:status_updater -->
## 🚦 Project status

🟢 done and verified · 🟡 works, with known limits · 🟠 half done or not verified · 🔴 not done or not working. Nothing is green if it never ran on real hardware.

| Part | Status | What the repository can show |
| --- | :---: | --- |
| Software | 🟡 | Works on a PC and against the simulator; never run against a real board. |
| Interface | 🟡 | The window runs and is checked against a simulated board; not tried with a real adapter. |
| Tests | 🟢 | The test suite passes in the CI on every push. |
| Updates | 🟡 | Installs from signed packages with a rollback; tried on a PC only. |
| Security | 🟡 | Releases are signed with Ed25519 and checked before use; the key handling was not reviewed by anyone else. |
| Documentation | 🟡 | README in eight languages and reference documents; the translations were not reviewed by native speakers. |

<!-- /urtc-section:status_updater -->

## 🎯 Overview

URTC-UPDATER is a small tool - windowed GUI by default, full CLI with
`--cli` - meant to run on a developer's own Windows/Linux/macOS machine
(any workspace checked out the same way) that answers three questions
for every other real project it discovers via each sibling checkout's
own `urtc.project.json` manifest - the count itself is never hardcoded
here, since it grows as the ecosystem does:

1. **What's actually installed here, and what version is it?**
2. **What's the latest version published on GitHub?**
3. **If GitHub is newer, let me choose one project or a confirmed sequential batch.**

That last point is deliberate and non-negotiable: this tool never changes a
project on its own initiative. A selected-project action always needs an
explicit confirmation. The GUI may also offer **Install all missing** or
**Update all outdated**; each is a separately confirmed, sequential batch
whose projects follow the same manifest, version and safety gates. A
robot-control cell must never auto-update overnight without a person
approving the exact action.

Every real URTC repository declares `deployment_target: "user-pc"` -
there is no CM5/server role in this ecosystem, unlike HYDRA-UMC's.
Firmware repos (URTC, URTC-SMART-RACK, URTC-VISION-TOOL) are still
compiled and flashed FROM a workstation, they just don't run there
afterward; `registry.py`'s own `deploy` field records this (see section
3), and the GUI's project table filter always starts on "show
everything", since there is no platform-specific subset worth
defaulting to.

Illustrative example (the exact project count and every version number
below is made up for the shape of the output, not a real captured run -
the real count is whatever `registry.py` discovers today, never a fixed
number baked into this doc):

```
$ urtc-updater --cli status
Workspace root: /home/user/GitHub
PROJECT       MATURITY     ROLE      STACK           LOCAL     GITHUB    STATE
-------------------------------------------------------------------------------
URTC          functional   firmware  firmware-c      0.3.0     0.3.1     OUTDATED
URTC-FLASHER  functional   tool      python-qtquick  0.2.1     0.2.1     up to date
URTC-TESTER   functional   tool      python-qtquick  0.2.2     0.2.2     NEW COMMITS

3/3 installed, 1 outdated, 1 with new commits at the same version
Run `urtc-updater update <project>` to update one by hand - never automatic, see this tool's own README.

$ urtc-updater --cli update URTC
Updating URTC into /home/user/GitHub ...
OK  Updated /home/user/GitHub/URTC to v0.3.1 (commit 1a2b3c4d5e6f) after a verified build; previous installation kept at /home/user/GitHub/URTC.backup-1a2b3c4d
```

Running `urtc-updater` with no arguments (or double-clicking it)
opens the same information in a dark desktop control surface instead: a
**Local Ecosystem** panel with live discovery/install/update metrics, a
manifest-driven **Project Registry** tree, and a **Safe Update** panel for
the selected project. The layout makes the real guardrails visible:
manifest discovery, one explicit project action, manual confirmation,
optional build and an on-screen activity trail; the whole log is also written to a file under `~/.urtc_updater/logs` (the newest 20 are kept).

## 🧩 Role in URTC

URTC-UPDATER is the program that keeps a PC with the URTC repositories up to date. It finds every project next to it from the manifest each repository carries, says which version is installed and which one GitHub has, and installs or updates one project at a time after an explicit confirmation, running that project's own `build-test` script and never building anything itself. It does not change anything on its own: a robot-control cell must never update overnight without a person approving the exact action. It also installs the desktop programs (the flasher, the tester and itself) from the signed package of their release, and it can hand a firmware image whose release signature it checked to URTC-FLASHER, which does the flashing.

## 🏛️ Architecture

<p align="center">
  <img src="images/architecture.svg" alt="URTC-UPDATER architecture: who uses it, what it holds and what it depends on" width="100%">
</p>

How the parts of this repository fit together: who uses it, what it holds and what it depends on. The picture is drawn from `docs/architecture.json` and checked against the code.

### HOW A CHECK/UPDATE ACTUALLY WORKS

- **Version source**: the version of a project lives in a source file of that project (`pyproject.toml`, `Cargo.toml`, `version.go`, `package.json`, `version.properties`, `pubspec.yaml`, or a firmware `#define`, depending on its stack) that its own `bump.py` step writes, and that step has never created a git tag or a GitHub Release. So this tool reads that same file straight off the repo's default branch via GitHub's raw content host - not the Releases API, which would report every project as having no releases at all.
- **Local detection**: for each discovered project, checks whether
  a directory with that exact name exists under the workspace root (the
  standard ecosystem layout - every project as a sibling directory,
  exactly what URTC-FLASHER/URTC-TESTER's own build scripts
  already assume), and if so, reads its OWN local copy of that same
  version file.
- **One parsing implementation** (`version_parse.py`) is shared between
  the local read and the GitHub fetch, so a local checkout and a GitHub
  fetch are never interpreted by two independently-drifting regexes.
- **Install/update**: `git clone` (install) builds afterward as a
  separate step. Updating an EXISTING checkout is atomic-by-verification
  instead: the candidate is cloned, fast-forward-merged (never a force-
  reset, so real local edits fail loudly instead of being discarded),
  and built/verified in a fully independent staging clone FIRST - the
  live installation is only ever touched (via two back-to-back directory
  renames, the previous install kept at `<name>.backup-xxxxxxxx`, not deleted) if
  that staging build actually succeeds. A build failure, a diverged/
  dirty checkout, a crash, or a full disk at any point before that final
  promotion leaves the previous installation completely untouched and
  still operative - see `install.py`'s own `clone_or_pull` docstring.
  The staging clone's own git remote is restored to the real GitHub
  upstream right after it is created (a plain local clone would
  otherwise point it at the old install path, silently ending all future
  updates once promoted), and the installed checkout's own real local
  data (anything git considers untracked or ignored - `data/settings.json`
  and similar, excluding regenerable build artifacts) is carried into
  the staging clone before it builds, so a project's own real operational
  state survives an update instead of being stranded in the kept
  `.backup-xxxxxxxx` checkout.
  Either way this runs whichever of that project's own `build-test.sh`/
  `build-test.bat` (the non-versioning check - see section 3) it
  actually has. This tool never reimplements a project's own build
  steps.

### ARCHITECTURE & DESIGN DECISIONS

- **Qt Quick GUI by default, `--cli` for headless.** `main.py` checks for
  `--cli` before importing the optional PySide6 runtime, so CLI mode works on
  a genuinely headless machine with no display or desktop dependency. Bare
  invocation starts the QML client where the runtime is installed; the older
  Tkinter shell remains only as a temporary compatibility fallback.
- **The windowed GUI is real and speaks 8 languages (`i18n.py`) - `--cli` deliberately doesn't.** Every widget, and the text of every checkpoint and failure of an install or update, is shown in the language chosen in a selector (en/es/fr/it/de/zh/ja/pt, Portugal Portuguese for pt), taken from a saved preference or the system locale. Install and update steps travel as message codes plus parameters and only the window turns them into text, so a language switch re-renders them. Project and family names and each project's own `notes`/`tech` text stay untranslated: the manifest is their one source of truth. `--cli` output stays English on purpose, because it is meant to be scripted and piped.
- **`deploy` is a classification, not a restriction.** A first pass of this
  adaptation copied HYDRA-UMC-UPDATER's own GUI default verbatim - defaulting
  the deploy filter to `"cm5"` on Linux - without checking that no real URTC
  repository ever declares that deployment target (every one of them is
  `"user-pc"`: firmware is compiled and flashed FROM a workstation, it never
  runs there afterward). The GUI would have opened to an empty table on
  Linux. Fixed: the filter always starts on "show everything" here, since
  there is no CM5/server role in this ecosystem to special-case for.
  `registry.py`'s `deploy` field ("cm5" / "user-pc" / "mobile" / "wearable" /
  "dev-server") still records the classification per repository manifest -
  it is just never used as a startup default.
- **No per-stack build logic in this tool.** The ecosystem spans several toolchains (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, ARM firmware). Reimplementing each project's build here would create a second place that claims to know how to build it, guaranteed to drift from the project's own script. `install.py` instead runs the project's own non-versioning `build-test.sh` (`build-test.bat` on Windows) and fails closed when a checkout has none. The versioning build scripts (`build.sh` and similar) are never run by this tool.
- **GitHub raw content, not the Releases API.** See section 2 above -
  this ecosystem's versioning convention never creates a tag/release, so
  the Releases API would be actively wrong here, not just less
  convenient.
- **A transient network failure gets a real retry; a definitive answer never does.** Every real GitHub request (`github_client.py`'s `_urlopen_with_retries`) retries up to 3 times with backoff, but only for a connection that never got a response at all (DNS/timeout/reset). A real HTTP status GitHub actually returned - 404, 403, 500 - is never retried: GitHub already answered, and hammering it again would only spend more of the rate limit for the same result.
- **A malformed remote catalog fails loudly; one malformed project doesn't.** If GitHub's repository listing itself is unreachable or unparseable, `discover_remote_projects()` raises and the desktop bridge falls back to a locally-discovered project list rather than showing a broken/empty scan. One single repository's malformed manifest, by contrast, is isolated into that scan's own `errors` list and never aborts discovery of the rest - a real fixture-server test (`tests/test_github_client.py`) proves both paths.
- **CLI actions remain explicit; GUI batches remain confirmed.** The CLI
  `install`/`update` commands take one project name. The desktop GUI can also
  run **Install all missing** or **Update all outdated**, but only after a
  separate confirmation and sequentially through the same safety gates. No
  unattended automatic update exists.
- **stdlib only.** `urllib` for the GitHub fetches (`github_client.py`),
  `subprocess` for git/build-script calls (`install.py`), nothing else -
  a tool responsible for keeping every OTHER project's dependencies sane
  staying dependency-free itself is deliberate.
- **Known simplification:** a repository made of several independently versioned binaries (URTC has four: main and slave, application and bootloader) is tracked by ONE version, the one its own `urtc.project.json` declares in `native_version`. That answers "is this repository roughly up to date", not a flash's own per-component version check.

<!-- urtc-section:updates -->
### How it updates

This program can look for a newer version of itself: the "Check for updates" button asks GitHub once and offers a signed package only if it is for your system and newer. Nothing is checked or installed on its own unless you turn the check on, and an update needs your confirmation. The package must match its SHA-256 and the signature of the releases key pinned in the program; the previous version is kept, and it is restored by itself if the new one does not start. `urtc-updater --cli package list|check|install|rollback` does the same from the command line for the flasher and the tester, and `install --file` works without a network.
<!-- /urtc-section:updates -->

## 🖼️ Screenshots

<!-- urtc-shots -->
Captured at 1920×1080 on a test bench, with sample data and no real installation behind them.

<table>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/deck.png" alt="The window over a workspace with the family in it: every project with its maturity, stack and local version, and the safe update actions." width="100%"><br><sub>The window over a workspace with the family in it: every project with its maturity, stack and local version, and the safe update actions.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/packages.png" alt="The Packages window: the programs of the family that a release publishes as a signed package, each checking its own release." width="100%"><br><sub>The Packages window: the programs of the family that a release publishes as a signed package, each checking its own release.</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/help.png" alt="The Help window: the steps for using the program, written in the language of the window." width="100%"><br><sub>The Help window: the steps for using the program, written in the language of the window.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/updates.png" alt="The update window: a newer signed package is installed only after you confirm it." width="100%"><br><sub>The update window: a newer signed package is installed only after you confirm it.</sub></td>
</tr>
</table>
<!-- /urtc-shots -->

These pictures are the real window, drawn without a screen as it opens (nothing checked, nothing installed). The guide goes through the window, the Help window, the update window and the Packages window, and shows them in the eight languages of the program.

[Guide with pictures](docs/WINDOW_GUIDE.md)

## 🔒 Security & Safety

| Threat | Defence |
|---|---|
| An update nobody approved, for instance overnight on a robot cell | Nothing changes on its own: an action on a project needs an explicit confirmation, and a batch is confirmed separately and runs one project at a time |
| A broken or half-finished update leaves a working install unusable | The candidate is cloned, fast-forward-merged (never a force reset, so local edits fail loudly) and built in a staging clone first; the live install is only replaced, by two directory renames, if that build passes, and the previous one is kept as `<name>.backup-xxxxxxxx` |
| A build that cannot be run here | A build-test that answers 75 means the validation is unavailable: the update is refused unless the person accepts it in the settings |
| A commit nobody signed | A revision without a valid signature is installed with a warning; with `"signature_policy": "require"` it is refused |
| A package that was tampered with | A package is accepted only if its size, its SHA-256 and its Ed25519 signature match and it comes from GitHub's download hosts; it is installed only after a confirmation, never while another install runs, and the previous version can be restored |
| A trace of what was done is lost | Every install, update and restore is written, with time, host and user, to a log chained by hashes |

The rest of the policy follows, in the words of the program.

**What the build-test may answer:** exit code 0 means validated and any other code means failed, except 75, which means that the validation is *unavailable* (a tool it needs is not installed). That is reported as such and the update is refused, unless you accept it by setting `validation_unavailable` to `accept` in the settings (or `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). A build-test should leave the tree as it found it: when it changes a file that git tracks, the file is put back to the committed content before the promotion and the steps say which.

**Signed commits (warn only by default; requiring them is an opt-in, off by default):** a revision that carries no valid signature (`git verify-commit`: GPG keyring, or SSH with `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) is installed anyway, and the steps of the window and of the command line say that it is not signed. With `"signature_policy": "require"` in `~/.urtc_updater_settings.json` (or `URTC_UPDATER_REQUIRE_SIGNED=1`; the older `"require_signed_commits": true` means the same) the candidate - a fresh clone's `HEAD` or an update's fetched `FETCH_HEAD` - must pass `git verify-commit` before its manifest is read or anything in it is built, and a refused candidate leaves the installed checkout untouched.

**Security options (both off by default; changeable from the window's Security button, the `security` command, the settings file, the environment and the command line):** besides requiring signed commits, the updater can *ask before the build check* of a candidate runs (`"confirm_before_build": true`, `URTC_UPDATER_CONFIRM_BUILD=1`, `--confirm-build`). It fetches and validates the candidate, shows the project, the commit, its author, its signature and the build or tool scripts that changed, and runs nothing until you answer; with no window and no terminal to ask, it runs nothing (`--yes` answers for scripts). `--require-signed` / `--no-require-signed` and `--confirm-build` / `--no-confirm-build` apply to one run, and a run that turns off a protection that the saved settings have on says so; the window, and `urtc-updater --cli security --require-signed off`, ask for confirmation before saving a lower level. A settings file that exists but cannot be read counts as "signatures required" until it is fixed or removed. The build check is also told `URTC_PYTHON`, the interpreter that runs the updater, so a project tests with that Python and not with whichever one the system finds first.

## 🔌 Interfaces

The program starts the Qt Quick window when it is run without arguments and has a full command line with `--cli` (it needs no display and no PySide6): `status [--offline]`, `install PROJECT`, `update PROJECT [--preview]`, `restore-backup PROJECT [--list]`, `clean-backups [--keep N] [--dry-run]`, `check [--notify] [--quiet]` (exit code 10 when something can be updated), `package list|check|install|rollback`, `evidence [--export FILE]` and `security`. Every command, flag and exit code, with real output, is in [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md); the window is described in [docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md). What the housekeeping and station commands do:

- **Kept previous installations.** Every update keeps the installation it replaced in `<name>.backup-xxxxxxxx`. The newest 2 per project are kept (`"backups_to_keep"` in `~/.urtc_updater_settings.json` changes the number) and older ones are removed after a successful update. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` removes them on demand, together with any hidden staging folder a crashed run left behind.
- **Optionally, install from the signed package of a release.** `urtc-updater --cli package list|check|install|rollback` installs a program (the flasher, the tester or this updater) from the `.zip` / `.tar.gz` its release carries, instead of a clone and a build. Only a strictly higher version is offered, only from GitHub's download hosts, and the package must match its announced size and SHA-256 and the Ed25519 signature of the key of the releases pinned in the program; a package that fails any check is deleted. It asks before installing (`--yes` answers for scripts), keeps the two latest releases and `rollback` points back to the previous one. `install --file PACKAGE` works from a file on disk with its `.sha256` and `.sig` next to it, with no network. The window has a "Check for updates" button for the updater itself with the same rules; the automatic check at start is an option, off by default. Tested with packages generated on a computer, not yet with a published release.
- **A Packages window and a Help window.** The "Packages" button lists the signed packages of the flasher, the tester and this updater: each row checks its release when you press "Check for updates", downloads and verifies the package, asks before it installs and goes back to the previous version, with the same rules and security options as the `package` command; nothing is installed while a project is being installed or updated. The "Help" button opens a five-step guide in the language of the window.
- **Restoring one.** `urtc-updater --cli restore-backup <PROJECT> [--backup FOLDER] [--list]` puts a kept installation back. The installation being replaced is kept too, so the swap can be undone. The window offers the same two actions next to Update selected: Preview update (what the update would bring, without changing anything) and Restore previous version.
- **Same version, new commits.** The version only moves on a release build, so `status` also compares each installed project's commit with the remote one (`git ls-remote`) and shows `NEW COMMITS` when GitHub has work the checkout lacks. The window shows the same state and offers Update.
- **Looking before approving.** `urtc-updater --cli update <PROJECT> --preview` fetches the candidate and shows its commit, author, version, signature state and the build or tool files it changes, without touching the checkout.
- **Notify only.** `urtc-updater --cli check [--notify] [--quiet]` lists what could be updated and changes nothing. It exits with code 10 when something can be updated, so a scheduled task can notify a person; `--notify` also shows a desktop notification.
- **Evidence.** Every install, update and restore is recorded with time, host and user in `.urtc-updater/evidence.jsonl`, each line chained to the previous one by hash. `urtc-updater --cli evidence [--export FILE]` verifies the chain and can export it as one JSON document.
- **Station profiles.** `"profiles"` in the settings file names the projects a machine works with and whether batches are allowed; `--profile NAME` (or `"profile"` in the settings) restricts `status`, `check`, `install` and `update` to it, and the window follows the same profile.

## 🚀 Quick start

```bash
chmod +x build.sh   # one-time
./build.sh          # creates .venv, pip install -e ., compile-checks everything
./run.sh                              # windowed GUI (default)
./run.sh --cli status                 # what's installed, local vs. GitHub version
./run.sh --cli status --offline       # same, skipping the GitHub check
./run.sh --cli install <PROJECT-NAME> # clone + build one project not yet installed
./run.sh --cli update  <PROJECT-NAME> # pull + rebuild one project already installed
```

On Windows: `build.bat`, then `run.bat` (GUI) / `run.bat --cli status` /
`run.bat --cli install <name>` / `run.bat --cli update <name>`.

The preferred GUI needs the optional Qt runtime (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` already install it). `--cli` has no GUI dependency and
is the correct entry point for a headless machine. If Qt is unavailable, the
older Tkinter shell is only a compatibility fallback.

<!-- urtc-section:compatibility -->
### Requirements & compatibility

Which versions of the URTC programs work together, and which protocol version each one speaks, is listed in the compatibility table that URTC-COMMON generates: [docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md).
<!-- /urtc-section:compatibility -->

## 🧪 Testing

The suite has 482 tests (`QT_QPA_PLATFORM=offscreen python -m pytest tests -q`; a few skip where an optional dependency is missing): the discovery and the manifests, the one version parser, the GitHub client against a local server (retries, errors, a malformed catalogue), install and update on real local git repositories (staging, promotion, backup, refusals, a build-test that answers 75, workspace safety), restoring and cleaning backups, the signed-commit policy, the security options, signed packages and their rollback, the evidence chain, the settings and profiles, the window texts in the eight languages and the Qt bridge, and the pictures of the window guide, drawn without a screen. `python -m mypy` and `ruff check .` run in CI.

## 🏗️ Build & Release

`build.sh` / `build.bat` create the `.venv`, install the package (`pip install -e .`, with the Qt runtime for the window) and compile-check everything; `build-test.sh` / `build-test.bat` check without installing; `run.sh` / `run.bat` start the window, or the command line with `--cli`; `run-gui.vbs` opens it on Windows with no console window. A packaged standalone executable is not built yet.

## 🩺 Troubleshooting

- `status` shows `?` for a project's GitHub version: GitHub could not be read for it. The STATE column says why (for example `installed, GitHub unknown (HTTP 404)` or a rate-limit notice).
- `status` shows `-` for GitHub with no error shown: run `status`
  (without `--offline`) - `-` only appears when the GitHub check was
  skipped entirely.
- `install`/`update` fails with "No non-versioning build-test.sh/.bat found": that checkout has no `build-test.sh` (`build-test.bat` on Windows). Update the project itself, or verify it by hand; this tool never runs a versioning build script instead.
- `git pull --ff-only` fails: the local checkout has uncommitted changes
  or diverged history - resolve that manually (`git status` in that
  project's own directory) before retrying `update`. This tool never
  force-resets a checkout.

## 📂 Repository Structure

<p align="center">
  <img src="images/repository-structure.svg" alt="Repository structure of URTC-UPDATER" width="100%">
</p>

<details>
<summary>Text version of the tree</summary>

```text
URTC-UPDATER/
├── src/urtc_updater/                                  the program: discovery, versions, install and update, security, signed packages, the Qt Quick window and its texts in eight languages
├── tests/                                             real tests for every module
├── docs/                                              command reference, GUI and window guide
├── tools/                                             build check, screenshots, icon, shared tools
├── images/                                            banner and the pictures of this README
├── .github/                                           CI workflow, issue and pull-request templates
├── build.sh build.bat                                 build scripts
├── build-test.sh build-test.bat                       build and test scripts that change nothing in the repository
├── test.sh test.bat                                   run the tests
├── run.sh run.bat                                     start the program
├── urtc.project.json                                  manifest: version, role, maturity and build command
├── CHANGELOG.md                                       what changed in each version
├── SECURITY.md SUPPORT.md LICENSE                     security policy, support and license
├── CONTRIBUTING.md CODE_OF_CONDUCT.md                 how to contribute and the code of conduct
├── .gitattributes .gitignore                          Git settings
├── run-gui.vbs                                        Windows launcher with no console window
├── bump.py bump_version.py bump_manifest_version.py   scripts that raise the version
├── urtc_i18n.lock.json                                lock of the window texts
├── LICENSE.md .env.example                            documentation license and variables
└── pyproject.toml requirements-dev.lock ruff.toml     package, locked tools, lint settings
```

</details>

The annotated list of every source file, one line each, is in [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md).

## 🗺️ Roadmap & Known limits

- A packaged standalone GUI executable (PyInstaller, matching
  URTC-FLASHER/URTC-TESTER's own `build_exe.bat`/`.sh` convention) for a
  double-click install with no `pip`/venv step at all - today's GUI still
  needs `./build.sh` first like the CLI does.
- Optional per-project dependency preflight (report a missing
  arm-none-eabi-gcc/Node toolchain before an `install` fails partway
  through).
- Per-component tracking for URTC's own multi-binary firmware (see the
  "known simplification" in section 3), once there's a real need beyond
  the single representative component this tracks today.

## 🌍 Languages

README and texts exist in English, Spanish, French, Italian, German, Chinese, Japanese and European Portuguese.

## 🔗 Related Projects

URTC is made of independent repositories, each with its own version, tests and README. This is the family, by group:

* **URTC Tool Platform:**
  * [URTC](https://github.com/JuanenRac/URTC) - firmware of the tool-head board (25 tool profiles, CAN bootloader) and the CAN protocol reference.
  * [URTC-COMMON](https://github.com/JuanenRac/URTC-COMMON) - the CAN protocol written once as data (specification, generated tables, conformance vectors) and the code the programs share.
  * [URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER) - desktop tool that updates the board firmware over CAN or over SWD/JTAG.
  * [URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY) - gateway in front of the CAN bus: lets only listed identifiers through, limits their rate and asks for a session key.
  * [URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK) - hardware-independent C logic and command protocol for a tool rack with pre-heating and lifecycle tracking.
  * [URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER) - desktop live CAN-bus tester that shows the controls and telemetry of the tool profile a board reports.
  * [URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL) - sensor-frame protocol in C and a Python thermal/RGB companion for an inspection tool head.
  * [URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO) - browser app that flashes and tests the board over Web Serial and SLCAN, with nothing to install.
* **Ecosystem Operations:**
  * [URTC-DEVTOOLS](https://github.com/JuanenRac/URTC-DEVTOOLS) - the shared repository tools of the family as one versioned set, with a lock file that tells a copy that was edited from one that fell behind.
  * [URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS) - architecture, interfaces, security baseline and generated catalogue of the ecosystem, plus the tools that compare all repositories.
  * **URTC-UPDATER** (this repository) - desktop tool that detects, installs and updates the repositories of the URTC family, one explicit action at a time.

**Sister projects (independent, with the same base and tools):**

* **[HYDRA-UMC-DOCS](https://github.com/JuanenRac/HYDRA-UMC-DOCS)** - sister project: the documentation hub of HYDRA-UMC, an independent ecosystem that shares this one's base and tools
* **[ARMOR-DOCS](https://github.com/JuanenRac/ARMOR-DOCS)** - sister project: the documentation hub of A.R.M.O.R., the security ecosystem, also independent and on the same base
* **[JuanenRac](https://github.com/JuanenRac/JuanenRac)** - the profile and the status dashboard of all the ecosystems

## 📚 Documentation

- **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — every `--cli` subcommand, real output captured from an installed run, and the exit-code contract.
- **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — how the Qt Quick/QML desktop client is structured, and how it stays a real control surface over the same backend `--cli` uses rather than a second implementation.
- **[Changelog of this repository](CHANGELOG.md)**
- Questions, ideas and reports: electrohobby3d@gmail.com

## 🤝 Contributing & Community

* Before a pull request run `URTC_CI=1 python tools/ci_validate.py`: it must pass. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).
* The README exists in eight languages: a change to the text is made in all eight files, and the sections shared with other repositories are written by `tools/readme_sections.py` of URTC-COMMON.
* A change to the CAN protocol starts in URTC-COMMON (`spec/can_protocol.json`) and reaches this repository through the checked copy.
* Do not describe as working on a board what has only been built.
* Report a vulnerability privately: [SECURITY.md](SECURITY.md). Questions, ideas and reports: electrohobby3d@gmail.com ([SUPPORT.md](SUPPORT.md)).

## 👤 AUTHOR

**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENSE

GPL-3.0-or-later - see [LICENSE](LICENSE).
