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
from pytest_cuke import given, parsers, step, then, when
from tests.support.testing_utils import mask_npm_package_from_node_resolution


_OFFICIAL_CUCUMBER_PACKAGES = {"@cucumber/cucumber": "13.3.0"}
_MIXED_SNIPPET_EXPRESSIONS = (
    ("Given", "a customer named {string} is registered"),
    ("When", "the customer waits {int} seconds"),
    ("When", "the customer waits {float} seconds"),
    ("Then", "the customer receives {int} results"),
    ("Then", "the customer receives {float} results"),
    ("Given", "the selected shade is {shade}"),
)
_USAGE_JSON_PLUGIN = """\
import json
import sys
from pathlib import Path

from pytest_cuke.formatter_api import FormatterRequest


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
    print("snippets passing-step stdout sentinel", flush=True)


@given("a snippets preflight scenario records that it started")
def snippets_preflight_scenario_records_that_it_started():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""
_STDOUT_CONFLICT_PLUGIN = """\
import sys
from pathlib import Path

from pytest_cuke.formatter_api import FormatterRequest


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
    package_metadata = root / "node_modules" / "@cucumber" / "cucumber" / "package.json"
    installed_version = json.loads(package_metadata.read_text(encoding="utf-8")).get("version")
    assert installed_version == _OFFICIAL_CUCUMBER_PACKAGES["@cucumber/cucumber"], (
        f"expected the pinned official @cucumber/cucumber version, got {installed_version!r}"
    )
    consumer.env["PATH"] = environment["PATH"]
    consumer._snippets_node = node
    consumer._snippets_cucumber_version = installed_version


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


def _assert_pytest_undefined_failure(
    consumer: Any,
    *,
    expected_failure_count: int,
    expected_pass_count: int = 0,
) -> str:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, f"undefined steps must keep pytest failing:\n{output}"
    assert re.search(r"(?m)^=+ FAILURES =+$", output), f"pytest's failure section was lost:\n{output}"
    assert re.search(r"(?im)^=+\s*short test summary info\s*=+\s*$", output), (
        f"pytest's short failure summary was lost:\n{output}"
    )
    assert "StepDefinitionNotFoundError" in output or "step definition is not found" in output.lower(), output
    summary_lines = [
        line.strip()
        for line in output.splitlines()
        if re.search(r"\b\d+ failed\b", line) and re.search(r"\bin \d+(?:\.\d+)?s\b", line)
    ]
    assert len(summary_lines) == 1, f"pytest's normal result summary should appear once:\n{output}"
    summary = summary_lines[0]
    assert re.search(rf"\b{expected_failure_count} failed\b", summary), summary
    if expected_pass_count:
        assert re.search(rf"\b{expected_pass_count} passed\b", summary), summary
    else:
        assert not re.search(r"\b\d+ passed\b", summary), summary
    return output


def _snippet_output(output: str) -> str:
    declarations = list(re.finditer(r"(?://\s*)?(?:Given|When|Then|And|But)\(['\"]", output))
    assert declarations, f"the official Cucumber formatter emitted no step declarations:\n{output}"
    start = declarations[0].start()
    end = output.find("});", declarations[-1].start())
    assert end >= 0, f"the final JavaScript snippet did not close:\n{output}"
    return output[start : end + len("});")]


def _assert_keyworded_snippets(
    snippet_output: str,
    expected_keyword_expressions: tuple[tuple[str, str], ...],
) -> None:
    for keyword, expression in expected_keyword_expressions:
        pattern = re.compile(rf"(?m)^\s*(?://\s*)?{keyword}\(\s*(['\"]){re.escape(expression)}\1\s*,\s*function\s*\(")
        matches = list(pattern.finditer(snippet_output))
        assert len(matches) == 1, (
            f"expected exactly one {keyword} snippet for {expression!r}, got {len(matches)}:\n{snippet_output}"
        )


def _assert_official_js_snippets(
    consumer: Any,
    *,
    expected_count: int,
    expected_failure_count: int = 4,
    expected_pass_count: int = 1,
    expected_keyword_expressions: tuple[tuple[str, str], ...] = (),
    defined_step_not_suggested: str | None = "a snippet control step that records normal execution",
) -> str:
    _assert_pytest_undefined_failure(
        consumer,
        expected_failure_count=expected_failure_count,
        expected_pass_count=expected_pass_count,
    )
    result = consumer.pytest_result
    assert result is not None
    snippet_pattern = re.compile(r"(?://\s*)?(?:Given|When|Then|And|But)\(['\"]")
    assert snippet_pattern.search(result.stdout), (
        "the official Cucumber snippets should be written to stdout:\n"
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert not snippet_pattern.search(result.stderr), (
        "the official Cucumber snippets must not be written to stderr:\n"
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    snippet_output = _snippet_output(result.stdout)
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
    if defined_step_not_suggested is not None:
        assert defined_step_not_suggested not in snippet_output, snippet_output
    _assert_keyworded_snippets(snippet_output, expected_keyword_expressions)
    return snippet_output


def _assert_selected_snippets_and_messages(consumer: Any) -> None:
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    _assert_official_js_snippets(
        consumer,
        expected_count=6,
        expected_keyword_expressions=_MIXED_SNIPPET_EXPRESSIONS,
    )
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
    assert isinstance(cucumber_report, list) and len(cucumber_report) == 1, cucumber_report
    feature = cucumber_report[0]
    assert feature.get("name") == "Official Cucumber snippets use Messages metadata", feature
    scenarios = feature.get("elements")
    assert isinstance(scenarios, list) and len(scenarios) == 5, scenarios
    expected_scenarios = {
        "A defined control step runs normally": (
            "Given",
            "a snippet control step that records normal execution",
            "passed",
        ),
        "An undefined Given with a quoted parameter produces a snippet": (
            "Given",
            'a customer named "Zoë" is registered',
            "undefined",
        ),
        "An undefined When with a numeric parameter produces a snippet": (
            "When",
            "the customer waits 42 seconds",
            "undefined",
        ),
        "An undefined Then with a numeric parameter produces a snippet": (
            "Then",
            "the customer receives 3 results",
            "undefined",
        ),
        "A custom parameter type is available for a snippet": (
            "Given",
            "the selected shade is cobalt",
            "undefined",
        ),
    }
    assert {scenario.get("name") for scenario in scenarios} == set(expected_scenarios), scenarios
    for scenario in scenarios:
        steps = scenario.get("steps")
        assert isinstance(steps, list) and len(steps) == 1, scenario
        step = steps[0]
        assert (step.get("keyword", "").strip(), step.get("name"), step.get("result", {}).get("status")) == (
            *expected_scenarios[scenario["name"]],
        ), scenario

    junit_path = root / "artifacts" / "junit.xml"
    assert junit_path.is_file() and junit_path.stat().st_size > 0, junit_path
    junit_root = ET.parse(junit_path).getroot()
    assert junit_root.tag in {"testsuite", "testsuites"}, junit_root.tag
    junit_suites = [suite for suite in junit_root.iter() if suite.tag == "testsuite"]
    assert len(junit_suites) == 1, [suite.attrib for suite in junit_suites]
    junit_counts = {
        attribute: sum(int(suite.get(attribute, "0")) for suite in junit_suites)
        for attribute in ("tests", "failures", "errors")
    }
    assert junit_counts == {"tests": 5, "failures": 4, "errors": 0}, junit_counts
    failure_entries = list(junit_root.iter("failure"))
    assert len(failure_entries) == 4, failure_entries
    assert all("StepDefinitionNotFoundError" in failure.get("message", "") for failure in failure_entries), (
        failure_entries
    )
    assert not list(junit_root.iter("error")), "undefined steps should be test failures, not JUnit errors"

    usage_path = root / "artifacts" / "usage.json"
    assert usage_path.is_file() and usage_path.stat().st_size > 0, usage_path
    usage_report = json.loads(usage_path.read_text(encoding="utf-8"))
    event_counts = usage_report.get("event_counts")
    assert isinstance(event_counts, dict), usage_report
    assert {
        event_name: event_counts.get(event_name)
        for event_name in ("pickle", "testCase", "testStepFinished", "testCaseFinished", "testRunFinished")
    } == {
        "pickle": 5,
        "testCase": 5,
        "testStepFinished": 5,
        "testCaseFinished": 5,
        "testRunFinished": 1,
    }, usage_report

    usage_json_path = root / "artifacts" / "cucumber-usage.json"
    assert usage_json_path.is_file() and usage_json_path.stat().st_size > 0, usage_json_path
    usage_json = json.loads(usage_json_path.read_text(encoding="utf-8"))
    assert isinstance(usage_json, list) and all(isinstance(definition, dict) for definition in usage_json), usage_json
    control_definitions = [
        definition
        for definition in usage_json
        if definition.get("pattern") == "a snippet control step that records normal execution"
    ]
    assert len(control_definitions) == 1, control_definitions
    control_definition = control_definitions[0]
    assert control_definition.get("patternType") == "CucumberExpression", control_definition
    assert isinstance(control_definition.get("uri"), str), control_definition
    assert control_definition["uri"].endswith("snippets_consumer_steps.py"), control_definition
    assert isinstance(control_definition.get("line"), int) and control_definition["line"] > 0, control_definition
    control_matches = control_definition.get("matches")
    assert isinstance(control_matches, list) and len(control_matches) == 1, control_definition
    assert control_matches[0].get("text") == "a snippet control step that records normal execution", control_matches
    assert all(
        isinstance(control_matches[0].get(key), expected_type)
        for key, expected_type in (("uri", str), ("line", int), ("duration", dict))
    ), control_matches

    selected_file_paths = (
        root / "artifacts" / "messages.ndjson",
        cucumber_json_path,
        junit_path,
        usage_path,
        usage_json_path,
    )
    assert len({path.resolve() for path in selected_file_paths}) == len(selected_file_paths), selected_file_paths


def _patch_official_snippets_formatter_to_fail_after_messages(consumer: Any) -> None:
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    formatter_path = root / "node_modules" / "@cucumber" / "cucumber" / "lib" / "formatter" / "snippets_formatter.js"
    formatter_source = formatter_path.read_text(encoding="utf-8")
    hook = "    logSnippets() {\n"
    assert formatter_source.count(hook) == 1, (
        "the pinned Cucumber SnippetsFormatter.logSnippets hook changed; "
        f"cannot inject the backend failure sentinel into {formatter_path}"
    )
    formatter_path.write_text(
        formatter_source.replace(
            hook,
            f"{hook}        throw new Error('{_SNIPPETS_BACKEND_FAILURE_SENTINEL}');\n",
            1,
        ),
        encoding="utf-8",
    )


_SNIPPETS_BACKEND_FAILURE_SENTINEL = "PYTEST_CUKE_SNIPPETS_BACKEND_FAILURE_SENTINEL"


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
    output = _assert_pytest_undefined_failure(consumer, expected_failure_count=1)
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


@when(
    parsers.re(
        r'I run installed pytest from consumer directory "(?P<working_directory>[^"]+)" '
        r'with shared arguments "(?P<shared_arguments>[^"]+)" and Snippets capture variants '
        r'"(?P<fd_arguments>[^"]+)", "(?P<sys_arguments>[^"]+)", and "(?P<no_arguments>[^"]+)"'
    )
)
def run_installed_pytest_with_snippets_capture_variants(
    consumer: Any,
    working_directory: str,
    shared_arguments: str,
    fd_arguments: str,
    sys_arguments: str,
    no_arguments: str,
) -> None:
    cwd = _safe_workspace(consumer, working_directory)
    results = {}
    for mode, arguments in (
        ("fd", fd_arguments),
        ("sys", sys_arguments),
        ("no", no_arguments),
    ):
        results[mode] = _run_pytest(consumer, f"{shared_arguments} {arguments}", cwd=cwd)
    consumer.snippets_capture_results = results


def _assert_snippets_capture_mode(consumer: Any, mode: str, *, passing_output_visible: bool) -> None:
    results = getattr(consumer, "snippets_capture_results", {})
    assert mode in results, f"the installed pytest {mode} capture variant did not run"
    previous_result = getattr(consumer, "pytest_result", None)
    consumer.pytest_result = results[mode]
    try:
        _assert_official_js_snippets(
            consumer,
            expected_count=6,
            expected_failure_count=4,
            expected_pass_count=1,
            expected_keyword_expressions=_MIXED_SNIPPET_EXPRESSIONS,
        )
        result = consumer.pytest_result
        assert result is not None
        sentinel = "snippets passing-step stdout sentinel"
        if passing_output_visible:
            assert result.stdout.count(sentinel) == 1, result.stdout
        else:
            assert sentinel not in result.stdout, result.stdout
        assert sentinel not in result.stderr, result.stderr
    finally:
        consumer.pytest_result = previous_result


@then("fd capture should preserve JavaScript snippets and undefined-step failures while hiding passing step output")
def fd_capture_preserves_snippets_and_failures(consumer: Any) -> None:
    _assert_snippets_capture_mode(consumer, "fd", passing_output_visible=False)


@then("sys capture should preserve JavaScript snippets and undefined-step failures while hiding passing step output")
def sys_capture_preserves_snippets_and_failures(consumer: Any) -> None:
    _assert_snippets_capture_mode(consumer, "sys", passing_output_visible=False)


@then("disabled capture should preserve JavaScript snippets and undefined-step failures while showing passing step output")
def disabled_capture_preserves_snippets_and_failures(consumer: Any) -> None:
    _assert_snippets_capture_mode(consumer, "no", passing_output_visible=True)


@given("the public Cucumber snippets example is copied to the installed consumer")
def copy_public_cucumber_snippets_example(consumer: Any) -> None:
    source = Path(__file__).resolve().parents[2] / "examples" / "cucumber-snippets"
    assert source.is_dir(), f"the checked-in Cucumber snippets example is missing: {source}"
    destination = _safe_workspace(consumer, "cucumber-snippets-example")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    consumer._snippets_workspace = destination


@then("the public snippets example should emit JavaScript suggestions and preserve its undefined failure")
def public_cucumber_snippets_example_preserves_undefined_failure(consumer: Any) -> None:
    assert consumer._snippets_cucumber_version == "13.3.0"
    _assert_official_js_snippets(
        consumer,
        expected_count=5,
        expected_failure_count=3,
        expected_pass_count=0,
        expected_keyword_expressions=(
            ("Given", "a customer named {string} is registered"),
            ("When", "the customer waits {int} seconds"),
            ("When", "the customer waits {float} seconds"),
            ("Then", "the customer receives {int} results"),
            ("Then", "the customer receives {float} results"),
        ),
        defined_step_not_suggested="the snippets example is ready",
    )


@then("duplicate snippets file destinations should fail before marker execution or artifact publication")
def duplicate_snippets_file_destinations_preflight(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    assert consumer._snippets_cucumber_version == "13.3.0"
    assert result is not None and result.returncode != 0, output
    assert "shared.json" in output, output
    assert "same output path" in output.lower(), output
    assert not (root / "scenario-started.marker").exists(), output
    assert not (root / "artifacts" / "shared.json").exists(), output
    snippet_declaration = re.compile(r"(?://\s*)?(?:Given|When|Then|And|But)\(['\"]")
    assert not snippet_declaration.search(result.stdout), result.stdout


@step("the consumer patches the pinned snippets formatter to fail after receiving the run messages")
def patch_official_snippets_formatter_to_fail_after_messages(consumer: Any) -> None:
    _patch_official_snippets_formatter_to_fail_after_messages(consumer)


@then("the snippets backend failure should preserve pytest's undefined-step failures")
def snippets_backend_failure_preserves_undefined_step_failures(consumer: Any) -> None:
    output = _assert_pytest_undefined_failure(
        consumer,
        expected_failure_count=4,
        expected_pass_count=1,
    )
    assert re.search(rf"(?m)^Error: {re.escape(_SNIPPETS_BACKEND_FAILURE_SENTINEL)}$", output), (
        f"the selected official snippets backend should report its post-startup failure; output was:\n{output}"
    )


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
    mask_npm_package_from_node_resolution(root, "@cucumber/cucumber")
    consumer.env.update(environment)


@given("the consumer exposes an isolated Node executable without npm")
def consumer_exposes_node_without_npm(consumer: Any) -> None:
    root = getattr(consumer, "_snippets_workspace", _consumer_root(consumer))
    node_bin = root / "node-only-bin"
    node_bin.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        node_stub = node_bin / "node.cmd"
        node_stub.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        pathext = consumer.env.get("PATHEXT", os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"))
        extensions = [extension for extension in pathext.split(";") if extension]
        if not any(extension.casefold() == ".cmd" for extension in extensions):
            extensions.append(".CMD")
        consumer.env["PATHEXT"] = ";".join(extensions)
    else:
        node_stub = node_bin / "node"
        node_stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        node_stub.chmod(node_stub.stat().st_mode | 0o111)

    isolated_path = os.pathsep.join((str(node_bin), str(Path(consumer.python).parent)))
    consumer.env["PATH"] = isolated_path
    consumer.env.pop("NODE_PATH", None)
    assert len(consumer.env["PATH"].split(os.pathsep)) == 2, consumer.env["PATH"]
    assert shutil.which("npm", path=isolated_path) is None, "the isolated consumer PATH must not expose npm"
    if os.name == "nt":
        detected_output = subprocess.run(
            [str(consumer.python), "-c", "import shutil; print(shutil.which('node') or '')"],
            env=consumer.env,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert detected_output.returncode == 0, detected_output.stderr
        assert Path(detected_output.stdout.strip()).name.casefold() == "node.cmd", detected_output.stdout
    else:
        detected_path = shutil.which("node", path=isolated_path)
        assert detected_path is not None and Path(detected_path).resolve() == node_stub.resolve(), detected_path


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


@then("missing npm snippets preflight should be actionable and happen before execution")
def missing_npm_cucumber_preflight_fails_before_scenario(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "formatter 'cucumber-snippets' requires executable 'npm'" in output, output
    assert "but it was not found on PATH" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the test scenario ran before missing npm was rejected"
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
