"""Installed-consumer acceptance steps for Cucumber SummaryFormatter."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, then
from pytest_cuke.model.message_stream_validation import validate_message_stream
from pytest_cuke.model.message_types import message_from_dict


_PRODUCT_ROOT = Path(__file__).resolve().parents[2]
_CUCUMBER_PACKAGES = {"@cucumber/cucumber": "13.3.0"}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_SUMMARY_FEATURE = """\
Feature: Cucumber Summary outcome projection
  Background:
    Given the summary background step passes

  Scenario Outline: A passing outline row <record>
    When the summary action passes
    Then the summary result passes

    Examples:
      | record |
      | alpha  |
      | beta   |

  Scenario: A failing scenario preserves its detail
    When the summary failure is recorded
    Then the step after the summary failure remains skipped

  Scenario: A skipped scenario is counted
    When the summary scenario deliberately skips
"""
_PASSING_FEATURE = """\
Feature: Cucumber Summary default and configuration selection
  Scenario: A passing summary consumer scenario
    Given the summary consumer scenario passes
"""
_CONFLICT_FEATURE = """\
Feature: Cucumber Summary terminal conflict
  Scenario: The marker scenario must not start before conflict validation
    Given the summary conflict scenario records that it started
"""
_SETUP_SKIP_FEATURE = """\
Feature: Cucumber Summary setup skip
  Scenario: Summary scenario skipped during pytest setup
    Given the setup-skipped summary step would execute

  Scenario: The independent summary scenario passes
    Given the summary consumer scenario passes
"""
_RETRY_FEATURE = """\
Feature: Cucumber Summary retry attempts
  Scenario: The failed first attempt passes on retry
    When the summary retry step fails once and then passes
"""
_BACKEND_FAILURE_FEATURE = """\
Feature: Cucumber Summary backend finalization failure
  Scenario: A failing scenario remains failed when the summary backend fails
    When the summary failure is recorded
"""
_PREFLIGHT_FEATURE = """\
Feature: Cucumber Summary dependency preflight
  Scenario: The scenario marker must not run without formatter dependencies
    Given the summary conflict scenario records that it started
"""
_SUPPORT_PLUGIN = """\
from pathlib import Path

import pytest
from pytest_cuke import given, then, when

ROOT = Path(__file__).parent


@pytest.fixture(autouse=True)
def skip_the_named_summary_scenario_during_setup(request):
    if "Summary scenario skipped during pytest setup" in request.node.name:
        (ROOT / "setup-fixture-ran.marker").write_text("started", encoding="utf-8")
        pytest.skip("official summary setup skip detail sentinel")


@given("the summary background step passes")
def summary_background_step_passes():
    with (ROOT / "background-executions.log").open("a", encoding="utf-8") as stream:
        stream.write("background\\n")


@when("the summary action passes")
def summary_action_passes():
    pass


@then("the summary result passes")
def summary_result_passes():
    pass


@when("the summary failure is recorded")
def summary_failure_is_recorded():
    raise AssertionError("official summary failure detail sentinel")


@then("the step after the summary failure remains skipped")
def step_after_summary_failure_remains_skipped():
    pass


@when("the summary scenario deliberately skips")
def summary_scenario_deliberately_skips():
    pytest.skip("official summary skip detail sentinel")


@given("the summary consumer scenario passes")
def summary_consumer_scenario_passes():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
    print("summary tee-sys capture sentinel")


@given("the setup-skipped summary step would execute")
def setup_skipped_summary_step_would_execute():
    (ROOT / "setup-step-ran.marker").write_text("started", encoding="utf-8")


@given("the summary conflict scenario records that it started")
def summary_conflict_scenario_records_that_it_started():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")


@when("the summary retry step fails once and then passes")
def summary_retry_step_fails_once_then_passes():
    counter = ROOT / "retry-attempt-count.txt"
    attempt = int(counter.read_text(encoding="utf-8")) if counter.exists() else 0
    counter.write_text(str(attempt + 1), encoding="utf-8")
    if attempt == 0:
        raise AssertionError("official summary retry warning sentinel")
"""
_PUBLIC_FILE_FORMATTER = """\
from pathlib import Path
import sys

from pytest_cuke.formatter_api import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    usage_json = (
        "import json, sys; "
        "rows = [json.loads(line) for line in sys.stdin if line.strip()]; "
        "usage = {'messageCount': len(rows), "
        "'testCases': sum('testCase' in row for row in rows), "
        "'finishedSteps': sum('testStepFinished' in row for row in rows)}; "
        "print(json.dumps(usage, sort_keys=True))"
    )
    command = (
        sys.executable,
        "-c",
        usage_json,
    )
    return (FormatterRequest(
        name="summary-public-api-file-probe",
        command=command,
        output_path=Path("artifacts/usage.json"),
        working_directory=Path(__file__).parent,
    ),)
"""
_SUMMARY_BACKEND_PRELOAD = """\
if (
  process.execArgv.includes("--input-type=module") &&
  process.execArgv.some((argument) => argument.includes("SummaryFormatter"))
) {
  process.once("beforeExit", () => {
    throw new Error("summary backend finalization sentinel");
  });
}
"""
_PUBLIC_TERMINAL_FORMATTER = """\
from pathlib import Path
import sys

from pytest_cuke.formatter_api import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('terminal-formatter-started.marker').write_text('started'); "
        "import sys; sys.stdin.read()",
    )
    return (FormatterRequest(
        name="summary-public-api-terminal-probe",
        command=command,
        output_path=None,
        working_directory=Path(__file__).parent,
    ),)
"""


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _safe_workspace(consumer: Any, workspace: str) -> Path:
    root = _consumer_root(consumer)
    relative = Path(workspace)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("summary consumer workspaces must stay inside the consumer project")
    destination = (root / relative).resolve()
    if root not in destination.parents and destination != root:
        raise ValueError("summary consumer workspaces must stay inside the consumer project")
    return destination


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("summary consumer files must stay inside the consumer project")
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _prepare_consumer(
    consumer: Any,
    *,
    workspace: str,
    feature: str,
    feature_name: str,
    summary_enabled: bool = False,
    public_file_formatter: bool = False,
    public_terminal_formatter: bool = False,
) -> Path:
    root = _safe_workspace(consumer, workspace)
    root.mkdir(parents=True, exist_ok=True)
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    if summary_enabled:
        config += "cuke_summary = true\n"
    _write_file(root, "pyproject.toml", config)

    plugins = ["summary_consumer_steps"]
    if public_file_formatter:
        plugins.append("summary_public_file_formatter")
        _write_file(root, "summary_public_file_formatter.py", _PUBLIC_FILE_FORMATTER)
    if public_terminal_formatter:
        plugins.append("summary_public_terminal_formatter")
        _write_file(root, "summary_public_terminal_formatter.py", _PUBLIC_TERMINAL_FORMATTER)
    _write_file(root, "conftest.py", f"pytest_plugins = {plugins!r}\n")
    _write_file(root, "summary_consumer_steps.py", _SUPPORT_PLUGIN)
    _write_file(root, f"features/{feature_name}", feature)
    (root / "artifacts").mkdir(exist_ok=True)
    consumer._summary_workspace = root
    return root


def _node_environment(consumer: Any) -> tuple[str, str, dict[str, str]] | None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None
    environment = dict(consumer.env)
    path_entries = (
        str(Path(node).parent),
        str(Path(npm).parent),
        str(Path(consumer.python).parent),
        os.defpath,
    )
    environment["PATH"] = os.pathsep.join(dict.fromkeys(path_entries))
    environment.pop("NODE_PATH", None)
    return node, npm, environment


def _install_official_summary_runtime(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the official Cucumber Summary acceptance lane requires Node.js and npm")
    _, npm, environment = runtime
    root = getattr(consumer, "_summary_workspace", _consumer_root(consumer))
    package_json = {
        "name": "pytest-cuke-summary-consumer",
        "private": True,
        "type": "module",
        "dependencies": _CUCUMBER_PACKAGES,
    }
    _write_file(root, "package.json", json.dumps(package_json, indent=2) + "\n")
    install = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert install.returncode == 0, (
        f"could not install pinned official @cucumber/cucumber@13.3.0:\n{install.stdout}\n{install.stderr}"
    )
    package_metadata = json.loads((root / "node_modules/@cucumber/cucumber/package.json").read_text(encoding="utf-8"))
    assert package_metadata.get("version") == "13.3.0", package_metadata
    consumer._summary_cucumber_version = package_metadata["version"]
    consumer.env["PATH"] = environment["PATH"]


def _install_pytest_rerunfailures(consumer: Any) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("the summary retry acceptance lane requires uv to install pytest-rerunfailures")
    install = subprocess.run(
        [uv, "pip", "install", "--python", str(consumer.python), "pytest-rerunfailures"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if install.returncode != 0:
        pytest.skip(f"pytest-rerunfailures could not be installed in the consumer:\n{install.stdout}\n{install.stderr}")


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this consumer"
    return _ANSI.sub("", f"{result.stdout}\n{result.stderr}")


def _messages(consumer: Any, relative_path: str) -> list[dict[str, Any]]:
    path = _consumer_root(consumer) / relative_path
    assert path.is_file(), f"Cucumber Messages artifact was not written: {path}"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and all(isinstance(row, dict) for row in rows), rows
    envelopes = [message_from_dict(row) for row in rows]
    diagnostics = validate_message_stream(envelopes)
    assert not diagnostics, f"invalid Cucumber Messages run finalization: {diagnostics!r}"
    return rows


def _message_link_context(consumer: Any) -> str:
    path = consumer._summary_workspace / "artifacts/messages.ndjson"
    if not path.is_file():
        return f"Messages link context unavailable; artifact was not written: {path}"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    test_cases = [row["testCase"] for row in rows if "testCase" in row]
    definitions = {row["stepDefinition"]["id"] for row in rows if "stepDefinition" in row}
    references_by_case = {
        case["id"]: sorted(
            {definition_id for step in case.get("testSteps", []) for definition_id in step.get("stepDefinitionIds", [])}
        )
        for case in test_cases
    }
    missing = {
        case_id: [definition_id for definition_id in references if definition_id not in definitions]
        for case_id, references in references_by_case.items()
    }
    missing = {case_id: ids for case_id, ids in missing.items() if ids}
    return (
        f"Messages testCase IDs={sorted(references_by_case)!r}; "
        f"stepDefinition IDs by testCase={references_by_case!r}; "
        f"missing stepDefinition IDs from Messages={missing!r}"
    )


def _summary_line(output: str, kind: str) -> str:
    pattern = re.compile(rf"\b\d+ {re.escape(kind)}s? \([^()\r\n]*\)")
    matches = [match.group(0) for match in pattern.finditer(output)]
    assert len(matches) == 1, f"expected one official Cucumber {kind} summary line, got {matches!r}:\n{output}"
    return matches[0]


def _assert_duration(output: str) -> None:
    duration = re.compile(r"\b\d+m\d{2}\.\d{3}s \(executing steps: \d+m\d{2}\.\d{3}s\)")
    matches = list(duration.finditer(output))
    assert len(matches) == 1, f"expected one official Cucumber run and step duration, got {len(matches)}:\n{output}"


def _assert_no_consumer_execution(consumer: Any) -> None:
    root = consumer._summary_workspace
    assert not (root / "scenario-started.marker").exists(), "scenario execution began before formatter preflight"


@given("the summary consumer prepares a passing feature with the default configuration")
def prepare_default_summary_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary default workspace",
        feature=_PASSING_FEATURE,
        feature_name="default-summary.feature",
    )


@given("the installed consumer PATH excludes Node.js and npm")
def hide_node_and_npm_for_summary_consumer(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@given("the installed consumer PATH exposes Node.js but excludes npm")
def expose_node_without_npm_for_summary_consumer(consumer: Any) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("the missing npm preflight lane requires Node.js")

    node_only_bin = consumer._summary_workspace / "node-only-bin"
    node_only_bin.mkdir()
    try:
        (node_only_bin / "node").symlink_to(Path(node).resolve())
    except OSError as error:
        pytest.skip(f"could not isolate Node.js from npm using a temporary PATH: {error}")

    consumer.env["PATH"] = os.pathsep.join((str(node_only_bin), str(Path(consumer.python).parent)))
    assert shutil.which("node", path=consumer.env["PATH"])
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@then("the normal consumer scenario should pass without starting the summary formatter")
def normal_consumer_passes_without_summary_runtime(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result.returncode == 0, f"default consumer run failed:\n{result.stdout}\n{result.stderr}"
    output = _output(consumer)
    assert not re.search(r"(?m)^\s*1 scenario \(1 passed\)\s*$", output), output
    root = _safe_workspace(consumer, "summary default workspace")
    assert not (root / "package.json").exists(), "the unselected formatter must not install Node packages"
    assert not (root / "terminal-formatter-started.marker").exists()


@given(
    "the summary consumer prepares a Background, two outline rows, a failure, and a skip with a public file formatter"
)
def prepare_mixed_summary_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary workspace café",
        feature=_SUMMARY_FEATURE,
        feature_name="summary-outcomes.feature",
        public_file_formatter=True,
    )


@given("the consumer installs the pinned official Cucumber Summary runtime in its workspace")
def install_official_summary_runtime(consumer: Any) -> None:
    _install_official_summary_runtime(consumer)


@given("the public Cucumber Summary example is copied to the installed consumer")
def copy_public_cucumber_summary_example(consumer: Any) -> None:
    source = _PRODUCT_ROOT / "examples" / "cucumber-summary"
    assert source.is_dir(), f"the public Cucumber Summary example is missing: {source}"
    destination = _safe_workspace(consumer, "cucumber-summary-example")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    consumer._summary_workspace = destination


@given("the summary consumer prepares a marker scenario for destination preflight")
def prepare_summary_destination_preflight_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary destination conflict workspace",
        feature=_PREFLIGHT_FEATURE,
        feature_name="destination-conflict.feature",
    )


@then("the official summary should appear on stdout and not stderr")
def official_summary_is_written_only_to_stdout(consumer: Any) -> None:
    _assert_summary_output_on_stdout(
        consumer,
        expected_scenario_summary="4 scenarios (1 failed, 1 skipped, 2 passed)",
        expected_step_summary="11 steps (1 failed, 2 skipped, 8 passed)",
    )


def _assert_summary_output_on_stdout(
    consumer: Any,
    *,
    expected_scenario_summary: str,
    expected_step_summary: str,
) -> str:
    result = consumer.pytest_result
    assert result is not None, "the installed consumer has not run"
    stdout = _ANSI.sub("", result.stdout)
    stderr = _ANSI.sub("", result.stderr)
    assert _summary_line(stdout, "scenario") == expected_scenario_summary, stdout
    assert _summary_line(stdout, "step") == expected_step_summary, stdout
    assert not re.search(r"\b\d+ scenarios? \([^()\r\n]*\)", stderr), stderr
    assert not re.search(r"\b\d+ steps? \([^()\r\n]*\)", stderr), stderr
    _assert_duration(stdout)
    return stdout


@then("the public Summary example should pass with the official summary")
def public_summary_example_passes_with_official_formatter(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, (
        f"public Summary example failed:\n{result.stdout if result else ''}\n{result.stderr if result else ''}"
    )
    assert consumer._summary_cucumber_version == "13.3.0"
    _assert_summary_output_on_stdout(
        consumer,
        expected_scenario_summary="2 scenarios (2 passed)",
        expected_step_summary="6 steps (6 passed)",
    )
    assert "2 passed" in _output(consumer), _output(consumer)


@then("duplicate summary file destinations should fail before the marker scenario runs")
def duplicate_summary_file_destination_preflights(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert consumer._summary_cucumber_version == "13.3.0"
    assert result is not None and result.returncode != 0, output
    assert "shared.json" in output, output
    assert any(token in output.lower() for token in ("same output path", "duplicate", "same path", "resolve")), output
    assert not (consumer._summary_workspace / "scenario-started.marker").exists(), output
    assert not (consumer._summary_workspace / "artifacts/shared.json").exists(), output


@then("the official Cucumber summary should report finalized scenario and step outcomes with duration")
def summary_reports_mixed_outcomes_and_duration(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result.returncode != 0, f"the failed BDD scenario should fail pytest:\n{result.stdout}\n{result.stderr}"
    output = _output(consumer)
    link_context = _message_link_context(consumer)
    try:
        scenario_summary = _summary_line(output, "scenario")
    except AssertionError as error:
        raise AssertionError(f"{error}\n{link_context}") from error
    assert scenario_summary == "4 scenarios (1 failed, 1 skipped, 2 passed)", f"{output}\n{link_context}"
    assert _summary_line(output, "step") == "11 steps (1 failed, 2 skipped, 8 passed)", f"{output}\n{link_context}"
    assert "official summary failure detail sentinel" in output, output
    assert "Failures:" in output, output
    assert re.search(r"# file:[^\r\n]*summary-outcomes\.feature:\d+", output), f"{output}\n{link_context}"
    assert re.search(r"summary_consumer_steps\.py:\d+", output), f"{output}\n{link_context}"
    assert "1 failed, 2 passed, 1 skipped" in output, "pytest's normal result summary was lost:\n" + output
    _assert_duration(output)


@then(
    "Messages, Cucumber JSON, JUnit XML, and the public FormatterRequest usage JSON should agree on four execution cases"
)
def summary_artifacts_agree_on_execution_cases(consumer: Any) -> None:
    root = consumer._summary_workspace
    rows = _messages(consumer, "summary workspace café/artifacts/messages.ndjson")
    assert rows[-1].get("testRunFinished") is not None, "Summary should finish from the finalized Messages stream"
    assert sum("pickle" in row for row in rows) == 4
    assert sum("testCase" in row for row in rows) == 4
    assert sum("testCaseStarted" in row for row in rows) == 4
    assert sum("testCaseFinished" in row for row in rows) == 4
    assert sum("testStepFinished" in row for row in rows) == 11
    step_status_counts: dict[str, int] = {}
    for row in rows:
        step_finished = row.get("testStepFinished")
        if step_finished is None:
            continue
        status = step_finished["testStepResult"]["status"]
        step_status_counts[status] = step_status_counts.get(status, 0) + 1
    assert step_status_counts == {"PASSED": 8, "FAILED": 1, "SKIPPED": 2}, step_status_counts

    report = json.loads((root / "artifacts/report.json").read_text(encoding="utf-8"))
    assert len(report) == 1, report
    elements = report[0]["elements"]
    assert len(elements) == 4, elements
    outline_name = "A passing outline row <record>"
    failure_name = "A failing scenario preserves its detail"
    skip_name = "A skipped scenario is counted"
    outline_elements = [element for element in elements if element["name"].startswith(outline_name)]
    assert len(outline_elements) == 2, elements
    assert [element["name"] for element in elements].count(failure_name) == 1, elements
    assert [element["name"] for element in elements].count(skip_name) == 1, elements

    outline_row_lines = set()
    for element in outline_elements:
        row_line = re.search(r"table_rows:\[line: (\d+)\]", element["name"])
        assert row_line is not None, element["name"]
        outline_row_lines.add(row_line.group(1))
        assert [step["result"]["status"] for step in element["steps"]] == ["passed", "passed", "passed"], element
    assert outline_row_lines == {"11", "12"}, outline_elements

    failure_element = next(element for element in elements if element["name"] == failure_name)
    assert [step["name"] for step in failure_element["steps"]] == [
        "the summary background step passes",
        "the summary failure is recorded",
        "the step after the summary failure remains skipped",
    ], failure_element
    assert [step["result"]["status"] for step in failure_element["steps"]] == ["passed", "failed", "skipped"], (
        failure_element
    )

    skip_element = next(element for element in elements if element["name"] == skip_name)
    assert [step["name"] for step in skip_element["steps"]] == [
        "the summary background step passes",
        "the summary scenario deliberately skips",
    ], skip_element
    assert [step["result"]["status"] for step in skip_element["steps"]] == ["passed", "skipped"], skip_element

    junit_root = ET.parse(root / "artifacts/junit.xml").getroot()
    suites = [junit_root] if junit_root.tag == "testsuite" else list(junit_root.findall("testsuite"))
    assert len(suites) == 1, ET.tostring(junit_root, encoding="unicode")
    assert suites[0].attrib.get("tests") == "4", suites[0].attrib
    assert suites[0].attrib.get("failures") == "1", suites[0].attrib
    assert suites[0].attrib.get("skipped") == "1", suites[0].attrib

    usage_report = root / "artifacts/usage.json"
    assert usage_report.is_file(), "the public FormatterRequest did not write its distinct usage JSON artifact"
    usage = json.loads(usage_report.read_text(encoding="utf-8"))
    assert usage["messageCount"] > 0, usage
    assert usage["testCases"] == 4, usage
    assert usage["finishedSteps"] == 11, usage
    assert (root / "background-executions.log").read_text(encoding="utf-8").splitlines() == [
        "background",
        "background",
        "background",
        "background",
    ]


@then("the built-in Usage JSON should contain the used summary background definition")
def built_in_usage_json_contains_summary_background(consumer: Any) -> None:
    path = consumer._summary_workspace / "artifacts/cucumber-usage.json"
    assert path.is_file(), f"the built-in Usage JSON artifact was not written: {path}"
    usage = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(usage, list) and all(isinstance(definition, dict) for definition in usage), usage
    matches = [definition for definition in usage if definition.get("pattern") == "the summary background step passes"]
    assert len(matches) == 1, matches
    definition = matches[0]
    assert definition.get("patternType") == "CucumberExpression", definition
    assert isinstance(definition.get("uri"), str) and definition["uri"].endswith("summary_consumer_steps.py"), (
        definition
    )
    assert isinstance(definition.get("line"), int) and definition["line"] > 0, definition
    assert isinstance(definition.get("matches"), list), definition
    assert len(definition["matches"]) == 4, definition
    assert [match.get("text") for match in definition["matches"]] == [
        "the summary background step passes",
        "the summary background step passes",
        "the summary background step passes",
        "the summary background step passes",
    ], definition


@given("the summary consumer prepares a passing feature with cuke_summary enabled in configuration")
def prepare_configured_summary_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary config workspace",
        feature=_PASSING_FEATURE,
        feature_name="configured-summary.feature",
        summary_enabled=True,
    )


@then("the official Cucumber summary should report one passed scenario and one passed step with duration")
def summary_reports_configured_pass_and_duration(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result.returncode == 0, f"configured summary consumer failed:\n{result.stdout}\n{result.stderr}"
    output = _output(consumer)
    assert _summary_line(output, "scenario") == "1 scenario (1 passed)", output
    assert _summary_line(output, "step") == "1 step (1 passed)", output
    assert "summary tee-sys capture sentinel" in output, output
    _assert_duration(output)


@then("verbose tee-sys output should forward the consumer step and the summary once")
def verbose_tee_sys_forwards_summary_once(consumer: Any) -> None:
    output = _output(consumer)
    assert output.count("summary tee-sys capture sentinel") == 1, output
    assert len(re.findall(r"\b1 scenario \(1 passed\)", output)) == 1, output
    assert len(re.findall(r"\b1 step \(1 passed\)", output)) == 1, output
    assert "test_scenarios" in output, f"verbose pytest output was not forwarded:\n{output}"


@given("the summary consumer prepares a terminal conflict marker scenario and a public terminal formatter")
def prepare_summary_terminal_conflict_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary conflict workspace",
        feature=_CONFLICT_FEATURE,
        feature_name="terminal-conflict.feature",
        public_terminal_formatter=True,
    )


@then("the competing terminal formatter should be rejected before formatting or scenario execution")
def competing_terminal_formatter_is_rejected_before_execution(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result.returncode != 0, f"terminal formatter conflict unexpectedly passed:\n{result.stdout}\n{result.stderr}"
    output = _output(consumer)
    assert "terminal" in output.lower() and "formatter" in output.lower(), output
    assert "summary-public-api-terminal-probe" in output, output
    root = consumer._summary_workspace
    assert not (root / "terminal-formatter-started.marker").exists()
    assert not (root / "scenario-started.marker").exists()
    assert " scenarios (" not in output, output


@given("the summary consumer prepares one setup-time skip and one passing scenario")
def prepare_summary_setup_skip_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary setup-skip workspace",
        feature=_SETUP_SKIP_FEATURE,
        feature_name="setup-skip.feature",
    )


@then("the official Cucumber summary should count the setup-time skip and passing scenario")
def summary_counts_setup_time_skip(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result.returncode == 0, f"setup-skip consumer failed:\n{result.stdout}\n{result.stderr}"
    output = _output(consumer)
    assert _summary_line(output, "scenario") == "2 scenarios (1 skipped, 1 passed)", output
    assert _summary_line(output, "step") == "2 steps (1 skipped, 1 passed)", output
    _assert_duration(output)
    root = consumer._summary_workspace
    assert (root / "setup-fixture-ran.marker").is_file()
    assert not (root / "setup-step-ran.marker").exists(), "the setup-skipped step body must not run"
    assert (root / "scenario-started.marker").is_file(), "the independent passing scenario did not run"
    rows = _messages(consumer, "summary setup-skip workspace/artifacts/messages.ndjson")
    assert rows[-1].get("testRunFinished") is not None


@given("the summary consumer prepares a dependency preflight marker scenario without runtime packages")
def prepare_summary_dependency_preflight_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary dependency preflight workspace",
        feature=_PREFLIGHT_FEATURE,
        feature_name="dependency-preflight.feature",
    )


@then("the selected summary runtime failure should identify missing Node.js before execution")
def selected_summary_without_node_fails_before_execution(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result.returncode != 0, f"selected summary unexpectedly passed without Node.js:\n{output}"
    assert "cucumber-summary" in output.lower(), output
    assert "node" in output.lower(), output
    _assert_no_consumer_execution(consumer)
    assert not (consumer._summary_workspace / "package.json").exists()


@then("the selected summary runtime failure should identify missing npm before execution")
def selected_summary_without_npm_fails_before_execution(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result.returncode != 0, f"selected summary unexpectedly passed without npm:\n{output}"
    assert "cucumber-summary" in output.lower(), output
    assert "npm" in output.lower(), output
    _assert_no_consumer_execution(consumer)
    assert not (consumer._summary_workspace / "package.json").exists()


@given("the consumer PATH exposes Node.js and npm without installing the Cucumber Summary package")
def expose_node_without_summary_package(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the missing Cucumber package preflight lane requires Node.js and npm")
    _, _, environment = runtime
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)
    assert not (consumer._summary_workspace / "node_modules/@cucumber/cucumber").exists()


@then("the selected summary runtime failure should identify the missing Cucumber package before execution")
def selected_summary_without_package_fails_before_execution(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result.returncode != 0, f"selected summary unexpectedly passed without its npm package:\n{output}"
    assert "cucumber-summary" in output.lower(), output
    assert "@cucumber/cucumber" in output, output
    assert any(
        marker in output.lower() for marker in ("requires", "cannot find", "not found", "err_module_not_found")
    ), output
    _assert_no_consumer_execution(consumer)
    assert not (consumer._summary_workspace / "package.json").exists()


@given("the summary consumer prepares a scenario that fails once and passes on retry")
def prepare_summary_retry_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary retry workspace",
        feature=_RETRY_FEATURE,
        feature_name="retry-outcomes.feature",
    )


@given("the summary consumer installs pytest-rerunfailures")
def install_summary_rerun_plugin(consumer: Any) -> None:
    _install_pytest_rerunfailures(consumer)


@given("the summary consumer prepares one failing scenario for backend finalization")
def prepare_summary_backend_failure_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        workspace="summary-backend-error",
        feature=_BACKEND_FAILURE_FEATURE,
        feature_name="backend-finalization.feature",
    )


@given("the summary consumer installs a Node preload that fails during SummaryFormatter finalization")
def install_summary_backend_failure_preload(consumer: Any) -> None:
    root = consumer._summary_workspace
    preload = _write_file(root, "fail-summary-backend.cjs", _SUMMARY_BACKEND_PRELOAD)
    consumer.env["NODE_OPTIONS"] = f"--require={preload.resolve()}"


@then("the official summary should count the final retry as passed and the earlier attempt as a warning")
def summary_counts_only_final_retry_attempt(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result.returncode == 0, f"the retried summary scenario should pass:\n{output}"
    assert _summary_line(output, "scenario") == "1 scenario (1 passed)", output
    assert _summary_line(output, "step") == "1 step (1 passed)", output
    assert "Warnings:" in output, output
    assert "official summary retry warning sentinel" in output, output
    _assert_duration(output)


@then("the Messages artifact should contain one test case with both retry attempts and their outcomes")
def messages_keep_one_summary_retry_test_case(consumer: Any) -> None:
    rows = _messages(consumer, "summary retry workspace/artifacts/messages.ndjson")
    assert rows[-1].get("testRunFinished") is not None
    test_cases = [row["testCase"] for row in rows if "testCase" in row]
    assert len(test_cases) == 1, test_cases
    test_case_id = test_cases[0]["id"]
    started = [row["testCaseStarted"] for row in rows if "testCaseStarted" in row]
    finished = {
        row["testCaseFinished"]["testCaseStartedId"]: row["testCaseFinished"]
        for row in rows
        if "testCaseFinished" in row
    }
    assert len(started) == 2, started
    assert len(finished) == 2, finished
    attempts = sorted(started, key=lambda item: item["attempt"])
    assert [attempt.get("attempt") for attempt in attempts] == [0, 1], attempts
    assert [attempt["testCaseId"] for attempt in attempts] == [test_case_id, test_case_id], attempts
    assert [finished[item["id"]].get("willBeRetried") for item in attempts] == [True, False], finished

    statuses_by_attempt: dict[str, list[str]] = {item["id"]: [] for item in attempts}
    for row in rows:
        step_finished = row.get("testStepFinished")
        if step_finished is not None:
            statuses_by_attempt[step_finished["testCaseStartedId"]].append(step_finished["testStepResult"]["status"])
    assert [statuses_by_attempt[item["id"]] for item in attempts] == [["FAILED"], ["PASSED"]], statuses_by_attempt


@then("the Summary backend failure should be visible beside one failed scenario")
def summary_backend_failure_is_visible_without_success(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result.returncode != 0, f"the failed scenario and formatter backend error must fail pytest:\n{output}"
    assert "summary backend finalization sentinel" in output, output
    assert "official summary failure detail sentinel" in output, output
    assert _summary_line(output, "scenario") == "1 scenario (1 failed)", output
    assert _summary_line(output, "step") == "1 step (1 failed)", output
    _assert_duration(output)


@then("the Messages artifact should retain one failed scenario and an unsuccessful test run")
def messages_retain_failure_when_summary_backend_fails(consumer: Any) -> None:
    rows = _messages(consumer, "summary-backend-error/artifacts/messages.ndjson")
    assert rows[-1].get("testRunFinished") is not None, rows[-1]
    assert rows[-1]["testRunFinished"].get("success") is False, rows[-1]
    assert sum("testCase" in row for row in rows) == 1
    assert sum("testCaseStarted" in row for row in rows) == 1
    assert sum("testCaseFinished" in row for row in rows) == 1
    results = [row["testStepFinished"]["testStepResult"]["status"] for row in rows if "testStepFinished" in row]
    assert results == ["FAILED"], results
