"""Installed-consumer acceptance steps for the official Cucumber JSON formatter."""

from __future__ import annotations

import base64
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
from typing import Any

import pytest
from pytest_cuke import given, parsers, then, when


_CUCUMBER_VERSION = "13.3.0"
_CUCUMBER_DEPENDENCY = {"@cucumber/cucumber": _CUCUMBER_VERSION}
_RICH_FEATURE = '''\
@feature-tag
Feature: Cucumber JSON contract café
  Feature description line one
  Feature description line two

  Background: Common setup
    Given cuke json shared background

  @rule-tag
  Rule: Account actions
    Rule description line one
    Rule description line two

    Background: Rule setup
      Given cuke json rule background

    @scenario-tag
    Scenario: A described JSON scenario
      Scenario description line
      When cuke json accepts a document
        """application/json
        {"greeting": "привет", "ready": true}
        """
      And cuke json accepts a table
        | field | value |
        | café  | alpha |
      Then cuke json response succeeds
      And cuke json response attaches a text report

    Scenario Outline: An outline row is recorded
      Given cuke json outline row <value>

      Examples:
        | value |
        | alpha |
        | bravo |
'''
_REPLAY_FEATURE = """\
Feature: Cucumber JSON replay
  Scenario: Saved messages are self contained
    Given cuke json replay scenario passes
"""
_OUTCOMES_FEATURE = """\
Feature: Cucumber JSON outcomes
  Scenario: A step passes
    Given cuke json outcome passes

  Scenario: A step fails
    When cuke json outcome fails

  Scenario: A step skips
    When cuke json outcome skips

  Scenario: An undefined step is reported
    Given cuke json intentionally has no definition
    Then cuke json successor after undefined step
"""
_MARKER_FEATURE = """\
Feature: Cucumber JSON marker
  Scenario: The marker records that execution began
    Given cuke json marker scenario starts
"""
_REPLAY_SUPPORT = """\
from pathlib import Path

import pytest
from pytest_cuke import given

ROOT = Path(__file__).parent
(ROOT / "support-imported.marker").write_text("imported", encoding="utf-8")


@pytest.fixture(autouse=True)
def trap_fixture():
    (ROOT / "fixture-executed.marker").write_text("executed", encoding="utf-8")


@given("cuke json replay scenario passes")
def cuke_json_replay_scenario_passes():
    pass
"""
_SUPPORT = """\
from pathlib import Path

import pytest
from pytest_cuke import given, parsers, then, when

ROOT = Path(__file__).parent


@given("cuke json shared background")
def cuke_json_shared_background():
    pass


@given("cuke json rule background")
def cuke_json_rule_background():
    pass


@when("cuke json accepts a document")
def cuke_json_accepts_document(step):
    assert step.doc_string is not None
    assert step.doc_string.media_type == "application/json"
    assert '"greeting": "привет"' in step.doc_string.content


@when("cuke json accepts a table")
def cuke_json_accepts_table(step):
    assert step.data_table is not None
    assert step.data_table.as_dicts() == [{"field": "café", "value": "alpha"}]


@then("cuke json response succeeds")
def cuke_json_response_succeeds():
    pass


@then("cuke json response attaches a text report")
def cuke_json_response_attaches_report(attach):
    attach(
        "official JSON attachment café",
        media_type="text/plain",
        file_name="cucumber-json-attachment.txt",
    )


@given(
    parsers.cucumber_expression("cuke json outline row {word}"),
    anonymous_group_names=["value"],
)
def cuke_json_outline_row(value):
    assert value in {"alpha", "bravo"}


@given("cuke json outcome passes")
def cuke_json_outcome_passes():
    pass


@when("cuke json outcome fails")
def cuke_json_outcome_fails():
    raise AssertionError("Cucumber JSON failure sentinel")


@when("cuke json outcome skips")
def cuke_json_outcome_skips():
    pytest.skip("Cucumber JSON skip sentinel")


@then("cuke json successor after undefined step")
def cuke_json_successor_after_undefined():
    pass


@given("cuke json marker scenario starts")
def cuke_json_marker_scenario_starts():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""
_CONFTST_REPLAY = """\
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
(ROOT / "conftest-imported.marker").write_text("imported", encoding="utf-8")
pytest_plugins = ["cucumber_json_consumer_steps"]
"""
_FINALIZATION_PRELOAD = """\
if (process.argv.length === 1) {
  process.once("beforeExit", () => {
    throw new Error("Cucumber JSON finalization failure sentinel");
  });
}
"""
_SOURCE_MARKERS = (
    "conftest-imported.marker",
    "support-imported.marker",
    "fixture-executed.marker",
)
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _workspace(consumer: Any) -> Path:
    root = Path(consumer.path).resolve()
    relative = Path("cucumber-json café workspace")
    destination = (root / relative).resolve()
    if root not in destination.parents:
        raise ValueError("Cucumber JSON workspace must remain inside the consumer project")
    return destination


def _write(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Cucumber JSON consumer files must stay inside the workspace")
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _prepare(consumer: Any, feature: str, *, replay_traps: bool = False) -> Path:
    root = _workspace(consumer)
    root.mkdir(parents=True, exist_ok=True)
    (root / "artifacts").mkdir(exist_ok=True)
    _write(
        root,
        "pyproject.toml",
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
    )
    _write(root, "features/cucumber-json-consumer.feature", feature)
    if replay_traps:
        _write(root, "cucumber_json_consumer_steps.py", _REPLAY_SUPPORT)
        _write(root, "conftest.py", _CONFTST_REPLAY)
    else:
        _write(root, "cucumber_json_consumer_steps.py", _SUPPORT)
        _write(root, "conftest.py", 'pytest_plugins = ["cucumber_json_consumer_steps"]\n')
    consumer._cucumber_json_workspace = root
    return root


def _node_paths(consumer: Any) -> tuple[str, str, str]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        pytest.skip("the real Cucumber JSON acceptance lane requires Node.js and npm")
    return node, npm, str(Path(consumer.pytest).parent)


def _install_official_runtime(consumer: Any) -> None:
    node, npm, consumer_bin = _node_paths(consumer)
    root = consumer._cucumber_json_workspace
    package_json = {
        "name": "pytest-cuke-cucumber-json-consumer",
        "private": True,
        "type": "module",
        "dependencies": _CUCUMBER_DEPENDENCY,
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
        f"could not install pinned @cucumber/cucumber@{_CUCUMBER_VERSION}:\n{install.stdout}\n{install.stderr}"
    )
    metadata = root / "node_modules" / "@cucumber" / "cucumber" / "package.json"
    installed_version = json.loads(metadata.read_text(encoding="utf-8")).get("version")
    assert installed_version == _CUCUMBER_VERSION, installed_version
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)
    consumer._cucumber_json_node = node
    consumer._cucumber_json_npm = npm
    consumer._cucumber_json_consumer_bin = consumer_bin


def _run_pytest(consumer: Any, arguments: str) -> subprocess.CompletedProcess[str]:
    root = consumer._cucumber_json_workspace
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
        readonly_state = getattr(consumer, "_cucumber_json_readonly_directory", None)
        if readonly_state is not None:
            directory, original_mode = readonly_state
            directory.chmod(original_mode)
            del consumer._cucumber_json_readonly_directory
    consumer.cucumber_json_result = result
    consumer.pytest_result = result
    return result


def _run_cuke(consumer: Any, arguments: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(consumer.cuke), *shlex.split(arguments)],
        cwd=consumer._cucumber_json_workspace,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    consumer.cucumber_json_replay_result = result
    return result


def _combined_output(consumer: Any, *, replay: bool = False) -> str:
    result = consumer.cucumber_json_replay_result if replay else consumer.cucumber_json_result
    assert result is not None, "the Cucumber JSON process has not run"
    return f"{result.stdout}\n{result.stderr}"


def _read_json(consumer: Any, relative_path: str) -> tuple[Any, str]:
    artifact = consumer._cucumber_json_workspace / relative_path
    assert artifact.is_file(), (
        f"Cucumber JSON artifact {relative_path!r} was not produced; {_combined_output(consumer)}"
    )
    raw = artifact.read_bytes()
    text = raw.decode("utf-8", errors="strict")
    assert not raw.startswith(b"\xef\xbb\xbf"), "Cucumber JSON must be UTF-8 without a BOM"
    assert "\ufffd" not in text, "Cucumber JSON contains a replacement character"
    assert _ANSI.search(text) is None, f"Cucumber JSON contains terminal escapes: {text!r}"
    return json.loads(text), text


def _one_feature(report: Any, feature_name: str) -> dict[str, Any]:
    assert isinstance(report, list) and len(report) == 1, report
    feature = report[0]
    assert feature.get("name") == feature_name, feature
    assert feature.get("keyword") == "Feature", feature
    assert isinstance(feature.get("uri"), str) and feature["uri"].replace("\\", "/").endswith(
        "cucumber-json-consumer.feature"
    ), feature
    return feature


def _scenario(feature: dict[str, Any], name: str) -> dict[str, Any]:
    found = [element for element in feature.get("elements", []) if element.get("name") == name]
    assert len(found) == 1, (name, feature.get("elements"))
    return found[0]


def _assert_rich_report(consumer: Any, relative_path: str) -> None:
    report, _ = _read_json(consumer, relative_path)
    feature = _one_feature(report, "Cucumber JSON contract café")
    assert "Feature description line one" in feature.get("description", ""), feature
    assert {tag.get("name") for tag in feature.get("tags", [])} == {"@feature-tag"}, feature
    elements = feature["elements"]
    described = _scenario(feature, "A described JSON scenario")
    assert described.get("type") == "scenario", described
    assert "account-actions" in described.get("id", ""), described
    assert "Scenario description line" in described.get("description", ""), described
    described_tags = {tag.get("name") for tag in described.get("tags", [])}
    assert described_tags == {
        "@rule-tag",
        "@scenario-tag",
    }, described
    described_steps = described.get("steps", [])
    step_names = [step.get("name") for step in described_steps]
    assert step_names[:2] == ["cuke json shared background", "cuke json rule background"], described_steps
    document_step = next(step for step in described_steps if step.get("name") == "cuke json accepts a document")
    document_arguments = document_step.get("arguments", [])
    assert len(document_arguments) == 1, document_step
    assert '"greeting": "привет"' in document_arguments[0].get("content", ""), document_arguments
    table_step = next(step for step in described_steps if step.get("name") == "cuke json accepts a table")
    table_arguments = table_step.get("arguments", [])
    assert len(table_arguments) == 1, table_step
    assert table_arguments[0].get("rows") == [
        {"cells": ["field", "value"]},
        {"cells": ["café", "alpha"]},
    ], table_arguments
    attachment_step = next(
        step for step in described_steps if step.get("name") == "cuke json response attaches a text report"
    )
    assert attachment_step.get("embeddings") == [
        {
            "data": base64.b64encode("official JSON attachment café".encode("utf-8")).decode("ascii"),
            "mime_type": "text/plain",
        }
    ], attachment_step
    assert all(step.get("result", {}).get("status") == "passed" for step in described_steps), described_steps
    durations = [step.get("result", {}).get("duration") for step in described_steps]
    assert all(isinstance(duration, (int, float)) and duration >= 0 for duration in durations), durations

    outline_name = re.compile(r"^An outline row is recorded\[table_rows:\[line: (?P<line>\d+)\]\]$")
    outlines = [element for element in elements if outline_name.fullmatch(str(element.get("name", "")))]
    assert len(outlines) == 2, elements
    outline_names = [element["name"] for element in outlines]
    assert len(set(outline_names)) == 2, outlines
    outline_source_lines = {int(outline_name.fullmatch(name)["line"]) for name in outline_names}
    assert len(outline_source_lines) == 2, outlines
    assert Counter(
        step.get("name")
        for element in outlines
        for step in element.get("steps", [])
        if str(step.get("name", "")).startswith("cuke json outline row ")
    ) == Counter({"cuke json outline row alpha": 1, "cuke json outline row bravo": 1}), outlines
    outline_ids = [element.get("id") for element in outlines]
    assert all(isinstance(identifier, str) and "account-actions" in identifier for identifier in outline_ids), outlines
    assert all({tag.get("name") for tag in element.get("tags", [])} == {"@rule-tag"} for element in outlines), outlines


def _require_preflight_failure(consumer: Any, expected: str) -> str:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert expected.lower() in output.lower(), output
    assert not (consumer._cucumber_json_workspace / "scenario-started.marker").exists(), output
    return output


def _semantic_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _semantic_json(item) for key, item in value.items() if key != "duration"}
    if isinstance(value, list):
        return [_semantic_json(item) for item in value]
    return value


def _write_consumer_config(consumer: Any, cuke_json_value: str | None) -> None:
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    if cuke_json_value is not None:
        config += f'cuke_json = "{cuke_json_value}"\n'
    _write(consumer._cucumber_json_workspace, "pyproject.toml", config)


@given("the Cucumber JSON consumer prepares a rich feature in a Unicode workspace with spaces")
def prepare_rich_cucumber_json_consumer(consumer: Any) -> None:
    _prepare(consumer, _RICH_FEATURE)


@given("the consumer installs the pinned official Cucumber JSON runtime")
def install_official_cucumber_json_runtime(consumer: Any) -> None:
    _install_official_runtime(consumer)


@when(parsers.re(r'I run installed pytest in the Cucumber JSON workspace with arguments "(?P<arguments>[^"]*)"'))
def run_cucumber_json_pytest(arguments: str, consumer: Any) -> None:
    _run_pytest(consumer, arguments)


@then(
    "the selected Cucumber JSON report should preserve the official feature scenario background outline tags doc string table attachments and durations"
)
def selected_cucumber_json_preserves_official_schema(consumer: Any) -> None:
    assert consumer.cucumber_json_result.returncode == 0, _combined_output(consumer)
    _assert_rich_report(consumer, "artifacts/cli résumé.json")


@then("Cucumber JSON Messages JUnit and terminal summary should coexist as independent outputs")
def cucumber_json_outputs_coexist(consumer: Any) -> None:
    root = consumer._cucumber_json_workspace
    report_paths = [
        root / "artifacts/cli résumé.json",
        root / "artifacts/messages.ndjson",
        root / "artifacts/junit.xml",
    ]
    assert len({path.resolve() for path in report_paths}) == 3, report_paths
    assert all(path.is_file() for path in report_paths), report_paths
    messages = [json.loads(line) for line in report_paths[1].read_text(encoding="utf-8").splitlines() if line]
    assert messages and any("testRunStarted" in envelope for envelope in messages), messages
    junit = ET.parse(report_paths[2]).getroot()
    assert junit.tag in {"testsuite", "testsuites"}, junit.tag
    output = _combined_output(consumer).lower()
    assert "3 passed" in output, output


@when(parsers.re(r'the Cucumber JSON consumer sets cuke_json to "(?P<relative_path>[^"]+)"'))
def set_cucumber_json_ini(relative_path: str, consumer: Any) -> None:
    _write_consumer_config(consumer, relative_path)


@then("the configured Cucumber JSON report should preserve the official schema")
def configured_cucumber_json_preserves_official_schema(consumer: Any) -> None:
    assert consumer.cucumber_json_result.returncode == 0, _combined_output(consumer)
    _assert_rich_report(consumer, "artifacts/from-ini.json")


@when("the Cucumber JSON consumer removes cuke_json from configuration")
def remove_cucumber_json_ini(consumer: Any) -> None:
    _write_consumer_config(consumer, None)


@then(
    parsers.re(
        r'the bare Cucumber JSON option should write the official report to "(?P<relative_path>[^"]+)" under pytest root'
    )
)
def bare_cucumber_json_uses_default_path(relative_path: str, consumer: Any) -> None:
    assert consumer.cucumber_json_result.returncode == 0, _combined_output(consumer)
    assert relative_path == "cucumber.json"
    _assert_rich_report(consumer, relative_path)


@given("the Cucumber JSON consumer prepares a replay feature with source import and fixture traps")
def prepare_cucumber_json_replay_consumer(consumer: Any) -> None:
    _prepare(consumer, _REPLAY_FEATURE, replay_traps=True)


@then("the live Cucumber JSON report and Messages stream should be complete")
def live_cucumber_json_and_messages_are_complete(consumer: Any) -> None:
    assert consumer.cucumber_json_result.returncode == 0, _combined_output(consumer)
    report, _ = _read_json(consumer, "artifacts/live.json")
    feature = _one_feature(report, "Cucumber JSON replay")
    scenario = _scenario(feature, "Saved messages are self contained")
    assert scenario["steps"][0]["result"]["status"] == "passed", scenario
    messages = [
        json.loads(line)
        for line in (consumer._cucumber_json_workspace / "messages.ndjson").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert messages and any("testRunFinished" in envelope for envelope in messages), messages
    assert all((consumer._cucumber_json_workspace / marker).is_file() for marker in _SOURCE_MARKERS)


@when("I remove the Cucumber JSON consumer test sources and clear their execution markers")
def remove_cucumber_json_sources(consumer: Any) -> None:
    root = consumer._cucumber_json_workspace
    for relative_path in ("conftest.py", "cucumber_json_consumer_steps.py"):
        (root / relative_path).unlink()
    shutil.rmtree(root / "features")
    for marker in _SOURCE_MARKERS:
        (root / marker).unlink(missing_ok=True)


@when(parsers.re(r'I run command "cuke" in the Cucumber JSON workspace with arguments "(?P<arguments>[^"]*)"'))
def replay_cucumber_json_messages(arguments: str, consumer: Any) -> None:
    _run_cuke(consumer, arguments)


@then("replay should succeed without importing removed sources or running pytest fixtures")
def cucumber_json_replay_does_not_import_sources(consumer: Any) -> None:
    result = consumer.cucumber_json_replay_result
    output = _combined_output(consumer, replay=True)
    assert result.returncode == 0, output
    assert (consumer._cucumber_json_workspace / "artifacts/replayed.json").is_file(), output
    assert all(not (consumer._cucumber_json_workspace / marker).exists() for marker in _SOURCE_MARKERS)


@then("replayed Cucumber JSON should be semantically equivalent to the live report")
def replayed_cucumber_json_matches_live(consumer: Any) -> None:
    live, _ = _read_json(consumer, "artifacts/live.json")
    replayed, _ = _read_json(consumer, "artifacts/replayed.json")
    assert _semantic_json(live) == _semantic_json(replayed)


@given("the Cucumber JSON consumer prepares passing failing skipped and undefined scenarios")
def prepare_cucumber_json_outcomes(consumer: Any) -> None:
    _prepare(consumer, _OUTCOMES_FEATURE)


@then("the Cucumber JSON run should fail while publishing every outcome")
def cucumber_json_outcomes_preserve_pytest_failure(consumer: Any) -> None:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result.returncode != 0, output
    assert (consumer._cucumber_json_workspace / "artifacts/outcomes.json").is_file(), output
    assert (consumer._cucumber_json_workspace / "artifacts/outcomes.ndjson").is_file(), output


@then("the official report should preserve pass fail skip undefined status failure text and durations")
def official_cucumber_json_preserves_mixed_outcomes(consumer: Any) -> None:
    report, _ = _read_json(consumer, "artifacts/outcomes.json")
    feature = _one_feature(report, "Cucumber JSON outcomes")
    cases = {
        "A step passes": "passed",
        "A step fails": "failed",
        "A step skips": "skipped",
        "An undefined step is reported": "undefined",
    }
    scenarios = {name: _scenario(feature, name) for name in cases}
    for name, expected_status in cases.items():
        first_step = scenarios[name]["steps"][0]
        result = first_step.get("result", {})
        assert result.get("status") == expected_status, (name, first_step)
        if expected_status in {"passed", "failed"}:
            duration = result.get("duration")
            assert isinstance(duration, (int, float)) and duration >= 0, (name, result)
    failure = scenarios["A step fails"]["steps"][0]["result"]
    assert "Cucumber JSON failure sentinel" in failure.get("error_message", ""), failure
    undefined = scenarios["An undefined step is reported"]["steps"]
    assert undefined[0]["result"].get("status") == "undefined", undefined
    assert len(undefined) == 2 and undefined[1]["result"].get("status") == "skipped", undefined


@given("the Cucumber JSON consumer prepares a marker scenario for destination preflight")
def prepare_cucumber_json_preflight(consumer: Any) -> None:
    _prepare(consumer, _MARKER_FEATURE)


@then("the missing Cucumber JSON parent should fail before the marker scenario runs")
def missing_cucumber_json_parent_preflights(consumer: Any) -> None:
    output = _require_preflight_failure(consumer, "missing-parent")
    assert any(token in output.lower() for token in ("parent", "directory", "destination")), output


@then("duplicate canonical Cucumber JSON destinations should fail before the marker scenario runs")
def duplicate_cucumber_json_destination_preflights(consumer: Any) -> None:
    output = _require_preflight_failure(consumer, "shared.json")
    assert any(token in output.lower() for token in ("duplicate", "same output", "same path", "resolve")), output


@given("the Cucumber JSON output parent is read-only")
def make_cucumber_json_parent_read_only(consumer: Any) -> None:
    directory = consumer._cucumber_json_workspace / "read-only"
    directory.mkdir(exist_ok=True)
    original_mode = stat.S_IMODE(directory.stat().st_mode)
    directory.chmod(original_mode & ~0o222)
    probe = directory / "write-probe"
    try:
        probe.write_text("probe", encoding="utf-8")
    except OSError:
        consumer._cucumber_json_readonly_directory = (directory, original_mode)
    else:
        probe.unlink(missing_ok=True)
        directory.chmod(original_mode)
        pytest.skip("the current platform or user can still write into a read-only directory")


@then("the unwritable Cucumber JSON destination should fail before the marker scenario runs")
def unwritable_cucumber_json_destination_preflights(consumer: Any) -> None:
    output = _require_preflight_failure(consumer, "read-only")
    assert any(token in output.lower() for token in ("writable", "permission", "read-only")), output


@given("the Cucumber JSON consumer prepares a passing marker scenario")
def prepare_cucumber_json_marker(consumer: Any) -> None:
    _prepare(consumer, _MARKER_FEATURE)


@given("the Cucumber JSON consumer PATH excludes Node.js and npm")
def hide_cucumber_json_node_tools(consumer: Any) -> None:
    consumer_bin = getattr(consumer, "_cucumber_json_consumer_bin", str(Path(consumer.pytest).parent))
    consumer.env["PATH"] = consumer_bin


@then("ordinary pytest should pass without starting a JSON backend")
def unselected_cucumber_json_is_inert(consumer: Any) -> None:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result.returncode == 0, output
    root = consumer._cucumber_json_workspace
    assert (root / "scenario-started.marker").is_file(), output
    assert not (root / "cucumber.json").exists()
    assert "node.js" not in output.lower() and "npm" not in output.lower(), output


@when("the Cucumber JSON consumer clears the marker scenario result")
def clear_cucumber_json_marker(consumer: Any) -> None:
    (consumer._cucumber_json_workspace / "scenario-started.marker").unlink(missing_ok=True)


@then("the explicit native backend should preserve the legacy report and run without Node or npm")
def explicit_native_cucumber_json_preserves_legacy(consumer: Any) -> None:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result.returncode == 0, output
    root = consumer._cucumber_json_workspace
    assert (root / "scenario-started.marker").is_file(), output
    report, _ = _read_json(consumer, "artifacts/native.json")
    feature = _one_feature(report, "Cucumber JSON marker")
    scenario = _scenario(feature, "The marker records that execution began")
    assert scenario["steps"][0]["result"]["status"] == "passed", scenario
    assert scenario["steps"][0]["match"]["location"] == "", scenario
    assert "node.js" not in output.lower() and "npm" not in output.lower(), output


@given("the Cucumber JSON consumer prepares a marker scenario for runtime preflight")
def prepare_cucumber_json_runtime_preflight(consumer: Any) -> None:
    _prepare(consumer, _MARKER_FEATURE)


@then("missing Node diagnostics should stop the Cucumber JSON run before the marker scenario")
def missing_node_cucumber_json_preflights(consumer: Any) -> None:
    output = _require_preflight_failure(consumer, "node")
    assert "cucumber-json" in output.lower() or "cuke-json" in output.lower(), output


@given("the Cucumber JSON consumer exposes Node.js without npm")
def expose_node_without_npm_for_cucumber_json(consumer: Any) -> None:
    node, _, consumer_bin = _node_paths(consumer)
    isolated = consumer._cucumber_json_workspace / "node-only"
    isolated.mkdir(exist_ok=True)
    node_name = "node.exe" if os.name == "nt" else "node"
    destination = isolated / node_name
    if os.name == "nt":
        shutil.copy2(node, destination)
    else:
        destination.symlink_to(Path(node).resolve())
        destination.chmod(destination.stat().st_mode | 0o111)
    consumer.env["PATH"] = os.pathsep.join((str(isolated), consumer_bin))


@then("missing npm diagnostics should stop the Cucumber JSON run before the marker scenario")
def missing_npm_cucumber_json_preflights(consumer: Any) -> None:
    _require_preflight_failure(consumer, "npm")


@given("the Cucumber JSON consumer exposes Node.js and npm without installing Cucumber")
def expose_node_and_npm_without_cucumber(consumer: Any) -> None:
    node, npm, consumer_bin = _node_paths(consumer)
    consumer.env["PATH"] = os.pathsep.join(dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), consumer_bin)))


@then("missing Cucumber package diagnostics should stop the Cucumber JSON run before the marker scenario")
def missing_cucumber_package_preflights(consumer: Any) -> None:
    output = _require_preflight_failure(consumer, "@cucumber/cucumber")
    assert "npm install" in output.lower(), output


@given("the Cucumber JSON consumer installs a Node preload that fails during JSON finalization")
def install_cucumber_json_finalization_preload(consumer: Any) -> None:
    preload = _write(
        consumer._cucumber_json_workspace,
        "fail-cucumber-json-finalization.cjs",
        _FINALIZATION_PRELOAD,
    )
    consumer.env["NODE_OPTIONS"] = f'--require="{preload.resolve()}"'


@then("the Cucumber JSON backend failure should be visible and no partial report should be published")
def cucumber_json_backend_finalization_failure_is_visible(consumer: Any) -> None:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result.returncode != 0, output
    assert "Cucumber JSON finalization failure sentinel" in output, output
    assert re.search(r"\b1 passed\b", output), output
    assert not (consumer._cucumber_json_workspace / "artifacts/finalization.json").exists(), output
