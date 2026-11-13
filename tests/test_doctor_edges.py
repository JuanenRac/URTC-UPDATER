# =============================================================================
# URTC-UPDATER - tests/test_doctor_edges.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The doctor at the edges of its inputs, with every system call replaced by a fake that answers on command: a program that is missing, that fails, that hangs or that answers
nothing; a module that is not installed; a port that is busy, silent or answers; the way the checks are drawn and the exit status."""
from __future__ import annotations

import importlib.metadata
import subprocess
from types import SimpleNamespace

import pytest

from urtc_updater import doctor

CONFIG = doctor.load_config()


def _run(stdout="", stderr="", returncode=0, error=None):
    def run(command, **_kwargs):
        if error is not None:
            raise error
        return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    return run


# ---- the programs ------------------------------------------------------------------------------------------------------------------------------

def test_a_program_that_is_not_found_has_no_version():
    assert doctor.program_version("git", CONFIG, which=lambda name: None, run=_run("x")) is None


def test_the_version_is_the_first_line_that_says_something_and_is_cut_at_120_characters():
    run = _run(stdout="\n   \ngit version 2.45.0\nsecond line\n")
    assert doctor.program_version("git", CONFIG, which=lambda name: "/usr/bin/git", run=run) == "git version 2.45.0"
    long = _run(stdout="x" * 500)
    assert len(doctor.program_version("git", CONFIG, which=lambda name: "/g", run=long)) == 120


def test_the_error_stream_counts_when_the_output_is_empty():
    run = _run(stdout="", stderr="gcc (Debian) 12\n")
    assert doctor.program_version("gcc", CONFIG, which=lambda name: "/g", run=run) == "gcc (Debian) 12"


@pytest.mark.parametrize("error", [OSError("no"), subprocess.TimeoutExpired("git", 1), subprocess.SubprocessError("x")])
def test_a_program_that_fails_to_run_or_hangs_is_found_with_an_unknown_version(error):
    assert doctor.program_version("git", CONFIG, which=lambda name: "/g", run=_run(error=error)) == "?"


def test_a_program_that_exits_with_an_error_has_an_unknown_version_and_an_empty_answer_too():
    assert doctor.program_version("git", CONFIG, which=lambda name: "/g", run=_run(stdout="boom", returncode=1)) == "?"
    assert doctor.program_version("git", CONFIG, which=lambda name: "/g", run=_run(stdout="", stderr="")) == "?"


# ---- the modules -------------------------------------------------------------------------------------------------------------------------------

def test_a_module_that_is_not_there_or_cannot_be_looked_up_has_no_version():
    assert doctor.module_version("nothing_here_at_all", "nothing", find_spec=lambda name: None) is None
    for error in (ImportError("x"), ValueError("y")):
        def find(name, error=error):
            raise error
        assert doctor.module_version("m", "d", find_spec=find) is None


def test_a_module_that_is_there_without_a_distribution_has_an_unknown_version(monkeypatch):
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(importlib.metadata, "version", missing)
    assert doctor.module_version("m", "d", find_spec=lambda name: object()) == "?"
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "1.2.3")
    assert doctor.module_version("m", "d", find_spec=lambda name: object()) == "1.2.3"


def test_the_machine_checks_say_what_is_missing_and_how_serious_it_is():
    checks = doctor.check_machine(CONFIG, which=lambda name: None, run=_run(), find_spec=lambda name: None, python_version="3.99.0")
    states = {check.key: check.state for check in checks}
    assert states["python"] == doctor.INFO and states["git_missing"] == doctor.FAIL and states["toolchain_missing"] == doctor.WARN
    assert states["hostcc_missing"] == doctor.INFO and states["node_missing"] == doctor.INFO
    assert states["pyside_missing"] == doctor.WARN and states["pyserial_missing"] == doctor.WARN
    assert doctor.exit_status(checks) == 1


def test_the_first_program_of_a_group_that_answers_is_the_one_that_counts():
    seen = []

    def which(name):
        seen.append(name)
        return "/bin/" + name if name == CONFIG["tools"]["git"][-1] else None
    checks = doctor.check_machine(CONFIG, which=which, run=_run(stdout="v1"), find_spec=lambda name: object(), python_version="3")
    git = next(check for check in checks if check.key.startswith("git_"))
    assert git.key == "git_ok" and git.state == doctor.OK
    assert seen[0] == CONFIG["tools"]["git"][0]


# ---- the ports ---------------------------------------------------------------------------------------------------------------------------------

def test_a_port_is_an_adapter_by_its_usb_identifier_first_and_by_a_word_of_its_description_after():
    entry = CONFIG["usb_ids"][0]
    by_id = doctor.Port("COM3", "something", int(entry["vid"], 16), int(entry["pid"], 16))
    assert doctor.classify_port(by_id, CONFIG) == entry["name"]
    word = CONFIG["keywords"][0]
    assert doctor.classify_port(doctor.Port("COM4", f"My {word.upper()} thing"), CONFIG) == word
    assert doctor.classify_port(doctor.Port("COM5", "Bluetooth link"), CONFIG) is None
    assert doctor.classify_port(doctor.Port("COM6", "x", 0x1234, None), CONFIG) is None


class _Handle:
    def __init__(self, raw=b"", fail=None):
        self.raw, self.fail, self.written, self.closed = raw, fail, [], False

    def reset_input_buffer(self):
        if self.fail == "reset":
            raise OSError("reset")

    def write(self, data):
        if self.fail == "write":
            raise OSError("write")
        self.written.append(data)

    def read(self, size):
        if self.fail == "read":
            raise OSError("read")
        return self.raw

    def close(self):
        self.closed = True
        if self.fail == "close":
            raise OSError("close")


def _probe(handle=None, opener_error=None):
    def opener(*args, **kwargs):
        if opener_error is not None:
            raise opener_error
        return handle
    return doctor.probe_serial(doctor.Port("COM3", ""), CONFIG, opener=opener)


def test_a_port_that_answers_with_the_prefix_is_an_answer_and_only_the_query_is_written():
    prefix = CONFIG["probe"]["answer_prefix"]
    handle = _Handle(raw=(prefix + "1.2\r").encode())
    assert _probe(handle) == ("answer", prefix + "1.2") and handle.closed
    assert handle.written == [CONFIG["probe"]["query"].encode("ascii")]


@pytest.mark.parametrize("raw", [b"", b"\r\x07 ", b"zz", b"\xff\xfe"])
def test_an_answer_without_the_prefix_or_too_short_is_silence(raw):
    assert _probe(_Handle(raw=raw)) == ("silent", "")


@pytest.mark.parametrize("fail", ["reset", "write", "read"])
def test_a_port_that_fails_while_it_is_asked_is_silent_and_is_still_closed(fail):
    handle = _Handle(fail=fail)
    assert _probe(handle) == ("silent", "") and handle.closed


def test_a_port_that_cannot_be_closed_does_not_change_the_answer():
    prefix = CONFIG["probe"]["answer_prefix"]
    assert _probe(_Handle(raw=(prefix + "9").encode(), fail="close"))[0] == "answer"


@pytest.mark.parametrize("error", [OSError("busy"), ValueError("bad"), RuntimeError("serial exception of its own")])
def test_a_port_that_cannot_be_opened_is_busy(error):
    assert _probe(opener_error=error) == ("busy", "")


# ---- the drawing -------------------------------------------------------------------------------------------------------------------------------

def test_the_exit_status_is_one_only_when_a_check_fails():
    ok = doctor.Check(doctor.SECTION_MACHINE, doctor.OK, "git_ok", {"version": "1"})
    warn = doctor.Check(doctor.SECTION_MACHINE, doctor.WARN, "toolchain_missing")
    fail = doctor.Check(doctor.SECTION_MACHINE, doctor.FAIL, "git_missing")
    assert doctor.exit_status([]) == 0 and doctor.exit_status([ok, warn]) == 0 and doctor.exit_status([ok, fail]) == 1


def test_a_report_leaves_out_the_sections_that_have_no_check_and_names_each_state():
    checks = [doctor.Check(doctor.SECTION_MACHINE, doctor.OK, "git_ok", {"version": "2.0"}), doctor.Check(doctor.SECTION_SYNC, doctor.WARN, "sync_pending", {"count": 3})]
    for language in ("english", "spanish", "german", "french", "italian", "japanese", "chinese", "portuguese"):
        text = doctor.render(checks, language)
        lines = text.splitlines()
        assert len(lines) == 4 and "2.0" in lines[1] and "3" in lines[3]
        assert lines[0].endswith(":") or lines[0].endswith("：")
    assert doctor.render([], "english") == ""
