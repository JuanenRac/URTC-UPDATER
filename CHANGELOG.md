# Changelog: URTC-UPDATER 🛠️

All notable changes to this project will be documented in this file. The
version number follows this ecosystem's "odometer" scheme: PATCH +1 on
every real build, rolling into MINOR past 9 (`0.0.9` -> `0.1.0`); MAJOR is
bumped manually only. See `bump_version.py`.

## [0.0.1] - First release: URTC gets its own updater

- **New project.** URTC-UPDATER detects, installs and updates the URTC ecosystem's own repositories (`urtc.project.json`, `ecosystem: "URTC"`) on the machine it runs on - the same manifest discovery, atomic-by-verification staging-clone install/update, evidence log and CLI/GUI design already proven by HYDRA-UMC-UPDATER and ARMOR-UPDATER, adapted to URTC's own six-repository scope instead of duplicating either.
- Every URTC repository is public, so remote discovery works with no `GITHUB_TOKEN` at all; an optional one only raises the 60-requests-an-hour unauthenticated ceiling.
- Two real bugs found while adapting the shared codebase rather than copying it blindly: the desktop GUI's default deploy-target filter defaulted to `"cm5"` on Linux, a deployment target no real URTC repository ever declares (every one of them is `"user-pc"`) - the GUI would have opened to an empty table. Fixed in both the Tkinter and Qt Quick shells to default to showing everything.
- Not yet run against a real URTC repository end to end.
