"""Installed-consumer acceptance steps for the official Cucumber JUnit XML formatter."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, parsers, then, when
from tests.support.testing_utils import mask_npm_package_from_node_resolution
from tests.support.windows_acl import (
    assert_windows_identity_lookup_command,
    windows_acl_user_sid,
    windows_identity_lookup_command,
)


_PRODUCT_ROOT = Path(__file__).resolve().parents[2]


def _write(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Cucumber JUnit consumer files must stay inside the workspace")
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _node_paths(consumer: Any) -> tuple[str, str, str]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        pytest.skip("the real Cucumber JUnit acceptance lane requires Node.js and npm")
    return node, npm, str(Path(consumer.pytest).parent)


_CUCUMBER_JUNIT_VERSION = "0.14.1"
_CUCUMBER_JUNIT_PACKAGE = "@cucumber/junit-xml-formatter"
_JUNIT_RICH_FEATURE = '''\
@junit-feature-tag
Feature: Cucumber JUnit report café
  Feature description marker café.

  Background: Shared report setup
    Given junit feature background passes

  @junit-rule-tag
  Rule: Customer profiles
    Rule description marker.

    Background: Profile report setup
      Given junit rule background passes

    @junit-scenario-tag
    Scenario: A described structured profile
      Scenario description marker.
      When junit accepts a document
        """application/json
        {"customer": "Ada", "note": "document-body-marker café"}
        """
      And junit accepts a table
        | field    | value             |
        | customer | Ada               |
        | note     | table-body-marker |
      Then junit structured profile passes

    @junit-outline-tag
    Scenario Outline: A profile row for <customer>
      Outline description marker.
      Given junit row <customer> is started
      Then junit row <customer> passes

      Examples: Named customer rows
        | customer |
        | Ada      |
        | Boris    |
'''
_JUNIT_OUTCOMES_FEATURE = """\
Feature: Cucumber JUnit outcomes
  Scenario: A JUnit case passes
    Given junit outcome passes

  Scenario: A JUnit case fails
    When junit outcome fails

  Scenario: A JUnit case skips
    When junit outcome skips

  Scenario: A JUnit case has an undefined step
    Given junit intentionally has no matching definition
    Then junit step after undefined remains skipped
"""
_JUNIT_BACKGROUND_FAILURE_FEATURE = """\
Feature: Cucumber JUnit background failure
  Background: The setup fails
    Given junit background fails with a sentinel

  Scenario: The case cannot pass after a background failure
    Then junit body after the background must not pass
"""
_JUNIT_HOOK_FAILURE_FEATURE = """\
Feature: Cucumber JUnit scenario hook failures
  Scenario: The case records a before hook failure
    Given junit before-hook failure scenario starts

  Scenario: The case records an after hook failure
    Given junit after-hook failure scenario starts
"""
_JUNIT_DUPLICATE_IDENTITY_FEATURE = """\
Feature: Duplicate JUnit identity
  Scenario: Same scenario identity
    Given junit outcome passes
"""
_JUNIT_HISTORICAL_FEATURE = """\
Feature: formatter_suite
  Scenario: passing scenario
    Given junit outcome passes

  Scenario: failing scenario
    When junit outcome fails
"""
_JUNIT_MARKER_FEATURE = """\
Feature: Cucumber JUnit marker
  Scenario: The marker records that execution began
    Given junit marker scenario starts
"""
_JUNIT_FINALIZATION_PRELOAD = """\
if (process.argv.length === 1) {
  process.once("beforeExit", () => {
    throw new Error("Cucumber JUnit finalization failure sentinel");
  });
}
"""
_JUNIT_SUPPORT = """\
from pathlib import Path
import json
import pytest
from pytest_cuke import given, parsers, then, when

ROOT = Path(__file__).parent


@given("junit feature background passes", target_fixture="junit_profile")
def junit_feature_background_passes():
    return {"feature_background": True}


@given("junit rule background passes")
def junit_rule_background_passes(junit_profile):
    assert junit_profile["feature_background"] is True
    junit_profile["rule_background"] = True


@when("junit accepts a document")
def junit_accepts_document(step, junit_profile):
    assert junit_profile["rule_background"] is True
    assert step.doc_string is not None
    assert step.doc_string.media_type == "application/json"
    junit_profile["document"] = json.loads(step.doc_string.content)


@when("junit accepts a table")
def junit_accepts_table(step, junit_profile):
    assert step.data_table is not None
    junit_profile["table"] = step.data_table.as_dicts()


@then("junit structured profile passes")
def junit_structured_profile_passes(junit_profile):
    assert junit_profile["document"] == {"customer": "Ada", "note": "document-body-marker café"}
    assert junit_profile["table"] == [
        {"field": "customer", "value": "Ada"},
        {"field": "note", "value": "table-body-marker"},
    ]


@given(parsers.parse("junit row {customer} is started"))
def junit_row_is_started(customer, junit_profile):
    assert customer in {"Ada", "Boris"}
    junit_profile["outline_customer"] = customer


@then(parsers.parse("junit row {customer} passes"))
def junit_row_passes(customer, junit_profile):
    assert junit_profile["outline_customer"] == customer


@given("junit outcome passes")
def junit_outcome_passes():
    pass


@when("junit outcome fails")
def junit_outcome_fails():
    raise AssertionError("Cucumber JUnit failure sentinel")


@when("junit outcome skips")
def junit_outcome_skips():
    pytest.skip("Cucumber JUnit skip sentinel")


@then("junit step after undefined remains skipped")
def junit_step_after_undefined_remains_skipped():
    raise AssertionError("step after undefined JUnit case unexpectedly ran")


@given("junit background fails with a sentinel")
def junit_background_fails_with_sentinel():
    pytest.fail("Cucumber JUnit background failure sentinel")


@then("junit body after the background must not pass")
def junit_body_after_background_must_not_pass():
    raise AssertionError("JUnit case body ran after the failing background")


@given("junit before-hook failure scenario starts")
def junit_before_hook_failure_scenario_starts():
    (ROOT / "scenario-before-hook.marker").write_text("started", encoding="utf-8")


@given("junit after-hook failure scenario starts")
def junit_after_hook_failure_scenario_starts():
    (ROOT / "scenario-after-hook.marker").write_text("started", encoding="utf-8")


@given("junit marker scenario starts")
def junit_marker_scenario_starts():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""
_JUNIT_FAILURE_CONFTST = """\
import pytest

pytest_plugins = ["cucumber_junit_consumer_steps"]


@pytest.hookimpl(tryfirst=True)
def pytest_cuke_before_scenario(request, run):
    del request
    if run.scenario.name == "The case records a before hook failure":
        raise RuntimeError("Cucumber JUnit before-scenario hook failure sentinel")


@pytest.hookimpl(trylast=True)
def pytest_cuke_after_scenario(request, run):
    del request
    if run.scenario.name == "The case records an after hook failure":
        raise RuntimeError("Cucumber JUnit after-scenario hook failure sentinel")
"""
_JUNIT_HISTORICAL_PACKAGE = """\
import { readFileSync } from "node:fs";

export default {
  formatter({ on, write }) {
    let runStarted = false;
    let finishedCases = 0;
    const statuses = [];
    on("message", (envelope) => {
      if (envelope.testRunStarted) runStarted = true;
      if (envelope.testCaseFinished) finishedCases += 1;
      if (envelope.testStepFinished) statuses.push(envelope.testStepFinished.testStepResult.status);
      if (envelope.testRunFinished) {
        const passed = statuses.filter((status) => status === "PASSED").length;
        const failed = statuses.filter((status) => status === "FAILED").length;
        if (!runStarted || finishedCases !== 2 || passed !== 1 || failed !== 1) {
          throw new Error("historical JUnit transport did not receive one passing and one failing case");
        }
        write(readFileSync("historical-junit.xml", "utf8"));
      }
    });
  },
};
"""


def _junit_workspace(consumer: Any) -> Path:
    root = Path(consumer.path).resolve()
    destination = (root / "cucumber-junit café workspace").resolve()
    if root not in destination.parents:
        raise ValueError("Cucumber JUnit workspace must remain inside the consumer project")
    return destination


def _prepare_junit_consumer(
    consumer: Any,
    feature: str,
    *,
    support: str = _JUNIT_SUPPORT,
    scenario_hook_failure: bool = False,
) -> Path:
    root = _junit_workspace(consumer)
    root.mkdir(parents=True, exist_ok=True)
    (root / "artifacts").mkdir(exist_ok=True)
    (root / "features").mkdir(exist_ok=True)
    (root / "features/cucumber-junit-consumer.feature").write_text(feature, encoding="utf-8")
    (root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "cuke_autoload = true\n"
        "cuke_features_dir = 'features'\n"
        "markers = [\n"
        "  'junit-feature-tag: Cucumber JUnit feature tag',\n"
        "  'junit-rule-tag: Cucumber JUnit rule tag',\n"
        "  'junit-scenario-tag: Cucumber JUnit scenario tag',\n"
        "  'junit-outline-tag: Cucumber JUnit outline tag',\n"
        "]\n",
        encoding="utf-8",
    )
    (root / "cucumber_junit_consumer_steps.py").write_text(support, encoding="utf-8")
    conftest = (
        _JUNIT_FAILURE_CONFTST if scenario_hook_failure else 'pytest_plugins = ["cucumber_junit_consumer_steps"]\n'
    )
    (root / "conftest.py").write_text(conftest, encoding="utf-8")
    consumer._cucumber_junit_workspace = root
    consumer._cucumber_junit_readonly_directory = None
    return root


def _install_official_junit_runtime(consumer: Any) -> None:
    node, npm, consumer_bin = _node_paths(consumer)
    root = consumer._cucumber_junit_workspace
    package_json = {
        "name": "pytest-cuke-cucumber-junit-consumer",
        "private": True,
        "type": "module",
        "dependencies": {_CUCUMBER_JUNIT_PACKAGE: _CUCUMBER_JUNIT_VERSION},
    }
    _write(root, "package.json", json.dumps(package_json, ensure_ascii=False, indent=2) + "\n")
    environment = dict(consumer.env)
    environment["PATH"] = os.pathsep.join(dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), consumer_bin)))
    environment.pop("NODE_PATH", None)
    install = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert install.returncode == 0, (
        f"could not install pinned {_CUCUMBER_JUNIT_PACKAGE}@{_CUCUMBER_JUNIT_VERSION}:\n"
        f"{install.stdout}\n{install.stderr}"
    )
    metadata = root / "node_modules" / "@cucumber" / "junit-xml-formatter" / "package.json"
    installed_version = json.loads(metadata.read_text(encoding="utf-8")).get("version")
    assert installed_version == _CUCUMBER_JUNIT_VERSION, installed_version
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)
    consumer._cucumber_junit_node = node
    consumer._cucumber_junit_npm = npm


def _run_junit_pytest(consumer: Any, arguments: str) -> subprocess.CompletedProcess[str]:
    root = consumer._cucumber_junit_workspace
    try:
        result = subprocess.run(
            [str(consumer.python), "-m", "pytest", *shlex.split(arguments)],
            cwd=root,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    finally:
        readonly_state = consumer._cucumber_junit_readonly_directory
        if readonly_state is not None:
            _restore_cucumber_junit_parent_permissions(consumer, readonly_state)
    consumer.cucumber_junit_result = result
    consumer.pytest_result = result
    return result


def _run_junit_replay(consumer: Any, relative_messages: str, relative_output: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(consumer.cuke), "replay", relative_messages, "--formatter", f"cucumber-junit={relative_output}"],
        cwd=consumer._cucumber_junit_workspace,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    consumer.cucumber_junit_replay_result = result
    return result


def _junit_output(consumer: Any, *, replay: bool = False) -> str:
    result = consumer.cucumber_junit_replay_result if replay else consumer.cucumber_junit_result
    assert result is not None, "the Cucumber JUnit process has not run"
    return f"{result.stdout}\n{result.stderr}"


def _read_junit(consumer: Any, relative_path: str) -> tuple[ET.Element, list[ET.Element]]:
    artifact = consumer._cucumber_junit_workspace / relative_path
    assert artifact.is_file(), f"Cucumber JUnit artifact {relative_path!r} was not produced; {_junit_output(consumer)}"
    root = ET.parse(artifact).getroot()
    assert root.tag in {"testsuite", "testsuites"}, ET.tostring(root, encoding="unicode")
    cases = list(root.iter("testcase"))
    assert cases, ET.tostring(root, encoding="unicode")
    return root, cases


def _normalized_junit_artifact(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    declaration = raw.splitlines()[0] if raw.startswith("<?xml") else ""
    root = ET.fromstring(raw)
    for node in root.iter():
        node.attrib.pop("timestamp", None)
    canonical = ET.canonicalize(ET.tostring(root, encoding="unicode"), strip_text=False)
    return f"{declaration}\n{canonical}\n" if declaration else f"{canonical}\n"


def _message_timestamp_nanoseconds(value: Any) -> int:
    if isinstance(value, dict):
        return int(value["seconds"]) * 1_000_000_000 + int(value.get("nanos", 0))
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    delta = parsed - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86_400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1_000


def _junit_message_durations(messages_path: Path) -> tuple[float, list[float]]:
    envelopes = [json.loads(line) for line in messages_path.read_text(encoding="utf-8").splitlines() if line]
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(run_started) == len(run_finished) == 1, (run_started, run_finished)
    suite_duration = (
        _message_timestamp_nanoseconds(run_finished[0]["timestamp"])
        - _message_timestamp_nanoseconds(run_started[0]["timestamp"])
    ) / 1_000_000_000

    started_by_id = {
        envelope["testCaseStarted"]["id"]: envelope["testCaseStarted"]
        for envelope in envelopes
        if "testCaseStarted" in envelope
    }
    finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    assert len(started_by_id) == len(finished), (started_by_id, finished)
    case_durations = [
        (
            _message_timestamp_nanoseconds(event["timestamp"])
            - _message_timestamp_nanoseconds(started_by_id[event["testCaseStartedId"]]["timestamp"])
        )
        / 1_000_000_000
        for event in finished
    ]
    return suite_duration, case_durations


def _assert_junit_durations_match_messages(consumer: Any, relative_xml: str, relative_messages: str) -> None:
    root, cases = _read_junit(consumer, relative_xml)
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    assert suite is not None, ET.tostring(root, encoding="unicode")
    expected_suite_duration, expected_case_durations = _junit_message_durations(
        consumer._cucumber_junit_workspace / relative_messages
    )
    assert float(suite.get("time", "nan")) == pytest.approx(expected_suite_duration, abs=1e-6), suite.attrib
    assert len(cases) == len(expected_case_durations), (cases, expected_case_durations)
    for case, expected_duration in zip(cases, expected_case_durations, strict=True):
        assert float(case.get("time", "nan")) == pytest.approx(expected_duration, abs=1e-6), (
            case.attrib,
            expected_duration,
        )


def _write_deterministic_junit_messages(consumer: Any) -> Path:
    workspace = consumer._cucumber_junit_workspace
    source = workspace / "artifacts/messages.ndjson"
    destination = workspace / "artifacts/deterministic-messages.ndjson"
    envelopes = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(started) == len(finished) == 2, (started, finished)
    assert len(run_started) == len(run_finished) == 1, (run_started, run_finished)

    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    base_seconds = int(base.timestamp())
    intervals = ((1, 3), (4, 7))
    case_start_offsets = {event["id"]: start for event, (start, _) in zip(started, intervals, strict=True)}
    case_finish_offsets = {event["id"]: finish for event, (_, finish) in zip(started, intervals, strict=True)}

    def timestamp(offset_seconds: int) -> dict[str, int]:
        return {"seconds": base_seconds + offset_seconds, "nanos": 0}

    for envelope in envelopes:
        if "testRunStarted" in envelope:
            envelope["testRunStarted"]["timestamp"] = timestamp(0)
        elif "testCaseStarted" in envelope:
            event = envelope["testCaseStarted"]
            event["timestamp"] = timestamp(case_start_offsets[event["id"]])
        elif "testCaseFinished" in envelope:
            event = envelope["testCaseFinished"]
            started_id = event["testCaseStartedId"]
            event["timestamp"] = timestamp(case_finish_offsets[started_id])
        elif "testRunFinished" in envelope:
            envelope["testRunFinished"]["timestamp"] = timestamp(10)

    destination.write_text(
        "".join(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")) + "\n" for envelope in envelopes),
        encoding="utf-8",
    )
    return destination


def _assert_junit_rich_report(consumer: Any, relative_path: str) -> None:
    root, cases = _read_junit(consumer, relative_path)
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    assert suite is not None, ET.tostring(root, encoding="unicode")
    properties = suite.find("properties")
    assert properties is not None, ET.tostring(suite, encoding="unicode")
    document_prefix = "cucumber.file%3Acucumber-junit-consumer.feature.document.0"
    scenario_prefix = f"{document_prefix}.scenario.0.A%20described%20structured%20profile"
    outline_prefix = f"{document_prefix}.outline.1.A%20profile%20row%20for%20%3Ccustomer%3E"
    examples_prefix = f"{outline_prefix}.examples.0.Named%20customer%20rows"
    expected_values = {
        f"{document_prefix}.feature.uri": "file:cucumber-junit-consumer.feature",
        f"{document_prefix}.feature.description": "Feature description marker café.",
        f"{document_prefix}.feature.tags": ["@junit-feature-tag"],
        f"{document_prefix}.rule.0.Customer%20profiles.description": "Rule description marker.",
        f"{document_prefix}.rule.0.Customer%20profiles.tags": ["@junit-rule-tag"],
        f"{scenario_prefix}.description": "Scenario description marker.",
        f"{scenario_prefix}.tags": ["@junit-rule-tag", "@junit-scenario-tag"],
        f"{scenario_prefix}.step.0.docString":
            '{"customer": "Ada", "note": "document-body-marker café"}',
        f"{scenario_prefix}.step.1.dataTable": [
            ["field", "value"],
            ["customer", "Ada"],
            ["note", "table-body-marker"],
        ],
        f"{outline_prefix}.description": "Outline description marker.",
        f"{outline_prefix}.tags": ["@junit-rule-tag", "@junit-outline-tag"],
        f"{examples_prefix}.table": [["customer"], ["Ada"], ["Boris"]],
    }
    property_nodes = properties.findall("property")
    values = {property_node.get("name"): property_node.get("value") for property_node in property_nodes}
    assert len(property_nodes) == len(expected_values), (property_nodes, expected_values)
    assert set(values) == set(expected_values), (values, expected_values)
    for name, expected in expected_values.items():
        actual = values.get(name)
        if isinstance(expected, list):
            assert actual is not None and json.loads(actual) == expected, (name, actual, expected, values)
        else:
            assert actual == expected, (name, actual, expected, values)
    assert len(cases) == 3, ET.tostring(root, encoding="unicode")
    assert root.get("tests", "3") == "3", root.attrib
    assert root.get("failures", "0") == "0", root.attrib
    assert root.get("skipped", "0") == "0", root.attrib
    names = [case.get("name", "") for case in cases]
    assert len(set(names)) == 3, names
    assert any("described structured profile" in name for name in names), names
    outline_cases = [
        case for case in cases if any(row_id in case.get("name", "") for row_id in ("#1.1", "#1.2"))
    ]
    assert len(outline_cases) == 2, names
    outline_markers = [
        [row_id for row_id in ("#1.1", "#1.2") if row_id in case.get("name", "")]
        for case in outline_cases
    ]
    assert outline_markers == [["#1.1"], ["#1.2"]], names
    assert all("Cucumber JUnit report café" in case.get("classname", "") for case in cases), cases

    for case in cases:
        duration = case.get("time")
        assert duration is not None and float(duration) >= 0, case.attrib
        assert not list(case.findall("failure")), case
        assert not list(case.findall("error")), case
        assert not list(case.findall("skipped")), case
        output = case.findtext("system-out", default="")
        assert "passed" in output.lower(), (case, output)
        feature_background = output.find("junit feature background passes")
        rule_background = output.find("junit rule background passes")
        assert feature_background >= 0 and rule_background > feature_background, output

    structured = next(case for case in cases if "described structured profile" in case.get("name", ""))
    output = structured.findtext("system-out", default="")
    step_names = [
        "junit feature background passes",
        "junit rule background passes",
        "junit accepts a document",
        "junit accepts a table",
        "junit structured profile passes",
    ]
    positions = [output.find(name) for name in step_names]
    assert all(position >= 0 for position in positions), output
    assert positions == sorted(positions), output

    for row, (row_id, customer) in zip(
        outline_cases,
        (("#1.1", "Ada"), ("#1.2", "Boris")),
        strict=True,
    ):
        assert row_id in row.get("name", ""), row.attrib
        output = row.findtext("system-out", default="")
        started = output.find(f"junit row {customer} is started")
        passed = output.find(f"junit row {customer} passes")
        assert started >= 0 and passed > started, output


def _restore_cucumber_junit_parent_permissions(consumer: Any, state: tuple[Any, ...]) -> None:
    directory, original_mode, sid = state
    if sid is None:
        directory.chmod(original_mode)
    else:
        icacls = shutil.which("icacls.exe") or shutil.which("icacls")
        assert icacls is not None, "Windows icacls is required to restore the JUnit destination ACL"
        restored = subprocess.run(
            [icacls, str(directory), "/remove:d", f"*{sid}"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        assert restored.returncode == 0, f"could not restore the JUnit destination ACL:\n{restored.stdout}\n{restored.stderr}"
    consumer._cucumber_junit_readonly_directory = None


def _set_junit_ini(consumer: Any, relative_path: str) -> None:
    config = (
        "[tool.pytest.ini_options]\n"
        "cuke_autoload = true\n"
        "cuke_features_dir = 'features'\n"
        "markers = [\n"
        "  'junit-feature-tag: Cucumber JUnit feature tag',\n"
        "  'junit-rule-tag: Cucumber JUnit rule tag',\n"
        "  'junit-scenario-tag: Cucumber JUnit scenario tag',\n"
        "  'junit-outline-tag: Cucumber JUnit outline tag',\n"
        "]\n"
        f"cuke_junit = {json.dumps(relative_path, ensure_ascii=False)}\n"
    )
    (consumer._cucumber_junit_workspace / "pyproject.toml").write_text(config, encoding="utf-8")
    consumer._cucumber_junit_ini_path = relative_path


def _junit_preflight_failure(consumer: Any, expected: str) -> str:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert expected.lower() in output.lower(), output
    assert not (consumer._cucumber_junit_workspace / "scenario-started.marker").exists(), output
    return output


@given("the Cucumber JUnit consumer prepares a rich feature with backgrounds and outline rows")
def prepare_cucumber_junit_rich_consumer(consumer: Any) -> None:
    _prepare_junit_consumer(consumer, _JUNIT_RICH_FEATURE)


@given("the Cucumber JUnit consumer prepares two same-named feature files without metadata")
def prepare_cucumber_junit_duplicate_identity_consumer(consumer: Any) -> None:
    root = _prepare_junit_consumer(consumer, _JUNIT_DUPLICATE_IDENTITY_FEATURE)
    feature_directory = root / "features"
    (feature_directory / "cucumber-junit-consumer.feature").unlink()
    for filename in ("alpha.feature", "bravo.feature"):
        (feature_directory / filename).write_text(_JUNIT_DUPLICATE_IDENTITY_FEATURE, encoding="utf-8")


@given("the consumer installs the pinned official Cucumber JUnit runtime")
def install_official_cucumber_junit_runtime(consumer: Any) -> None:
    _install_official_junit_runtime(consumer)


@given("the public Cucumber JUnit example is copied to the installed consumer")
def copy_public_cucumber_junit_example_to_consumer(consumer: Any) -> None:
    source = _PRODUCT_ROOT / "examples" / "cucumber-junit"
    destination = Path(consumer.path) / "cucumber-junit-example"
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destination / "artifacts").mkdir()
    consumer._cucumber_junit_workspace = destination.resolve()
    consumer._cucumber_junit_readonly_directory = None


@when(parsers.re(r'I run installed pytest in the Cucumber JUnit workspace with arguments "(?P<arguments>[^"]*)"'))
def run_cucumber_junit_pytest(arguments: str, consumer: Any) -> None:
    _run_junit_pytest(consumer, arguments)


@then("the selected Cucumber JUnit report should preserve cases fields order and durations")
def selected_cucumber_junit_preserves_contract(consumer: Any) -> None:
    assert consumer.cucumber_junit_result.returncode == 0, _junit_output(consumer)
    relative_path = "artifacts/cli.xml"
    if not (consumer._cucumber_junit_workspace / relative_path).is_file():
        relative_path = "artifacts/live.xml"
    _assert_junit_rich_report(consumer, relative_path)


@then("Cucumber JUnit Messages native JUnit and pytest terminal summary should coexist")
def cucumber_junit_outputs_coexist(consumer: Any) -> None:
    root = consumer._cucumber_junit_workspace
    junit_path = root / "artifacts/cli.xml"
    native_path = root / "artifacts/native.xml"
    messages_path = root / "artifacts/messages.ndjson"
    assert len({path.resolve() for path in (junit_path, native_path, messages_path)}) == 3
    assert junit_path.is_file() and native_path.is_file() and messages_path.is_file()
    _, native_cases = _read_junit(consumer, "artifacts/native.xml")
    assert len(native_cases) == 3, native_cases
    assert "3 passed" in _junit_output(consumer).lower(), _junit_output(consumer)


@when(parsers.re(r'the Cucumber JUnit consumer sets cuke_junit to "(?P<relative_path>[^"]+)"'))
def set_cucumber_junit_ini(relative_path: str, consumer: Any) -> None:
    _set_junit_ini(consumer, relative_path)


@then("the configured Cucumber JUnit report should preserve the same public contract")
def configured_cucumber_junit_preserves_contract(consumer: Any) -> None:
    assert consumer.cucumber_junit_result.returncode == 0, _junit_output(consumer)
    _assert_junit_rich_report(consumer, consumer._cucumber_junit_ini_path)


@then(parsers.re(r'the bare Cucumber JUnit option should write "(?P<relative_path>[^"]+)" under pytest root'))
def bare_cucumber_junit_uses_default_path(relative_path: str, consumer: Any) -> None:
    assert relative_path == "cucumber.xml"
    assert consumer.cucumber_junit_result.returncode == 0, _junit_output(consumer)
    _assert_junit_rich_report(consumer, relative_path)


@when(parsers.re(r'I replay Cucumber JUnit from the saved Messages stream to "(?P<relative_path>[^"]+)"'))
def replay_cucumber_junit_saved_messages(relative_path: str, consumer: Any) -> None:
    result = _run_junit_replay(consumer, "artifacts/messages.ndjson", relative_path)
    assert result.returncode == 0, _junit_output(consumer, replay=True)


@then("replayed Cucumber JUnit XML should match live XML after normalizing timestamps")
def replayed_cucumber_junit_matches_live(consumer: Any) -> None:
    live_root, live_cases = _read_junit(consumer, "artifacts/live.xml")
    replay_root, replay_cases = _read_junit(consumer, "artifacts/replayed.xml")
    assert len(live_cases) == len(replay_cases) == 3

    def normalized(root: ET.Element) -> str:
        for node in root.iter():
            node.attrib.pop("timestamp", None)
        return ET.canonicalize(ET.tostring(root, encoding="unicode"), strip_text=False)

    assert normalized(live_root) == normalized(replay_root), (
        ET.tostring(live_root, encoding="unicode"),
        ET.tostring(replay_root, encoding="unicode"),
    )


@given("the Cucumber JUnit consumer prepares passing failing skipped and undefined scenarios")
def prepare_cucumber_junit_outcomes(consumer: Any) -> None:
    _prepare_junit_consumer(consumer, _JUNIT_OUTCOMES_FEATURE)


@then("the Cucumber JUnit run should fail while publishing every case outcome")
def cucumber_junit_outcomes_are_truthful(consumer: Any) -> None:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "Cucumber JUnit failure sentinel" in output, output
    root, cases = _read_junit(consumer, "artifacts/outcomes.xml")
    assert len(cases) == 4, ET.tostring(root, encoding="unicode")
    case_by_name = {case.get("name", ""): case for case in cases}
    assert len(case_by_name) == 4, cases
    passed = next(case for name, case in case_by_name.items() if "JUnit case passes" in name)
    failed = next(case for name, case in case_by_name.items() if "JUnit case fails" in name)
    skipped = next(case for name, case in case_by_name.items() if "JUnit case skips" in name)
    undefined = next(case for name, case in case_by_name.items() if "undefined step" in name)
    outcome_tags = {"failure", "error", "skipped"}

    def outcomes(case: ET.Element) -> list[str]:
        return [child.tag for child in case if child.tag in outcome_tags]

    assert outcomes(passed) == [], ET.tostring(passed, encoding="unicode")
    assert outcomes(failed) == ["failure"], ET.tostring(failed, encoding="unicode")
    assert "Cucumber JUnit failure sentinel" in ET.tostring(failed, encoding="unicode"), failed
    assert outcomes(skipped) == ["skipped"], ET.tostring(skipped, encoding="unicode")
    assert outcomes(undefined) == ["failure"], ET.tostring(undefined, encoding="unicode")
    assert root.get("tests") == "4", root.attrib
    assert root.get("failures") == "2", root.attrib
    assert root.get("errors") == "0", root.attrib
    assert root.get("skipped") == "1", root.attrib


@given("the Cucumber JUnit consumer prepares a failing background scenario")
def prepare_cucumber_junit_background_failure(consumer: Any) -> None:
    _prepare_junit_consumer(consumer, _JUNIT_BACKGROUND_FAILURE_FEATURE)


@then("the Cucumber JUnit case should retain the failed background diagnostic")
def cucumber_junit_background_failure_is_not_a_pass(consumer: Any) -> None:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    root, cases = _read_junit(consumer, "artifacts/background.xml")
    assert len(cases) == 1, ET.tostring(root, encoding="unicode")
    assert cases[0].find("failure") is not None, ET.tostring(cases[0], encoding="unicode")
    assert "Cucumber JUnit background failure sentinel" in ET.tostring(cases[0], encoding="unicode"), cases[0]
    assert "JUnit case body ran after" not in ET.tostring(cases[0], encoding="unicode"), cases[0]


@given("the Cucumber JUnit consumer prepares a failing scenario hook")
def prepare_cucumber_junit_hook_failure(consumer: Any) -> None:
    _prepare_junit_consumer(consumer, _JUNIT_HOOK_FAILURE_FEATURE, scenario_hook_failure=True)


@then("the Cucumber JUnit cases should retain failed before and after hook diagnostics")
def cucumber_junit_before_and_after_hook_failures_are_not_passes(consumer: Any) -> None:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    root, cases = _read_junit(consumer, "artifacts/hook.xml")
    assert len(cases) == 2, ET.tostring(root, encoding="unicode")
    assert root.get("tests") == "2" and root.get("failures") == "2", root.attrib
    assert root.get("skipped", "0") == "0", root.attrib
    before = next(case for case in cases if case.get("name") == "The case records a before hook failure")
    after = next(case for case in cases if case.get("name") == "The case records an after hook failure")
    before_failure = before.find("failure")
    after_failure = after.find("failure")
    assert before_failure is not None and before_failure.get("type") == "RuntimeError", before
    assert before_failure.get("message") == "Cucumber JUnit before-scenario hook failure sentinel", before_failure
    assert "Cucumber JUnit before-scenario hook failure sentinel" in (before_failure.text or ""), before_failure
    assert after_failure is not None and after_failure.get("type") == "RuntimeError", after
    assert after_failure.get("message") == "Cucumber JUnit after-scenario hook failure sentinel", after_failure
    assert "Cucumber JUnit after-scenario hook failure sentinel" in (after_failure.text or ""), after_failure
    assert "skipped" in before.findtext("system-out", default="").lower(), before
    assert "passed" in after.findtext("system-out", default="").lower(), after
    workspace = consumer._cucumber_junit_workspace
    assert not (workspace / "scenario-before-hook.marker").exists(), output
    assert (workspace / "scenario-after-hook.marker").is_file(), output


@given("the Cucumber JUnit consumer prepares passing and failing cases for the historical golden")
def prepare_historical_cucumber_junit_consumer(consumer: Any) -> None:
    root = _prepare_junit_consumer(consumer, _JUNIT_HISTORICAL_FEATURE)
    golden = _PRODUCT_ROOT / "tests/fixtures/cucumber-junit/cucumber-junit-reference.xml"
    shutil.copyfile(golden, root / "historical-junit.xml")


@given("the Cucumber JUnit consumer exposes its deterministic historical formatter")
def expose_historical_cucumber_junit_formatter(consumer: Any) -> None:
    node, npm, consumer_bin = _node_paths(consumer)
    root = consumer._cucumber_junit_workspace
    package = root / "node_modules/@cucumber/junit-xml-formatter"
    package.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps({"name": "pytest-cuke-historical-junit-consumer", "private": True, "type": "module"}) + "\n",
        encoding="utf-8",
    )
    (package / "package.json").write_text(
        json.dumps(
            {
                "name": _CUCUMBER_JUNIT_PACKAGE,
                "version": _CUCUMBER_JUNIT_VERSION,
                "type": "module",
                "exports": "./index.js",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (package / "index.js").write_text(_JUNIT_HISTORICAL_PACKAGE, encoding="utf-8")
    consumer.env["PATH"] = os.pathsep.join(dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), consumer_bin)))
    consumer.env.pop("NODE_PATH", None)


@then("the Cucumber JUnit report should match the historical reference golden")
def historical_cucumber_junit_matches_golden(consumer: Any) -> None:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert re.search(r"\b1 passed\b", output) and re.search(r"\b1 failed\b", output), output
    report = consumer._cucumber_junit_workspace / "artifacts/historical.xml"
    assert report.is_file(), output
    golden = _PRODUCT_ROOT / "tests/fixtures/cucumber-junit/cucumber-junit-reference.xml"
    assert _normalized_junit_artifact(report) == _normalized_junit_artifact(golden)
    root, cases = _read_junit(consumer, "artifacts/historical.xml")
    assert root.get("name") == "pytest-bdd-ng", root.attrib
    assert root.get("tests") == "2" and root.get("failures") == "1", root.attrib
    assert [case.get("name") for case in cases] == ["passing scenario", "failing scenario"], cases
    assert [case.get("classname") for case in cases] == ["formatter_suite", "formatter_suite"], cases
    failure = cases[1].find("failure")
    assert failure is not None and failure.get("message") == "boom", cases[1]
    assert failure.text == "RuntimeError: boom", failure


@given("the Cucumber JUnit consumer prepares a marker scenario for destination preflight")
def prepare_cucumber_junit_preflight(consumer: Any) -> None:
    _prepare_junit_consumer(consumer, _JUNIT_MARKER_FEATURE)


@then("the missing Cucumber JUnit parent should fail before the marker scenario runs")
def missing_cucumber_junit_parent_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, "missing-parent")
    assert "parent" in output.lower() or "directory" in output.lower(), output


@then("duplicate canonical JUnit destinations should fail before the marker scenario runs")
def duplicate_junit_destination_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, "same output path")
    assert "cucumber-junit" in output and "--junitxml" in output, output


@given(
    "the Cucumber JUnit ACL identity lookup command is selected",
    target_fixture="cucumber_junit_acl_identity_command",
)
def select_cucumber_junit_acl_identity_command() -> tuple[str, ...] | None:
    return windows_identity_lookup_command()


@then("the Cucumber JUnit ACL identity lookup should use System32 whoami on Windows")
def verify_cucumber_junit_acl_identity_command(
    cucumber_junit_acl_identity_command: tuple[str, ...] | None,
) -> None:
    assert_windows_identity_lookup_command(cucumber_junit_acl_identity_command)


@given("the Cucumber JUnit consumer output parent is read-only")
def make_cucumber_junit_parent_read_only(consumer: Any) -> None:
    directory = consumer._cucumber_junit_workspace / "read-only"
    directory.mkdir(exist_ok=True)
    if os.name == "nt":
        icacls = shutil.which("icacls.exe") or shutil.which("icacls")
        assert icacls is not None, "Windows icacls is required to prove an unwritable JUnit destination"
        identity_command = windows_identity_lookup_command()
        assert identity_command is not None, "Windows identity lookup is only available on Windows"
        sid = windows_acl_user_sid(identity_command)
        denied = subprocess.run(
            [icacls, str(directory), "/deny", f"*{sid}:(WD,AD)"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        assert denied.returncode == 0, f"could not deny writes to the JUnit output parent:\n{denied.stdout}\n{denied.stderr}"
        state = (directory, None, sid)
        consumer._cucumber_junit_readonly_directory = state
        try:
            (directory / ".write-permission-probe").write_text("probe", encoding="utf-8")
        except PermissionError:
            return
        except OSError as error:
            _restore_cucumber_junit_parent_permissions(consumer, state)
            raise AssertionError(f"the Windows ACL probe failed for an unexpected reason: {error}") from error
        else:
            _restore_cucumber_junit_parent_permissions(consumer, state)
            raise AssertionError("the denied Windows JUnit output ACL still permits creating files")

    original_mode = stat.S_IMODE(directory.stat().st_mode)
    directory.chmod(original_mode & ~0o222)
    try:
        probe = directory / ".write-permission-probe"
        probe.write_text("probe", encoding="utf-8")
    except PermissionError:
        pass
    else:
        probe.unlink()
        directory.chmod(original_mode)
        pytest.skip("filesystem does not enforce read-only directory permissions")
    consumer._cucumber_junit_readonly_directory = (directory, original_mode, None)


@then("the unwritable Cucumber JUnit destination should fail before the marker scenario runs")
def unwritable_cucumber_junit_destination_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, "PermissionError")
    assert "read-only" in output.lower(), output
    assert "write" in output.lower() or "permission" in output.lower(), output
    assert not (consumer._cucumber_junit_workspace / "read-only/report.xml").exists(), output


@given("the Cucumber JUnit consumer PATH excludes Node.js and npm")
def hide_cucumber_junit_runtime(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.pytest).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@given("the Cucumber JUnit consumer exposes Node.js without npm")
def expose_node_without_npm_for_cucumber_junit(consumer: Any) -> None:
    node, _, consumer_bin = _node_paths(consumer)
    isolated = consumer._cucumber_junit_workspace / "node-only"
    isolated.mkdir(exist_ok=True)
    node_name = "node.exe" if os.name == "nt" else "node"
    destination = isolated / node_name
    if os.name == "nt":
        shutil.copy2(node, destination)
    else:
        destination.symlink_to(Path(node).resolve())
        destination.chmod(destination.stat().st_mode | 0o111)
    consumer.env["PATH"] = os.pathsep.join((str(isolated), consumer_bin))
    consumer.env.pop("NODE_PATH", None)
    assert shutil.which("node", path=consumer.env["PATH"]) is not None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@given("the Cucumber JUnit consumer exposes Node.js and npm without the official formatter package")
def expose_node_and_npm_without_cucumber_junit_formatter(consumer: Any) -> None:
    node, npm, consumer_bin = _node_paths(consumer)
    entries = (str(Path(node).parent), str(Path(npm).parent), consumer_bin)
    consumer.env["PATH"] = os.pathsep.join(dict.fromkeys(entries))
    consumer.env.pop("NODE_PATH", None)
    assert shutil.which("node", path=consumer.env["PATH"]) is not None
    assert shutil.which("npm", path=consumer.env["PATH"]) is not None
    mask_npm_package_from_node_resolution(
        consumer._cucumber_junit_workspace,
        _CUCUMBER_JUNIT_PACKAGE,
    )


@then("missing Cucumber JUnit runtime diagnostics should stop the run before the marker scenario")
def missing_cucumber_junit_runtime_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, "node")
    assert "node" in output.lower() or "npm install" in output.lower(), output
    assert not (consumer._cucumber_junit_workspace / "artifacts/report.xml").exists(), output


@then("missing npm Cucumber JUnit diagnostics should stop the run before the marker scenario")
def missing_npm_cucumber_junit_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, "npm")
    assert "requires executable 'npm'" in output, output
    assert "cucumber-junit" in output, output
    assert not (consumer._cucumber_junit_workspace / "artifacts/report.xml").exists(), output


@then("the missing official Cucumber JUnit package should fail preflight before the marker scenario")
def missing_cucumber_junit_formatter_package_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, _CUCUMBER_JUNIT_PACKAGE)
    assert "npm install" in output.lower(), output
    assert not (consumer._cucumber_junit_workspace / "artifacts/report.xml").exists(), output


@given("the Cucumber JUnit consumer installs a Node preload that fails during XML finalization")
def install_cucumber_junit_finalization_preload(consumer: Any) -> None:
    preload = _write(
        consumer._cucumber_junit_workspace,
        "fail-cucumber-junit-finalization.cjs",
        _JUNIT_FINALIZATION_PRELOAD,
    )
    consumer.env["NODE_OPTIONS"] = f'--require="{preload.as_posix()}"'


@then("the Cucumber JUnit backend failure should be visible without publishing a partial report")
def cucumber_junit_backend_finalization_failure_is_visible(consumer: Any) -> None:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "Cucumber JUnit finalization failure sentinel" in output, output
    assert re.search(r"\b1 passed\b", output), output
    assert not (consumer._cucumber_junit_workspace / "artifacts/finalization.xml").exists(), output


@then("the public Cucumber JUnit example should preserve its contract and match live durations to Messages")
def public_cucumber_junit_example_preserves_contract(consumer: Any) -> None:
    assert consumer.cucumber_junit_result.returncode == 0, _junit_output(consumer)
    root, cases = _read_junit(consumer, "report.xml")
    assert len(cases) == 2, ET.tostring(root, encoding="unicode")
    assert root.get("tests", "2") == "2", root.attrib
    names = [case.get("name", "") for case in cases]
    assert len(set(names)) == 2, names
    assert any("#1.1" in name for name in names), names
    assert any("#1.2" in name for name in names), names
    assert all("Cucumber JUnit example café" in case.get("classname", "") for case in cases), cases
    for case in cases:
        assert float(case.get("time", "-1")) >= 0, case.attrib
        output = case.findtext("system-out", default="")
        assert "Cucumber JUnit example receives a profile document" in output, output
        assert "Cucumber JUnit example receives profile fields" in output, output
        assert "passed" in output.lower(), output
        expected_customer = "Ada" if "#1.1" in case.get("name", "") else "Boris"
        assert f'Cucumber JUnit example accepts "{expected_customer}"' in output, output
    _assert_junit_durations_match_messages(consumer, "report.xml", "artifacts/messages.ndjson")


@then("the public outline rows should identify their source URI and example line")
def public_outline_rows_retain_source_identity(consumer: Any) -> None:
    _, cases = _read_junit(consumer, "report.xml")
    expected_sources = {
        "#1.1": ("file:cucumber-junit-example.feature", "30"),
        "#1.2": ("file:cucumber-junit-example.feature", "31"),
    }
    actual_sources: dict[str, tuple[str | None, str | None]] = {}
    assert len(cases) == len(expected_sources), cases
    for case in cases:
        markers = [marker for marker in expected_sources if marker in case.get("name", "")]
        assert len(markers) == 1, case.attrib
        marker = markers[0]
        assert marker not in actual_sources, case.attrib
        actual_sources[marker] = (case.get("file"), case.get("line"))
    assert actual_sources == expected_sources, actual_sources


@then("duplicate-named Cucumber JUnit cases should retain source URI and line")
def duplicate_cucumber_junit_cases_retain_source_identity(consumer: Any) -> None:
    root, cases = _read_junit(consumer, "artifacts/duplicate-identities.xml")
    assert len(cases) == 2, ET.tostring(root, encoding="unicode")
    assert {case.get("classname") for case in cases} == {"Duplicate JUnit identity"}, cases
    assert {case.get("name") for case in cases} == {"Same scenario identity"}, cases
    source_locations = {(case.get("file"), case.get("line")) for case in cases}
    assert source_locations == {("file:alpha.feature", "2"), ("file:bravo.feature", "2")}, cases


@when("the consumer creates deterministic Cucumber JUnit Messages for golden comparison")
def prepare_deterministic_junit_messages(consumer: Any) -> None:
    _write_deterministic_junit_messages(consumer)


@when(parsers.re(r'I replay deterministic Cucumber JUnit Messages to "(?P<relative_path>[^"]+)"'))
def replay_deterministic_junit_messages(relative_path: str, consumer: Any) -> None:
    result = _run_junit_replay(consumer, "artifacts/deterministic-messages.ndjson", relative_path)
    assert result.returncode == 0, _junit_output(consumer, replay=True)


@then("deterministic Cucumber JUnit replay should match the pinned example golden including numeric durations")
def deterministic_cucumber_junit_replay_matches_pinned_golden(consumer: Any) -> None:
    _assert_junit_durations_match_messages(
        consumer,
        "report-replayed.xml",
        "artifacts/deterministic-messages.ndjson",
    )
    actual = _normalized_junit_artifact(consumer._cucumber_junit_workspace / "report-replayed.xml")
    golden_path = _PRODUCT_ROOT / "tests/fixtures/cucumber-junit/cucumber-junit-example.xml"
    golden = golden_path.read_text(encoding="utf-8")
    assert actual == golden, f"normalized deterministic replay XML differs from {golden_path}:\n{actual}"
