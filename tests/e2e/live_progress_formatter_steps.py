"""Installed-consumer BDD steps for the live Cucumber progress formatter."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, then
from pytest_cuke.model.message_stream_validation import validate_message_stream
from pytest_cuke.model.message_validation import validate_envelope
from pytest_cuke.model.message_types import message_from_dict


_PROGRESS_SUPPORT = '''\
from pathlib import Path

import pytest
from pytest_cuke import given, then

ROOT = Path(__file__).parent


@given("a progress scenario passes")
def progress_scenario_passes():
    pass


@given("a progress scenario fails before its following step")
def progress_scenario_fails_before_following_step():
    raise AssertionError("progress failed step sentinel")


@then("the step after the failure remains skipped")
def step_after_progress_failure_remains_skipped():
    pass


@given("a progress scenario deliberately skips")
def progress_scenario_deliberately_skips():
    pytest.skip("progress skip sentinel")


@given("the first retry attempt fails and the second passes")
def first_retry_attempt_fails_then_passes():
    counter = ROOT / "retry-attempt-count.txt"
    attempt = int(counter.read_text(encoding="utf-8")) if counter.exists() else 0
    counter.write_text(str(attempt + 1), encoding="utf-8")
    if attempt == 0:
        raise AssertionError("progress first retry attempt sentinel")
'''

_OUTCOME_FEATURE = '''\
Feature: Progress status projection
  Scenario: A passing progress scenario
    Given a progress scenario passes

  Scenario: Failure survives a skipped continuation
    Given a progress scenario fails before its following step
    Then the step after the failure remains skipped

  Scenario: An independent progress scenario passes
    Given a progress scenario passes

  Scenario: A progress scenario is skipped
    Given a progress scenario deliberately skips

  Scenario: A progress scenario is undefined
    When an undefined progress step is reached
'''

_RETRY_FEATURE = '''\
Feature: Progress retry projection
  Scenario: A retryable progress scenario records both attempts
    Given the first retry attempt fails and the second passes
'''

_OFFICIAL_PACKAGES = {
    "@cucumber/messages": "34.2.1",
    "@cucumber/pretty-formatter": "4.0.2",
    "@cucumber/query": "16.1.1",
    "luxon": "3.7.2",
}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_MARKERS = {
    "AMBIGUOUS": "A",
    "FAILED": "F",
    "PASSED": ".",
    "PENDING": "P",
    "SKIPPED": "-",
    "UNDEFINED": "U",
    "UNKNOWN": "?",
}
_SEVERITY = {
    "UNKNOWN": 0,
    "PASSED": 1,
    "SKIPPED": 2,
    "PENDING": 3,
    "UNDEFINED": 4,
    "AMBIGUOUS": 5,
    "FAILED": 6,
}


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("progress consumer files must stay inside the consumer project")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _prepare_consumer(consumer: Any, feature: str, feature_name: str) -> None:
    root = _consumer_root(consumer)
    _write_file(root, "pyproject.toml", "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n")
    _write_file(root, "conftest.py", 'pytest_plugins = ["progress_consumer_steps"]\n')
    _write_file(root, "progress_consumer_steps.py", _PROGRESS_SUPPORT)
    _write_file(root, f"features/{feature_name}", feature)


def _node_environment(consumer: Any) -> tuple[str, str, dict[str, str]] | None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None
    environment = dict(consumer.env)
    environment["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), str(Path(consumer.python).parent), os.defpath))
    )
    return node, npm, environment


@given("the consumer prepares a progress feature with passing, failed, skipped, and undefined scenarios")
def prepare_progress_outcome_feature(consumer: Any) -> None:
    _prepare_consumer(consumer, _OUTCOME_FEATURE, "progress-outcomes.feature")
    consumer._progress_message_path = _consumer_root(consumer) / "progress.ndjson"


@given("the consumer prepares a retryable progress scenario and installs pytest-rerunfailures")
def prepare_retryable_progress_scenario(consumer: Any) -> None:
    _prepare_consumer(consumer, _RETRY_FEATURE, "progress-retry.feature")
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("the retry progress lane requires uv to install pytest-rerunfailures")
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


@given("the consumer installs the pinned official Cucumber progress formatter packages")
def install_official_progress_packages(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the official Cucumber progress lane requires both Node.js and npm")
    _, npm, environment = runtime
    root = _consumer_root(consumer)
    package_json = {
        "name": "pytest-cuke-live-progress-consumer",
        "private": True,
        "type": "module",
        "dependencies": _OFFICIAL_PACKAGES,
    }
    _write_file(root, "package.json", json.dumps(package_json, indent=2) + "\n")
    install = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert install.returncode == 0, f"could not install the pinned Cucumber progress runtime:\n{install.stdout}\n{install.stderr}"
    consumer.env["PATH"] = environment["PATH"]


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this consumer"
    return _ANSI.sub("", f"{result.stdout}\n{result.stderr}")


def _messages(consumer: Any, relative_path: str) -> list[dict[str, Any]]:
    path = _consumer_root(consumer) / relative_path
    assert path.is_file(), f"Cucumber Messages artifact was not written: {path}"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and all(isinstance(row, dict) for row in rows), rows
    envelopes = []
    for line_number, row in enumerate(rows, start=1):
        envelope = message_from_dict(row)
        diagnostics = validate_envelope(envelope)
        assert not diagnostics, f"invalid Messages envelope at line {line_number}: {diagnostics!r}"
        envelopes.append(envelope)
    diagnostics = validate_message_stream(envelopes)
    assert not diagnostics, f"invalid Cucumber Messages lifecycle: {diagnostics!r}"
    return rows


def _attempts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pickles = {message["pickle"]["id"]: message["pickle"]["name"] for message in rows if "pickle" in message}
    test_cases = {message["testCase"]["id"]: message["testCase"]["pickleId"] for message in rows if "testCase" in message}
    started = {message["testCaseStarted"]["id"]: message["testCaseStarted"] for message in rows if "testCaseStarted" in message}
    statuses: dict[str, list[str]] = defaultdict(list)
    for message in rows:
        step_finished = message.get("testStepFinished")
        if step_finished is not None:
            statuses[step_finished["testCaseStartedId"]].append(step_finished["testStepResult"]["status"])

    result = []
    for message in rows:
        finished = message.get("testCaseFinished")
        if finished is None:
            continue
        started_id = finished["testCaseStartedId"]
        start = started[started_id]
        pickle_id = test_cases[start["testCaseId"]]
        step_statuses = statuses[started_id]
        status = max(step_statuses, key=lambda item: _SEVERITY[item], default="PASSED")
        result.append(
            {
                "id": started_id,
                "attempt": start.get("attempt"),
                "name": pickles[pickle_id],
                "status": status,
                "step_statuses": step_statuses,
            }
        )
    return result


def _marker_line(output: str) -> str:
    candidates = [line.strip() for line in output.splitlines() if re.fullmatch(r"[.FPAU?\-]+", line.strip())]
    assert candidates, f"no compact Cucumber progress marker line was found:\n{output}"
    return candidates[-1]


@then(re.compile(r'Cucumber progress markers should match every completed scenario attempt in "(?P<relative_path>[^"]+)"'))
def progress_markers_match_attempt_messages(relative_path: str, consumer: Any) -> None:
    rows = _messages(consumer, relative_path)
    attempts = _attempts(rows)
    expected = "".join(_MARKERS[attempt["status"]] for attempt in attempts)
    actual = _marker_line(_output(consumer))
    assert actual == expected, f"one progress marker per scenario attempt expected {expected!r}, got {actual!r}"
    assert len(actual) == len(attempts), (actual, attempts)
    assert len({attempt["id"] for attempt in attempts}) == len(attempts), attempts
    assert {attempt["status"] for attempt in attempts} == {"PASSED", "FAILED", "SKIPPED", "UNDEFINED"}, attempts
    failure = next(attempt for attempt in attempts if attempt["name"] == "Failure survives a skipped continuation")
    assert failure["step_statuses"] == ["FAILED", "SKIPPED"], failure
    assert failure["status"] == "FAILED", failure


@then("the final Cucumber progress summary should report the four scenario outcomes")
def final_progress_summary_reports_outcomes(consumer: Any) -> None:
    output = _output(consumer)
    scenario_line = next((line for line in output.splitlines() if re.search(r"\b5 scenarios?\b", line)), None)
    assert scenario_line is not None, f"the official Cucumber scenario summary is missing:\n{output}"
    for expected in ("2 passed", "1 failed", "1 skipped", "1 undefined"):
        assert expected in scenario_line, f"summary omitted {expected!r}: {scenario_line!r}"
    assert "Failure survives a skipped continuation" in output, output
    assert "A progress scenario is undefined" in output, output


@then(re.compile(r'retry progress markers should correlate with distinct TestCaseStarted IDs in "(?P<relative_path>[^"]+)"'))
def retry_markers_correlate_with_attempt_ids(relative_path: str, consumer: Any) -> None:
    rows = _messages(consumer, relative_path)
    attempts = _attempts(rows)
    assert len(attempts) == 2, attempts
    attempt_numbers = [attempt["attempt"] for attempt in attempts]
    assert all(isinstance(number, int) for number in attempt_numbers), attempts
    assert attempt_numbers[1] > attempt_numbers[0], attempts
    assert len({attempt["id"] for attempt in attempts}) == 2, attempts
    assert [attempt["status"] for attempt in attempts] == ["FAILED", "PASSED"], attempts
    assert _marker_line(_output(consumer)) == "F.", _output(consumer)
