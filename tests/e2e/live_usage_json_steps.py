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
from typing import Any
from urllib.parse import unquote

import pytest
from pytest_cuke import given, parsers, then, when


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
            assert isinstance(duration, dict), match
            assert isinstance(duration.get("seconds"), (int, float)), duration
            assert isinstance(duration.get("nanos"), (int, float)), duration
            assert duration["seconds"] >= 0 and duration["nanos"] >= 0, duration
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


@then("missing Cucumber package diagnostics should stop the Usage JSON run before the marker scenario")
def missing_cucumber_usage_json_preflights(consumer: Any) -> None:
    output = _require_diagnostic_failure(consumer, "@cucumber/cucumber")
    assert "npm install" in output.lower(), output


@given("the usage-json consumer prepares a passing scenario for backend finalization")
def prepare_usage_json_backend_failure_consumer(consumer: Any) -> None:
    _prepare(consumer, feature=_BACKEND_FEATURE, feature_name="usage-json-backend-finalization.feature")


@given("the usage-json consumer installs a Node preload that fails during Usage JSON finalization")
def install_usage_json_backend_failure_preload(consumer: Any) -> None:
    root = consumer._usage_json_workspace
    preload = _write(root, "fail-usage-json-backend.cjs", _USAGE_JSON_BACKEND_PRELOAD)
    consumer.env["NODE_OPTIONS"] = f'--require="{preload.resolve()}"'


@then("the Usage JSON backend failure should remain visible")
def usage_json_backend_failure_is_visible(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _combined_output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "usage JSON backend finalization sentinel" in output, output
    assert re.search(r"\b1 passed\b", output), output
    assert re.search(r"\b1 failed\b", output) is None, output
