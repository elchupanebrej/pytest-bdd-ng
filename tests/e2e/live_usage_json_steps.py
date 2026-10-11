"""Installed-consumer BDD steps for Cucumber's Usage JSON formatter."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote

import pytest
from pytest_cuke import given, parsers, then, when
from tests.support.testing_utils import mask_npm_package_from_node_resolution


_PRODUCT_ROOT = Path(__file__).resolve().parents[2]
_CUCUMBER_PACKAGES = {"@cucumber/cucumber": "13.3.0"}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_IDENTITY_FEATURE = """\
Feature: Usage JSON identities
  Background:
    Given usage json shared background café

  Scenario Outline: The formatter records interpolated outline rows
    When usage json action for <value>
    Then usage json result for <value>

    Examples:
      | value |
      | alpha |
      | bravo |

  Scenario: Repeated execution keeps both usage matches
    When usage json repeated action
    When usage json repeated action
"""
_OUTCOMES_FEATURE = """\
Feature: Usage JSON outcomes
  Scenario: A passing step is reported
    Given usage json passing step

  Scenario: A failed step is reported
    When usage json failure sentinel

  Scenario: A skipped step is reported
    When usage json skip sentinel

  Scenario: An undefined step and its successor are reported
    Given usage json intentionally undefined step
    Then usage json successor after undefined step
"""
_REPORTS_FEATURE = """\
Feature: Usage JSON independent reports
  Scenario: The first report scenario passes
    Given usage json passing step

  Scenario: The second report scenario passes
    Given usage json passing step
"""
_MARKER_FEATURE = """\
Feature: Usage JSON preflight marker
  Scenario: The marker should run only after configuration succeeds
    Given usage json marker scenario starts
"""
_BACKEND_FEATURE = """\
Feature: Usage JSON backend finalization
  Scenario: The formatter backend fails after a passing scenario
    Given usage json passing step
"""
_SUPPORT_PLUGIN = """\
from pathlib import Path

import pytest
from pytest_cuke import given, parsers, then, when

ROOT = Path(__file__).parent


@given("usage json shared background café")
def usage_json_shared_background():
    pass


@when(
    parsers.cucumber_expression("usage json action for {word}"),
    anonymous_group_names=["value"],
)
def usage_json_action(value):
    assert value


@then(
    parsers.cucumber_expression("usage json result for {word}"),
    anonymous_group_names=["value"],
)
def usage_json_result(value):
    assert value


@when("usage json repeated action")
def usage_json_repeated_action():
    pass


@given("usage json passing step")
def usage_json_passing_step():
    pass


@when("usage json failure sentinel")
def usage_json_failure():
    raise AssertionError("usage JSON scenario failure sentinel")


@when("usage json skip sentinel")
def usage_json_skip():
    pytest.skip("usage JSON scenario skip sentinel")


@then("usage json successor after undefined step")
def usage_json_successor_after_undefined():
    pass


@given("usage json marker scenario starts")
def usage_json_marker_scenario_starts():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""
_USAGE_JSON_BACKEND_PRELOAD = """\
if (process.execArgv.some((argument) => argument.includes("UsageJsonFormatter"))) {
  process.once("beforeExit", () => {
    throw new Error("usage JSON backend finalization sentinel");
  });
}
"""


def _root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _safe_workspace(consumer: Any, workspace: str) -> Path:
    root = _root(consumer)
    relative = Path(workspace)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Usage JSON workspaces must stay inside the consumer project")
    destination = (root / relative).resolve()
    if root not in destination.parents and destination != root:
        raise ValueError("Usage JSON workspaces must stay inside the consumer project")
    return destination


def _write(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Usage JSON consumer files must stay inside the consumer project")
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _prepare(
    consumer: Any,
    *,
    feature: str,
    feature_name: str,
) -> Path:
    root = _safe_workspace(consumer, "usage-json café workspace with spaces")
    root.mkdir(parents=True, exist_ok=True)
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    _write(root, "pyproject.toml", config)
    _write(root, "usage_json_consumer_steps.py", _SUPPORT_PLUGIN)
    _write(root, "conftest.py", 'pytest_plugins = ["usage_json_consumer_steps"]\n')
    _write(root, f"features/{feature_name}", feature)
    (root / "artifacts").mkdir(exist_ok=True)
    consumer._usage_json_workspace = root
    return root


def _node_environment(consumer: Any) -> tuple[str, str, dict[str, str]] | None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None
    environment = dict(consumer.env)
    entries = (
        str(Path(node).parent),
        str(Path(npm).parent),
        str(Path(consumer.python).parent),
        os.defpath,
    )
    environment["PATH"] = os.pathsep.join(dict.fromkeys(entries))
    environment.pop("NODE_PATH", None)
    return node, npm, environment


def _install_official_runtime(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the real Cucumber Usage JSON acceptance lane requires Node.js and npm")
    node, npm, environment = runtime
    root = consumer._usage_json_workspace
    package_json = {
        "name": "pytest-cuke-usage-json-consumer",
        "private": True,
        "type": "module",
        "dependencies": _CUCUMBER_PACKAGES,
    }
    _write(root, "package.json", json.dumps(package_json, ensure_ascii=False, indent=2) + "\n")
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
        f"could not install pinned @cucumber/cucumber@13.3.0:\n{install.stdout}\n{install.stderr}"
    )
    metadata = root / "node_modules" / "@cucumber" / "cucumber" / "package.json"
    version = json.loads(metadata.read_text(encoding="utf-8")).get("version")
    assert version == _CUCUMBER_PACKAGES["@cucumber/cucumber"], version
    node_version = subprocess.run(
        [node, "--version"],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert node_version.returncode == 0, node_version.stderr
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)
    consumer._usage_json_node_version = node_version.stdout.strip()
    consumer._usage_json_cucumber_version = version


def _run(consumer: Any, arguments: str) -> subprocess.CompletedProcess[str]:
    root = consumer._usage_json_workspace
    try:
        result = subprocess.run(
            [str(consumer.pytest), *shlex.split(arguments)],
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
        state = getattr(consumer, "_usage_json_readonly_directory", None)
        if state is not None:
            directory, original_mode = state
            directory.chmod(original_mode)
            del consumer._usage_json_readonly_directory
    consumer.pytest_result = result
    return result


def _combined_output(consumer: Any) -> str:
    result = consumer.pytest_result
    assert result is not None, "the installed pytest process has not run"
    return f"{result.stdout}\n{result.stderr}"


def _read_usage_json(consumer: Any, relative_path: str) -> tuple[list[dict[str, Any]], str]:
    artifact = consumer._usage_json_workspace / relative_path
    assert artifact.is_file(), f"Usage JSON file was not created: {artifact}; {_combined_output(consumer)}"
    raw = artifact.read_bytes()
    text = raw.decode("utf-8", errors="strict")
    assert not raw.startswith(b"\xef\xbb\xbf"), "Usage JSON should be UTF-8 without a BOM"
    assert "\ufffd" not in text, "Usage JSON contains a replacement character"
    assert _ANSI.search(text) is None, f"Usage JSON contains terminal escape codes: {text!r}"
    document = json.loads(text)
    assert isinstance(document, list), f"the official Usage JSON schema is an array, got {type(document).__name__}"
    assert all(isinstance(definition, dict) for definition in document), document
    consumer._usage_json_last_report = document
    return document, text


def _normalized_usage_json_report(report: list[dict[str, Any]], workspace: Path) -> list[dict[str, Any]]:
    workspace = workspace.resolve()
    uri_prefixes = (
        (workspace.as_uri().rstrip("/"), "file:///workspace"),
        (f"file://{workspace.as_posix()}".rstrip("/"), "file:///workspace"),
        (workspace.as_posix().rstrip("/"), "<workspace>"),
    )

    def normalize_uri(value: str) -> str:
        normalized = value.replace("\\", "/")
        for prefix, replacement in uri_prefixes:
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return replacement + normalized[len(prefix) :]
        return normalized

    def normalize_duration(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: 0 if key in {"seconds", "nanos"} and isinstance(item, (int, float)) else normalize(item)
                for key, item in value.items()
            }
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return 0
        if isinstance(value, str):
            return "0"
        return normalize(value)

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            normalized: dict[str, Any] = {}
            for key, item in value.items():
                if key == "uri" and isinstance(item, str):
                    normalized[key] = normalize_uri(item)
                elif key in {"duration", "meanDuration"}:
                    normalized[key] = normalize_duration(item)
                else:
                    normalized[key] = normalize(item)
            return normalized
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    normalized = normalize(json.loads(json.dumps(report, ensure_ascii=False)))
    for definition in normalized:
        # Match array order is not contractual; retain and sort every record for semantic comparison.
        definition["matches"] = sorted(
            definition["matches"],
            key=lambda match: (match.get("uri", ""), match.get("line", 0), match.get("text", "")),
        )
    # Definition array order is also not contractual and can vary across fresh consumers.
    normalized.sort(
        key=lambda definition: (
            definition.get("pattern", ""),
            definition.get("uri", ""),
            definition.get("line", 0),
            definition.get("patternType", ""),
            definition.get("code", ""),
            json.dumps(definition, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
    )
    return cast(list[dict[str, Any]], normalized)


def _definition(report: list[dict[str, Any]], pattern_fragment: str) -> dict[str, Any]:
    found = [definition for definition in report if pattern_fragment in str(definition.get("pattern", ""))]
    assert len(found) == 1, f"expected one Usage JSON definition containing {pattern_fragment!r}, got {found!r}"
    definition = found[0]
    assert isinstance(definition.get("matches"), list), definition
    assert isinstance(definition.get("uri"), str) and definition["uri"], definition
    assert isinstance(definition.get("line"), int) and definition["line"] > 0, definition
    assert isinstance(definition.get("patternType"), str) and definition["patternType"], definition
    assert isinstance(definition.get("code"), str) and definition["code"], definition
    return definition


def _duration_nanoseconds(duration: Any) -> int:
    assert isinstance(duration, dict), duration
    seconds = duration.get("seconds")
    nanos = duration.get("nanos")
    assert isinstance(seconds, (int, float)) and isinstance(nanos, (int, float)), duration
    assert seconds >= 0 and nanos >= 0, duration
    return round(seconds * 1_000_000_000 + nanos)


def _assert_match_source(
    definition: dict[str, Any],
    *,
    uri_suffix: str,
    feature_line: int | list[int],
    expected_texts: list[str],
    durations: bool,
) -> None:
    matches = definition["matches"]
    assert len(matches) == len(expected_texts), matches
    assert Counter(match.get("text") for match in matches) == Counter(expected_texts), matches
    expected_lines = [feature_line] * len(matches) if isinstance(feature_line, int) else feature_line
    assert Counter(match.get("line") for match in matches) == Counter(expected_lines), matches
    for match in matches:
        assert str(match.get("uri", "")).replace("\\", "/").endswith(uri_suffix), match
        duration = match.get("duration")
        if durations:
            _duration_nanoseconds(duration)
        else:
            assert duration is None, match


def _feature_line(feature: str, text: str) -> int:
    return next(line_number for line_number, line in enumerate(feature.splitlines(), 1) if text in line)


def _feature_lines(feature: str, text: str) -> list[int]:
    return [line_number for line_number, line in enumerate(feature.splitlines(), 1) if text in line]


def _read_messages(consumer: Any, relative_path: str) -> list[dict[str, Any]]:
    path = consumer._usage_json_workspace / relative_path
    assert path.is_file(), f"Messages artifact is missing: {path}; {_combined_output(consumer)}"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _latest_test_run(envelopes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    run_starts = [index for index, envelope in enumerate(envelopes) if isinstance(envelope.get("testRunStarted"), dict)]
    assert run_starts, "Messages artifact has no TestRunStarted envelope"
    latest = envelopes[run_starts[-1] :]
    assert sum(isinstance(envelope.get("testRunStarted"), dict) for envelope in latest) == 1, latest
    assert sum(isinstance(envelope.get("testRunFinished"), dict) for envelope in latest) == 1, latest
    return latest


def _message_durations_by_definition_and_text(envelopes: list[dict[str, Any]]) -> dict[tuple[str, str], list[int]]:
    definitions = {
        envelope["stepDefinition"]["id"]: envelope["stepDefinition"]["pattern"]["source"]
        for envelope in envelopes
        if isinstance(envelope.get("stepDefinition"), dict)
    }
    pickles = {
        envelope["pickle"]["id"]: {
            step["id"]: step["text"] for step in envelope["pickle"].get("steps", []) if isinstance(step, dict)
        }
        for envelope in envelopes
        if isinstance(envelope.get("pickle"), dict)
    }
    test_cases = {
        envelope["testCase"]["id"]: envelope["testCase"]
        for envelope in envelopes
        if isinstance(envelope.get("testCase"), dict)
    }
    case_starts = {
        envelope["testCaseStarted"]["id"]: envelope["testCaseStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseStarted"), dict)
    }
    durations: dict[tuple[str, str], list[int]] = {}

    for envelope in envelopes:
        finished = envelope.get("testStepFinished")
        if not isinstance(finished, dict):
            continue
        started_id = finished.get("testCaseStartedId")
        assert started_id in case_starts, finished
        case_start = case_starts[started_id]
        test_case_id = case_start["testCaseId"]
        test_case = test_cases[test_case_id]
        test_step = next(
            (
                step
                for step in test_case.get("testSteps", [])
                if isinstance(step, dict) and step.get("id") == finished.get("testStepId")
            ),
            None,
        )
        assert test_step is not None, (test_case, finished)
        definition_ids = test_step.get("stepDefinitionIds", [])
        if not definition_ids:
            continue
        pickle_id = test_case["pickleId"]
        pickle_step_id = test_step.get("pickleStepId")
        step_text = pickles[pickle_id][pickle_step_id]
        duration = _duration_nanoseconds(finished["testStepResult"].get("duration"))
        for definition_id in definition_ids:
            pattern = definitions[definition_id]
            durations.setdefault((pattern, step_text), []).append(duration)

    return durations


def _assert_usage_json_durations_match_messages(consumer: Any) -> None:
    report, _ = _read_usage_json(consumer, "artifacts/usage.json")
    envelopes = _latest_test_run(_read_messages(consumer, "artifacts/messages.ndjson"))
    expected = _message_durations_by_definition_and_text(envelopes)
    observed: dict[tuple[str, str], list[int]] = {}

    for definition in report:
        pattern = str(definition.get("pattern", ""))
        for match in definition.get("matches", []):
            key = (pattern, str(match.get("text", "")))
            observed.setdefault(key, []).append(_duration_nanoseconds(match.get("duration")))

    assert set(observed) == set(expected), (observed, expected)
    for key, message_durations in expected.items():
        assert Counter(observed[key]) == Counter(message_durations), (key, observed[key], message_durations)

    for definition in report:
        mean_duration = definition.get("meanDuration")
        if mean_duration is None:
            continue
        matched_durations = [
            duration
            for (pattern, _), values in expected.items()
            if pattern == definition.get("pattern")
            for duration in values
        ]
        assert matched_durations, definition
        expected_mean = round(sum(matched_durations) / len(matched_durations))
        actual_mean = _duration_nanoseconds(mean_duration)
        assert abs(actual_mean - expected_mean) <= 1, (definition, expected_mean, actual_mean)


def _assert_usage_json_success(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _combined_output(consumer)


def _hide_node_and_npm(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    consumer.env.pop("NODE_PATH", None)


def _require_diagnostic_failure(consumer: Any, expected: str) -> str:
    result = consumer.pytest_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert expected.lower() in output.lower(), output
    assert not (consumer._usage_json_workspace / "scenario-started.marker").exists(), output
    return output


@given("the usage-json consumer prepares an outline and background feature in a Unicode workspace")
def prepare_usage_json_identity_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_IDENTITY_FEATURE, feature_name="usage-json-identities.feature")


@given("the consumer installs the pinned official Cucumber Usage JSON runtime")
def install_usage_json_runtime(consumer: Any) -> None:
    _install_official_runtime(consumer)


@when(parsers.re(r'I run installed pytest in the usage-json workspace with arguments "(?P<arguments>[^"]*)"'))
def run_usage_json_consumer_pytest(arguments: str, consumer: Any) -> None:
    _run(consumer, arguments)


@then("the Usage JSON artifact should preserve UTF-8 definitions matches and durations")
def usage_json_preserves_definition_match_identity(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    report, content = _read_usage_json(consumer, "artifacts/usage résultat.json")
    assert "café" in content, content
    assert len(report) > 0, report
    assert getattr(consumer, "_usage_json_cucumber_version", None) == "13.3.0"

    background = _definition(report, "usage json shared background café")
    assert background["uri"].replace("\\", "/").endswith("usage_json_consumer_steps.py"), background
    assert "usage-json café workspace with spaces/usage_json_consumer_steps.py" in unquote(background["uri"]).replace(
        "\\", "/"
    ), background
    assert background["patternType"] == "CucumberExpression", background
    _assert_match_source(
        background,
        uri_suffix="usage-json-identities.feature",
        feature_line=_feature_line(_IDENTITY_FEATURE, "Given usage json shared background café"),
        expected_texts=["usage json shared background café"] * 3,
        durations=True,
    )

    action = _definition(report, "usage json action for")
    _assert_match_source(
        action,
        uri_suffix="usage-json-identities.feature",
        feature_line=_feature_line(_IDENTITY_FEATURE, "When usage json action for <value>"),
        expected_texts=["usage json action for alpha", "usage json action for bravo"],
        durations=True,
    )
    result = _definition(report, "usage json result for")
    _assert_match_source(
        result,
        uri_suffix="usage-json-identities.feature",
        feature_line=_feature_line(_IDENTITY_FEATURE, "Then usage json result for <value>"),
        expected_texts=["usage json result for alpha", "usage json result for bravo"],
        durations=True,
    )
    repeated = _definition(report, "usage json repeated action")
    _assert_match_source(
        repeated,
        uri_suffix="usage-json-identities.feature",
        feature_line=_feature_lines(_IDENTITY_FEATURE, "When usage json repeated action"),
        expected_texts=["usage json repeated action"] * 2,
        durations=True,
    )
    consumer._usage_json_initial_patterns = [str(item.get("pattern", "")) for item in report]
    consumer._usage_json_initial_report_length = len(report)


@when("the consumer adds an unused Usage JSON definition")
def add_unused_usage_json_definition(consumer: Any) -> None:
    root = consumer._usage_json_workspace
    plugin = root / "usage_json_consumer_steps.py"
    with plugin.open("a", encoding="utf-8") as stream:
        stream.write(
            '\n\n@given("usage json newly unused definition")\ndef usage_json_newly_unused_definition():\n    pass\n'
        )


@then("the real Usage JSON artifact should include the unused definition without matches")
def usage_json_adds_unused_definition(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    report, _ = _read_usage_json(consumer, "artifacts/usage résultat.json")
    unused = _definition(report, "usage json newly unused definition")
    assert unused["matches"] == [], unused
    assert "meanDuration" not in unused, unused
    assert unused["uri"].replace("\\", "/").endswith("usage_json_consumer_steps.py"), unused
    assert len(report) == consumer._usage_json_initial_report_length + 1, report
    assert not any("usage json newly unused definition" in pattern for pattern in consumer._usage_json_initial_patterns)
    consumer._usage_json_initial_report_length = len(report)


@when("the consumer selects Usage JSON through cuke_usage_json configuration")
def configure_usage_json_path(consumer: Any) -> None:
    root = consumer._usage_json_workspace
    path = "artifacts/configured usage résumé.json"
    config = (
        "[tool.pytest.ini_options]\n"
        "cuke_autoload = true\n"
        "cuke_features_dir = 'features'\n"
        f"cuke_usage_json = {json.dumps(path, ensure_ascii=False)}\n"
    )
    (root / "pyproject.toml").write_text(config, encoding="utf-8")
    consumer._usage_json_configured_path = path


@then("the configured Usage JSON path should contain the real schema")
def configured_usage_json_path_is_written(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    report, content = _read_usage_json(consumer, consumer._usage_json_configured_path)
    assert report and "café" in content, report
    assert "UsageJsonFormatter" not in _combined_output(consumer), _combined_output(consumer)


@given("the usage-json consumer prepares passing failing skipped and undefined scenarios")
def prepare_usage_json_outcomes_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_OUTCOMES_FEATURE, feature_name="usage-json-outcomes.feature")


@then("the Usage JSON artifact should retain matched steps across all outcomes and pytest should fail")
def usage_json_is_valid_for_mixed_outcomes(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "usage JSON scenario failure sentinel" in output, output
    report, _ = _read_usage_json(consumer, "artifacts/outcomes.json")
    passed = _definition(report, "usage json passing step")
    _assert_match_source(
        passed,
        uri_suffix="usage-json-outcomes.feature",
        feature_line=_feature_line(_OUTCOMES_FEATURE, "Given usage json passing step"),
        expected_texts=["usage json passing step"],
        durations=True,
    )
    failed = _definition(report, "usage json failure sentinel")
    _assert_match_source(
        failed,
        uri_suffix="usage-json-outcomes.feature",
        feature_line=_feature_line(_OUTCOMES_FEATURE, "When usage json failure sentinel"),
        expected_texts=["usage json failure sentinel"],
        durations=True,
    )
    skipped = _definition(report, "usage json skip sentinel")
    _assert_match_source(
        skipped,
        uri_suffix="usage-json-outcomes.feature",
        feature_line=_feature_line(_OUTCOMES_FEATURE, "When usage json skip sentinel"),
        expected_texts=["usage json skip sentinel"],
        durations=False,
    )
    successor = _definition(report, "usage json successor after undefined step")
    _assert_match_source(
        successor,
        uri_suffix="usage-json-outcomes.feature",
        feature_line=_feature_line(_OUTCOMES_FEATURE, "Then usage json successor after undefined step"),
        expected_texts=["usage json successor after undefined step"],
        durations=False,
    )
    assert not any("intentionally undefined step" in str(item.get("pattern")) for item in report), report


@then("the Messages artifact should report passed failed skipped and undefined outcomes")
def messages_report_usage_json_mixed_outcomes(consumer: Any) -> None:
    messages = _read_messages(consumer, "artifacts/messages.ndjson")
    assert messages[-1].get("testRunFinished", {}).get("success") is False, messages[-1]
    statuses = {row["testStepFinished"]["testStepResult"]["status"] for row in messages if "testStepFinished" in row}
    assert {"PASSED", "FAILED", "SKIPPED", "UNDEFINED"} <= statuses, statuses


@given("the usage-json consumer prepares two passing scenarios for combined reports")
def prepare_usage_json_coexistence_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_REPORTS_FEATURE, feature_name="usage-json-combined-reports.feature")


@then("Usage JSON Summary Messages Cucumber JSON and JUnit should be distinct valid outputs")
def usage_json_coexists_with_independent_reports(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    root = consumer._usage_json_workspace
    usage, usage_text = _read_usage_json(consumer, "artifacts/usage.json")
    messages = _read_messages(consumer, "artifacts/messages.ndjson")
    cucumber_path = root / "artifacts/cucumber.json"
    junit_path = root / "artifacts/junit.xml"
    assert cucumber_path.is_file() and junit_path.is_file(), _combined_output(consumer)
    cucumber_json = json.loads(cucumber_path.read_text(encoding="utf-8"))
    junit_root = ET.parse(junit_path).getroot()
    assert isinstance(cucumber_json, list) and len(cucumber_json) == 1, cucumber_json
    assert len(cucumber_json[0].get("elements", [])) == 2, cucumber_json
    assert junit_root.tag in {"testsuite", "testsuites"}, junit_root.tag
    assert len(list(junit_root.iter("testcase"))) == 2, ET.tostring(junit_root, encoding="unicode")
    assert messages[-1].get("testRunFinished", {}).get("success") is True, messages[-1]
    assert len([row for row in messages if "testCase" in row]) == 2
    assert _definition(usage, "usage json passing step")["matches"]
    output = _combined_output(consumer)
    assert "2 scenarios" in output.lower() and "2 passed" in output.lower(), output
    assert "usage json passing step" not in output, output
    destinations = [
        root / "artifacts" / name
        for name in (
            "usage.json",
            "messages.ndjson",
            "cucumber.json",
            "junit.xml",
        )
    ]
    assert len({path.resolve() for path in destinations}) == 4, destinations
    assert usage_text != (root / "artifacts/messages.ndjson").read_text(encoding="utf-8")
    assert usage_text != cucumber_path.read_text(encoding="utf-8")


@then("Usage JSON and live progress should both report the two passing scenarios")
def usage_json_coexists_with_live_progress(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    report, _ = _read_usage_json(consumer, "artifacts/usage.json")
    passing_step = _definition(report, "usage json passing step")
    assert len(passing_step["matches"]) == 2, passing_step
    for match in passing_step["matches"]:
        _duration_nanoseconds(match.get("duration"))

    output = _combined_output(consumer)
    progress_lines = [
        line.strip()
        for line in output.splitlines()
        if re.fullmatch(r"[.FPAU?\-]+", line.strip())
    ]
    assert progress_lines == [".", "."], output
    assert re.search(r"\b2 scenarios\b.*\b2 passed\b", output), output


@given("the usage-json consumer prepares a marker scenario for preflight checks")
def prepare_usage_json_preflight_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_MARKER_FEATURE, feature_name="usage-json-preflight-marker.feature")


@then("the missing Usage JSON parent should fail before the marker scenario runs")
def missing_usage_json_parent_preflights(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "parent")
    assert "missing-parent" in output, output


@then("duplicate canonical Usage JSON outputs should fail before the marker scenario runs")
def duplicate_usage_json_destination_preflights(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "report.json")
    assert any(word in output.lower() for word in ("duplicate", "same output", "same path")), output


@then("competing terminal formatters should fail before the marker scenario runs")
def competing_usage_json_terminal_formatters_preflight(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "formatter")
    assert any(word in output.lower() for word in ("terminal", "stdout", "only one")), output


@then("an empty Usage JSON path should fail before the marker scenario runs")
def empty_usage_json_path_preflights(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "cuke-usage-json")
    assert any(word in output.lower() for word in ("empty", "required", "path")), output


@given("the Usage JSON output parent is read-only")
def make_usage_json_parent_read_only(consumer: Any) -> None:
    directory = consumer._usage_json_workspace / "read-only"
    directory.mkdir(exist_ok=True)
    original_mode = stat.S_IMODE(directory.stat().st_mode)
    directory.chmod(original_mode & ~0o222)
    probe = directory / "write-probe"
    try:
        probe.write_text("probe", encoding="utf-8")
    except OSError:
        consumer._usage_json_readonly_directory = (directory, original_mode)
    else:
        probe.unlink(missing_ok=True)
        directory.chmod(original_mode)
        pytest.skip("the current platform or user can still write into a read-only directory")


@then("the unwritable Usage JSON destination should fail before the marker scenario runs")
def unwritable_usage_json_destination_preflights(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert any(text in output.lower() for text in ("not writable", "permission denied", "permissionerror")), output
    assert not (consumer._usage_json_workspace / "scenario-started.marker").exists(), output


@given("the usage-json consumer prepares a passing marker scenario")
def prepare_usage_json_default_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_MARKER_FEATURE, feature_name="usage-json-default.feature")


@given("the usage-json consumer PATH excludes Node.js and npm")
def hide_node_and_npm_for_usage_json(consumer: Any) -> None:
    _hide_node_and_npm(consumer)


@then("the normal scenario should pass without starting a Usage JSON backend")
def default_usage_json_is_inactive(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    assert (consumer._usage_json_workspace / "scenario-started.marker").is_file()
    assert not (consumer._usage_json_workspace / "artifacts/usage.json").exists()
    output = _combined_output(consumer).lower()
    assert "node.js" not in output and "npm" not in output and "cucumber/cucumber" not in output, output


@given("the usage-json consumer prepares a marker scenario for dependency checks")
def prepare_usage_json_dependency_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_MARKER_FEATURE, feature_name="usage-json-dependency-marker.feature")


@then("missing Node diagnostics should stop the Usage JSON run before the marker scenario")
def missing_node_usage_json_preflights(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "node")
    assert "usage-json" in output.lower() or "cucumber-usage-json" in output.lower(), output


@given("the usage-json consumer exposes Node.js without npm")
def expose_node_without_npm_for_usage_json(consumer: Any) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("the missing-npm Usage JSON check requires a host Node.js executable")
    root = consumer._usage_json_workspace
    isolated = root / "node-without-npm"
    isolated.mkdir(exist_ok=True)
    name = "node.exe" if os.name == "nt" else "node"
    destination = isolated / name
    if os.name == "nt":
        shutil.copy2(node, destination)
    else:
        destination.symlink_to(Path(node).resolve())
        destination.chmod(destination.stat().st_mode | 0o111)
    consumer.env["PATH"] = os.pathsep.join((str(isolated), str(Path(consumer.python).parent)))
    consumer.env.pop("NODE_PATH", None)


@then("missing npm diagnostics should stop the Usage JSON run before the marker scenario")
def missing_npm_usage_json_preflights(consumer: Any) -> None:
    _require_diagnostic_failure(consumer, "npm")


@given("the usage-json consumer restores Node.js and npm without installing Cucumber")
def expose_node_and_npm_without_cucumber_for_usage_json(consumer: Any) -> None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        pytest.skip("the missing-package Usage JSON check requires host Node.js and npm executables")
    entries = (str(Path(node).parent), str(Path(npm).parent), str(Path(consumer.python).parent), os.defpath)
    consumer.env["PATH"] = os.pathsep.join(dict.fromkeys(entries))
    consumer.env.pop("NODE_PATH", None)
    mask_npm_package_from_node_resolution(consumer._usage_json_workspace, "@cucumber/cucumber")


@then("missing Cucumber package diagnostics should stop the Usage JSON run before the marker scenario")
def missing_cucumber_usage_json_preflights(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "@cucumber/cucumber")
    assert "npm install" in output.lower(), output


@given("the usage-json consumer prepares a passing marker scenario for package resolution")
def prepare_usage_json_package_resolution_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_MARKER_FEATURE, feature_name="usage-json-package-resolution.feature")


@given("the usage-json consumer exposes a resolvable Cucumber package with a failing entrypoint")
def expose_failing_usage_json_package_entrypoint(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the package resolution Usage JSON check requires host Node.js and npm executables")
    _, _, environment = runtime
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)

    package = _safe_workspace(consumer, "usage-json café workspace with spaces/node_modules/@cucumber/cucumber")
    package.mkdir(parents=True, exist_ok=True)
    (package / "package.json").write_text(
        json.dumps(
            {
                "name": "@cucumber/cucumber",
                "type": "module",
                "exports": {".": "./index.js"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (package / "index.js").write_text(
        'import { writeFileSync } from "node:fs";\n'
        'export const FormatterBuilder = {};\n'
        'export const UsageJsonFormatter = {};\n'
        'export const formatterHelpers = {};\n'
        'export const supportCodeLibraryBuilder = {};\n'
        'writeFileSync(new URL("./entrypoint-executed.marker", import.meta.url), "loaded\\n");\n'
        'throw new Error("Usage JSON formatter sink package entrypoint sentinel");\n',
        encoding="utf-8",
    )


@then("the formatter sink failure should remain visible after scenario execution")
def usage_json_package_resolution_does_not_execute_entrypoint(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert (consumer._usage_json_workspace / "scenario-started.marker").is_file(), output
    package_marker = consumer._usage_json_workspace / "node_modules/@cucumber/cucumber/entrypoint-executed.marker"
    assert package_marker.is_file(), output
    assert "SINK_FAILURE" in output, output
    assert "requires npm package '@cucumber/cucumber'" not in output.lower(), output
    assert re.search(r"\b1 passed\b", output), output
    assert re.search(r"\b1 failed\b", output) is None, output


@given("the usage-json consumer prepares a passing scenario for backend finalization")
def prepare_usage_json_backend_failure_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_BACKEND_FEATURE, feature_name="usage-json-backend-finalization.feature")


@given("the usage-json consumer installs a Node preload that fails during Usage JSON finalization")
def install_usage_json_backend_failure_preload(consumer: Any) -> None:
    root = consumer._usage_json_workspace
    preload = _write(root, "fail-usage-json-backend.cjs", _USAGE_JSON_BACKEND_PRELOAD)
    consumer.env["NODE_OPTIONS"] = f'--require="{preload.as_posix()}"'


@then("the Usage JSON backend failure should remain visible")
def usage_json_backend_failure_is_visible(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "usage JSON backend finalization sentinel" in output, output
    assert re.search(r"\b1 passed\b", output), output
    assert re.search(r"\b1 failed\b", output) is None, output


@given("the public Cucumber Usage JSON example is copied to the installed consumer")
def copy_public_usage_json_example_to_consumer(consumer: Any) -> None:
    source = _PRODUCT_ROOT / "examples" / "cucumber-usage-json"
    destination = Path(consumer.path) / "cucumber-usage-json-example"
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destination / "artifacts").mkdir(exist_ok=True)
    consumer._usage_json_workspace = destination.resolve()
    consumer._usage_json_readonly_directory = None


@then("the public Usage JSON example should preserve used and unused definitions")
def public_usage_json_example_preserves_definition_semantics(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    report, _ = _read_usage_json(consumer, "artifacts/usage.json")
    assert consumer._usage_json_cucumber_version == "13.3.0"
    assert len(report) == 4, report

    workspace = consumer._usage_json_workspace
    feature_source = (workspace / "features/cucumber-usage-json-example.feature").read_text(encoding="utf-8")
    step_source = (workspace / "cucumber_usage_json_example_steps.py").read_text(encoding="utf-8")
    background = _definition(report, "the Usage JSON example starts a clean request")
    assert background["pattern"] == "the Usage JSON example starts a clean request", background
    assert background["patternType"] == "CucumberExpression", background
    assert background["uri"].replace("\\", "/").endswith("cucumber_usage_json_example_steps.py"), background
    assert background["line"] == _feature_line(
        step_source,
        '@given("the Usage JSON example starts a clean request")',
    )
    _assert_match_source(
        background,
        uri_suffix="cucumber-usage-json-example.feature",
        feature_line=_feature_line(feature_source, "Given the Usage JSON example starts a clean request"),
        expected_texts=["the Usage JSON example starts a clean request"] * 2,
        durations=True,
    )

    handler = _definition(report, "the Usage JSON example handles")
    assert handler["pattern"] == "the Usage JSON example handles {word}", handler
    assert handler["patternType"] == "CucumberExpression", handler
    assert handler["uri"].replace("\\", "/").endswith("cucumber_usage_json_example_steps.py"), handler
    assert handler["line"] == _feature_line(step_source, "@when(")
    _assert_match_source(
        handler,
        uri_suffix="cucumber-usage-json-example.feature",
        feature_line=_feature_line(feature_source, "When the Usage JSON example handles <value>"),
        expected_texts=["the Usage JSON example handles alpha", "the Usage JSON example handles bravo"],
        durations=True,
    )

    recorder = _definition(report, "the Usage JSON example records")
    assert recorder["pattern"] == "the Usage JSON example records {word}", recorder
    assert recorder["patternType"] == "CucumberExpression", recorder
    assert recorder["uri"].replace("\\", "/").endswith("cucumber_usage_json_example_steps.py"), recorder
    assert recorder["line"] == _feature_line(step_source, "@then(")
    _assert_match_source(
        recorder,
        uri_suffix="cucumber-usage-json-example.feature",
        feature_line=_feature_line(feature_source, "Then the Usage JSON example records <value>"),
        expected_texts=["the Usage JSON example records alpha", "the Usage JSON example records bravo"],
        durations=True,
    )

    unused = _definition(report, "the Usage JSON example documents an unused definition")
    assert unused["pattern"] == "the Usage JSON example documents an unused definition", unused
    assert unused["patternType"] == "CucumberExpression", unused
    assert unused["uri"].replace("\\", "/").endswith("cucumber_usage_json_example_steps.py"), unused
    assert unused["matches"] == [], unused
    assert "meanDuration" not in unused, unused
    consumer._usage_json_example_baseline_patterns = {str(item.get("pattern", "")) for item in report}
    consumer._usage_json_example_baseline_count = len(report)


@then("Usage JSON match durations should equal the emitted Messages durations")
def usage_json_match_durations_match_messages(consumer: Any) -> None:
    _assert_usage_json_durations_match_messages(consumer)


@when("the consumer adds a new unused definition to the public Usage JSON example")
def add_new_unused_public_usage_json_definition(consumer: Any) -> None:
    plugin = consumer._usage_json_workspace / "cucumber_usage_json_example_steps.py"
    with plugin.open("a", encoding="utf-8") as stream:
        stream.write(
            '\n\n@given("the Usage JSON example introduces a new unused definition")\n'
            "def newly_unused_definition():\n"
            '    """This added definition should appear without matches."""\n'
        )


@then("the newly added Usage JSON definition should appear without matches")
def newly_added_usage_json_definition_is_present(consumer: Any) -> None:
    _assert_usage_json_success(consumer)
    report, _ = _read_usage_json(consumer, "artifacts/usage.json")
    baseline_patterns = consumer._usage_json_example_baseline_patterns
    newly_added_pattern = "the Usage JSON example introduces a new unused definition"
    assert newly_added_pattern not in baseline_patterns, baseline_patterns
    assert len(report) == consumer._usage_json_example_baseline_count + 1, report
    assert {str(item.get("pattern", "")) for item in report} >= baseline_patterns, report
    added = _definition(report, newly_added_pattern)
    assert added["pattern"] == newly_added_pattern, added
    assert added["matches"] == [], added
    assert "meanDuration" not in added, added
    built_in_unused = _definition(report, "the Usage JSON example documents an unused definition")
    assert built_in_unused["matches"] == [], built_in_unused


@then("the real pinned Usage JSON artifact should match the checked-in semantic golden")
def real_pinned_usage_json_matches_semantic_golden(consumer: Any) -> None:
    report, _ = _read_usage_json(consumer, "artifacts/usage.json")
    actual = _normalized_usage_json_report(report, consumer._usage_json_workspace)
    golden_path = _PRODUCT_ROOT / "tests/fixtures/cucumber-usage-json/cucumber-usage-json-example.golden.json"
    assert golden_path.is_file(), f"the pinned Usage JSON semantic golden is missing: {golden_path}"
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    assert actual == expected, (
        "normalized live Usage JSON differs from the pinned Cucumber semantic golden:\n"
        f"{json.dumps(actual, ensure_ascii=False, indent=2)}"
    )
