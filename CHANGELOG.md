# Changelog

All notable changes to this project are documented here.

## [Unreleased]

- **The README follows the universal layout in the eight languages:** the sections are in the fixed order with the fixed names, the Architecture and the Repository Structure are drawn from `docs/architecture.json` and `docs/structure.json`, the security options and the signed-commit policy moved to Security & Safety, the command line and the housekeeping commands to Interfaces, and the troubleshooting list has its own section. The source of the version is now described without explaining how versions are raised.
- **The layout of the README is checked in the CI:** the validator runs `tools/universal_readme_check.py` and lists, as a warning, what differs from the universal layout of the README.
- **Project status is the second section of the README,** right after At a glance, in the eight languages.

## [0.1.8] - The last English-only messages are translated and the wheel is held by a test

### Firmware and protocol

- The README lists URTC-GATEWAY, the new gateway in front of the CAN bus, among the related projects.

### Programs and windows

- The description of the desktop window, the project tree and the statement about the tests of the window are current in the eight READMEs, and the Portuguese tree and examples are in Portuguese; the command reference describes the `package` and `security` commands, and URTC-COMMON is listed among the related projects.
- **The last English-only messages are translated:** the results of restoring a kept installation (nothing to restore, an unusable backup, the installation that could not be set aside, a restore that failed and could not put the old one back, the restore that worked with and without the installation it replaced) and the errors of the GitHub client (the hourly rate limit with the time it resets, an HTTP error, a manifest that cannot be read or is not valid, a repository list that cannot be made or has an unexpected answer) are messages with a code and parameters, like the checkpoints already were, and the window says them in its language (14 texts in the eight languages). The command line and the logs still print the English text, and an exception that carries such a message keeps its code (`exc.args[0]`).
- The tests that start a Qt process keep the module path they were given (`PYTHONPATH` is added to the paths of the repository), so they run where PySide6 is installed in another folder.
- **A guide of the window with pictures, in the eight languages:** `docs/WINDOW_GUIDE.md` goes through the window, the Help window, the update window and the Packages window, and shows each of them in every language of the program (32 pictures in `docs/screenshots/`). `tools/capture_screens.py` takes them from the real Qt Quick window, loaded without a screen, in an empty workspace with the box "Offline" ticked, with the settings in a folder that is thrown away and no network (`--language NAME` for one language, `--all-languages` for all). The eight READMEs show the first picture and link to the guide; `tests/test_window_guide.py` checks the pictures, the links and the READMEs. The update window of `Main.qml` got an `objectName` so the script can open it.
- **A Packages window:** the "Packages" button lists the signed packages of the flasher, the tester and this updater, one row each with the installed version and the versions kept; each row checks its release only when the button is pressed, downloads and verifies the package (size, SHA-256, signature of the key of the releases), asks before it installs and goes back to the previous version after a second question. It is the window of what `--cli package` does, with the same rules and the same security options, and nothing is installed while a project is being installed or updated; every text is in the eight languages.
- **A Help window:** a five-step guide (the list, install or update, going back, packages, security and updates) in the eight languages, shared with the flasher and the tester through URTC-COMMON.
- **The window no longer fills the console with `Cannot read property ... of null` when it closes:** the windows are deleted before the object their bindings read, instead of the other way round.

### Tests, builds and checks

- **The wheel is held by a test:** `tests/test_wheel.py` builds the wheel from a copy of the sources and checks that it carries the `urtc-updater` command, the window files and the assets, declares the Python it needs, and that a program installed from it takes the current folder, not the Python installation, for a workspace.
- **The texts of the window are generated** from the catalog of texts of URTC-COMMON (`tools/i18n_generate.py sync`), with a lock (`urtc_i18n.lock.json`) and a test of this program (`tests/test_i18n_generated.py`) that fails when a generated file is edited by hand; a text the glossary names is a reference to it. `i18n.py` keeps the language logic and reads the table from `translations_data.py`; every text is the same as before.
- **The dev dependencies are closed with hashes:** `requirements-dev.lock` pins every package the tests and the window need (Qt included, held at the version the tests run with), with the hash of every file; the CI and `build.sh` / `build.bat` install it with `--require-hashes`, then the project itself without dependencies.
- **A static check on every push:** `ruff.toml` (unused names, exception chaining and syntax errors, the rules the flasher and the tester already ran) and a step of the CI that runs `ruff check .` with a pinned ruff; it found an unused import in a test, now removed.
- **Install a program from the signed package of its release (`package`):** `urtc-updater --cli package list|check|install|rollback` installs the flasher, the tester or this updater from the `.zip` / `.tar.gz` of a release instead of a clone and a build, with the rules of URTC-COMMON's `self_update` (copied to `urtc_pkg/`): only a strictly higher version, only GitHub's download hosts, the announced size and SHA-256, the Ed25519 signature of the key of the releases pinned in the program, a safe extraction, two releases kept and a rollback. It asks before installing (`--yes` for scripts); `install --file` works from a package on disk with its `.sha256` and `.sig`, with no network. The window gets a "Check for updates" button for the updater itself (dialog and texts shared with the flasher and the tester); the automatic check at start (`update_auto_check`) is off by default and the confirmation (`update_require_confirmation`) on.
- The CI holds the tests to a coverage floor of 61 percent (measured 69, with the Qt window code included; `pytest-cov` is in the `dev` extra).
- **The build scripts work when the python first on the PATH makes a venv with no activate script** (for example the python that ESP-IDF installs): the venv is made with the `py` launcher when there is one and its own python, or its folder first on the PATH, is used instead of the activate script.

### Documentation

- **The README files carry sections written once in URTC-COMMON:** "How it updates" and "Compatibility", in the eight languages, between marker comments before the license heading (`tools/readme_sections.py` of URTC-COMMON writes and checks them; the rest of each README is hand-written as before).

### Other changes

- **A missing letter in the German title of the activity log** (`AKTIVITAETSPROTOKOLL`, as in the flasher and the tester) and the texts it shares with the other programs are checked against the shared glossary of URTC-COMMON by its nightly comparison.

## [0.1.7] - Security options you can turn on and off, and a settings file that fails on the safe side

- `tools/ci_validate.py` fails when a versioned file has the name of a Windows path (a colon, the character a file system uses to store one, or a first folder named like a drive or a user profile): a path handed to WSL without translation once put build output inside a repository. The same check (`tools/_tracked_names.py`) is in every URTC repository.
- The dashboard notice is sent only after the CI of the push finished green (`workflow_run`).
- **Security options you can turn on and off from the tool** (`security.py`): *require signed commits* (it already existed in the settings file and the environment) and the new *ask before the build check*. Both are off by default and change nothing until turned on. Each can be set in the window (a Security button opens a dialog with both switches), with the `urtc-updater --cli security` command, in the settings file (`signature_policy`, `confirm_before_build`), with the environment (`URTC_UPDATER_REQUIRE_SIGNED`, `URTC_UPDATER_CONFIRM_BUILD`) and with flags on `install` and `update` (`--require-signed` / `--no-require-signed`, `--confirm-build` / `--no-confirm-build`, `--yes`).
- **Ask before the build check**: once the candidate is fetched and validated, the project, commit, author, signature and the build or tool scripts it changed are shown (a window dialog, or a question in the terminal) and nothing is run until the answer is yes. With no window and no terminal nothing is run, and `--yes` (or `URTC_UPDATER_ASSUME_YES=1`) answers for scripts. A first install asks before its build check too.
- **A warning when protection is lowered**: a run whose flag or environment variable turns off a protection that the saved settings have on says so, and the window and the `security` command ask for confirmation before saving a lower level.
- **A settings file that cannot be read now fails on the safe side**: it counts as "signatures required" until it is fixed or removed (the environment variable can still say otherwise); saving the language no longer overwrites it, and saving the security options keeps the damaged file next to the new one as `.corrupt`. The texts of the dialogs and messages are in the eight languages.
- **The build check runs with the interpreter of the updater**: it is given `URTC_PYTHON` (unless already set), and the `build-test` scripts of the URTC projects use it instead of whichever `python3` or `py -3` the system finds first.
- **The version reader no longer has a magic threshold**: the `build` field of a header is part of the version when it is not 0 or when the project's versions have four parts; before, it was ignored below 0.8.0, a number that belonged to another ecosystem.
- The banner follows the animated style of the ecosystem banners, with the name, the kind and the technologies of the project.
- **The manifest parser accepts the optional `evidence` field** (`host-test`, `simulator`, `bench` or `field`) that the URTC repositories now declare next to their maturity; without it every URTC project was rejected as an invalid manifest and disappeared from the dashboard and from the list of projects to update.

## [0.1.6] - Preview an update and restore the previous version from the window

- The window can preview an update (candidate commit, author, signature state and the build or tool scripts it would change) without touching the checkout, and can put the newest kept previous installation back after a confirmation. Both texts exist in the eight languages, and the README of each language says so.
- The manifest declares how far the project has been shown to work (`evidence`) and `tools/ci_validate.py` checks it.

## [0.1.5] - Manifest schema 1.1, an unavailable validation is refused unless accepted, and an explicit bump

- Manifest schema 1.1: `urtc.project.json` may declare `components[]` (name, kind app or bootloader, version, target and an optional source file and prefix) and the deployment target `mcu`. A 1.0 manifest keeps validating unchanged, and a 1.0 manifest that uses components or `mcu` is refused. The parsed components reach the project entries and `status --json` (`deployment_target` and `components`).
- An install or update whose build check says it cannot validate here (a missing tool) is refused by default. The new `--accept-unavailable-validation` flag of `install` and `update` is the explicit, per-run opt-in (the setting and `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1` still work).
- Building no longer changes the version: `build.sh` and `build.bat` only read it, and raising it is the explicit `python bump.py` step.
- Every licence statement and source header says GPL-3.0-or-later.

## [0.1.4] - A build-test that cannot validate is not a failed one, and the tree a build-test touched is put back

- A build-test that exits with code 75 is reported as validation unavailable (a tool it needs is missing) and not as a failed build. The install or update is refused unless the person accepts it with validation_unavailable set to accept in the settings (or URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1); the steps say so, in the eight languages.
- When the build-test changes a file that git tracks, the file is put back to the committed content before the staging clone is promoted and right after a fresh install, so the checkout stays clean and the next update is not refused for local changes; the steps name the files.
- Repository discovery no longer asks forks or archived repositories for a manifest.
- tools/build_test.py runs the tests of this repository after the syntax check when pytest is installed, and says so when it is not.
- CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, LICENSE.md, the issue forms and the pull request template were added, and tools/ci_validate.py requires the four documents.
- The status example of the README uses the real stack name and maturity; the manifest notes no longer quote a test count; bump_manifest_version.py prints URTC instead of the name of another ecosystem.
- The README (all eight languages) describes the exit code 75 and the restored files, and lists the documents above.
- The CI workflow no longer carries steps for stacks this repository does not have.
- The CI runs the tests with PySide6 installed and the offscreen platform, on Linux and on Windows, so the tests of the Qt bridge run there instead of being skipped.
- The license is GPL-3.0-or-later everywhere: LICENSE.md, source headers, script banners, About texts and README (eight languages).

## [0.1.3] - URTC-DOCS in the list of related projects

- The Related Projects section of the README, in all 8 languages, lists URTC-DOCS, the documentation and cross-repository tooling hub of the ecosystem.
- The sentence about how many repositories are discovered no longer gives a number that would go stale; the status table is the source of the count.
- Build version synchronized with `urtc.project.json` and the repository-native version source.

## [0.1.2] - An unsigned commit is warned about, not refused, unless the signature policy asks for it

- The default signature policy is warn: a revision with no valid signature (git verify-commit) is installed or updated anyway, and the steps of the window and of the command line say in the chosen language that it is not signed.
- The policy require stays available with signature_policy require in the settings, the older require_signed_commits or URTC_UPDATER_REQUIRE_SIGNED=1: the candidate must be verified before its manifest is read or anything is built.
- Tests: the default mode, both ways of requiring, the warning in a fresh install and in an update, the refusal under require, and the message in all eight languages.

## [0.1.1] - Messages in every language, commit comparison, backup retention and station commands

- The checkpoints and failures of an install or update are message codes plus parameters, shown in the language of the window in all 8 languages (Portugal Portuguese for pt); the command line keeps printing the English text.
- A project whose version equals GitHub but whose remote has new commits is now detected with one git ls-remote per project: status shows NEW COMMITS, the window offers Update, and an update at the same version is accepted (only a lower version is refused).
- Previous installations are kept as name.backup-xxxxxxxx; after a successful update the newest 2 per project are kept (the backups_to_keep setting changes the number) and older ones are removed.
- New commands: clean-backups (removes old backups and the hidden staging folders a dead run left, with --keep and --dry-run), restore-backup (puts a kept installation back and keeps the one it replaces), update --preview (shows the candidate commit, author, signature state and the build or tool files it changes, without touching the checkout), check (notify only, exit code 10 when something can be updated, optional desktop notification) and evidence (verifies the evidence hash chain and exports it as JSON).
- Every evidence line is chained to the previous one by hash, so an edited, removed or reordered line is detected.
- Station profiles in the settings (--profile on the command line, followed by the window) limit the projects of a machine and whether batch actions are allowed.
- The repository listing is cached with its ETag and answered with 304 when unchanged, which does not use the hourly request quota.
- An exception that escapes an install or update no longer leaves its hidden staging folder behind, and the window log files are rotated (the newest 20 are kept).
- Removed the unused ecosystem catalog parser and two unreachable ecosystem checks; the default deployment target of a project entry is user-pc; an unused import was removed from the legacy window.
- README and CLI reference corrected: backup folder names, the real build-test contract, the status table, maturity, the test list, empty image references, and the new commands in all 8 languages.

## [0.1.0] - Workspace safety: one instance at a time, clean discovery, safer cleanup

- Only one install or update can run in a workspace at a time: an operating-system lock is held for the whole operation, so a window and a command line run (or two windows) can no longer fetch and promote the same checkout together; the second one is told to wait.
- The fetched commit is resolved to a single SHA once, and the signature check, manifest read and merge all use that SHA instead of the shared FETCH_HEAD name.
- Kept previous installations (name.backup-xxxxxxxx) and the updater hidden staging folders are no longer reported as invalid projects on every scan.
- A refused or failed fresh clone is now removed even when git left read-only files in it (Windows), so nothing is left behind in the workspace.
- Local data carried over to a new version now skips build folders at any depth (tools/node_modules, app/build, src/__pycache__) and keeps symlinks as links instead of copying what they point to.
- The program running right now is never replaced by an update (it is skipped in Update all and refused with a clear message).
- Every evidence line now records the time (UTC), updater version, host and user.
- Saved preferences are written to a temporary file and swapped in, so a cut during the write cannot truncate them.
- A very long Retry-After from GitHub is no longer waited out; the request fails with the answer instead of freezing the window.
- Raw URLs follow the repository real default branch instead of a fixed main.
- The default workspace is never inside a Python installation when the updater is installed as a package.
- Starting without any GUI available now exits with a non-zero code; run.sh works from a bare checkout (src on the path, python3 fallback); pytest finds the sources without PYTHONPATH.

## [0.0.9] - An installation that fails never leaves the window stuck, and Portuguese

- **Nothing escapes an install:**  returns a result with its message for any failure (a command that cannot be started, the installation folder open in another program, an unexpected error) instead of an exception that left the window with its buttons disabled for ever.
- **Worker threads are logged:** an exception in a thread now reaches the log when the window runs without a console.
- **Read-only files do not block clean-up:** removing a staging clone makes read-only files writable first.
- **Portuguese (Portugal):** a language of the interface, and README_por.md, which every README links to from its language bar.

## [0.0.8] - Copy-log icon button

- **Copy-log button:** the activity log has a small copy icon (two sheets) that puts the whole log on the clipboard and flashes green when done.

## [0.0.7] - Optional signed-commits policy

- **`signature.py` (new):** with `"require_signed_commits": true` in the
  settings file (or `URTC_UPDATER_REQUIRE_SIGNED=1`), the candidate revision
  of an install (`HEAD` of the staging clone) or an update (`FETCH_HEAD`)
  must pass `git verify-commit` - GPG keyring, or SSH with
  `allowed_signers_file` / `URTC_UPDATER_ALLOWED_SIGNERS` - before its
  manifest is read or anything in it is built. A refused install leaves no
  directory behind; a refused update leaves the installed checkout as it
  was. Off by default.
- **Tests:** `tests/test_signature.py` (6 tests, real repositories and a
  real SSH signing key); `tests/conftest.py` runs every test with the policy
  off and without the machine's global git config.
- READMEs in all 7 languages describe the policy.

## [0.0.6] - A failed write of the evidence is said

- **The evidence file:** when the line of evidence of an install or update attempt cannot be written, the log now says so (it used to return nothing without a word).

## [0.0.5] - The logo shows when the updater is opened from Electro Hobby 3D Updater

- **Real bug, reported by the user:** the window icon and the logo at the top of the window were looked for next to the project's folder, which does not exist when the updater is installed as a package (as Electro Hobby 3D Updater installs it) - so they never showed when opened from there. The icons now live inside the package (`assets/`) and are shipped with it.

## [0.0.4] - The window icon shows reliably

- **Window and taskbar icon:** the `.ico` now has seven sizes (16 to 256, made from the SVG) instead of a single large one, the window is given its icon itself, and on Windows the process gets its own identity so the taskbar shows it and not the one of Python. The `.ico` is now shipped too (it was missing).

## [0.0.3]

- Build version synchronized with `urtc.project.json` and the repository-native version source.

## [0.0.2] - The GUI still called itself HYDRA-UMC Updater

- **Real bug, reported by the user directly comparing this GUI against its two siblings:** the About dialog's title and description (all 7 languages), the Qt Quick window's own OS-level title and taskbar/Alt-Tab display name, the QML splash's big brand text and a label under its icon, and the legacy Tkinter shell's own header label all still literally read "HYDRA-UMC" - never adapted when this project was copied from HYDRA-UMC-UPDATER. Every one of those now says URTC (the QML brand text now follows URTC's own "UR" + cyan "TC" mark, not HYDRA-UMC's three-color one). Three module docstrings that likewise claimed to be about "a HYDRA-UMC manifest"/"HYDRA-UMC repositories" were corrected the same way - they describe this project's own code, not HYDRA-UMC's.
- The six non-English READMEs' own `--cli status`/`update` example output was still HYDRA-UMC's from before this project existed (`/home/pi/HYDRA-UMC`, `HYDRA-UMC-SERVER`, 59/59 projects); only the English one had been updated to a real URTC-shaped example. Synced across all seven now.

## [0.0.1] - First release: URTC gets its own updater

- **New project.** URTC-UPDATER detects, installs and updates the URTC ecosystem's own repositories (`urtc.project.json`, `ecosystem: "URTC"`) on the machine it runs on - the same manifest discovery, atomic-by-verification staging-clone install/update, evidence log and CLI/GUI design already proven by HYDRA-UMC-UPDATER and ARMOR-UPDATER, adapted to URTC's own six-repository scope instead of duplicating either.
- Every URTC repository is public, so remote discovery works with no `GITHUB_TOKEN` at all; an optional one only raises the 60-requests-an-hour unauthenticated ceiling.
- Two real bugs found while adapting the shared codebase rather than copying it blindly: the desktop GUI's default deploy-target filter defaulted to `"cm5"` on Linux, a deployment target no real URTC repository ever declares (every one of them is `"user-pc"`) - the GUI would have opened to an empty table. Fixed in both the Tkinter and Qt Quick shells to default to showing everything.
- Not yet run against a real URTC repository end to end.
