"""Provide test cucumber formatters feature helpers."""

from __future__ import annotations

import os
import subprocess  # noqa: S404
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest

from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.testing.cucumber_formatters import (
    assert_pytest_terminal_reporter_suppressed,
    build_sample_suite,
    install_fake_node,
    read_fake_formatter_telemetry,
    requests_terminal_formatter_output,
    run_pytest_via_real_entrypoint,
)
from pytest_bdd.testing.pytest_results import attach_command_result_outputs

test = scenarios("../../../../tests/e2e/_cucumber_formatters.feature")


@pytest.fixture
def formatter_artifacts(tmp_path: Path) -> dict[str, object]:
    """Handle formatter artifacts."""
    return {"root": tmp_path, "outputs": {}}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_e2e_formatter_support_module_is_only_a_thin_reexport() -> None:
    """Verify e2e formatter support module is only a thin reexport."""
    shim_source = (_repo_root() / "tests" / "e2e" / "cucumber_formatter_support.py").read_text(encoding="utf-8")

    assert "from pytest_bdd.testing.cucumber_formatters import (" in shim_source
    assert "materialize_fake_node_runtime" in shim_source


def _run_pytest_subprocess_with_attachments(testdir, attach, *cli_args: str):
    if requests_terminal_formatter_output(*cli_args):
        result = run_pytest_via_real_entrypoint(testdir, *cli_args, preserve_fake_node=True)
    else:
        result = testdir.runpytest_subprocess(*cli_args)
    attach_command_result_outputs(
        attach,
        result,
        label="nested-pytest",
        command="pytest " + " ".join(cli_args),
        harness_stdout="",
        harness_stderr="",
    )
    return result


@given("a fake node executable is available")
def fake_node_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Handle fake node available."""
    install_fake_node(monkeypatch, tmp_path)


@given("a fake node executable without preinstalled formatter packages is available")
def fake_node_without_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Handle fake node without packages."""
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())


@given("a BDD suite with one passing and one failing scenario")
def formatter_sample_suite(testdir) -> None:
    """Handle formatter sample suite."""
    build_sample_suite(testdir)


@when(
    parsers.parse('I run pytest with the console formatter flag "{flag}"'),
    target_fixture="pytest_result",
)
def run_pytest_with_console_formatter(testdir, flag: str, attach):
    """Run pytest with console formatter."""
    return _run_pytest_subprocess_with_attachments(testdir, attach, flag)


@when(
    parsers.parse('I run pytest with the file formatter flag "{flag}" writing to "{report_name}"'),
    target_fixture="pytest_result",
)
def run_pytest_with_file_formatter(
    testdir,
    formatter_artifacts: dict[str, object],
    flag: str,
    report_name: str,
    attach,
):
    """Run pytest with file formatter."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    output_path = output_root / report_name
    outputs = formatter_artifacts["outputs"]
    assert isinstance(outputs, dict)
    outputs[report_name] = output_path
    return _run_pytest_subprocess_with_attachments(testdir, attach, f"{flag}={output_path}")


@when("I run pytest with multiple cucumber formatter flags", target_fixture="pytest_result")
def run_pytest_with_multiple_formatters(testdir, formatter_artifacts: dict[str, object], attach):
    """Run pytest with multiple formatters."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    outputs = formatter_artifacts["outputs"]
    assert isinstance(outputs, dict)
    json_path = output_root / "combined.json"
    usage_json_path = output_root / "usage.json"
    outputs["combined.json"] = json_path
    outputs["usage.json"] = usage_json_path
    return _run_pytest_subprocess_with_attachments(
        testdir,
        attach,
        "--cucumber-summary",
        f"--cucumber-json={json_path}",
        f"--cucumber-usage-json={usage_json_path}",
    )


@when("I run pytest with conflicting terminal formatter flags", target_fixture="pytest_result")
def run_pytest_with_conflicting_terminal_formatters(testdir, attach):
    """Run pytest with conflicting terminal formatters."""
    return _run_pytest_subprocess_with_attachments(testdir, attach, "--cucumber-summary", "--cucumber-progress")


@when("I run pytest with a file formatter pointing to a missing directory", target_fixture="pytest_result")
def run_pytest_with_missing_output_directory(testdir, formatter_artifacts: dict[str, object], attach):
    """Run pytest with missing output directory."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    output_path = output_root / "missing-dir" / "report.json"
    return _run_pytest_subprocess_with_attachments(testdir, attach, f"--cucumber-json={output_path}")


@when("I run pytest with conflicting file formatter output paths", target_fixture="pytest_result")
def run_pytest_with_conflicting_file_paths(testdir, formatter_artifacts: dict[str, object], attach):
    """Run pytest with conflicting file paths."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    output_path = output_root / "report.out"
    return _run_pytest_subprocess_with_attachments(
        testdir,
        attach,
        f"--cucumber-json={output_path}",
        f"--cucumber-junit={output_path}",
    )


@given(
    parsers.parse('a canonical messages NDJSON report generated at "{report_name}"'),
)
def canonical_messages_report(testdir, formatter_artifacts: dict[str, object], report_name: str, attach) -> None:
    """Handle canonical messages report."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    outputs = formatter_artifacts["outputs"]
    assert isinstance(outputs, dict)
    messages_path = output_root / report_name
    outputs[report_name] = messages_path
    result = _run_pytest_subprocess_with_attachments(testdir, attach, "--messages-ndjson", str(messages_path))
    result.assert_outcomes(passed=1, failed=1)
    assert messages_path.exists()


@when("I run the standalone cucumber formatter renderer from that NDJSON", target_fixture="renderer_result")
def run_standalone_formatter_renderer(formatter_artifacts: dict[str, object], attach):
    """Run standalone formatter renderer."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    outputs = formatter_artifacts["outputs"]
    assert isinstance(outputs, dict)
    messages_path = outputs["messages.ndjson"]
    assert isinstance(messages_path, Path)
    json_path = output_root / "standalone.json"
    usage_json_path = output_root / "standalone-usage.json"
    outputs["standalone.json"] = json_path
    outputs["standalone-usage.json"] = usage_json_path
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            [
                str(_repo_root() / "src"),
                env.get("PYTHONPATH", ""),
            ],
        ),
    )
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest_bdd.script.render_cucumber_formatters",
            "--messages-ndjson",
            str(messages_path),
            "--cucumber-summary",
            "--cucumber-json",
            str(json_path),
            "--cucumber-usage-json",
            str(usage_json_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(output_root),
        env=env,
    )
    attach_command_result_outputs(
        attach,
        result,
        label="standalone-renderer",
        command="python -m pytest_bdd.script.render_cucumber_formatters",
    )
    return result


@then(
    parsers.parse('stdout contains the user-visible line "{visible_output}"'),
)
def stdout_contains_user_visible_line(pytest_result, visible_output: str) -> None:
    """Handle stdout contains user visible line."""
    stdout = pytest_result.stdout if isinstance(pytest_result.stdout, str) else pytest_result.stdout.str()
    assert fnmatch(stdout, f"*{visible_output}*")


@then("stdout omits the default pytest terminal reporter output")
def stdout_omits_default_pytest_terminal_reporter_output(pytest_result) -> None:
    """Handle stdout omits default pytest terminal reporter output."""
    stdout = pytest_result.stdout if isinstance(pytest_result.stdout, str) else pytest_result.stdout.str()
    assert_pytest_terminal_reporter_suppressed(stdout)


@then(
    parsers.parse('stderr contains the user-visible line "{visible_output}"'),
)
def stderr_contains_user_visible_line(pytest_result, visible_output: str) -> None:
    """Handle stderr contains user visible line."""
    stderr = pytest_result.stderr if isinstance(pytest_result.stderr, str) else pytest_result.stderr.str()
    assert fnmatch(stderr, f"*{visible_output}*")


@then("the standalone renderer succeeds")
def standalone_renderer_succeeds(renderer_result: subprocess.CompletedProcess[str]) -> None:
    """Handle standalone renderer succeeds."""
    assert renderer_result.returncode == 0, renderer_result.stdout + renderer_result.stderr


@then("pytest exits with usage error")
def pytest_exits_with_usage_error(pytest_result) -> None:
    """Handle exits with usage error."""
    exit_code = getattr(pytest_result, "ret", None)
    if exit_code is None:
        exit_code = pytest_result.returncode
    assert exit_code == pytest.ExitCode.USAGE_ERROR


@then(
    parsers.parse('standalone stdout contains the user-visible line "{visible_output}"'),
)
def standalone_stdout_contains_user_visible_line(
    renderer_result: subprocess.CompletedProcess[str],
    visible_output: str,
) -> None:
    """Handle standalone stdout contains user visible line."""
    assert visible_output in renderer_result.stdout


@then(
    parsers.parse('the fake formatter stream source is "{source_mode}"'),
)
def fake_formatter_stream_source_is(
    formatter_artifacts: dict[str, object],
    source_mode: str,
) -> None:
    """Handle fake formatter stream source is."""
    output_root = formatter_artifacts["root"]
    assert isinstance(output_root, Path)
    telemetry = read_fake_formatter_telemetry(output_root)
    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == source_mode
    assert int(telemetry[0]["envelopeCount"]) > 0


@then(
    parsers.parse('file "{report_name}" contains the rendered line "{visible_output}"'),
)
def file_contains_rendered_line(
    formatter_artifacts: dict[str, object],
    report_name: str,
    visible_output: str,
) -> None:
    """Handle file contains rendered line."""
    outputs = formatter_artifacts["outputs"]
    assert isinstance(outputs, dict)
    output_path = outputs[report_name]
    assert isinstance(output_path, Path)
    assert output_path.exists()
    assert visible_output in output_path.read_text(encoding="utf-8")
