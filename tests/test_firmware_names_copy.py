# =============================================================================
# URTC-UPDATER - tests/test_firmware_names_copy.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The copy of the firmware file names: what is an image, what travels with it, and that the signature record (.imgsig) is one of those files."""
from __future__ import annotations

import pytest

from urtc_updater.urtc_pkg import firmware_names as names


def test_the_signature_record_is_one_of_the_files_that_travel_with_an_image():
    assert ".imgsig" in names.SIDECAR_SUFFIXES
    assert len(set(names.SIDECAR_SUFFIXES)) == len(names.SIDECAR_SUFFIXES)
    assert all(suffix.startswith(".") for suffix in names.SIDECAR_SUFFIXES)


@pytest.mark.parametrize("suffix", names.SIDECAR_SUFFIXES)
def test_a_file_that_travels_with_an_image_is_never_taken_for_an_image(suffix):
    assert names.IMAGE_NAME.match("URTC_MAIN_FIRMWARE_v0.4.1.bin" + suffix) is None


@pytest.mark.parametrize("board", names.BOARDS)
@pytest.mark.parametrize("kind", names.KINDS)
@pytest.mark.parametrize("version", ["1.2.3", "0.8.0.1", "10.20.30.40"])
def test_every_board_kind_and_version_shape_is_an_image(board, kind, version):
    found = names.IMAGE_NAME.match(f"URTC_{board}_{kind}_v{version}.bin")
    assert found and found.group(1) == board and found.group(2) == kind and found.group(3) == version


@pytest.mark.parametrize("name", [
    "URTC_MAIN_FIRMWARE_v1.2.3.bin ", " URTC_MAIN_FIRMWARE_v1.2.3.bin", "URTC_MAIN_FIRMWARE_1.2.3.bin", "URTC_MAIN_APP_v1.2.3.bin",
    "URTC_TOP_FIRMWARE_v1.2.3.bin", "URTC_MAIN_FIRMWARE_v1..3.bin", "URTC_MAIN_FIRMWARE_v1.bin", "URTC_MAIN_FIRMWARE_v1.2.3.hex", "",
])
def test_names_that_are_not_images_are_refused(name):
    assert names.IMAGE_NAME.match(name) is None


def test_the_names_are_read_whatever_the_case():
    assert names.IMAGE_NAME.match("urtc_slave_bootloader_v0.2.5.BIN")
