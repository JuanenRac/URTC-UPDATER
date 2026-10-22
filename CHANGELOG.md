# Changelog: URTC-UPDATER 🛠️

All notable changes to this project will be documented in this file. The
version number follows this ecosystem's "odometer" scheme: PATCH +1 on
every explicit bump, rolling into MINOR past 9 (`0.0.9` -> `0.1.0`); MAJOR is
bumped manually only. See `bump_version.py`.

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
