# Changelog: URTC-UPDATER 🛠️

All notable changes to this project will be documented in this file. The
version number follows this ecosystem's "odometer" scheme: PATCH +1 on
every real build, rolling into MINOR past 9 (`0.0.9` -> `0.1.0`); MAJOR is
bumped manually only. See `bump_version.py`.

## [0.1.0] - Workspace safety: one instance at a time, clean discovery, safer cleanup

Only one install or update can run in a workspace at a time: an operating-system lock is held for the whole operation, so a window and a command line run (or two windows) can no longer fetch and promote the same checkout together; the second one is told to wait.
The fetched commit is resolved to a single SHA once, and the signature check, manifest read and merge all use that SHA instead of the shared FETCH_HEAD name.
Kept previous installations (name.backup-xxxxxxxx) and the updater hidden staging folders are no longer reported as invalid projects on every scan.
A refused or failed fresh clone is now removed even when git left read-only files in it (Windows), so nothing is left behind in the workspace.
Local data carried over to a new version now skips build folders at any depth (tools/node_modules, app/build, src/__pycache__) and keeps symlinks as links instead of copying what they point to.
The program running right now is never replaced by an update (it is skipped in Update all and refused with a clear message).
Every evidence line now records the time (UTC), updater version, host and user.
Saved preferences are written to a temporary file and swapped in, so a cut during the write cannot truncate them.
A very long Retry-After from GitHub is no longer waited out; the request fails with the answer instead of freezing the window.
Raw URLs follow the repository real default branch instead of a fixed main.
The default workspace is never inside a Python installation when the updater is installed as a package.
Starting without any GUI available now exits with a non-zero code; run.sh works from a bare checkout (src on the path, python3 fallback); pytest finds the sources without PYTHONPATH.

## [0.0.9] - An installation that fails never leaves the window stuck, and Portuguese

**Nothing escapes an install:**  returns a result with its message for any failure (a command that cannot be started, the installation folder open in another program, an unexpected error) instead of an exception that left the window with its buttons disabled for ever.
**Worker threads are logged:** an exception in a thread now reaches the log when the window runs without a console.
**Read-only files do not block clean-up:** removing a staging clone makes read-only files writable first.
**Portuguese (Portugal):** a language of the interface, and README_por.md, which every README links to from its language bar.

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
