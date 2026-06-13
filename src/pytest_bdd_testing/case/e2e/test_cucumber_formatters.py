"""

Provide test cucumber formatters helpers.
"""

from __future__ import annotations

from glob import escape
from pathlib import Path

import pytest

from pytest_bdd_testing.tool.cucumber_formatter import (
    assert_pytest_terminal_reporter_suppressed,
    assert_pytest_terminal_reporter_visible,
    build_sample_suite,
    expected_formatter_output_lines,
    expected_formatter_visible_line,
    install_fake_node,
    materialize_fake_node_runtime,
    read_fake_formatter_telemetry,
    run_pytest_via_real_entrypoint,
    with_pytester_terminal_capture_disabled,
)
from pytest_bdd_testing.tool.pytest_results import combined_result_output


def test_fake_runtime_support_uses_template_assets_from_shared_support_module() -> None:
    """
    Verify fake runtime support uses template assets from shared support module.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    repo_root = Path(__file__).resolve().parents[5]
    support_source = (repo_root / "src" / "pytest_bdd_testing" / "cucumber_formatters" / "rendering.py").read_text(
        encoding="utf-8",
    )

    assert "fake_node_runtime.py.j2" in support_source
    assert "fake_npm_runtime.py.j2" in support_source
    assert "fake node expected either" not in support_source


def test_fake_runtime_support_materializes_windows_command_shims(tmp_path: Path) -> None:
    """
    Verify fake runtime support materializes windows command shims.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    runtime = materialize_fake_node_runtime(tmp_path)

    assert (runtime["bin_dir"] / "node.cmd").exists()
    assert (runtime["bin_dir"] / "npm.cmd").exists()


@pytest.mark.parametrize(
    ("cli_args", "formatter_name"),
    [
        (["--cucumber-summary"], "summary"),
        (["--cucumber-progress"], "progress"),
        (["--cucumber-progress-bar"], "progress-bar"),
        (["--cucumber-snippets"], "snippets"),
        (["--cucumber-pretty"], "pretty"),
        (["--cucumber-usage"], "usage"),
    ],
)
def test_console_formatter_flags_emit_stdout(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cli_args,
    formatter_name: str,
) -> None:
    """
    Verify console formatter flags emit stdout.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)

    result = testdir.runpytest_subprocess(*with_pytester_terminal_capture_disabled(*cli_args))

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert_pytest_terminal_reporter_suppressed(result.stdout.str())
    result.stdout.fnmatch_lines([f"*{escape(line)}*" for line in expected_formatter_output_lines(formatter_name)])


@pytest.mark.parametrize(
    ("option_name", "file_name", "formatter_name"),
    [
        ("--cucumber-json", "report.json", "json"),
        ("--cucumber-junit", "report.xml", "junit"),
        ("--cucumber-usage", "usage.txt", "usage"),
        ("--cucumber-usage-json", "usage.json", "usage-json"),
    ],
)
def test_file_formatter_flags_write_output(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    option_name: str,
    file_name: str,
    formatter_name: str,
) -> None:
    """
    Verify file formatter flags write output.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)
    output_path = tmp_path / file_name

    result = testdir.runpytest_subprocess(f"{option_name}={output_path}")

    result.assert_outcomes(passed=1, failed=1)
    assert output_path.exists()
    assert expected_formatter_visible_line(formatter_name) in output_path.read_text(encoding="utf-8")


def test_multiple_cucumber_formatters_run_in_one_session(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify multiple cucumber formatters run in one session.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)
    json_path = tmp_path / "combined.json"
    usage_json_path = tmp_path / "usage.json"

    result = testdir.runpytest_subprocess(
        *with_pytester_terminal_capture_disabled(
            "--cucumber-summary",
            f"--cucumber-json={json_path}",
            f"--cucumber-usage-json={usage_json_path}",
        ),
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert_pytest_terminal_reporter_suppressed(result.stdout.str())
    result.stdout.fnmatch_lines(
        [
            f"*{escape(expected_formatter_visible_line('summary'))}*",
        ],
    )
    assert expected_formatter_visible_line("json") in json_path.read_text(encoding="utf-8")
    assert expected_formatter_visible_line("usage-json") in usage_json_path.read_text(encoding="utf-8")
    telemetry = read_fake_formatter_telemetry(tmp_path)
    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == "stdin"
    assert telemetry[0]["formatterNames"] == ["summary", "json", "usage-json"]
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is True
    assert int(telemetry[0]["envelopeCount"]) > 0


def test_console_formatter_consumes_live_stdin_stream(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify console formatter consumes live stdin stream.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)

    result = testdir.runpytest_subprocess(*with_pytester_terminal_capture_disabled("--cucumber-summary"))

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert_pytest_terminal_reporter_suppressed(result.stdout.str())
    telemetry = read_fake_formatter_telemetry(tmp_path)
    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == "stdin"
    assert telemetry[0]["formatterNames"] == ["summary"]
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is True
    assert int(telemetry[0]["envelopeCount"]) > 0


def test_file_formatter_consumes_live_stdin_stream(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify file formatter consumes live stdin stream.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)
    output_path = tmp_path / "report.json"

    result = testdir.runpytest_subprocess(f"--cucumber-json={output_path}")

    result.assert_outcomes(passed=1, failed=1)
    assert expected_formatter_visible_line("json") in output_path.read_text(encoding="utf-8")
    telemetry = read_fake_formatter_telemetry(tmp_path)
    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == "stdin"
    assert telemetry[0]["formatterNames"] == ["json"]
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is False
    assert int(telemetry[0]["envelopeCount"]) > 0


def test_multiple_terminal_formatters_fail_before_test_execution(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify multiple terminal formatters fail before test execution.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)

    result = testdir.runpytest_subprocess("--cucumber-summary", "--cucumber-progress")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*Only one terminal-output formatter may be active per run*"])


def test_missing_output_directory_fails_before_test_execution(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify missing output directory fails before test execution.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)
    output_path = tmp_path / "missing-dir" / "report.json"

    result = testdir.runpytest_subprocess(f"--cucumber-json={output_path}")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*Formatter output directory does not exist*"])
    assert output_path.parent.exists() is False


def test_duplicate_file_output_paths_fail_before_test_execution(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify duplicate file output paths fail before test execution.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)
    output_path = tmp_path / "report.out"

    result = testdir.runpytest_subprocess(
        f"--cucumber-json={output_path}",
        f"--cucumber-junit={output_path}",
    )

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*Multiple formatter outputs target the same path*"])


def test_missing_cucumber_package_is_auto_installed_for_console_formatter(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify missing cucumber package is auto installed for console formatter.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())
    build_sample_suite(testdir)

    result = testdir.runpytest_subprocess(*with_pytester_terminal_capture_disabled("--cucumber-progress"))

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert_pytest_terminal_reporter_suppressed(result.stdout.str())
    result.stderr.fnmatch_lines(
        [
            (
                "*Installing missing global npm package(s) for cucumber formatter rendering "
                "(--cucumber-progress): @cucumber/cucumber*"
            ),
        ],
    )
    result.stdout.fnmatch_lines([f"*{escape(expected_formatter_visible_line('progress'))}*"])


def test_live_formatter_startup_failure_preserves_default_pytest_terminal_output(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify live formatter startup failure preserves default pytest terminal output.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)

    result = run_pytest_via_real_entrypoint(
        testdir,
        "--cucumber-summary",
        extra_env={"PATH": ""},
    )

    assert result.returncode in {pytest.ExitCode.TESTS_FAILED, pytest.ExitCode.INTERNAL_ERROR}
    combined_output = combined_result_output(result)
    assert "Unable to start the live cucumber formatter session" in combined_output
    assert_pytest_terminal_reporter_visible(combined_output)


def test_console_formatter_emits_output_via_real_entrypoint(
    testdir,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify console formatter emits output via real entrypoint.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    build_sample_suite(testdir)

    result = run_pytest_via_real_entrypoint(testdir, "--cucumber-summary", preserve_fake_node=True)

    assert result.returncode == pytest.ExitCode.TESTS_FAILED
    assert expected_formatter_visible_line("summary") in result.stdout
    assert_pytest_terminal_reporter_suppressed(result.stdout)
