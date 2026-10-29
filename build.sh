#!/usr/bin/env bash
# PRETTY_RUN_BEGIN
if [ -z "${PRETTY_RUN:-}" ] && [ -f "$(dirname "$0")/tools/pretty_run.py" ] && command -v python3 >/dev/null 2>&1; then
    PRETTY_RUN=1 exec python3 "$(dirname "$0")/tools/pretty_run.py" --wrap --mode "${PRETTY_MODE:-build}" -- bash "$0" "$@"
fi
# PRETTY_RUN_END
# HYDRA_UMC_SCRIPT_STANDARD_HEADER_BEGIN
# *****************************************************************************
# Project   : URTC-UPDATER
# Script    : build.sh
# Purpose   : Incremental project build, verification and packaging workflow.
# Author    : JuanenRac (Electro Hobby 3D)
# Email     : electrohobby3d@gmail.com
# Copyright : (C) 2026 JuanenRac
# License   : GPL-3.0-or-later - see LICENSE
# *****************************************************************************
# HYDRA_UMC_SCRIPT_STANDARD_HEADER_END
# HYDRA_UMC_SCRIPT_STANDARD_BANNER_BEGIN
printf '\n*******************************************************************************\n'
printf '%s\n' "* URTC-UPDATER - build.sh"
printf '%s\n' "* Mode      : BUILD (no version change)"
printf '%s\n' "* Author    : JuanenRac (Electro Hobby 3D)"
printf '%s\n' "* Email     : electrohobby3d@gmail.com"
printf '%s\n' "* Copyright : (C) 2026 JuanenRac"
printf '%s\n' "* License   : GPL-3.0-or-later - see LICENSE"
printf '%s\n' "* ------------------------------------------------------------------------- *"
printf '%s\n' "* 1. Read the project version (compiling never changes it; run bump.py to raise it)."
printf '%s\n' "* 2. Run this project's declared build, verification and packaging commands."
printf '%s\n' "* 3. Report the result and keep an interactive terminal open."
printf '%s\n' "*******************************************************************************"
printf '\n'
# HYDRA_UMC_SCRIPT_STANDARD_BANNER_END
# Builds URTC-UPDATER: creates/activates a venv, installs the project
# (editable, with dev extras), verifies it compiles/imports cleanly, and
# runs the real test suite. Run this before run.sh.
#
# Usage:
#   chmod +x build.sh   (one-time)
#   ./build.sh
set -euo pipefail
cd "$(dirname "$0")"

# Keep the window open if this was double-clicked (e.g. from a file
# manager) instead of run from an already-open terminal - fires on
# success AND on a `set -e` early exit alike, but only prompts when
# stdin is actually a terminal (never in CI/piped/non-interactive runs).
trap '[ -t 0 ] && read -r -p "Press Enter to close..." _' EXIT
# HYDRA_UMC_SCRIPT_STANDARD_VERSION_STEP
printf '%s\n' "[1/5] Reading the project version (compiling never changes it; raise it with bump.py first)..."
# HYDRA_UMC_SCRIPT_STANDARD_VERSION_CAPTURE_BEFORE
HYDRA_UMC_VERSION_BEFORE="$(python3 -c 'import json, pathlib, sys; print(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["version"])' "$(dirname "$0")/urtc.project.json")"
# HYDRA_UMC_SCRIPT_STANDARD_VERSION_CAPTURE_AFTER
HYDRA_UMC_VERSION_AFTER="$(python3 -c 'import json, pathlib, sys; print(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["version"])' "$(dirname "$0")/urtc.project.json")"
printf '\n*******************************************************************************\n'
printf '%s\n' '* VERSION UNCHANGED BY THIS BUILD'
printf '%s\n' "* v${HYDRA_UMC_VERSION_BEFORE:-unknown} -> v${HYDRA_UMC_VERSION_AFTER:-unknown}"
printf '%s\n' '* Raise the version explicitly with bump.py before a release build.'
printf '%s\n' '*******************************************************************************'
printf '\n'
echo "      Done."
echo

echo "[2/5] Creating/activating virtual environment..."
# The venv is made with python3 (or python); the scripts below use the python of the venv directly instead of an activate script: the python that is first on the PATH
# may be a stripped one (for example the one of ESP-IDF) whose venv has none.
if [ ! -x .venv/bin/python ] && [ ! -x .venv/Scripts/python.exe ]; then
    (python3 -m venv .venv 2>/dev/null || python -m venv .venv)
fi
if [ -x .venv/bin/python ]; then
    VPY=".venv/bin/python"
elif [ -x .venv/Scripts/python.exe ]; then
    VPY=".venv/Scripts/python.exe"
else
    echo "ERROR: the venv has no python; delete the .venv folder and run this again." >&2
    exit 1
fi
echo "      Done."
echo

echo "[3/5] Installing project (editable) and the pinned dev and QML GUI dependencies into the venv..."
"$VPY" -m pip install --upgrade pip >/dev/null
"$VPY" -m pip install --require-hashes -r requirements-dev.lock
"$VPY" -m pip install --no-deps -e .
echo "      Done."
echo

echo "[4/5] Verifying the package compiles/imports without errors..."
"$VPY" -m py_compile src/urtc_updater/__init__.py src/urtc_updater/registry.py src/urtc_updater/version_parse.py src/urtc_updater/detect.py src/urtc_updater/github_client.py src/urtc_updater/install.py src/urtc_updater/main.py src/urtc_updater/gui.py src/urtc_updater/qt_gui.py src/urtc_updater/i18n.py
"$VPY" -c "import urtc_updater; print('import OK - version', urtc_updater.__version__)"
echo "      Done."
echo

echo "[5/5] Running the real test suite (pytest)..."
"$VPY" -m pytest tests/ -q
echo "      Done."
echo

echo " ==============================================================="
echo "  Build complete. Run ./run.sh to check the ecosystem's status."
echo " ==============================================================="
echo
