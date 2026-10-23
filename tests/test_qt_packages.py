# =============================================================================
# URTC-UPDATER - tests/test_qt_packages.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The Packages window: the model of its rows (check, download and verify, install, go back, the refusals) and the window itself loaded offscreen.
The packages are built and signed in the test with a throw-away key pinned in place of the key of the releases; nothing goes over the network."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from test_package import KEY_ID, PUBLIC, environment, fake_github, make_package  # noqa: E402,F401  (the fixture is the one of the package tests)

from urtc_updater import i18n, package, packages_qt, qt_gui  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def model():
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])
    return packages_qt.PackagesModel(lambda: "en")


def synchronous(entry, fetch):
    entry.controller.background = False
    entry.controller.service.fetch = fetch
    return entry


def test_the_list_has_the_programs_of_the_command_line_and_one_row_each(model):
    assert list(model.apps) == list(package.KNOWN_APPS)
    assert [row.appName for row in model.entries] == list(package.KNOWN_APPS)
    assert model.entry("urtc-tester") is model.entry("urtc-tester")
    with pytest.raises(ValueError):
        model.entry("urtc-unknown")


def test_a_row_starts_idle_with_the_conservative_options_and_says_it_is_not_installed(model):
    row = model.entry("urtc-flasher")
    assert row.state == "idle" and not row.autoCheck and row.requireConfirmation
    assert row.installedText == "not installed" and row.keptText == "-"
    assert row.folder == str(package.root_of("urtc-flasher"))
    assert not row.canDownload and not row.canInstall and not row.canRollBack and row.canCheck


def test_nothing_goes_over_the_network_until_a_button_is_pressed(model):
    calls = []
    row = synchronous(model.entry("urtc-flasher"), lambda url: calls.append(url))
    row.startupCheck()
    assert calls == [] and row.state == "idle"


def test_check_download_install_and_go_back_one_row_at_a_time(tmp_path, model):
    first = make_package(tmp_path / "rel1", version="0.5.0")
    row = synchronous(model.entry("urtc-flasher"), fake_github(first))
    row.check()
    assert row.state == "available" and row.version == "0.5.0" and "Notes line" in row.notes and row.canDownload
    row.download()
    assert row.state == "ready" and row.canInstall
    assert package.installed_version("urtc-flasher") == "0.0.0"  # a downloaded package is not an installed one
    row.install()
    assert row.state == "installed" and row.installedText == "0.5.0" and row.keptText == "0.5.0"
    assert not row.canRollBack
    other = model.entry("urtc-tester")
    assert other.installedText == "not installed"  # the other rows are untouched

    second = make_package(tmp_path / "rel2", version="0.6.0")
    row.controller.service.fetch = fake_github(second, version="0.6.0")
    row.check()
    assert row.state == "available" and row.version == "0.6.0"  # the check compares with the version now in use
    row.download()
    row.install()
    assert row.installedText == "0.6.0" and row.canRollBack
    row.rollBack()
    assert row.state == "rolled_back" and row.installedText == "0.5.0"
    row.check()
    assert row.state == "available" and row.version == "0.6.0"  # after going back, the newer one is offered again


def test_an_install_is_refused_while_a_project_is_being_installed(tmp_path):
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])
    busy = {"on": True}
    model = packages_qt.PackagesModel(lambda: "en", busy=lambda: "install/update" if busy["on"] else None)
    row = synchronous(model.entry("urtc-flasher"), fake_github(make_package(tmp_path / "rel")))
    row.check()
    row.download()
    row.install()
    assert row.isError and row.installedText == "not installed"
    assert "busy" in row.statusText.lower() or row.statusText


def test_a_package_with_a_wrong_signature_is_refused_and_deleted(tmp_path, model):
    built = make_package(tmp_path / "rel")
    signature = built.with_name(built.name + ".sig")
    signature.write_text("00" * 64 + "\n")
    row = synchronous(model.entry("urtc-flasher"), fake_github(built))
    row.check()
    row.download()
    assert row.state == "error" and row.isError and not row.canInstall
    assert not list((package.root_of("urtc-flasher") / "downloads").glob("*.zip"))
    assert package.installed_version("urtc-flasher") == "0.0.0"


def test_a_failed_request_is_a_message_in_the_row_and_changes_nothing(model):
    def broken(url):
        raise OSError("no network")

    row = synchronous(model.entry("urtc-tester"), broken)
    row.check()
    assert row.state == "error" and row.isError and row.statusText
    assert row.canCheck and package.installed_version("urtc-tester") == "0.0.0"


def test_the_texts_follow_the_language_of_the_window_and_use_the_words_of_the_update_window():
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])
    language = ["pt"]
    model = packages_qt.PackagesModel(lambda: language[0])
    assert model.t("pkg_title") == "Pacotes" and model.t("UPD_BTN_CLOSE") == "Fechar"
    assert model.entry("urtc-flasher").installedText == "não instalado"
    language[0] = "de"
    model.languageChanged()
    assert model.t("pkg_title") == "Pakete" and model.t("UPD_BTN_CLOSE") == "Schließen"
    assert model.entry("urtc-flasher").installedText == "nicht installiert"
    language[0] = "xx"
    assert model.t("pkg_title") == "Packages"


def test_every_language_says_every_text_of_the_window():
    keys = [key for key in i18n.TRANSLATIONS["en"] if key.startswith("pkg_")]
    assert len(keys) == 8
    for code in i18n.TRANSLATIONS:
        for key in keys:
            assert i18n.TRANSLATIONS[code][key].strip(), (code, key)
        assert "{" not in "".join(i18n.TRANSLATIONS[code][key] for key in keys), code
    assert i18n.TRANSLATIONS["pt"]["pkg_menu"] == "Pacotes" and "arquivo" not in " ".join(i18n.TRANSLATIONS["pt"][key] for key in keys)


def test_the_buttons_are_in_the_window_and_the_bridge_offers_the_models():
    qml_dir = Path(qt_gui.__file__).with_name("qml")
    main = (qml_dir / "Main.qml").read_text(encoding="utf-8")
    assert "PackagesDialog {" in main and "packagesDialog.open()" in main and "backend.packages" in main
    assert "HelpDialog {" in main and "helpDialog.open()" in main and "backend.help" in main
    for name in ("PackagesDialog.qml", "HelpDialog.qml", "UpdateDialog.qml"):
        assert (qml_dir / name).is_file()


def test_the_window_opens_the_packages_and_the_help_in_every_language():
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run([sys.executable, str(ROOT / "tests" / "qt_packages_check.py")], capture_output=True, text=True, timeout=180, env=env, check=False)
    assert result.returncode == 0 and "QT_PACKAGES=PASS" in result.stdout, result.stdout + result.stderr
