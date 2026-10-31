# =============================================================================
# URTC-UPDATER - tests/test_security.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The two security options (require signed commits, ask before the build check): off by default, settable from the settings file, the environment and the command line,
a warning when a run lowers them, and a damaged settings file that fails on the safe side."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from repo_helpers import NAME, entry, make_remote

from urtc_updater import i18n, install, security, settings
from urtc_updater import main as main_module
from urtc_updater.install import install_or_update
from urtc_updater.signature import current_policy, verify_revision


@pytest.fixture(autouse=True)
def _clean_security(monkeypatch):
    for variable in (security.ENV_REQUIRE_SIGNED, security.ENV_CONFIRM_BUILD, security.ENV_ASSUME_YES):
        # set-then-delete so the test run restores the variable even when the code under test sets it
        monkeypatch.setenv(variable, "")
        monkeypatch.delenv(variable)
    security.set_confirmer(None)
    yield
    security.set_confirmer(None)


# --- defaults and precedence --------------------------------------------------

def test_both_protections_are_on_by_default():
    assert security.effective_require_signed()
    assert security.effective_confirm_build()
    assert security.saved_require_signed() and security.saved_confirm_build()
    assert security.lowering_warnings() == []
    assert current_policy().mode == "require"
    assert not security.assume_yes()


def test_the_settings_file_can_go_back_to_the_previous_level():
    settings.save_settings(signature_policy="warn", confirm_before_build=False)
    assert not security.effective_require_signed() and not security.effective_confirm_build()
    assert current_policy().mode == "warn"
    settings.SETTINGS_PATH.write_text(json.dumps({"require_signed_commits": False}), encoding="utf-8")
    assert not security.effective_require_signed() and security.effective_confirm_build()


def test_an_old_settings_file_with_other_keys_gets_the_new_defaults():
    settings.save_settings(lang="de", backups_to_keep=2)
    assert security.effective_require_signed() and security.effective_confirm_build()


def test_the_explicit_setting_answers_yes_for_unattended_runs(monkeypatch):
    settings.save_settings(assume_yes_without_asking=True)
    assert security.assume_yes()
    with security.confirmer(lambda request: False):
        assert security.decide_build(_request()) == security.BuildDecision(True, "assumed")
    monkeypatch.setenv(security.ENV_ASSUME_YES, "0")
    assert not security.assume_yes()
    assert security.decide_build(_request()) == security.BuildDecision(False, "nobody to ask")


def test_the_settings_file_turns_each_one_on():
    settings.save_settings(signature_policy="require", confirm_before_build=True)
    assert security.effective_require_signed() and security.effective_confirm_build()
    assert current_policy().mode == "require"


def test_the_older_settings_key_still_requires_signatures():
    settings.save_settings(require_signed_commits=True)
    assert security.effective_require_signed()


def test_the_environment_wins_over_the_settings_in_both_directions(monkeypatch):
    settings.save_settings(signature_policy="require", confirm_before_build=True)
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "off")
    assert not security.effective_require_signed() and not security.effective_confirm_build()
    monkeypatch.delenv(security.ENV_REQUIRE_SIGNED)
    monkeypatch.delenv(security.ENV_CONFIRM_BUILD)
    settings.save_settings(signature_policy="warn", confirm_before_build=False)
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "1")
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "yes")
    assert security.effective_require_signed() and security.effective_confirm_build()


def test_a_run_that_turns_a_saved_protection_off_is_warned_about(monkeypatch):
    settings.save_settings(signature_policy="require", confirm_before_build=True)
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")
    codes = [warning.code for warning in security.lowering_warnings()]
    assert codes == ["security_lowered_signed"]
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "0")
    assert [warning.code for warning in security.lowering_warnings()] == ["security_lowered_signed", "security_lowered_confirm"]


def test_raising_a_protection_for_one_run_is_not_a_warning(monkeypatch):
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "1")
    assert security.lowering_warnings() == []


def test_saving_a_lower_level_is_reported_before_it_is_saved():
    settings.save_settings(signature_policy="require", confirm_before_build=True)
    assert [w.code for w in security.lowering_of_change(require_signed=True, confirm_build=True)] == []
    assert [w.code for w in security.lowering_of_change(require_signed=False, confirm_build=True)] == ["security_lowered_signed"]
    assert len(security.lowering_of_change(require_signed=False, confirm_build=False)) == 2


def test_save_security_writes_the_name_the_signature_module_reads():
    settings.save_settings(require_signed_commits=True, lang="de")
    security.save_security(require_signed=False, confirm_build=True)
    data = json.loads(settings.SETTINGS_PATH.read_text(encoding="utf-8"))
    assert data["signature_policy"] == "warn" and data["confirm_before_build"] is True
    assert "require_signed_commits" not in data and data["lang"] == "de"
    security.save_security(require_signed=True, confirm_build=False)
    assert current_policy().mode == "require" and not security.effective_confirm_build()


# --- a damaged settings file fails on the safe side ------------------------------

def test_a_settings_file_that_cannot_be_read_requires_signatures():
    settings.SETTINGS_PATH.write_text('{"signature_policy": "war', encoding="utf-8")
    assert settings.settings_state() == "corrupt"
    assert security.effective_require_signed()
    policy = current_policy()
    assert policy.required and policy.settings_unreadable


def test_the_environment_can_still_say_otherwise_for_a_damaged_file(monkeypatch):
    settings.SETTINGS_PATH.write_text("not json", encoding="utf-8")
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")
    assert not security.effective_require_signed()


def test_the_refusal_says_why_the_signatures_are_required(tmp_path: Path, monkeypatch):
    settings.SETTINGS_PATH.write_text("[1, 2", encoding="utf-8")
    monkeypatch.setattr("urtc_updater.signature.unsigned_reason", lambda *_a, **_k: "candidate commit is not signed by a trusted key")
    reason = verify_revision(tmp_path, "HEAD", current_policy())
    assert reason and "settings file could not be read" in reason


def test_saving_the_language_does_not_overwrite_a_damaged_settings_file():
    settings.SETTINGS_PATH.write_text("{broken", encoding="utf-8")
    settings.save_settings(lang="fr")
    assert settings.SETTINGS_PATH.read_text(encoding="utf-8") == "{broken"


def test_saving_the_security_options_keeps_the_damaged_file_aside():
    settings.SETTINGS_PATH.write_text("{broken", encoding="utf-8")
    security.save_security(require_signed=True, confirm_build=False)
    assert settings.settings_state() == "ok" and security.saved_require_signed()
    assert settings.SETTINGS_PATH.with_name(settings.SETTINGS_PATH.name + ".corrupt").read_text(encoding="utf-8") == "{broken"


def test_a_missing_or_valid_file_is_not_corrupt():
    assert settings.settings_state() == "missing"
    settings.save_settings(lang="es")
    assert settings.settings_state() == "ok"
    settings.SETTINGS_PATH.write_text("[]", encoding="utf-8")
    assert settings.settings_state() == "corrupt"


# --- the question before the build check -----------------------------------------

def _request() -> security.BuildRequest:
    return security.BuildRequest("P", "build-test.sh", "abc123", "Someone <s@example.invalid>", "not signed", ("build-test.sh",))


def test_with_the_option_off_nobody_is_asked(monkeypatch):
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "0")
    asked = []
    security.set_confirmer(lambda request: asked.append(request) or False)
    decision = security.decide_build(_request())
    assert decision.allowed and decision.how == "not asked" and asked == []


def test_with_the_option_on_the_answer_decides(monkeypatch):
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "1")
    with security.confirmer(lambda request: True):
        assert security.decide_build(_request()) == security.BuildDecision(True, "confirmed")
    with security.confirmer(lambda request: False):
        assert security.decide_build(_request()) == security.BuildDecision(False, "declined")


def test_with_nobody_to_ask_nothing_is_run(monkeypatch):
    assert security.decide_build(_request()) == security.BuildDecision(False, "nobody to ask")


def test_yes_answers_without_asking(monkeypatch):
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "1")
    monkeypatch.setenv(security.ENV_ASSUME_YES, "1")
    with security.confirmer(lambda request: False):
        assert security.decide_build(_request()) == security.BuildDecision(True, "assumed")


# --- in the install and update flow ---------------------------------------------------

def _setup_update(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")   # the test commits are not signed; this file tests the question before the build check
    remote.push("1.1.0", "second", {"notes.txt": "x"})
    return remote


def _ran_marker(workspace: Path) -> Path:
    return workspace / "ran-build"


def test_a_declined_confirmation_runs_nothing_and_leaves_the_installed_version(tmp_path: Path, monkeypatch):
    remote = _setup_update(tmp_path, monkeypatch)
    ran = []
    monkeypatch.setattr(install, "_run_build_script_at", lambda *a, **k: ran.append(a) or install.InstallResult(True, "built"))
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "1")
    seen: list[security.BuildRequest] = []
    with security.confirmer(lambda request: seen.append(request) or False):
        results = install_or_update(entry(), remote.workspace)
    assert not results[0].ok and results[0].message.startswith("the build check of")
    assert ran == [] and len(seen) == 1
    assert seen[0].project == NAME and seen[0].script in {"build-test.sh", "build-test.bat"} and seen[0].commit
    assert "Contract" in seen[0].author and seen[0].changed_scripts == ()
    assert '"1.0.0"' in (remote.checkout / "urtc.project.json").read_text(encoding="utf-8")


def test_a_confirmed_update_goes_ahead(tmp_path: Path, monkeypatch):
    remote = _setup_update(tmp_path, monkeypatch)
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "1")
    steps: list[object] = []
    with security.confirmer(lambda request: True):
        results = install_or_update(entry(), remote.workspace, progress=lambda phase, text: steps.append(text))
    assert all(result.ok for result in results), [r.message for r in results]
    assert '"1.1.0"' in (remote.checkout / "urtc.project.json").read_text(encoding="utf-8")
    assert any(getattr(step, "code", "") == "cp_build_confirmed" for step in steps)


def test_without_the_option_the_flow_is_as_before(tmp_path: Path, monkeypatch):
    remote = _setup_update(tmp_path, monkeypatch)
    monkeypatch.setenv(security.ENV_CONFIRM_BUILD, "0")
    asked = []
    with security.confirmer(lambda request: asked.append(request) or False):
        results = install_or_update(entry(), remote.workspace)
    assert all(result.ok for result in results) and asked == []


def test_the_confirmation_lists_the_build_scripts_the_candidate_changed(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    remote.push("1.1.0", "second", {"tools/build_test.py": "print('changed')\n"})
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")
    seen: list[security.BuildRequest] = []
    with security.confirmer(lambda request: seen.append(request) or False):
        install_or_update(entry(), remote.workspace)
    assert seen and "tools/build_test.py" in seen[0].changed_scripts


def test_a_new_install_asks_before_its_build_check(tmp_path: Path, monkeypatch):
    remote = make_remote(tmp_path, clone=False)
    monkeypatch.setattr(install, "github_repo_url", lambda _entry: str(remote.bare))
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")
    ran = []
    monkeypatch.setattr(install, "_run_build_script_at", lambda *a, **k: ran.append(a) or install.InstallResult(True, "built"))
    with security.confirmer(lambda request: False):
        results = install_or_update(entry(), remote.workspace)
    assert results[0].ok and not results[-1].ok and "was not confirmed" in results[-1].message
    assert ran == []


def test_with_nobody_to_ask_an_update_is_refused_with_a_message_that_says_so(tmp_path: Path, monkeypatch):
    remote = _setup_update(tmp_path, monkeypatch)
    monkeypatch.setenv(security.ENV_REQUIRE_SIGNED, "0")   # the default would stop an unsigned test commit first; the question is what is under test
    results = install_or_update(entry(), remote.workspace)
    assert not results[0].ok and "nobody to ask" in results[0].message and "assume_yes_without_asking" in results[0].message


def test_the_messages_exist_in_every_language():
    for code, _label in i18n.LANGUAGES:
        for key in ("inst_security_lowered_signed", "inst_security_lowered_confirm", "inst_cp_build_confirmed", "inst_cp_build_assumed_yes", "inst_cp_build_not_confirmed"):
            assert i18n.t(code, key, project="P") != key, (code, key)
        assert "P" in i18n.t(code, "inst_build_not_confirmed", project="P")
        assert "P" in i18n.t(code, "inst_build_nobody_to_ask", project="P")
        text = i18n.t(code, "build_confirm_details", commit="c0ffee", author="A", signature="S", scripts="X")
        assert all(part in text for part in ("c0ffee", "A", "S", "X")) and "{" not in text, code
        assert "{items}" in i18n.t(code, "security_lowering_body")


# --- the interpreter of the build check -----------------------------------------------

def test_the_build_check_is_told_which_python_to_use(monkeypatch):
    monkeypatch.delenv(install.BUILD_PYTHON_VARIABLE, raising=False)
    assert install.build_environment()[install.BUILD_PYTHON_VARIABLE] == sys.executable
    monkeypatch.setenv(install.BUILD_PYTHON_VARIABLE, "/my/python")
    assert install.build_environment()[install.BUILD_PYTHON_VARIABLE] == "/my/python"


def test_the_script_is_run_with_that_environment(tmp_path: Path, monkeypatch):
    project = tmp_path / "P"
    project.mkdir()
    script = project / ("build-test.bat" if os.name == "nt" else "build-test.sh")
    script.write_text("exit 0\n", encoding="utf-8")
    captured = {}

    def fake_run(cmd, cwd, *, capture_output=False, env=None):
        captured["env"] = env

        class Done:
            returncode = 0
            stdout = ""
            stderr = ""
        return Done()

    monkeypatch.setattr(install, "_run", fake_run)
    monkeypatch.delenv(install.BUILD_PYTHON_VARIABLE, raising=False)
    assert install._run_build_script_at(project).ok
    assert captured["env"][install.BUILD_PYTHON_VARIABLE] == sys.executable


# --- the command line ---------------------------------------------------------------------

def _cli(args: list[str], monkeypatch) -> int:
    monkeypatch.setattr(sys, "argv", ["urtc-updater", "--cli", *args])
    return main_module.main()


def test_the_security_command_shows_the_state(monkeypatch, capsys):
    assert _cli(["security"], monkeypatch) == 0
    out = capsys.readouterr().out
    assert "Require signed commits" in out and "on (saved)" in out and "Both are on by default" in out


def test_the_security_command_saves_a_higher_level_without_asking(monkeypatch, capsys):
    assert _cli(["security", "--require-signed", "on", "--confirm-build", "on"], monkeypatch) == 0
    assert security.saved_require_signed() and security.saved_confirm_build()
    assert "Saved" in capsys.readouterr().out


def test_lowering_needs_a_confirmation_and_says_so(monkeypatch, capsys):
    security.save_security(require_signed=True, confirm_build=True)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert _cli(["security", "--require-signed", "off"], monkeypatch) == 1
    captured = capsys.readouterr()
    assert "does not require signed commits" in captured.err and "Not changed" in captured.err
    assert security.saved_require_signed()


def test_lowering_with_yes_is_saved_and_warned_about(monkeypatch, capsys):
    security.save_security(require_signed=True, confirm_build=True)
    assert _cli(["security", "--confirm-build", "off", "--yes"], monkeypatch) == 0
    captured = capsys.readouterr()
    assert "does not ask before the build check" in captured.err
    assert security.saved_require_signed() and not security.saved_confirm_build()


def test_lowering_is_confirmed_in_a_terminal(monkeypatch, capsys):
    security.save_security(require_signed=True, confirm_build=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    assert _cli(["security", "--require-signed", "off"], monkeypatch) == 1
    assert security.saved_require_signed()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")
    assert _cli(["security", "--require-signed", "off"], monkeypatch) == 0
    assert not security.saved_require_signed()


def test_the_flags_of_install_and_update_reach_the_environment_and_warn(monkeypatch, capsys):
    security.save_security(require_signed=True, confirm_build=True)
    parser = main_module.build_parser()
    args = parser.parse_args(["update", "X", "--no-require-signed", "--no-confirm-build", "--yes"])
    assert args.require_signed is False and args.confirm_build is False and args.yes
    main_module._apply_security_arguments(args)
    assert os.environ[security.ENV_REQUIRE_SIGNED] == "0" and os.environ[security.ENV_CONFIRM_BUILD] == "0"
    err = capsys.readouterr().err
    assert "does not require signed commits" in err and "does not ask before the build check" in err
    monkeypatch.delenv(security.ENV_REQUIRE_SIGNED)
    monkeypatch.delenv(security.ENV_CONFIRM_BUILD)
    monkeypatch.delenv(security.ENV_ASSUME_YES)


def test_defaults_of_the_flags_change_nothing(monkeypatch):
    args = main_module.build_parser().parse_args(["install", "X"])
    assert args.require_signed is None and args.confirm_build is None and not args.yes
    main_module._apply_security_arguments(args)
    assert security.ENV_REQUIRE_SIGNED not in os.environ and security.ENV_CONFIRM_BUILD not in os.environ


def test_the_terminal_confirmer_says_no_without_a_terminal(monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert main_module._terminal_confirmer(_request()) is False


def test_the_terminal_confirmer_asks_with_the_details(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "yes")
    assert main_module._terminal_confirmer(_request()) is True
    err = capsys.readouterr().err
    assert "abc123" in err and "Someone" in err and "not signed" in err and "build-test.sh" in err
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")
    assert main_module._terminal_confirmer(_request()) is False
