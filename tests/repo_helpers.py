# =============================================================================
# URTC-UPDATER - tests/repo_helpers.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""A real bare repository, a seed clone to push from, and a workspace
checkout, shared by the tests that need a remote."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from urtc_updater.registry import ProjectEntry

NAME = "URTC-EXAMPLE"


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def entry() -> ProjectEntry:
    return ProjectEntry(NAME, "python", "pyproject.toml", r"(\d+)\.(\d+)\.(\d+)")


def manifest_text(version: str, name: str = NAME) -> str:
    return json.dumps({
        "schema_version": "1.0", "ecosystem": "URTC", "name": name, "version": version,
        "role": "service", "stack": "python", "technologies": ["Python"],
        "deployment_target": "user-pc", "maturity": "functional", "family": "Test", "parent": None,
        "native_version": {"file": "pyproject.toml", "pattern": "(\\d+)\\.(\\d+)\\.(\\d+)"},
        "build": "python -m compileall src", "notes": "Test manifest.",
    })


def write_build_test(path: Path) -> None:
    if os.name == "nt":
        (path / "build-test.bat").write_text("@echo off\r\necho built\r\nexit /b 0\r\n", encoding="utf-8")
    else:
        (path / "build-test.sh").write_text("#!/bin/sh\necho built\nexit 0\n", encoding="utf-8")


@dataclass
class Remote:
    bare: Path
    seed: Path
    workspace: Path

    @property
    def checkout(self) -> Path:
        return self.workspace / NAME

    def push(self, version: str, message: str, files: dict[str, str] | None = None) -> str:
        (self.seed / "urtc.project.json").write_text(manifest_text(version), encoding="utf-8")
        for relative, content in (files or {}).items():
            target = self.seed / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        git("add", "-A", cwd=self.seed)
        git("commit", "-m", message, cwd=self.seed)
        git("push", "origin", "HEAD", cwd=self.seed)
        return git("rev-parse", "HEAD", cwd=self.seed)


def make_remote(tmp_path: Path, version: str = "1.0.0", *, clone: bool = True) -> Remote:
    """A bare remote with one commit, and (by default) the workspace checkout cloned from it."""
    bare = tmp_path / "remote.git"
    git("init", "--bare", str(bare), cwd=tmp_path)
    seed = tmp_path / "seed"
    git("clone", str(bare), str(seed), cwd=tmp_path)
    git("config", "user.email", "contract@example.invalid", cwd=seed)
    git("config", "user.name", "Contract", cwd=seed)
    remote = Remote(bare, seed, tmp_path / "workspace")
    remote.workspace.mkdir()
    write_build_test(seed)
    remote.push(version, "first")
    if clone:
        git("clone", str(bare), str(remote.checkout), cwd=tmp_path)
        git("config", "user.email", "contract@example.invalid", cwd=remote.checkout)
        git("config", "user.name", "Contract", cwd=remote.checkout)
    return remote
