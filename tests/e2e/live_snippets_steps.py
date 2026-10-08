"""Installed-consumer BDD steps for official Cucumber undefined-step snippets."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, step, then


_OFFICIAL_CUCUMBER_PACKAGES = {"@cucumber/cucumber": "13.3.0"}
_USAGE_JSON_PLUGIN = """\
import json
import sys
from pathlib import Path

from pytest_cuke import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    command = (
        sys.executable,
        "-c",
        "import collections,json,sys; counts=collections.Counter(); "
        "[counts.update(json.loads(line).keys()) for line in sys.stdin if line.strip()]; "
        "print(json.dumps({'event_counts': dict(counts)}))",
    )
    return (FormatterRequest(
        name="snippets-usage-json-probe",
        command=command,
        output_path=Path("artifacts/usage.json"),
        working_directory=Path(__file__).parent,
    ),)
"""
_MIXED_UNDEFINED_FEATURE = """\
Feature: Official Cucumber snippets use Messages metadata
  Scenario: A defined control step runs normally
    Given a snippet control step that records normal execution

  Scenario: An undefined Given with a quoted parameter produces a snippet
    Given a customer named "Zoë" is registered

  Scenario: An undefined When with a numeric parameter produces a snippet
    When the customer waits 42 seconds

  Scenario: An undefined Then with a numeric parameter produces a snippet
    Then the customer receives 3 results

  Scenario: A custom parameter type is available for a snippet
    Given the selected shade is cobalt
"""
_DEFAULT_UNDEFINED_FEATURE = """\
Feature: Snippets are inactive by default
  Scenario: An undefined step remains a normal pytest failure
    Given this customer has no implementation
"""
_PREFLIGHT_FEATURE = """\
Feature: Snippets dependency preflight
  Scenario: The scenario must not start before backend dependencies are checked
    Given a snippets preflight scenario records that it started
"""
_CONFLICT_FEATURE = """\
Feature: Snippets terminal formatter conflict
  Scenario: The scenario must not start when stdout formatters conflict
    Given a snippets preflight scenario records that it started
"""
_SUPPORT_PLUGIN = """\
from pathlib import Path

import pytest
from cucumber_expressions.parameter_type import ParameterType
from pytest_cuke import given, parsers


ROOT = Path(__file__).parent


def record_custom_shade_transform(value):
    (ROOT / "custom-shade-transformer-ran.marker").write_text(value, encoding="utf-8")
    return value


@pytest.fixture
def parameter_type_registry(parameter_type_registry):
    if parameter_type_registry.lookup_by_type_name("shade") is None:
        parameter_type_registry.define_parameter_type(
            ParameterType(
                name="shade",
                regexp=r"(?:cobalt|crimson)",
                type=str,
                transformer=record_custom_shade_transform,
                use_for_snippets=True,
                prefer_for_regexp_match=True,
            )
        )
    return parameter_type_registry


@given(
    parsers.cucumber_expression("the unused shade probe accepts {shade}"),
    anonymous_group_names=["shade"],
)
def unused_shade_probe(shade):
    (ROOT / "unused-shade-probe-ran.marker").write_text(shade, encoding="utf-8")


@given("a snippet control step that records normal execution")
def snippet_control_step_records_normal_execution():
    (ROOT / "control-step-ran.marker").write_text("ran", encoding="utf-8")


@given("a snippets preflight scenario records that it started")
def snippets_preflight_scenario_records_that_it_started():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""
_STDOUT_CONFLICT_PLUGIN = """\
import sys
from pathlib import Path

from pytest_cuke import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('stdout-formatter-started.marker').write_text('started'); "
        "import sys; sys.stdin.read()",
    )
    return (FormatterRequest(
        name="snippet-terminal-conflict-probe",
        command=command,
        output_path=None,
        working_directory=Path(__file__).parent,
    ),)
"""


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _safe_workspace(consumer: Any, workspace: str | None = None) -> Path:
    root = _consumer_root(consumer)
    relative = Path(workspace) if workspace else Path(".")
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("snippets consumer workspace must stay inside the consumer project")
    destination = (root / relative).resolve()
    if root not in destination.parents and destination != root:
        raise ValueError("snippets consumer workspace must stay inside the consumer project")
    return destination


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("snippets consumer files must stay inside the consumer project")
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _prepare_consumer(
    consumer: Any,
    feature: str,
    *,
    feature_name: str,
    workspace: str | None = None,
    snippets_enabled: bool = False,
    terminal_conflict: bool = False,
    usage_json: bool = False,
) -> Path:
    root = _safe_workspace(consumer, workspace)
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    if snippets_enabled:
        config += "cuke_snippets = true\n"
    _write_file(root, "pyproject.toml", config)
    plugins = ["snippets_consumer_steps"]
    if usage_json:
        plugins.append("snippets_usage_json_formatter")
        _write_file(root, "snippets_usage_json_formatter.py", _USAGE_JSON_PLUGIN)
    if terminal_conflict:
        plugins.append("snippets_stdout_conflict")
        _write_file(root, "snippets_stdout_conflict.py", _STDOUT_CONFLICT_PLUGIN)
    _write_file(root, "conftest.py", f"pytest_plugins = {plugins!r}\n")
    _write_file(root, "snippets_consumer_steps.py", _SUPPORT_PLUGIN)
    _write_file(root, f"features/{feature_name}", feature)
    (root / "artifacts").mkdir(exist_ok=True)
    consumer._snippets_workspace = root
    return root


def _node_environment(consumer: Any) -> tuple[str, str, dict[str, str]] | None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None
    environment = dict(consumer.env)
    environment["PATH"] = os.pathsep.join(
        dict.fromkeys(
            (
                str(Path(node).parent),
                str(Path(npm).parent),
                str(Path(consumer.python).parent),
                os.defpath,
            )
        )
    )
    environment.pop("NODE_PATH", None)
    return node, npm, environment


def _install_official_cucumber(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the official Cucumber snippets acceptance lane requires Node.js and npm")
    node, npm, environment = runtime
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    package_json = {
        "name": "pytest-cuke-snippets-consumer",
        "private": True,
        "type": "module",
        "dependencies": _OFFICIAL_CUCUMBER_PACKAGES,
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
        f"could not install pinned official @cucumber/cucumber packages:\n{install.stdout}\n{install.stderr}"
    )
    consumer.env["PATH"] = environment["PATH"]
    consumer._snippets_node = node


def _run_pytest(consumer: Any, arguments: str, *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [str(consumer.pytest), *shlex.split(arguments)]
    result = subprocess.run(
        command,
        cwd=cwd or _consumer_root(consumer),
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    consumer.pytest_result = result
    return result


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this consumer"
    return f"{result.stdout}\n{result.stderr}"


def _assert_pytest_undefined_failure(consumer: Any) -> str:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, f"undefined steps must keep pytest failing:\n{output}"
    assert re.search(r"(?m)^=+ FAILURES =+$", output), f"pytest's failure section was lost:\n{output}"
    assert re.search(r"(?im)^=+\s*short test summary info\s*=+\s*$", output), (
        f"pytest's short failure summary was lost:\n{output}"
    )
    assert "StepDefinitionNotFoundError" in output or "step definition is not found" in output.lower(), output
    return output


def _snippet_output(output: str) -> str:
    declarations = list(re.finditer(r"(?://\s*)?(?:Given|When|Then|And|But)\(['\"]", output))
    assert declarations, f"the official Cucumber formatter emitted no step declarations:\n{output}"
    start = declarations[0].start()
    end = output.find("});", declarations[-1].start())
    assert end >= 0, f"the final JavaScript snippet did not close:\n{output}"
    return output[start : end + len("});")]


def _assert_official_js_snippets(consumer: Any, *, expected_count: int) -> str:
    output = _assert_pytest_undefined_failure(consumer)
    snippet_output = _snippet_output(output)
    assert "function (" in snippet_output and "return 'pending';" in snippet_output, (
        f"the real Cucumber runtime did not emit JavaScript snippet bodies:\n{snippet_output}"
    )
    assert "def " not in snippet_output, (
        f"the snippets should use the official JavaScript output language:\n{snippet_output}"
    )
    assert snippet_output.count("function (") == expected_count, (
        "expected one readable function body per undefined step, "
        f"got {snippet_output.count('function (')}:\n{snippet_output}"
    )
    assert "\ufffd" not in snippet_output, f"Unicode output was not preserved:\n{snippet_output}"
    assert "a snippet control step that records normal execution" not in snippet_output, snippet_output
    return output


def _assert_selected_snippets_and_messages(consumer: Any) -> None:
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    output = _assert_official_js_snippets(consumer, expected_count=6)
    snippet_output = _snippet_output(output)
    for expression in (
        "a customer named {string} is registered",
        "the customer waits {int} seconds",
        "the customer waits {float} seconds",
        "the customer receives {int} results",
        "the customer receives {float} results",
        "the selected shade is {shade}",
    ):
        assert snippet_output.count(expression) == 1, (
            f"expected one Cucumber expression {expression!r}:\n{snippet_output}"
        )
    assert "Given('a snippet control step that records normal execution'" not in snippet_output
    assert (root / "control-step-ran.marker").is_file(), "the defined control step should run normally"
    assert not (root / "custom-shade-transformer-ran.marker").exists(), (
        "snippet generation must use parameter metadata without invoking user transformers"
    )
    assert not (root / "unused-shade-probe-ran.marker").exists(), (
        "snippet generation must not invoke the user step definition registered for custom-type metadata"
    )

    messages_path = root / "artifacts" / "messages.ndjson"
    assert messages_path.is_file(), f"the selected snippets formatter blocked a distinct Messages file: {messages_path}"
    envelopes = [json.loads(line) for line in messages_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    undefined_steps = [
        row["testStepFinished"]
        for row in envelopes
        if "testStepFinished" in row and row["testStepFinished"].get("testStepResult", {}).get("status") == "UNDEFINED"
    ]
    assert len(undefined_steps) == 4, f"Messages should retain all four undefined steps: {undefined_steps!r}"
    shade_types = [
        row["parameterType"]
        for row in envelopes
        if "parameterType" in row and row["parameterType"].get("name") == "shade"
    ]
    assert shade_types and shade_types[0].get("useForSnippets") is True, (
        f"custom parameter type metadata was absent from Messages: {shade_types!r}"
    )


def _assert_distinct_file_reports(consumer: Any) -> None:
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))

    cucumber_json_path = root / "artifacts" / "report.json"
    assert cucumber_json_path.is_file() and cucumber_json_path.stat().st_size > 0, cucumber_json_path
    cucumber_report = json.loads(cucumber_json_path.read_text(encoding="utf-8"))
    assert isinstance(cucumber_report, (dict, list)) and cucumber_report, cucumber_report

    junit_path = root / "artifacts" / "junit.xml"
    assert junit_path.is_file() and junit_path.stat().st_size > 0, junit_path
    junit_root = ET.parse(junit_path).getroot()
    assert junit_root.tag in {"testsuite", "testsuites"}, junit_root.tag
    test_count = int(junit_root.get("tests", "0"))
    if junit_root.tag == "testsuites":
        test_count += sum(int(suite.get("tests", "0")) for suite in junit_root.findall("testsuite"))
    assert test_count >= 5, f"JUnit should report all five consumer scenarios: {test_count}"

    usage_path = root / "artifacts" / "usage.json"
    assert usage_path.is_file() and usage_path.stat().st_size > 0, usage_path
    usage_report = json.loads(usage_path.read_text(encoding="utf-8"))
    event_counts = usage_report.get("event_counts")
    assert isinstance(event_counts, dict) and event_counts.get("testRunFinished") == 1, usage_report


@given("the consumer prepares an undefined-step snippets scenario with the default configuration")
def prepare_default_undefined_snippets_scenario(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _DEFAULT_UNDEFINED_FEATURE,
        feature_name="undefined-snippets-default.feature",
    )


@given("Node.js and npm are unavailable to the consumer")
def node_and_npm_are_unavailable_to_consumer(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@then("the undefined-step failure should remain and no snippet backend should be requested")
def default_snippets_are_inert_and_keep_pytest_failure(consumer: Any) -> None:
    output = _assert_pytest_undefined_failure(consumer)
    assert "function (" not in output and "return 'pending';" not in output, (
        f"snippets were emitted without opt-in:\n{output}"
    )
    assert "@cucumber/cucumber" not in output and "npm install" not in output.lower(), output
    assert not (_consumer_root(consumer) / "node_modules").exists(), "default selection must not install a Node backend"


@given("the consumer prepares mixed undefined-step snippets in a Unicode workspace with spaces")
def prepare_mixed_snippets_in_unicode_workspace(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _MIXED_UNDEFINED_FEATURE,
        feature_name="official-cucumber-snippets.feature",
        workspace="snippet workspace 東京 café",
        usage_json=True,
    )


@given("the consumer installs the pinned official Cucumber snippets runtime in that workspace")
def install_pinned_official_cucumber_snippets_runtime(consumer: Any) -> None:
    _install_official_cucumber(consumer)


@then("the CLI selection should emit usable JavaScript snippets and preserve the undefined failure")
def cli_snippets_are_javascript_and_preserve_undefined(consumer: Any) -> None:
    _assert_selected_snippets_and_messages(consumer)
    _assert_distinct_file_reports(consumer)


@step("the consumer enables cuke_snippets in its configuration")
def enable_snippets_in_consumer_configuration(consumer: Any) -> None:
    root = getattr(consumer, "_snippets_workspace", None)
    assert isinstance(root, Path), "the snippets workspace must be prepared before enabling the ini option"
    config_path = root / "pyproject.toml"
    config = config_path.read_text(encoding="utf-8")
    assert "cuke_snippets = true" not in config
    config_path.write_text(config + "cuke_snippets = true\n", encoding="utf-8")
    (root / "artifacts" / "messages.ndjson").unlink(missing_ok=True)


@then(
    "the configuration selection should emit each JavaScript expression alternative once and preserve the undefined failure"
)
def configured_snippets_are_javascript_and_preserve_undefined(consumer: Any) -> None:
    _assert_selected_snippets_and_messages(consumer)


@given("the consumer prepares a snippets backend preflight marker scenario")
def prepare_snippets_backend_preflight(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _PREFLIGHT_FEATURE,
        feature_name="snippets-backend-preflight.feature",
    )


@given("Node.js and npm are available but the official Cucumber snippets package is absent")
def node_and_npm_are_available_without_cucumber_snippets(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the missing Cucumber package preflight lane requires Node.js and npm")
    _, _, environment = runtime
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    package = root / "node_modules" / "@cucumber" / "cucumber"
    assert not package.exists(), f"fresh consumer unexpectedly contains {package}"
    consumer.env.update(environment)


@then("missing Cucumber snippets package preflight should be actionable and happen before execution")
def missing_cucumber_package_fails_before_scenario(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "requires npm package '@cucumber/cucumber'" in output, output
    assert "npm install @cucumber/cucumber" in output.lower(), output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the test scenario ran before missing @cucumber/cucumber was rejected"
    )


@then("missing Node.js snippets preflight should be actionable and happen before execution")
def missing_node_cucumber_preflight_fails_before_scenario(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "requires executable 'node', but it was not found on PATH" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the test scenario ran before missing Node.js was rejected"
    )


@given("the consumer prepares a terminal formatter conflict marker scenario")
def prepare_snippets_terminal_formatter_conflict(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _CONFLICT_FEATURE,
        feature_name="snippets-terminal-conflict.feature",
        terminal_conflict=True,
    )


@then("the snippets terminal conflict should be rejected before formatter or scenario execution")
def snippets_terminal_conflict_is_preflighted(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "Only one live formatter may write to the terminal" in output, output
    root = _consumer_root(consumer)
    assert not (root / "scenario-started.marker").exists(), (
        "the scenario ran before terminal formatter conflict validation"
    )
    assert not (root / "stdout-formatter-started.marker").exists(), (
        "the competing stdout formatter launched before terminal formatter conflict validation"
    )
