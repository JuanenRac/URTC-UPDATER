# Source map

Every file of the repository with a line on what it does: the annotated tree that the README carried before it was reduced to the first level (the first level, in eight languages, is in the section Repository Structure of the README).

```text
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - no static catalogue; built at discovery time from each repo's own manifest
│   ├── project_manifest.py # Reads/validates a repository-owned urtc.project.json
│   ├── version_parse.py   # ONE regex-extraction implementation, local+GitHub
│   ├── detect.py          # Scans a workspace root for what's installed
│   ├── github_client.py   # Concurrent raw-content fetch + real retry/backoff for transient network errors
│   ├── install.py         # git clone/pull + delegate to the project's own build script
│   ├── signature.py       # Optional signed-commits policy (git verify-commit before building)
│   ├── security.py        # The two protections of an install (signed commits, ask before the build check) and how to change them
│   ├── package.py         # Install a program from the signed package of its release (list, check, install, rollback)
│   ├── commits.py          # Compares a checkout with its remote by commit (git ls-remote)
│   ├── messages.py         # Install/update messages as codes plus parameters
│   ├── evidence.py         # Hash-chained log of every attempt
│   ├── settings.py         # Remembered preferences (language, workspace, retention, profiles)
│   ├── profiles.py         # Named station profiles
│   ├── notify.py           # Desktop notification for the notify-only check
│   ├── logs.py             # Rotation of the window log files
│   ├── i18n.py             # Real, complete GUI translations (8 languages)
│   ├── translations_data.py # The texts of the window, generated from the catalog of URTC-COMMON
│   ├── qt_gui.py           # Qt Quick bridge over the real discovery/update services
│   ├── packages_qt.py      # The Packages window: the signed packages of the releases
│   ├── qml/Main.qml        # Themed desktop shell: controls, checkpoints and About
│   ├── qml/HelpDialog.qml  # The quick-guide window (shared)
│   ├── qml/UpdateDialog.qml # The Check for updates window (shared)
│   ├── qml/PackagesDialog.qml # The Packages window: the signed packages of the releases
│   ├── gui.py              # Legacy Tkinter fallback if PySide6 is unavailable
│   ├── flasher_handoff.py  # Offers to start the Flasher with a firmware image whose release signature was checked here (it never flashes)
│   ├── main.py             # Dispatch: GUI by default, --cli for status/install/update
│   ├── urtc_pkg/           # Shared code copied from URTC-COMMON: self-update from a signed package, the update dialog and the quick guide
│   └── assets/             # The icon files the program ships with
├── tests/                  # Real tests for every module (`python -m pytest`)
├── docs/
│   ├── CLI_REFERENCE.md     # Command reference
│   ├── QML_DESKTOP_GUI.md   # Qt Quick GUI architecture
│   ├── WINDOW_GUIDE.md      # The window step by step, in pictures
│   └── screenshots/         # The window in the eight languages (written by tools/capture_screens.py)
├── images/                 # Media and app icons
├── tools/
│   ├── build_test.py        # Non-versioning build/compile check
│   ├── capture_screens.py   # Takes the pictures of the guide from the real window, without a screen
│   ├── ci_validate.py       # Manifest/CHANGELOG/docs validation used by CI
│   ├── generate_app_icon.py # Renders the public URTC SVG into the Windows-consumed icon
│   └── _doc_policy.py / _readme_parity.py / _tracked_names.py # Shared checks used by ci_validate.py
├── .env.example            # Environment variable template
├── build.sh / build.bat    # venv + editable install + compile-check
├── run.sh / run.bat        # GUI default / CLI entry point
├── run-gui.vbs             # Windows graphical launcher with no console window
├── pyproject.toml / requirements-dev.lock # Packaging, and the development dependencies closed with hashes
├── ruff.toml               # Settings of the static checks
├── urtc_i18n.lock.json     # Lock of the window texts generated from the catalog of URTC-COMMON
├── urtc.project.json       # Project manifest (version, maturity, evidence)
├── bump.py                 # Explicit version bump command (building never bumps)
├── bump_version.py         # Ecosystem-wide bump (pyproject.toml + __init__.py), called by bump.py
└── bump_manifest_version.py # Syncs urtc.project.json's version to the native one (--sync)
```
