# =============================================================================
# URTC-UPDATER - tests/test_package.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Installing a program from the signed package of its release: list, check, install (from GitHub and from a file), rollback and the refusals."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from urtc_updater import main as main_module
from urtc_updater import package, settings
from urtc_updater.urtc_pkg import self_update as su
from urtc_updater.urtc_pkg import update_service as svc

_P, _Q = su._P, su._Q
SEED = bytes(range(32))


def _compress(point) -> bytes:
    x, y, z, _ = point
    zi = pow(z, _P - 2, _P)
    x, y = x * zi % _P, y * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _expand(seed: bytes):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def sign(message: bytes) -> bytes:
    a, prefix = _expand(SEED)
    public = _compress(su._mul(a, su.BASE_POINT))
    r = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _Q
    r_bytes = _compress(su._mul(r, su.BASE_POINT))
    k = int.from_bytes(hashlib.sha512(r_bytes + public + message).digest(), "little") % _Q
    return r_bytes + ((r + k * a) % _Q).to_bytes(32, "little")


PUBLIC = _compress(su._mul(_expand(SEED)[0], su.BASE_POINT))
KEY_ID = hashlib.sha256(PUBLIC).hexdigest()[:16]


class Stream(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture(autouse=True)
def environment(tmp_path, monkeypatch):
    monkeypatch.setenv(svc.ENV_ROOT, str(tmp_path / "apps"))
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(svc, "RELEASE_PUBLIC_KEY_HEX", PUBLIC.hex())
    monkeypatch.setattr(svc, "RELEASE_KEY_ID", KEY_ID)
    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr("platform.machine", lambda: "AMD64")


def make_package(directory: Path, app="urtc-flasher", version="0.5.0"):
    name = su.package_name(app, version, "windows-x64")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("app.exe", b"MZ")
        archive.writestr("app_info.json", json.dumps({"name": app, "version": version, "entry": "app.exe"}))
    data = buffer.getvalue()
    sha = hashlib.sha256(data).hexdigest()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(data)
    (directory / (name + ".sha256")).write_text(f"{sha}  {name}\n")
    (directory / (name + ".sig")).write_text(sign(su.package_message(app, version, "windows-x64", sha, len(data))).hex() + "\n")
    return directory / name


def fake_github(package_file: Path, app="urtc-flasher", version="0.5.0"):
    base = f"https://github.com/JuanenRac/{app.upper()}/releases/download/v{version}/"
    name = package_file.name
    files = {base + name: package_file.read_bytes(), base + name + ".sha256": (package_file.parent / (name + ".sha256")).read_bytes(),
             base + name + ".sig": (package_file.parent / (name + ".sig")).read_bytes()}
    listing = {"tag_name": "v" + version, "body": "Notes line\nkey_id: " + KEY_ID,
               "assets": [{"name": Path(u).name, "browser_download_url": u, "size": len(d)} for u, d in files.items()]}
    return lambda url: Stream(json.dumps(listing).encode() if url.endswith("/latest") else files[url])


def run(argv, fetch=None, ask=None):
    args = main_module.build_parser().parse_args(argv)
    return package.cmd_package(args, fetch, ask)


def test_the_command_is_part_of_the_command_line():
    args = main_module.build_parser().parse_args(["package", "install", "urtc-flasher", "--file", "x.zip", "--yes"])
    assert (args.command, args.package_command, args.app, args.file, args.yes) == ("package", "install", "urtc-flasher", "x.zip", True)
    with pytest.raises(SystemExit):
        main_module.build_parser().parse_args(["package", "install", "urtc-unknown"])


def test_list_shows_every_known_program_not_installed(capsys):
    assert run(["package", "list"]) == 0
    out = capsys.readouterr().out
    assert all(app in out for app in package.KNOWN_APPS) and out.count("not installed") == 3


def test_check_reports_a_newer_package_with_exit_code_10_and_the_latest_with_0(tmp_path, capsys):
    built = make_package(tmp_path / "rel")
    assert run(["package", "check", "urtc-flasher"], fake_github(built)) == 10
    assert "0.5.0 is available" in capsys.readouterr().out
    assert run(["package", "check", "urtc-flasher"], fake_github(make_package(tmp_path / "old", version="0.0.0"), version="0.0.0")) == 0


def test_install_from_github_asks_first_and_installs_only_after_a_yes(tmp_path, capsys):
    built = make_package(tmp_path / "rel")
    fetch = fake_github(built)
    assert run(["package", "install", "urtc-flasher"], fetch, ask=lambda prompt: "n") == 1
    assert package.installed_version("urtc-flasher") == "0.0.0" and "Not installed" in capsys.readouterr().out
    assert run(["package", "install", "urtc-flasher"], fetch, ask=lambda prompt: "y") == 0
    assert package.installed_version("urtc-flasher") == "0.5.0"
    out = capsys.readouterr().out
    assert "Notes line" in out and "installed" in out
    assert (package.root_of("urtc-flasher") / "releases" / "0.5.0" / "app.exe").is_file()


def test_install_with_yes_does_not_ask(tmp_path):
    built = make_package(tmp_path / "rel")
    assert run(["package", "install", "urtc-flasher", "--yes"], fake_github(built), ask=lambda prompt: pytest.fail("asked")) == 0


def test_install_from_a_file_needs_no_network_and_keeps_the_file(tmp_path):
    built = make_package(tmp_path / "rel")

    def no_network(url):
        raise AssertionError("network used")

    assert run(["package", "install", "urtc-flasher", "--file", str(built), "--yes"], no_network) == 0
    assert built.is_file() and package.installed_version("urtc-flasher") == "0.5.0"


def test_a_package_with_a_wrong_signature_or_without_one_is_refused(tmp_path, capsys):
    built = make_package(tmp_path / "rel")
    (built.parent / (built.name + ".sig")).write_text(bytes(64).hex() + "\n")
    assert run(["package", "install", "urtc-flasher", "--file", str(built), "--yes"]) == 1
    assert "bad_signature" in capsys.readouterr().err and package.installed_version("urtc-flasher") == "0.0.0"
    (built.parent / (built.name + ".sig")).unlink()
    assert run(["package", "install", "urtc-flasher", "--file", str(built), "--yes"]) == 1
    assert "incomplete_release" in capsys.readouterr().err


def test_a_package_of_another_program_is_refused(tmp_path, capsys):
    built = make_package(tmp_path / "rel", app="urtc-tester")
    assert run(["package", "install", "urtc-flasher", "--file", str(built), "--yes"]) == 1
    assert "app_info_mismatch" in capsys.readouterr().err


def test_rollback_goes_back_to_the_previous_release_and_says_when_there_is_none(tmp_path, capsys):
    run(["package", "install", "urtc-flasher", "--file", str(make_package(tmp_path / "a", version="0.5.0")), "--yes"])
    assert run(["package", "rollback", "urtc-flasher"]) == 1
    assert "nothing_to_roll_back" in capsys.readouterr().err
    run(["package", "install", "urtc-flasher", "--file", str(make_package(tmp_path / "b", version="0.5.1")), "--yes"])
    assert package.installed_version("urtc-flasher") == "0.5.1"
    assert run(["package", "rollback", "urtc-flasher"]) == 0
    assert package.installed_version("urtc-flasher") == "0.5.0"


def test_an_unknown_program_is_refused_by_the_service():
    with pytest.raises(su.UpdateError) as caught:
        package.make_service("urtc-other")
    assert caught.value.code == "bad_app"


def test_without_a_terminal_and_without_yes_nothing_is_installed(tmp_path, monkeypatch, capsys):
    built = make_package(tmp_path / "rel")
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert run(["package", "install", "urtc-flasher", "--file", str(built)]) == 1
    assert "confirm in a terminal" in capsys.readouterr().err and package.installed_version("urtc-flasher") == "0.0.0"


def test_a_failing_download_is_reported_not_raised(capsys):
    def offline(url):
        raise OSError("offline")

    assert run(["package", "check", "urtc-flasher"], offline) == 1
    assert "network_or_disk" in capsys.readouterr().err
