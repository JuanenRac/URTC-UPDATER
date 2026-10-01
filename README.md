<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center">🇺🇸 <b>English</b> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a></p>

### 📦 Detect, Install, and Manually Update the Whole URTC Ecosystem

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0-blue.svg" alt="GPL 3.0">
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

**Honesty check - what actually runs today:** **Maturity: scaffolding.** This project adapts HYDRA-UMC-UPDATER's own proven design (the same manifest discovery, atomic-by-verification staging-clone install/update, evidence log) to just the URTC ecosystem's six repositories. The discovery/version logic (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), the real GitHub raw-content client with retry/backoff (`github_client.py`), and the install/update pipeline's clone-stage-verify-promote logic (`install.py`) are real and tested - 106 passing tests (`pytest tests/`), including a fixture HTTP server proving the malformed-catalog-vs-malformed-project isolation and real temp-directory git clone/build round-trips. It has never installed or updated a real URTC repository end to end yet. `i18n.py`'s 7-language coverage is enforced by test (`test_i18n.py`), but only for key-parity across languages, not translation quality. See `CHANGELOG.md` for exactly what has shipped so far.

---

## 1. 🛠️ TECHNICAL OVERVIEW

URTC-UPDATER is a small tool - windowed GUI by default, full CLI with
`--cli` - meant to run on a developer's own Windows/Linux/macOS machine
(any workspace checked out the same way) that answers three questions
for every other real project it discovers via each sibling checkout's
own `urtc.project.json` manifest - the count itself is never hardcoded
here, since it grows as the ecosystem does (six repositories today):

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
Checking GitHub... 6/6
PROJECT                        STACK       LOCAL     GITHUB    STATE
--------------------------------------------------------------------
URTC                           firmware-c  0.3.0     0.3.1     OUTDATED
URTC-FLASHER                   python-qt   0.2.1     0.2.1     up to date
URTC-TESTER                    python-qt   0.2.2     0.2.2     up to date
...
6/6 installed, 1 outdated

$ urtc-updater --cli update URTC
Updating URTC into /home/user/GitHub ...
OK  Pulled latest into /home/user/GitHub/URTC
OK  build_firmware.sh completed successfully.
```

Running `urtc-updater` with no arguments (or double-clicking it)
opens the same information in a dark desktop control surface instead: a
**Local Ecosystem** panel with live discovery/install/update metrics, a
manifest-driven **Project Registry** tree, and a **Safe Update** panel for
the selected project. The layout makes the real guardrails visible:
manifest discovery, one explicit project action, manual confirmation,
optional build and an on-screen activity trail; full command evidence
continues to be written to the launch terminal.

<p align="center">
  <img src="images/" alt="URTC-UPDATER real desktop overview" width="100%">
</p>

## 2. 🔄 HOW A CHECK/UPDATE ACTUALLY WORKS

- **Version source**: this ecosystem's own "odometer" auto-bump
  convention (every real build increments a version number that lives
  IN a source file - `pyproject.toml`, `Cargo.toml`, `version.go`,
  `package.json`, `version.properties`, `pubspec.yaml`, or a firmware
  `#define`, depending on the project's stack) has never created a git
  tag or a GitHub Release for that bump. So this tool reads the SAME
  file every project's own `bump_version.py`/build script already
  writes, straight off the repo's default branch via GitHub's raw
  content host - not the Releases API, which would report every project
  as having no releases at all.
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
  renames, the previous install kept at `<name>.backup`, not deleted) if
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
  `.backup` checkout.
  Either way this runs whichever of that project's own `build-test.sh`/
  `build-test.bat` (the non-versioning check - see section 3) it
  actually has. This tool never reimplements a project's own build
  steps.

<p align="center">
  <img src="images/" alt="URTC-UPDATER installation or update checkpoints in progress" width="100%">
</p>

## 3. 🧱 ARCHITECTURE & DESIGN DECISIONS

- **Qt Quick GUI by default, `--cli` for headless.** `main.py` checks for
  `--cli` before importing the optional PySide6 runtime, so CLI mode works on
  a genuinely headless machine with no display or desktop dependency. Bare
  invocation starts the QML client where the runtime is installed; the older
  Tkinter shell remains only as a temporary compatibility fallback.
- **The windowed GUI is real, 7-language multilingual (`i18n.py`) - `--cli` deliberately isn't.** Every real widget re-labels live from a language `Combobox` (en/es/fr/it/de/zh/ja, the same 7 the public dashboard and every README ship), detected from a saved preference or the OS's own locale. Project/family names and each project's own real `notes`/`tech` text stay untranslated - `registry.py` is their one source of truth, and 7 parallel copies of real engineering documentation would stop it being that. `--cli` output stays English-only on purpose: it's meant to be scripted/piped, where stable, greppable text matters more than localization.
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
- **No per-stack build logic in this tool.** The ecosystem spans 7
  toolchains (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, ARM
  firmware). Reimplementing `npm install && npm run build` /
  `cargo build --release` / `./gradlew assembleDebug` / etc. HERE would
  create a second place that claims to know how to build each project,
  guaranteed to drift from that project's own real (and already correct)
  `build.sh`/`.bat`. `install.py` instead probes for a known build-script
  name (`build.sh`, `build_firmware.sh`, `build_exe.sh`,
  `build-android.sh`, and their `.bat` equivalents - the real names used
  across the ecosystem's own discovered projects) and runs whichever one
  exists.
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
- **Known simplification**: URTC is a real multi-component firmware repo
  (4 independently-versioned binaries - main + slave, app + bootloader
  each - see its own `build_firmware.sh`) with no single "the" version
  number. `registry.py` tracks ONE representative component per repo -
  good enough to answer "is this repo roughly up to date", not a
  replacement for a real flash's own per-component version check.

## 📂 DIRECTORY STRUCTURE

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - no static catalogue; built at discovery time from each repo's own manifest
│   ├── project_manifest.py # Reads/validates a repository-owned urtc.project.json
│   ├── ecosystem_catalog.py # Parser for a public ecosystem discovery catalog (not yet wired into main.py)
│   ├── version_parse.py   # ONE regex-extraction implementation, local+GitHub
│   ├── detect.py          # Scans a workspace root for what's installed
│   ├── github_client.py   # Concurrent raw-content fetch + real retry/backoff for transient network errors
│   ├── install.py         # git clone/pull + delegate to the project's own build script
│   ├── i18n.py             # Real, complete GUI translations (7 languages)
│   ├── qt_gui.py           # Qt Quick bridge over the real discovery/update services
│   ├── qml/Main.qml        # Themed desktop shell: controls, checkpoints and About
│   ├── gui.py              # Legacy Tkinter fallback if PySide6 is unavailable
│   └── main.py             # Dispatch: GUI by default, --cli for status/install/update
├── tests/                  # Real tests: github_client, i18n, install, project_manifest, registry
├── docs/
│   ├── CLI_REFERENCE.md     # Command reference
│   └── QML_DESKTOP_GUI.md   # Qt Quick GUI architecture
├── images/                 # Media and app icons
├── tools/
│   ├── build_test.py        # Non-versioning build/compile check
│   ├── ci_validate.py       # Manifest/CHANGELOG/docs validation used by CI
│   └── generate_app_icon.py # Renders the public URTC SVG into the Windows-consumed icon
├── .env.example            # Environment variable template
├── build.sh / build.bat    # venv + editable install + compile-check
├── run.sh / run.bat        # GUI default / CLI entry point
├── run-gui.vbs             # Windows graphical launcher with no console window
├── bump_version.py         # Ecosystem-wide odometer bump (pyproject.toml + __init__.py)
└── bump_manifest_version.py # Syncs urtc.project.json's version to the native one (--sync)
```

## ⚙️ BUILD & RUN GUIDE

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

**Troubleshooting**

- `status` shows `?` for a project's local or GitHub version: its version
  file exists but this project's own convention changed since
  `registry.py` was last updated - check `registry.py`'s entry for that
  project against its real, current version file.
- `status` shows `-` for GitHub with no error shown: run `status`
  (without `--offline`) - `-` only appears when the GitHub check was
  skipped entirely.
- `install`/`update` fails with "No build.sh/.bat found": that project
  uses a build script name this tool doesn't recognize yet - check its
  own README for the real one, and consider adding it to
  `install.py`'s own `BUILD_SCRIPT_CANDIDATES_*` lists.
- `git pull --ff-only` fails: the local checkout has uncommitted changes
  or diverged history - resolve that manually (`git status` in that
  project's own directory) before retrying `update`. This tool never
  force-resets a checkout.

## 🚀 ROADMAP

- A packaged standalone GUI executable (PyInstaller, matching
  URTC-FLASHER/URTC-TESTER's own `build_exe.bat`/`.sh` convention) for a
  double-click install with no `pip`/venv step at all - today's GUI still
  needs `./build.sh` first like the CLI does.
- Optional per-project dependency preflight (report a missing
  arm-none-eabi-gcc/Node toolchain before an `install` fails partway
  through).
- A `--json` output mode for `status`, for scripting against it.
- Per-component tracking for URTC's own multi-binary firmware (see the
  "known simplification" in section 3), once there's a real need beyond
  the single representative component this tracks today.

## 🔗 Related Projects

**URTC** (Universal Robot Tool Controller) is a real physical tool-changer platform by the same author (JuanenRac / Electro Hobby 3D). Each repository has its own version, its own tests and its own README; this is the whole family:

- **[URTC](https://github.com/JuanenRac/URTC)** — firmware for the physical Universal Robot Tool Controller PCB, 25+ tool profiles over CAN bus.
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — desktop GUI flashing tool for URTC boards, CAN-OTA plus full-chip SWD/JTAG.
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — firmware for a board-mounting rack with real tool-ID decoding and Smart Idle pre-heating logic.
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — desktop live CAN-bus diagnostic tool for URTC boards, one panel per tool profile.
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — firmware plus a real Python vision companion for a thermal/RGB inspection tool head.
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — browser-based alternative to URTC-TESTER via the Web Serial API, no local install needed.
- **URTC-UPDATER** (this repository) — detects, installs and updates the ecosystem's own repositories.

This tool's design (manifest discovery, atomic-by-verification install/update, evidence log) is shared with **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** and **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** - the same author's updaters for the HYDRA-UMC and A.R.M.O.R. ecosystems, each scoped to its own repositories only.

---

## 📚 Documentation & Community

- **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — every `--cli` subcommand, real output captured from an installed run, and the exit-code contract.
- **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — how the Qt Quick/QML desktop client is structured, and how it stays a real control surface over the same backend `--cli` uses rather than a second implementation.
- **[Changelog of this repository](CHANGELOG.md)**
- Questions, ideas and reports: electrohobby3d@gmail.com

## 👤 AUTHOR
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENSE

GPL-3.0-or-later - see [LICENSE](LICENSE).
