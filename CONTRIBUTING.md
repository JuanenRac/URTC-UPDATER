# Contributing to URTC-UPDATER 🛠️

This tool installs and updates the other repositories of the URTC ecosystem on a user's PC, and it runs their build checks. A change here therefore touches the machine of whoever uses it: the most useful contributions keep every action explicit, reversible and verified.

## Technology Stack
- **Language**: Python 3.10+, with PySide6 / Qt Quick for the window; the command line uses the standard library only.
- **Tests**: pytest; no network and no board are needed.

## Guidelines
1. **Nothing happens by itself.** Installing, updating and restoring are explicit actions; checking is read-only. Do not add a background update.
2. **A live installation is only touched after its replacement has been verified** in a staging clone, and the previous one is kept as a backup. Keep that order.
3. **Messages are codes plus parameters**, worded in `i18n.py` in the eight languages (English, Spanish, German, French, Italian, Japanese, Chinese and European Portuguese). A test refuses a missing one.
4. **No secrets, no private paths.** Evidence logs and messages must not carry tokens or credentials.
5. **Tests.** `python -m pytest tests -q` (with `PYTHONPATH=src`) must pass, and a change needs a test that fails without it. Use `build-test.sh` / `build-test.bat` to check without changing the version; `build.sh` / `build.bat` raise it.
6. **Documentation.** A change to the behaviour is written in the README (eight languages), in `docs/` and in `CHANGELOG.md` in the same commit.
