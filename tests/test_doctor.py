# =============================================================================
# URTC-UPDATER - tests/test_doctor.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The doctor: tools of the machine, adapters seen and probed, projects and the firmware of the Flasher. It reads; the ports are opened only by the probe."""
from __future__ import annotations

import json
import os
import re
import socket
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_firmware_sync import workspace  # noqa: F401  (the fixture: a workspace with URTC and URTC-FLASHER)
from test_flasher_handoff import PUBLIC

from urtc_updater import doctor, doctor_texts, evidence
from urtc_updater import firmware_sync as fs
from urtc_updater.main import build_parser

CONFIG = doctor.load_config()


# ---- the words -----------------------------------------------------------------------------------------------------
def test_every_language_has_every_text_with_the_same_placeholders():
    english = doctor_texts.STRINGS["english"]
    for language in doctor_texts.LANGUAGES:
        table = doctor_texts.STRINGS[language]
        assert set(table) == set(english), (language, set(english) ^ set(table))
        for key, value in table.items():
            assert value.strip(), (language, key)
            assert set(re.findall(r"\{(\w+)\}", value)) == set(re.findall(r"\{(\w+)\}", english[key])), (language, key)


def test_portuguese_is_the_portuguese_of_portugal_and_an_unknown_key_falls_back():
    assert "ficheiro" in doctor_texts.text("portuguese", "sync_pending", count=2)
    assert doctor_texts.text("klingon", "close") == "Close"
    assert doctor_texts.text("english", "no such key") == "no such key"


# ---- the tools -----------------------------------------------------------------------------------------------------
def fake_run(output: str = "tool 1.2.3\n", code: int = 0):
    return lambda *a, **k: SimpleNamespace(stdout=output, stderr="", returncode=code)


def states(checks):
    return {c.key: c.state for c in checks}


def test_a_missing_git_is_the_only_failure_and_missing_optional_tools_are_not():
    checks = doctor.check_machine(CONFIG, which=lambda name: None, run=fake_run(), find_spec=lambda name: None)
    state = states(checks)
    assert state["git_missing"] == doctor.FAIL and state["toolchain_missing"] == doctor.WARN and state["hostcc_missing"] == doctor.INFO
    assert doctor.exit_status(checks) == 1
    found = doctor.check_machine(CONFIG, which=lambda name: "/bin/" + name, run=fake_run("gcc 13.2\nmore\n"), find_spec=lambda name: object())
    assert doctor.exit_status(found) == 0 and "toolchain_ok" in states(found)
    assert [c for c in found if c.key == "git_ok"][0].values["version"] == "gcc 13.2"


def test_a_program_that_cannot_run_is_found_with_an_unknown_version():
    def boom(*a, **k):
        raise OSError("no")

    assert doctor.program_version("git", CONFIG, which=lambda n: "/bin/git", run=boom) == "?"
    assert doctor.program_version("git", CONFIG, which=lambda n: None, run=boom) is None


# ---- the adapters --------------------------------------------------------------------------------------------------
def test_ports_are_classified_by_usb_identifier_then_by_the_words_of_the_description():
    assert doctor.classify_port(doctor.Port("COM5", "USB Serial Device", 0x1D50, 0x606F), CONFIG) == "candleLight / CANable"
    assert doctor.classify_port(doctor.Port("COM6", "CANable slcan adapter", 0x1234, 0x5678), CONFIG) == "slcan"
    assert doctor.classify_port(doctor.Port("COM1", "Communications Port"), CONFIG) is None
    assert doctor.classify_port(doctor.Port("COM2", "", None, None), CONFIG) is None


def adapters(ports, probe=False, serial=None, virtual=None, environ=None):
    return doctor.check_adapters(CONFIG, probe=probe, ports=lambda: ports, environ=environ or {},
                                 serial_probe=serial or (lambda *a, **k: ("silent", "")), virtual_probe=virtual or (lambda *a, **k: ("silent", "")))


def test_without_the_probe_no_port_is_opened_and_the_report_says_so():
    called = []
    checks = adapters([doctor.Port("COM5", "CANable", 0x1D50, 0x606F), doctor.Port("COM1", "Comm")], serial=lambda *a, **k: called.append(a) or ("answer", "V"), environ={"URTC_VIRTUAL_PORT": "socket://127.0.0.1:7777"})
    assert called == []
    keys = [c.key for c in checks]
    assert keys.count("adapter_found") == 1 and "adapter_other" in keys and "probe_off" in keys and "virtual_listed" in keys


def test_no_candidate_is_a_warning_with_advice():
    checks = adapters([doctor.Port("COM1", "Comm")])
    assert checks[0].key == "adapters_none" and checks[0].state == doctor.WARN


def test_the_probe_reports_an_answer_a_silence_and_a_busy_port():
    ports = [doctor.Port("COM5", "CANable", 0x1D50, 0x606F), doctor.Port("COM6", "slcan"), doctor.Port("COM7", "canusb")]
    results = iter([("answer", "V0101"), ("silent", ""), ("busy", "")])
    checks = adapters(ports, probe=True, serial=lambda *a, **k: next(results), virtual=lambda *a, **k: ("answer", "V0101"), environ={"URTC_VIRTUAL_PORT": "socket://127.0.0.1:7777, COM3"})
    state = states(checks)
    assert state["probe_answer"] == doctor.OK and state["probe_silent"] == doctor.WARN and state["probe_busy"] == doctor.WARN and state["virtual_up"] == doctor.OK
    assert "probe_off" not in state


class FakeSerial:
    def __init__(self, reply: bytes = b"V0101\r", fail: bool = False):
        self.reply, self.fail, self.written, self.closed = reply, fail, [], False

    def reset_input_buffer(self): pass

    def write(self, data):
        if self.fail:
            raise OSError("gone")
        self.written.append(data)

    def read(self, size):
        return self.reply

    def close(self):
        self.closed = True


def test_the_probe_writes_the_version_query_and_nothing_else_and_closes_the_port():
    port = FakeSerial()
    result = doctor.probe_serial(doctor.Port("COM5", "x"), CONFIG, opener=lambda *a, **k: port)
    assert result == ("answer", "V0101") and port.written == [b"V\r"] and port.closed


def test_a_bell_or_a_failure_is_not_an_answer_and_a_port_that_will_not_open_is_busy():
    assert doctor.probe_serial(doctor.Port("COM5", "x"), CONFIG, opener=lambda *a, **k: FakeSerial(b"\a"))[0] == "silent"
    assert doctor.probe_serial(doctor.Port("COM5", "x"), CONFIG, opener=lambda *a, **k: FakeSerial(fail=True))[0] == "silent"

    def refuse(*a, **k):
        raise OSError("in use")

    assert doctor.probe_serial(doctor.Port("COM5", "x"), CONFIG, opener=refuse)[0] == "busy"


def test_a_virtual_board_is_probed_with_the_same_query():
    seen = []
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    def serve():
        connection, _ = server.accept()
        seen.append(connection.recv(16))
        connection.sendall(b"V0101\r")
        connection.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    url = f"socket://127.0.0.1:{server.getsockname()[1]}"
    assert doctor.probe_virtual(url, CONFIG) == ("answer", "V0101")
    thread.join(2)
    server.close()
    assert seen == [b"V\r"]
    assert doctor.probe_virtual("socket://127.0.0.1:1", CONFIG)[0] == "silent"


# ---- the report ----------------------------------------------------------------------------------------------------
def test_the_report_lists_the_projects_and_the_firmware_of_the_flasher(workspace):  # noqa: F811
    checks = doctor.run_doctor(workspace, "english", probe=False)
    state = states(checks)
    assert "sync_off" in state and ("sync_pending" in state or "sync_current" in state or "sync_unavailable" in state)
    text = doctor.render(checks, "spanish")
    assert "Herramientas:" in text and "Firmware para el Flasher:" in text


def test_the_command_prints_json_and_the_exit_status(workspace, capsys, monkeypatch):  # noqa: F811
    monkeypatch.setattr(doctor, "serial_ports", lambda: [])
    args = build_parser().parse_args(["doctor", "--json", "--workspace", str(workspace), "--language", "german"])
    status = args.func(args)
    data = json.loads(capsys.readouterr().out)
    assert status in (0, 1) and data["workspace"] == str(workspace)
    assert {c["section"] for c in data["checks"]} >= {"machine", "adapters", "sync"} and all(c["text"] for c in data["checks"])
    args = build_parser().parse_args(["doctor", "--workspace", str(workspace / "absent")])
    assert args.func(args) == 2


def test_the_doctor_changes_nothing_in_the_workspace(workspace, monkeypatch):  # noqa: F811
    monkeypatch.setattr(doctor, "serial_ports", lambda: [])
    before = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*"))
    doctor.run_doctor(workspace, "english", probe=False)
    assert sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*")) == before


def test_the_config_file_has_what_the_code_reads():
    assert CONFIG["probe"]["query"] == "V\r" and CONFIG["probe"]["answer_prefix"] == "V"
    assert all(re.fullmatch(r"[0-9a-f]{4}", entry["vid"]) and re.fullmatch(r"[0-9a-f]{4}", entry["pid"]) for entry in CONFIG["usb_ids"])


# ---- the firmware of the Flasher is recorded -----------------------------------------------------------------------
def entries(workspace_path: Path):
    return [e for e in evidence.read_attempts(workspace_path) if e["project"] == "URTC-FLASHER firmware"]


def test_a_confirmed_copy_is_recorded_in_the_evidence_chain(workspace):  # noqa: F811
    assert fs.run(workspace, assume_yes=True, public_key_hex=PUBLIC) == 0
    lines = entries(workspace)
    assert len(lines) == 1 and lines[0]["ok"] is True and "copied" in lines[0]["message"] and "URTC_MAIN_FIRMWARE_v0.4.1.bin" in lines[0]["message"]
    assert evidence.verify_chain(workspace) == []


def test_a_refusal_is_recorded_too_and_nothing_is_copied(workspace):  # noqa: F811
    assert fs.run(workspace, ask=lambda prompt: "n", public_key_hex=PUBLIC) == 1
    lines = entries(workspace)
    assert len(lines) == 1 and lines[0]["ok"] is False and lines[0]["message"].startswith("declined")
    assert not (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").exists()


def test_a_dry_run_records_nothing(workspace):  # noqa: F811
    fs.run(workspace, dry_run=True, public_key_hex=PUBLIC)
    assert entries(workspace) == []


# ---- the window ----------------------------------------------------------------------------------------------------
@pytest.fixture
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QCoreApplication

    return QCoreApplication.instance() or QCoreApplication([])


def test_the_model_reports_in_the_language_of_the_window_and_the_switch_is_off_by_default(qapp, workspace, tmp_path, monkeypatch):  # noqa: F811
    from urtc_updater import settings
    from urtc_updater.doctor_qt import DoctorModel

    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.delenv(fs.ENV, raising=False)
    monkeypatch.setattr(doctor, "serial_ports", lambda: [])
    code = ["en"]
    model = DoctorModel(lambda: workspace, lambda: code[0])
    model.run_now()
    lines = model.lines
    assert lines[0]["header"] is True and lines[0]["text"] == "Tools" and model.syncEnabled is False
    code[0] = "pt"
    model.run_now()
    assert model.lines[0]["text"] == "Ferramentas" and model.title.startswith("Diagnóstico")
    model.setSyncEnabled(True)
    assert model.syncEnabled is True and json.loads((tmp_path / "settings.json").read_text())[fs.SETTING] is True
    model.setSyncEnabled(False)
    assert model.syncEnabled is False


def test_the_window_asks_after_an_update_of_urtc_only_when_the_option_is_on(qapp, workspace, tmp_path, monkeypatch):  # noqa: F811
    from urtc_updater import settings
    from urtc_updater.doctor_qt import DoctorModel

    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.delenv(fs.ENV, raising=False)
    real = fs.plan
    monkeypatch.setattr(fs, "plan", lambda ws, key=None: real(ws, PUBLIC))
    model = DoctorModel(lambda: workspace, lambda: "en")
    asked = []
    model.offerRequested.connect(lambda: asked.append(1))
    assert model.offer_after_update("URTC") is False and asked == []         # the option is off: no question
    model.setSyncEnabled(True)
    assert model.offer_after_update("URTC-TESTER") is False                   # another project
    assert model.offer_after_update("URTC") is True and asked == [1]


def test_the_answers_of_the_window_copy_or_leave_everything_and_both_are_recorded(qapp, workspace, tmp_path, monkeypatch):  # noqa: F811
    from urtc_updater import settings
    from urtc_updater.doctor_qt import DoctorModel

    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    real = fs.plan
    monkeypatch.setattr(fs, "plan", lambda ws, key=None: real(ws, PUBLIC))
    monkeypatch.setattr(doctor, "serial_ports", lambda: [])
    model = DoctorModel(lambda: workspace, lambda: "en")
    monkeypatch.setattr(model, "_start", lambda probe: None)
    assert model.syncCanRun is True and any(line.startswith("copy URTC_MAIN") for line in model.syncPlanLines())
    model.answerSync(False)
    assert model.message == "Nothing was copied." and not (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").exists()
    model.answerSync(True)
    assert "Firmware copied" in model.message and (workspace / "URTC-FLASHER" / "firmware" / "URTC_MAIN_FIRMWARE_v0.4.1.bin").is_file()
    assert [e["ok"] for e in entries(workspace)] == [False, True]
    assert model.syncCanRun is False                                          # nothing left to copy


def test_the_window_has_the_dialog_the_button_and_the_bridge_property(qapp, tmp_path):
    from urtc_updater import qt_gui

    qml = (Path(qt_gui.__file__).parent / "qml" / "Main.qml").read_text(encoding="utf-8")
    assert "DoctorDialog" in qml and 'backend.doctor.text("menu")' in qml and "onOfferRequested" in qml
    bridge = qt_gui.UpdaterBridge(tmp_path)
    assert bridge.doctor is bridge.doctor and bridge.doctor.title
