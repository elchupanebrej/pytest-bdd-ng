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
_PRODUCT_ROOT = Path(__file__).resolve().parents[2]
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
_HOOK_FEATURE = """\
Feature: Cucumber JSON hook lifecycle
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


def _one_feature(
    report: Any, feature_name: str, *, source_suffix: str = "cucumber-json-consumer.feature"
) -> dict[str, Any]:
    assert isinstance(report, list) and len(report) == 1, report
    feature = report[0]
    assert feature.get("name") == feature_name, feature
    assert feature.get("keyword") == "Feature", feature
    assert isinstance(feature.get("uri"), str) and feature["uri"].replace("\\", "/").endswith(source_suffix), feature
    return feature


def _scenario(feature: dict[str, Any], name: str) -> dict[str, Any]:
    found = [element for element in feature.get("elements", []) if element.get("name") == name]
    assert len(found) == 1, (name, feature.get("elements"))
    return found[0]


def _feature_line(source: str, expected_line: str) -> int:
    return next(index for index, line in enumerate(source.splitlines(), start=1) if line.strip() == expected_line)


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
    background_locations = [step.get("line") for step in described_steps[:2]]
    expected_background_locations = [
        _feature_line(_RICH_FEATURE, "Given cuke json shared background"),
        _feature_line(_RICH_FEATURE, "Given cuke json rule background"),
    ]
    assert background_locations == expected_background_locations, described_steps
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
    for element in outlines:
        assert [step.get("line") for step in element.get("steps", [])[:2]] == expected_background_locations, element


def _require_preflight_failure(consumer: Any, expected: str) -> str:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert expected.lower() in output.lower(), output
    assert not (consumer._cucumber_json_workspace / "scenario-started.marker").exists(), output
    return output


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


@given(
    parsers.re(
        r'the installed consumer uses staged directory "(?P<relative_path>[^"]+)" as its Cucumber JSON workspace'
    )
)
def use_staged_cucumber_json_example(relative_path: str, consumer: Any) -> None:
    workspace = Path(relative_path)
    if workspace.is_absolute() or ".." in workspace.parts:
        raise ValueError("staged Cucumber JSON example paths must stay inside the installed consumer")
    consumer._cucumber_json_workspace = (Path(consumer.path) / workspace).resolve()
    consumer._cucumber_json_workspace.joinpath("artifacts").mkdir(exist_ok=True)


@then("the public Cucumber JSON example should match the checked-in golden artifact")
def copy_cucumber_json_reference_messages(consumer: Any) -> None:
    source = _PRODUCT_ROOT / "tests/fixtures/cucumber-json/cucumber-json-example-messages.ndjson"
    destination = consumer._cucumber_json_workspace / "reference.ndjson"
    shutil.copyfile(source, destination)


@given("the fixed Cucumber JSON Messages reference fixture is copied to the installed consumer")
def given_cucumber_json_reference_messages_copied(consumer: Any) -> None:
    copy_cucumber_json_reference_messages(consumer)


@then("the public Cucumber JSON example should preserve live schema content and valid durations")
def public_cucumber_json_example_preserves_live_schema(consumer: Any) -> None:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result.returncode == 0, output
    report, _ = _read_json(consumer, "report.json")
    feature = _one_feature(
        report,
        "Cucumber JSON example",
        source_suffix="cucumber-json-example.feature",
    )
    feature_source = (_PRODUCT_ROOT / "examples/cucumber-json/features/cucumber-json-example.feature").read_text(
        encoding="utf-8"
    )
    assert feature.get("description", "").strip() == (
        "A checked-in project that demonstrates the public autoload contract."
    ), feature
    assert {tag.get("name") for tag in feature.get("tags", [])} == {"@public-json"}, feature
    scenarios = feature["elements"]
    assert len(scenarios) == 3, scenarios
    described = _scenario(feature, "A report includes structured inputs and an attachment")
    assert described.get("type") == "scenario", described
    assert "result-serialization" in described.get("id", ""), described
    assert {tag.get("name") for tag in described.get("tags", [])} == {"@report"}, described
    steps = described["steps"]
    assert [step.get("name") for step in steps[:2]] == [
        "the Cucumber JSON example prepares a request",
        "the Cucumber JSON example resets its output",
    ], steps
    assert [step.get("line") for step in steps[:2]] == [
        _feature_line(feature_source, "Given the Cucumber JSON example prepares a request"),
        _feature_line(feature_source, "Given the Cucumber JSON example resets its output"),
    ], steps
    doc_step = next(step for step in steps if step.get("name") == "the Cucumber JSON example receives a document")
    assert doc_step.get("arguments") == [
        {"content": '{"message": "hello", "ready": true}', "line": _feature_line(feature_source, '"""application/json')}
    ], doc_step
    table_step = next(step for step in steps if step.get("name") == "the Cucumber JSON example receives a table")
    assert table_step.get("arguments") == [{"rows": [{"cells": ["field", "value"]}, {"cells": ["café", "alpha"]}]}], (
        table_step
    )
    attachment_step = next(step for step in steps if step.get("name") == "the Cucumber JSON example attaches a report")
    assert attachment_step.get("embeddings") == [
        {
            "data": base64.b64encode("checked-in Cucumber JSON example attachment café".encode("utf-8")).decode(
                "ascii"
            ),
            "mime_type": "text/plain",
        }
    ], attachment_step
    outline_pattern = re.compile(r"^An example row is recorded\[table_rows:\[line: (?P<line>\d+)\]\]$")
    outlines = [scenario for scenario in scenarios if outline_pattern.fullmatch(str(scenario.get("name", "")))]
    assert len(outlines) == 2 and len({scenario.get("id") for scenario in outlines}) == 2, outlines
    assert {scenario["name"] for scenario in outlines} == {
        "An example row is recorded[table_rows:[line: 30]]",
        "An example row is recorded[table_rows:[line: 31]]",
    }, outlines
    assert all({tag.get("name") for tag in scenario.get("tags", [])} == set() for scenario in outlines), outlines
    assert all(
        step.get("result", {}).get("status") == "passed" for scenario in scenarios for step in scenario["steps"]
    ), scenarios
    durations = [step.get("result", {}).get("duration") for scenario in scenarios for step in scenario.get("steps", [])]
    assert durations and all(isinstance(duration, (int, float)) and duration >= 0 for duration in durations), durations
    assert all(
        re.search(r"(?:^|[/\\])cucumber_json_example_steps\.py:\d+$", step.get("match", {}).get("location", ""))
        for scenario in scenarios
        for step in scenario.get("steps", [])
    ), scenarios


@then("the pinned official formatter should match the checked-in reference golden exactly")
def pinned_official_formatter_matches_golden(consumer: Any) -> None:
    result = consumer.cucumber_json_replay_result
    output = _combined_output(consumer, replay=True)
    assert result.returncode == 0, output
    report, _ = _read_json(consumer, "reference.json")
    golden_path = _PRODUCT_ROOT / "tests/fixtures/cucumber-json/cucumber-json-example.golden.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert report == golden


@given("the Cucumber JSON consumer prepares a feature for run hook lifecycle coverage")
def prepare_cucumber_json_hook_lifecycle(consumer: Any) -> None:
    _prepare(consumer, _HOOK_FEATURE)


@then("the Cucumber JSON report should preserve the scenario while Messages records both test run hooks")
def cucumber_json_report_preserves_messages_run_hooks(consumer: Any) -> None:
    result = consumer.cucumber_json_result
    output = _combined_output(consumer)
    assert result.returncode == 0, output
    report, _ = _read_json(consumer, "artifacts/hooks.json")
    feature = _one_feature(report, "Cucumber JSON hook lifecycle")
    scenario = _scenario(feature, "The marker records that execution began")
    assert scenario["steps"][0]["result"]["status"] == "passed", scenario

    messages_path = consumer._cucumber_json_workspace / "artifacts/hooks.ndjson"
    envelopes = [json.loads(line) for line in messages_path.read_text(encoding="utf-8").splitlines() if line]
    meta = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    assert len(meta) == 1 and meta[0].get("protocolVersion") == "28.0.0", meta
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(run_started) == len(run_finished) == 1, (run_started, run_finished)
    run_id = run_started[0]["id"]
    assert run_finished[0].get("testRunStartedId") == run_id and run_finished[0].get("success") is True, run_finished

    expected_hooks = {
        "BEFORE_TEST_RUN": "pytest session start",
        "AFTER_TEST_RUN": "pytest session finish",
    }
    definitions = {
        hook["type"]: hook
        for envelope in envelopes
        if isinstance((hook := envelope.get("hook")), dict) and hook.get("type") in expected_hooks
    }
    assert set(definitions) == set(expected_hooks), definitions
    assert {kind: hook.get("name") for kind, hook in definitions.items()} == expected_hooks, definitions
    started_by_type = {}
    positions = {}
    for index, envelope in enumerate(envelopes):
        started = envelope.get("testRunHookStarted")
        if not isinstance(started, dict):
            continue
        kind = next((name for name, hook in definitions.items() if hook.get("id") == started.get("hookId")), None)
        assert kind is not None and kind not in started_by_type, started
        assert started.get("testRunStartedId") == run_id, started
        started_by_type[kind] = started
        positions[f"{kind}:start"] = index
    assert set(started_by_type) == set(expected_hooks), started_by_type

    finished_by_type = {}
    for index, envelope in enumerate(envelopes):
        finished = envelope.get("testRunHookFinished")
        if not isinstance(finished, dict):
            continue
        kind = next(
            (
                name
                for name, started in started_by_type.items()
                if started.get("id") == finished.get("testRunHookStartedId")
            ),
            None,
        )
        assert kind is not None and kind not in finished_by_type, finished
        assert finished.get("result", {}).get("status") == "PASSED", finished
        finished_by_type[kind] = finished
        positions[f"{kind}:finish"] = index
    assert set(finished_by_type) == set(expected_hooks), finished_by_type
    case_start = next(index for index, envelope in enumerate(envelopes) if "testCaseStarted" in envelope)
    case_finish = next(index for index, envelope in enumerate(envelopes) if "testCaseFinished" in envelope)
    run_start = next(index for index, envelope in enumerate(envelopes) if "testRunStarted" in envelope)
    run_finish = next(index for index, envelope in enumerate(envelopes) if "testRunFinished" in envelope)
    assert (
        run_start
        < positions["BEFORE_TEST_RUN:start"]
        < positions["BEFORE_TEST_RUN:finish"]
        < case_start
        < case_finish
        < positions["AFTER_TEST_RUN:start"]
        < positions["AFTER_TEST_RUN:finish"]
        < run_finish
    ), positions


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
    assert live == replayed


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


@pytest.hookimpl(trylast=True)
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
        readonly_state = consumer._cucumber_junit_readonly_directory
        if readonly_state is not None:
            directory, original_mode = readonly_state
            directory.chmod(original_mode)
            consumer._cucumber_junit_readonly_directory = None
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
        if "time" in node.attrib:
            node.set("time", "DURATION")
        node.attrib.pop("timestamp", None)
    canonical = ET.canonicalize(ET.tostring(root, encoding="unicode"), strip_text=False)
    return f"{declaration}\n{canonical}\n" if declaration else f"{canonical}\n"


def _assert_junit_rich_report(consumer: Any, relative_path: str) -> None:
    root, cases = _read_junit(consumer, relative_path)
    assert len(cases) == 3, ET.tostring(root, encoding="unicode")
    assert root.get("tests", "3") == "3", root.attrib
    assert root.get("failures", "0") == "0", root.attrib
    assert root.get("skipped", "0") == "0", root.attrib
    names = [case.get("name", "") for case in cases]
    assert len(set(names)) == 3, names
    assert any("described structured profile" in name for name in names), names
    assert any("#1.1" in name for name in names), names
    assert any("#1.2" in name for name in names), names
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

    for row_id, customer in (("#1.1", "Ada"), ("#1.2", "Boris")):
        row = next(case for case in cases if row_id in case.get("name", ""))
        output = row.findtext("system-out", default="")
        assert f"junit row {customer} is started" in output, output
        assert f"junit row {customer} passes" in output, output


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


@given("the consumer installs the pinned official Cucumber JUnit runtime")
def install_official_cucumber_junit_runtime(consumer: Any) -> None:
    _install_official_junit_runtime(consumer)


@given("the public Cucumber JUnit example is copied to the installed consumer")
def copy_public_cucumber_junit_example_to_consumer(consumer: Any) -> None:
    source = _PRODUCT_ROOT / "examples" / "cucumber-junit"
    destination = Path(consumer.path) / "cucumber-junit-example"
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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


@then("replayed Cucumber JUnit XML should match live XML after normalizing durations")
def replayed_cucumber_junit_matches_live(consumer: Any) -> None:
    live_root, live_cases = _read_junit(consumer, "artifacts/live.xml")
    replay_root, replay_cases = _read_junit(consumer, "artifacts/replayed.xml")
    assert len(live_cases) == len(replay_cases) == 3

    def normalized(root: ET.Element) -> str:
        for node in root.iter():
            if "time" in node.attrib:
                node.set("time", "<duration>")
            node.attrib.pop("timestamp", None)
        return ET.tostring(root, encoding="unicode")

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
    assert all(passed.find(tag) is None for tag in ("failure", "error", "skipped")), ET.tostring(
        passed, encoding="unicode"
    )
    assert failed.find("failure") is not None, ET.tostring(failed, encoding="unicode")
    assert "Cucumber JUnit failure sentinel" in ET.tostring(failed, encoding="unicode"), failed
    assert skipped.find("skipped") is not None, ET.tostring(skipped, encoding="unicode")
    assert undefined.find("failure") is not None, ET.tostring(undefined, encoding="unicode")
    assert root.get("tests", "4") == "4", root.attrib
    assert int(root.get("failures", "2")) >= 2, root.attrib
    assert root.get("skipped", "1") == "1", root.attrib


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


@given("the Cucumber JUnit consumer output parent is read-only")
def make_cucumber_junit_parent_read_only(consumer: Any) -> None:
    directory = consumer._cucumber_junit_workspace / "read-only"
    directory.mkdir(exist_ok=True)
    original_mode = stat.S_IMODE(directory.stat().st_mode)
    directory.chmod(original_mode & ~0o222)
    consumer._cucumber_junit_readonly_directory = (directory, original_mode)


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


@then("missing Cucumber JUnit runtime diagnostics should stop the run before the marker scenario")
def missing_cucumber_junit_runtime_preflights(consumer: Any) -> None:
    output = _junit_preflight_failure(consumer, "node")
    assert "node" in output.lower() or "npm install" in output.lower(), output
    assert not (consumer._cucumber_junit_workspace / "artifacts/report.xml").exists(), output


@given("the Cucumber JUnit consumer installs a Node preload that fails during XML finalization")
def install_cucumber_junit_finalization_preload(consumer: Any) -> None:
    preload = _write(
        consumer._cucumber_junit_workspace,
        "fail-cucumber-junit-finalization.cjs",
        _JUNIT_FINALIZATION_PRELOAD,
    )
    consumer.env["NODE_OPTIONS"] = f'--require="{preload.resolve()}"'


@then("the Cucumber JUnit backend failure should be visible without publishing a partial report")
def cucumber_junit_backend_finalization_failure_is_visible(consumer: Any) -> None:
    result = consumer.cucumber_junit_result
    output = _junit_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "Cucumber JUnit finalization failure sentinel" in output, output
    assert re.search(r"\b1 passed\b", output), output
    assert not (consumer._cucumber_junit_workspace / "artifacts/finalization.xml").exists(), output


@then("the public Cucumber JUnit example should match its pinned formatter golden and preserve its report contract")
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
    actual = _normalized_junit_artifact(consumer._cucumber_junit_workspace / "report.xml")
    golden_path = _PRODUCT_ROOT / "tests/fixtures/cucumber-junit/cucumber-junit-example.xml"
    golden = golden_path.read_text(encoding="utf-8")
    assert actual == golden, f"normalized live JUnit XML differs from {golden_path}:\n{actual}"
