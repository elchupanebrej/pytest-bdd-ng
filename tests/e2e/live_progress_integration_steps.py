"""Installed-consumer BDD steps for progress selection and terminal integration."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, then, when
from pytest_cuke.model.message_stream_validation import validate_message_stream
from pytest_cuke.model.message_validation import validate_envelope
from pytest_cuke.model.message_types import message_from_dict
from tests.support.testing_utils import mask_npm_package_from_node_resolution


_SUPPORT_PLUGIN = '''\
from pathlib import Path
import time

import pytest
from pytest_cuke import given, when, then

ROOT = Path(__file__).parent


@given("a progress consumer scenario passes")
def progress_consumer_scenario_passes():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
    print("PROGRESS_TEE_SYS_SENTINEL")


@given("the progress consumer scenario records that it started")
def progress_consumer_scenario_records_start():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")


@given("a progress consumer scenario deliberately skips")
def progress_consumer_scenario_skips():
    pytest.skip("progress integration skip sentinel")


@when("the later progress scenario waits for release")
def later_progress_scenario_waits_for_release():
    (ROOT / "gated-started.marker").write_text("started", encoding="utf-8")
    deadline = time.monotonic() + 30
    release = ROOT / "release-gated-scenario.marker"
    while time.monotonic() < deadline and not release.is_file():
        time.sleep(0.01)
    assert release.is_file(), "the progress marker observer did not release the later scenario"
    (ROOT / "gated-finished.marker").write_text("finished", encoding="utf-8")


@then("the later progress scenario is released")
def later_progress_scenario_is_released():
    assert (ROOT / "gated-finished.marker").is_file()
'''

_ONE_PASS_FEATURE = '''\
Feature: Default progress selection
  Scenario: The normal consumer scenario passes
    Given a progress consumer scenario passes
'''

_TWO_PASS_FEATURE = '''\
Feature: Progress file formatter coexistence
  Scenario: The first Unicode consumer scenario passes
    Given a progress consumer scenario passes

  Scenario: The second Unicode consumer scenario passes
    Given a progress consumer scenario passes
'''

_PREFLIGHT_FEATURE = '''\
Feature: Progress formatter preflight
  Scenario: The progress scenario must not start before preflight succeeds
    Given the progress consumer scenario records that it started
'''

_GATED_FEATURE = '''\
Feature: Live progress marker forwarding
  Scenario: A skipped scenario finishes first
    Given a progress consumer scenario deliberately skips

  Scenario: The later progress scenario remains gated
    When the later progress scenario waits for release
    Then the later progress scenario is released
'''

_OFFICIAL_PACKAGES = {
    "@cucumber/messages": "34.2.1",
    "@cucumber/pretty-formatter": "4.0.2",
    "@cucumber/query": "16.1.1",
    "luxon": "3.7.2",
}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_MARKER_LINE = re.compile(r"[.FPAU?\-]+")


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _safe_workspace(consumer: Any, workspace: str | None = None) -> Path:
    root = _consumer_root(consumer)
    destination = Path(workspace) if workspace else Path(".")
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("progress workspace must stay inside the consumer project")
    result = (root / destination).resolve()
    if root not in result.parents and result != root:
        raise ValueError("progress workspace must stay inside the consumer project")
    return result


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("progress consumer files must stay inside the consumer project")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _prepare(consumer: Any, feature: str, *, feature_name: str, workspace: str | None = None, ini_enabled: bool = False) -> Path:
    root = _safe_workspace(consumer, workspace)
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    if ini_enabled:
        config += "cuke_progress = true\n"
    _write_file(root, "pyproject.toml", config)
    _write_file(root, "conftest.py", 'pytest_plugins = ["progress_integration_steps"]\n')
    _write_file(root, "progress_integration_steps.py", _SUPPORT_PLUGIN)
    _write_file(root, f"features/{feature_name}", feature)
    consumer._progress_integration_workspace = root
    return root


def _runtime_paths(consumer: Any) -> tuple[str, str, dict[str, str]] | None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None
    environment = dict(consumer.env)
    environment["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), str(Path(consumer.python).parent), os.defpath))
    )
    return node, npm, environment


def _install_official_packages(consumer: Any, root: Path) -> None:
    runtime = _runtime_paths(consumer)
    if runtime is None:
        pytest.skip("the official progress formatter lane requires Node.js and npm")
    _, npm, environment = runtime
    package_json = {
        "name": "pytest-cuke-progress-integration-consumer",
        "private": True,
        "type": "module",
        "dependencies": _OFFICIAL_PACKAGES,
    }
    _write_file(root, "package.json", json.dumps(package_json, indent=2) + "\n")
    result = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, f"could not install pinned Cucumber progress packages:\n{result.stdout}\n{result.stderr}"
    consumer.env["PATH"] = environment["PATH"]


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this consumer"
    return _ANSI.sub("", f"{result.stdout}\n{result.stderr}")


def _progress_markers(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if _MARKER_LINE.fullmatch(line.strip())]
    assert lines, f"no compact Cucumber progress marker line was found:\n{output}"
    return "".join(lines)


def _messages(consumer: Any, relative_path: str) -> list[dict[str, Any]]:
    root = getattr(consumer, "_progress_integration_workspace", _consumer_root(consumer))
    path = root / relative_path
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


def _passed_attempt_count(rows: list[dict[str, Any]]) -> int:
    starts = {row["testCaseStarted"]["id"] for row in rows if "testCaseStarted" in row}
    finishes = [row["testCaseFinished"] for row in rows if "testCaseFinished" in row]
    assert len(finishes) == len(starts), (starts, finishes)
    assert {item["testCaseStartedId"] for item in finishes} == starts, finishes
    statuses: dict[str, list[str]] = {started_id: [] for started_id in starts}
    for row in rows:
        step_finish = row.get("testStepFinished")
        if step_finish is not None:
            statuses[step_finish["testCaseStartedId"]].append(step_finish["testStepResult"]["status"])
    assert all(case_statuses and set(case_statuses) == {"PASSED"} for case_statuses in statuses.values()), statuses
    return len(finishes)


@given("the consumer prepares a default progress scenario")
def prepare_default_progress_scenario(consumer: Any) -> None:
    _prepare(consumer, _ONE_PASS_FEATURE, feature_name="progress-default.feature")


@given("the consumer prepares an ini-enabled progress scenario")
def prepare_ini_progress_scenario(consumer: Any) -> None:
    _prepare(consumer, _ONE_PASS_FEATURE, feature_name="progress-ini.feature", ini_enabled=True)


@given("the consumer prepares two passing scenarios in a Unicode workspace with spaces")
def prepare_unicode_workspace_progress_scenarios(consumer: Any) -> None:
    root = _prepare(
        consumer,
        _TWO_PASS_FEATURE,
        feature_name="progress-files.feature",
        workspace="progress workspace café",
    )
    (root / "artifacts").mkdir()


@given("the consumer prepares a progress preflight marker scenario")
def prepare_progress_preflight_marker(consumer: Any) -> None:
    _prepare(consumer, _PREFLIGHT_FEATURE, feature_name="progress-preflight.feature")


@given("the consumer prepares a skipped scenario followed by a gated progress scenario")
def prepare_gated_progress_scenarios(consumer: Any) -> None:
    root = _prepare(consumer, _GATED_FEATURE, feature_name="progress-gated.feature")
    for name in ("gated-started.marker", "gated-finished.marker", "release-gated-scenario.marker"):
        (root / name).unlink(missing_ok=True)


@given("the consumer installs pinned official Cucumber progress packages")
def install_official_progress_in_consumer(consumer: Any) -> None:
    root = getattr(consumer, "_progress_integration_workspace", _consumer_root(consumer))
    _install_official_packages(consumer, root)


@given("the consumer installs pinned official Cucumber progress packages in that workspace")
def install_official_progress_in_workspace(consumer: Any) -> None:
    root = getattr(consumer, "_progress_integration_workspace", None)
    assert isinstance(root, Path), "the Unicode progress workspace must be prepared first"
    _install_official_packages(consumer, root)


@given("Node and npm are absent from the installed consumer PATH")
def remove_node_and_npm_from_consumer_path(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@given("Node and npm are available but the official progress package is unavailable to the consumer")
def mask_progress_package_from_consumer(consumer: Any) -> None:
    runtime = _runtime_paths(consumer)
    if runtime is None:
        pytest.skip("the missing progress package preflight lane requires Node.js and npm")
    _, _, environment = runtime
    root = _consumer_root(consumer)
    environment["npm_config_prefix"] = str(root / ".isolated-global-npm")
    environment.pop("NODE_PATH", None)
    mask_npm_package_from_node_resolution(root, "@cucumber/pretty-formatter")
    consumer.env.update(environment)


@then("progress should remain unselected by default")
def default_progress_is_not_selected(consumer: Any) -> None:
    output = _output(consumer)
    assert (_consumer_root(consumer) / "scenario-started.marker").is_file(), output
    assert "scenario (" not in output.lower(), output
    assert "step (" not in output.lower(), output


@then(re.compile(r'progress output should contain (?P<count>one|two) passing markers? from "(?P<relative_path>[^"]+)"'))
def progress_output_contains_passing_markers(count: str, relative_path: str, consumer: Any) -> None:
    expected_count = {"one": 1, "two": 2}[count]
    rows = _messages(consumer, relative_path)
    assert _passed_attempt_count(rows) == expected_count
    assert _progress_markers(_output(consumer)) == "." * expected_count, _output(consumer)


@then("the Cucumber progress summary should include one passing scenario")
def progress_summary_includes_one_passing_scenario(consumer: Any) -> None:
    output = _output(consumer)
    assert re.search(r"\b1 scenario\b.*\b1 passed\b", output), output


@then("Messages and JSON artifacts should be valid in the Unicode workspace")
def progress_files_are_valid_in_unicode_workspace(consumer: Any) -> None:
    root = getattr(consumer, "_progress_integration_workspace", None)
    assert isinstance(root, Path)
    rows = _messages(consumer, "artifacts/messages.ndjson")
    assert _passed_attempt_count(rows) == 2
    json_path = root / "artifacts" / "report.json"
    assert json_path.is_file(), f"Cucumber JSON output is missing: {json_path}"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(report, (dict, list)), report


@then("verbose tee-sys should forward the passing step output")
def verbose_tee_sys_forwards_passing_step_output(consumer: Any) -> None:
    output = _output(consumer)
    assert "PROGRESS_TEE_SYS_SENTINEL" in output, output
    assert re.search(r"\b2 scenarios\b.*\b2 passed\b", output), output


@then("the pretty and progress conflict should fail before the scenario starts")
def pretty_progress_conflict_is_preflighted(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "Only one live formatter may write to the terminal" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the progress scenario started before terminal formatter conflict validation"
    )


@then("missing Node progress preflight should fail before the scenario starts")
def missing_progress_node_preflight(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "node" in output.lower(), output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the progress scenario started before missing Node was rejected"
    )


@then("missing progress package preflight should fail before the scenario starts")
def missing_progress_package_preflight(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "@cucumber/pretty-formatter" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the progress scenario started before its missing npm package was rejected"
    )


@when("I release the gated scenario only after its skipped progress marker appears")
def release_gated_scenario_after_progress_marker(consumer: Any) -> None:
    root = _consumer_root(consumer)
    command = [
        str(consumer.pytest),
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-progress",
        "--cuke-messages-ndjson=progress-live.ndjson",
        "-s",
        "-q",
        "--tb=no",
        "--disable-warnings",
        "--color=no",
    ]
    process = subprocess.Popen(
        command,
        cwd=root,
        env=consumer.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    assert process.stdout is not None
    chunks: list[bytes] = []

    def read_output() -> None:
        while True:
            try:
                chunk = os.read(process.stdout.fileno(), 4096)
            except OSError:
                return
            if not chunk:
                return
            chunks.append(chunk)

    reader = threading.Thread(target=read_output, name="progress-output-reader", daemon=True)
    reader.start()
    deadline = time.monotonic() + 20
    marker_observed = False
    try:
        while time.monotonic() < deadline:
            current = _ANSI.sub("", b"".join(chunks).decode("utf-8", errors="replace"))
            if (root / "gated-started.marker").is_file() and "-" in current:
                assert not (root / "gated-finished.marker").exists(), (
                    "the later scenario finished before its predecessor's skipped marker was observed"
                )
                marker_observed = True
                break
            if process.poll() is not None:
                break
            time.sleep(0.01)
        assert marker_observed, (
            "the skipped scenario marker did not reach the consumer before the later scenario finished:\n"
            + b"".join(chunks).decode("utf-8", errors="replace")
        )
        (root / "release-gated-scenario.marker").write_text("release", encoding="utf-8")
        return_code = process.wait(timeout=30)
    except BaseException:
        (root / "release-gated-scenario.marker").write_text("release", encoding="utf-8")
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        reader.join(timeout=5)
    output = b"".join(chunks).decode("utf-8", errors="replace")
    consumer._progress_live_marker_observed = marker_observed
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")


@then("the installed consumer should finish after the marker was observed early")
def gated_progress_consumer_finished(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _output(consumer)
    assert getattr(consumer, "_progress_live_marker_observed", False)
    assert (_consumer_root(consumer) / "gated-finished.marker").is_file()
    assert _progress_markers(_output(consumer)) == "-."
