# =============================================================================
# URTC-UPDATER - tests/test_registry.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Tests for generic runtime entries; no fixed ecosystem project list."""

import dataclasses
import json

from urtc_updater.project_manifest import parse_manifest
from urtc_updater.registry import entry_from_manifest, github_native_version_url, github_raw_url


def test_runtime_entry_uses_repository_owned_native_version_data():
    manifest = parse_manifest(
        r'''{
          "schema_version": "1.0", "ecosystem": "URTC",
          "name": "HYDRA-UMC-EXAMPLE", "version": "1.2.3",
          "role": "service", "stack": "python", "technologies": ["Python"],
          "deployment_target": "cm5", "maturity": "functional",
          "family": "Examples", "parent": null,
          "native_version": {"file": "pyproject.toml", "pattern": "version = \"(\\d+)\\.(\\d+)\\.(\\d+)\""},
          "build": "python -m example", "notes": "Example."
        }''',
        expected_name="HYDRA-UMC-EXAMPLE",
    )
    entry = entry_from_manifest(manifest)

    assert entry.version_file == "pyproject.toml"
    assert entry.pattern == 'version = "(\\d+)\\.(\\d+)\\.(\\d+)"'
    assert github_raw_url(entry).endswith("/HYDRA-UMC-EXAMPLE/main/urtc.project.json")
    assert github_native_version_url(entry).endswith("/HYDRA-UMC-EXAMPLE/main/pyproject.toml")


def test_min_common_of_the_manifest_reaches_the_runtime_entry_and_changes_nothing_else():
    def entry_for(**extra):
        data = {
            "schema_version": "1.0", "ecosystem": "URTC", "name": "URTC-EXAMPLE", "version": "1.2.3",
            "role": "service", "stack": "python", "technologies": ["Python"],
            "deployment_target": "user-pc", "maturity": "functional", "family": "Examples", "parent": None,
            "native_version": {"file": "pyproject.toml", "pattern": r'version = "(\d+)\.(\d+)\.(\d+)"'},
            "build": "python -m example", "notes": "Example.", **extra,
        }
        return entry_from_manifest(parse_manifest(json.dumps(data), expected_name="URTC-EXAMPLE"))

    without = entry_for()
    assert without.min_common is None
    declared = entry_for(min_common="0.2.2")
    assert declared.min_common == "0.2.2"
    assert entry_for(min_common="soon").min_common is None
    assert declared == dataclasses.replace(without, min_common="0.2.2")
