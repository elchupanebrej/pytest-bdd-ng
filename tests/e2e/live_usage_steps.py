"""Installed-consumer BDD steps for the official Cucumber UsageFormatter."""

from __future__ import annotations

import csv
import json
import os
import re
import select
import shlex
import shutil
import stat
import struct
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, parsers, then, when
from pytest_cuke.model.message_stream_validation import validate_message_stream
from pytest_cuke.model.message_types import message_from_dict
from pytest_cuke.model.message_validation import validate_envelope


_PRODUCT_ROOT = Path(__file__).resolve().parents[2]
_OFFICIAL_CUCUMBER_PACKAGES = {"@cucumber/cucumber": "13.3.0"}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_USAGE_FEATURE = """\
Feature: Cucumber Usage real definition identities
  Scenario: The usage formatter reports repeated match examples
    Given shared usage identity
    When shared usage identity
    Given usage expression accepts alpha
    When usage regex records 11
    Then usage expression reports alpha 11
    Given usage expression accepts bravo
    When usage regex records 22
    Then usage expression reports bravo 22
    Given usage expression accepts charlie
    When usage regex records 33
    Then usage expression reports charlie 33
    Given usage expression accepts delta
    When usage regex records 44
    Then usage expression reports delta 44
    Given usage expression accepts echo
    When usage regex records 55
    Then usage expression reports echo 55
    Given usage expression accepts foxtrot
    When usage regex records 66
    Then usage expression reports foxtrot 66

  Scenario: A failing definition remains in pytest's failure summary
    When usage failure is retained
"""
_BACKEND_FAILURE_FEATURE = """\
Feature: Cucumber Usage backend finalization failure
  Scenario: A failing scenario stays failed if the UsageFormatter backend fails
    When usage backend failure scenario fails
"""
_USAGE_BACKEND_PRELOAD = """\
if (
    process.execArgv.includes("--input-type=module") &&
    process.execArgv.some((argument) => argument.includes("UsageFormatter"))
) {
  process.once("beforeExit", () => {
    throw new Error("usage backend finalization sentinel");
  });
}
"""
_PASSING_FEATURE = """\
Feature: Cucumber Usage selected definition
  Scenario: The usage consumer scenario passes
    Given usage consumer sample scenario passes
"""
_MARKER_FEATURE = """\
Feature: Cucumber Usage preflight marker
  Scenario: The marker scenario must not start before preflight finishes
    Given the usage consumer scenario records that it started
"""
_EMPTY_FEATURE = """\
Feature: Cucumber Usage without definitions
  Scenario: The missing step remains a pytest failure
    Given this usage step has no definition
"""
_WIDTH_FEATURE = """\
Feature: Cucumber Usage narrow terminal
  Scenario: A short usage row fits in a narrow terminal
    Given usage consumer sample scenario passes
"""
_SUPPORT_PLUGIN = """\
from pathlib import Path

from pytest_cuke import given, parsers, then, when

ROOT = Path(__file__).parent


@given("shared usage identity")
def given_shared_usage_identity():
    pass


@when("shared usage identity")
def when_shared_usage_identity():
    pass


@given(
    parsers.cucumber_expression("usage expression accepts {word}"),
    anonymous_group_names=["value"],
)
def usage_expression_accepts(value):
    assert value


@when(
    parsers.cucumber_regular_expression(r"^usage regex records (\\d+)$"),
    anonymous_group_names=["number"],
)
def usage_regex_records(number):
    assert number > 0


@then(
    parsers.cucumber_expression("usage expression reports {word} {int}"),
    anonymous_group_names=["value", "number"],
)
def usage_expression_reports(value, number):
    assert value and number > 0


@when("usage failure is retained")
def usage_failure_is_retained():
    raise AssertionError("official usage pytest failure sentinel")


@when("usage backend failure scenario fails")
def usage_backend_failure_scenario_fails():
    raise AssertionError("usage backend pytest failure sentinel")


@given("usage consumer sample scenario passes")
def usage_consumer_sample_scenario_passes():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")


@given("the usage consumer scenario records that it started")
def usage_consumer_scenario_records_that_it_started():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""
_PUBLIC_FILE_FORMATTER = """\
from pathlib import Path
import sys

from pytest_cuke.formatter_api import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    script = (
        "import json, sys; "
        "rows = [json.loads(line) for line in sys.stdin if line.strip()]; "
        "report = {'messageCount': len(rows), "
        "'testCases': sum('testCase' in row for row in rows), "
        "'finishedSteps': sum('testStepFinished' in row for row in rows)}; "
        "print(json.dumps(report, sort_keys=True))"
    )
    return (FormatterRequest(
        name="usage-public-json-probe",
        command=(sys.executable, "-c", script),
        output_path=Path("artifacts/public-usage.json"),
        working_directory=Path(__file__).parent,
    ),)
"""
_PUBLIC_TERMINAL_FORMATTER = """\
from pathlib import Path
import sys

from pytest_cuke.formatter_api import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    script = (
        "from pathlib import Path; import sys; "
        "Path('terminal-formatter-started.marker').write_text('started'); "
        "sys.stdin.read(); print('USAGE_PUBLIC_TERMINAL_SENTINEL')"
    )
    return (FormatterRequest(
        name="usage-public-terminal-probe",
        command=(sys.executable, "-c", script),
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
        raise ValueError("usage consumer workspaces must stay inside the consumer project")
    destination = (root / relative).resolve()
    if root not in destination.parents and destination != root:
        raise ValueError("usage consumer workspaces must stay inside the consumer project")
    return destination


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("usage consumer files must stay inside the consumer project")
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
    usage_setting: str | None = None,
    public_file_formatter: bool = False,
    public_terminal_formatter: bool = False,
    include_support_plugin: bool = True,
) -> Path:
    root = _safe_workspace(consumer, workspace)
    root.mkdir(parents=True, exist_ok=True)
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    if usage_setting is not None:
        config += f"cuke_usage = {json.dumps(usage_setting, ensure_ascii=False)}\n"
    _write_file(root, "pyproject.toml", config)

    plugins = []
    if include_support_plugin:
        plugins.append("usage_consumer_steps")
        _write_file(root, "usage_consumer_steps.py", _SUPPORT_PLUGIN)
    if public_file_formatter:
        plugins.append("usage_public_file_formatter")
        _write_file(root, "usage_public_file_formatter.py", _PUBLIC_FILE_FORMATTER)
    if public_terminal_formatter:
        plugins.append("usage_public_terminal_formatter")
        _write_file(root, "usage_public_terminal_formatter.py", _PUBLIC_TERMINAL_FORMATTER)
    _write_file(root, "conftest.py", f"pytest_plugins = {plugins!r}\n")
    _write_file(root, f"features/{feature_name}", feature)
    (root / "artifacts").mkdir(exist_ok=True)
    consumer._usage_workspace = root
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


def _install_official_usage_runtime(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the official Cucumber UsageFormatter lane requires Node.js and npm")
    node, npm, environment = runtime
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    package_json = {
        "name": "pytest-cuke-usage-consumer",
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
    node_version = subprocess.run(
        [node, "--version"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert node_version.returncode == 0, node_version.stderr
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)
    consumer._usage_node_version = node_version.stdout.strip()
    consumer._usage_cucumber_version = installed_version


def _restore_readonly_directory(consumer: Any) -> None:
    state = getattr(consumer, "_usage_readonly_directory", None)
    if state is None:
        return
    directory, original_mode, sid = state
    if sid is None:
        directory.chmod(original_mode)
    else:
        icacls = shutil.which("icacls.exe") or shutil.which("icacls")
        assert icacls is not None, "Windows icacls is required to restore the Usage destination ACL"
        restored = subprocess.run(
            [icacls, str(directory), "/remove:d", f"*{sid}"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        assert restored.returncode == 0, f"could not restore the Usage destination ACL:\n{restored.stdout}\n{restored.stderr}"
    consumer._usage_readonly_directory = None


def _run_pytest(consumer: Any, arguments: str) -> subprocess.CompletedProcess[str]:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    command = [str(consumer.pytest), *shlex.split(arguments)]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
    finally:
        _restore_readonly_directory(consumer)
    consumer.pytest_result = result
    return result


def _run_pytest_in_pty(
    consumer: Any,
    arguments: str,
    *,
    width: int,
) -> subprocess.CompletedProcess[str]:
    if os.name != "posix":
        pytest.skip("pseudo-terminal width acceptance requires POSIX PTY support")
    try:
        import fcntl
        import pty
        import termios
    except ImportError:
        pytest.skip("this platform does not provide pseudo-terminal support")

    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    command = [str(consumer.pytest), *shlex.split(arguments)]
    environment = dict(consumer.env)
    environment.update({"COLUMNS": str(width), "TERM": "xterm", "PY_COLORS": "0"})
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, width, 0, 0))
    process = subprocess.Popen(
        command,
        cwd=root,
        env=environment,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)
    output = bytearray()
    deadline = time.monotonic() + 90
    try:
        while process.poll() is None:
            if time.monotonic() >= deadline:
                process.kill()
                process.wait(timeout=5)
                raise AssertionError("pytest did not finish in the constrained usage terminal")
            readable, _, _ = select.select([master], [], [], 0.1)
            if readable:
                try:
                    output.extend(os.read(master, 4096))
                except OSError:
                    break
        while True:
            readable, _, _ = select.select([master], [], [], 0)
            if not readable:
                break
            try:
                output.extend(os.read(master, 4096))
            except OSError:
                break
    finally:
        if process.poll() is None:
            process.wait(timeout=5)
        os.close(master)

    result = subprocess.CompletedProcess(
        command,
        process.returncode,
        stdout=output.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n"),
        stderr="",
    )
    consumer.pytest_result = result
    consumer._usage_pty_output = result.stdout
    return result


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this usage consumer"
    return f"{result.stdout}\n{result.stderr}"


def _read_messages(consumer: Any, relative_path: str) -> list[dict[str, Any]]:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    path = root / relative_path
    assert path.is_file(), f"Cucumber Messages artifact is missing: {path}"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and all(isinstance(row, dict) for row in rows), rows
    envelopes = []
    for line_number, row in enumerate(rows, start=1):
        envelope = message_from_dict(row)
        envelope_diagnostics = validate_envelope(envelope)
        assert not envelope_diagnostics, f"invalid Messages envelope at line {line_number}: {envelope_diagnostics!r}"
        envelopes.append(envelope)
    stream_diagnostics = validate_message_stream(envelopes)
    assert not stream_diagnostics, f"invalid Messages lifecycle: {stream_diagnostics!r}"
    return rows


def _current_usage_messages_path(consumer: Any) -> str:
    return str(getattr(consumer, "_usage_messages_relative_path", "artifacts/messages.ndjson"))


def _usage_stream(consumer: Any) -> str:
    result = consumer.pytest_result
    assert result is not None, "installed pytest has not run in this usage consumer"
    streams = [stream for stream in (result.stdout, result.stderr) if "Pattern / Text" in stream]
    assert len(streams) == 1, (
        "the official usage report should appear once on a single terminal stream; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert streams[0].count("Pattern / Text") == 1, streams[0]
    return _ANSI.sub("", streams[0])


def _table_rows(output: str) -> list[list[str]]:
    rows = []
    for line in _ANSI.sub("", output).splitlines():
        if "│" not in line:
            continue
        cells = [cell.strip() for cell in line.split("│")[1:-1]]
        if len(cells) == 3:
            rows.append(cells)
    return rows


def _message_definition_records(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    definitions = {
        message["stepDefinition"]["id"]: message["stepDefinition"] for message in rows if "stepDefinition" in message
    }
    counts: Counter[str] = Counter()
    for message in rows:
        test_case = message.get("testCase")
        if not isinstance(test_case, dict):
            continue
        for test_step in test_case.get("testSteps", []):
            counts.update(test_step.get("stepDefinitionIds", []))
    return definitions, counts


def _latest_complete_test_run(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    starts = [index for index, row in enumerate(rows) if isinstance(row.get("testRunStarted"), dict)]
    assert starts, "Messages stream has no testRunStarted envelope"
    start = starts[-1]
    finishes = [index for index in range(start, len(rows)) if isinstance(rows[index].get("testRunFinished"), dict)]
    assert finishes, "latest Messages test run has no testRunFinished envelope"
    finish = finishes[-1]
    run = rows[start : finish + 1]
    assert sum(isinstance(row.get("testRunStarted"), dict) for row in run) == 1, run
    assert sum(isinstance(row.get("testRunFinished"), dict) for row in run) == 1, run
    return run


def _message_definition_durations(rows: list[dict[str, Any]]) -> dict[str, list[int]]:
    run = _latest_complete_test_run(rows)
    cases = {row["testCase"]["id"]: row["testCase"] for row in run if isinstance(row.get("testCase"), dict)}
    starts = {
        row["testCaseStarted"]["id"]: row["testCaseStarted"]
        for row in run
        if isinstance(row.get("testCaseStarted"), dict)
    }
    durations: dict[str, list[int]] = {}
    for row in run:
        finished = row.get("testStepFinished")
        if not isinstance(finished, dict):
            continue
        started = starts.get(finished.get("testCaseStartedId"))
        assert started is not None, finished
        test_case = cases[started["testCaseId"]]
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
        # Cucumber's UsageFormatter excludes ambiguous matches in the same way.
        if len(definition_ids) != 1:
            continue
        duration = finished.get("testStepResult", {}).get("duration")
        if not isinstance(duration, dict):
            continue
        seconds = duration.get("seconds", 0)
        nanos = duration.get("nanos", 0)
        assert isinstance(seconds, (int, float)) and isinstance(nanos, (int, float)), duration
        assert seconds >= 0 and nanos >= 0, duration
        duration_ns = round(seconds * 1_000_000_000 + nanos)
        durations.setdefault(definition_ids[0], []).append(duration_ns)
    return durations


def _assert_displayed_usage_durations_match_messages(report: str, messages: list[dict[str, Any]]) -> None:
    run = _latest_complete_test_run(messages)
    definitions, counts = _message_definition_records(run)
    durations_by_definition = _message_definition_durations(run)
    table_rows = _table_rows(report)
    assert table_rows and table_rows[0] == ["Pattern / Text", "Duration", "Location"], table_rows

    for definition_id, definition in definitions.items():
        match_count = counts[definition_id]
        durations = durations_by_definition.get(definition_id, [])
        if not match_count:
            assert not durations, (definition, durations)
            continue
        assert durations, f"Messages has no executed step duration for used definition {definition!r}"
        row = _assert_reported_definition(table_rows, definition)
        displayed = re.fullmatch(r"(?P<milliseconds>\d+(?:\.\d+)?)ms", row[1])
        assert displayed is not None, row
        actual_ms = float(displayed.group("milliseconds"))
        expected_ms = sum(durations) / len(durations) / 1_000_000
        # Cucumber UsageFormatter renders a two-decimal mean in milliseconds;
        # allow half of its last displayed unit plus sub-microsecond conversion noise.
        assert abs(actual_ms - expected_ms) <= 0.005001, (definition, expected_ms, actual_ms, durations)


def _source_line(definition: dict[str, Any]) -> tuple[str, int]:
    source_reference = definition["sourceReference"]
    uri = str(source_reference["uri"]).replace("\\", "/")
    line = int(source_reference["location"]["line"])
    return uri.rsplit("/", 1)[-1], line


def _assert_reported_definition(
    table_rows: list[list[str]],
    definition: dict[str, Any],
    *,
    expected_duration: bool = True,
) -> list[str]:
    filename, line = _source_line(definition)
    suffix = f"{filename}:{line}"
    matches = [row for row in table_rows if row[2].replace("\\", "/").endswith(suffix)]
    assert len(matches) == 1, f"expected one UsageFormatter row for Messages definition {definition!r}: {table_rows!r}"
    row = matches[0]
    pattern_source = definition["pattern"]["source"]
    assert pattern_source in row[0], f"UsageFormatter row did not preserve pattern {pattern_source!r}: {row!r}"
    if expected_duration:
        assert re.fullmatch(r"\d+(?:\.\d+)?ms", row[1]), f"used step duration was missing: {row!r}"
    return row


def _reported_examples_for_definition(table_rows: list[list[str]], definition: dict[str, Any]) -> tuple[list[str], int]:
    definition_row = _assert_reported_definition(table_rows, definition)
    definition_index = table_rows.index(definition_row)
    definition_filename, _ = _source_line(definition)
    examples: list[str] = []
    remainder_count = 0
    for row in table_rows[definition_index + 1 :]:
        location = row[2].replace("\\", "/")
        if location.rsplit("/", 1)[-1].startswith(f"{definition_filename}:"):
            break
        if row[0] == "1 more":
            remainder_count += 1
        elif row[2].startswith("file:"):
            examples.append(row[0])
    return examples, remainder_count


def _assert_pytest_failure(consumer: Any, *, expected_failures: int, expected_passes: int) -> str:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, f"the failing usage scenario should fail pytest:\n{output}"
    assert re.search(r"(?m)^=+ FAILURES =+$", output), f"pytest's normal failure section was lost:\n{output}"
    assert re.search(r"(?im)^=+\s*short test summary info\s*=+\s*$", output), (
        f"pytest's short test summary was lost:\n{output}"
    )
    result_lines = [
        line
        for line in output.splitlines()
        if re.search(r"\bin \d+(?:\.\d+)?s\b", line) and re.search(r"\b\d+ failed\b", line)
    ]
    assert len(result_lines) == 1, f"pytest's result summary should occur once:\n{output}"
    assert re.search(rf"\b{expected_failures} failed\b", result_lines[0]), result_lines[0]
    assert re.search(rf"\b{expected_passes} passed\b", result_lines[0]), result_lines[0]
    assert "official usage pytest failure sentinel" in output, output
    return output


def _assert_usage_matches_messages(consumer: Any) -> str:
    _assert_pytest_failure(consumer, expected_failures=1, expected_passes=1)
    output = _usage_stream(consumer)
    table_rows = _table_rows(output)
    assert table_rows and table_rows[0] == ["Pattern / Text", "Duration", "Location"], table_rows
    assert re.search(r"\b\d+(?:\.\d+)?ms\b", output), output

    messages = _read_messages(consumer, "artifacts/messages.ndjson")
    assert messages[-1].get("testRunFinished") is not None, "the UsageFormatter must receive the finalized Messages run"
    definitions, counts = _message_definition_records(messages)
    used = [definition for definition_id, definition in definitions.items() if counts[definition_id] > 0]
    assert len(used) == 6, f"expected five repeated-match definitions and one failing definition, got {used!r}"
    assert all(definition_id in definitions for definition_id in counts), counts

    expected_counts = {
        ("shared usage identity", "CUCUMBER_EXPRESSION"): 1,
        ("usage expression accepts {word}", "CUCUMBER_EXPRESSION"): 6,
        (r"^usage regex records (\d+)$", "REGULAR_EXPRESSION"): 6,
        ("usage expression reports {word} {int}", "CUCUMBER_EXPRESSION"): 6,
        ("usage failure is retained", "CUCUMBER_EXPRESSION"): 1,
    }
    for (source, pattern_type), expected_count in expected_counts.items():
        matches = [
            (definition_id, definition)
            for definition_id, definition in definitions.items()
            if definition["pattern"]["source"] == source and definition["pattern"]["type"] == pattern_type
        ]
        expected_definitions = 2 if source == "shared usage identity" else 1
        assert len(matches) == expected_definitions, f"Messages definition identities for {source!r}: {matches!r}"
        for definition_id, definition in matches:
            assert counts[definition_id] == expected_count, (
                f"Messages match count for {definition!r} should be {expected_count}, got {counts[definition_id]}"
            )

    for definition_id, definition in definitions.items():
        is_used = counts[definition_id] > 0
        row = _assert_reported_definition(table_rows, definition, expected_duration=is_used)
        assert (row[1] == "UNUSED") is (not is_used), (
            f"UsageFormatter usage status disagreed with Messages match identity {definition_id}: {row!r}"
        )

    shared_locations = {
        _source_line(definition)[1]
        for definition in definitions.values()
        if definition["pattern"]["source"] == "shared usage identity"
    }
    assert len(shared_locations) == 2, (
        f"identical text must retain distinct definition source locations: {shared_locations!r}"
    )
    expected_examples = {
        "usage expression accepts {word}": {
            f"usage expression accepts {value}" for value in ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot")
        },
        r"^usage regex records (\d+)$": {f"usage regex records {number}" for number in (11, 22, 33, 44, 55, 66)},
        "usage expression reports {word} {int}": {
            f"usage expression reports {value} {number}"
            for value, number in zip(
                ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot"),
                (11, 22, 33, 44, 55, 66),
                strict=True,
            )
        },
    }
    for definition in used:
        source = definition["pattern"]["source"]
        expected = expected_examples.get(source)
        if expected is None:
            continue
        examples, remainder_count = _reported_examples_for_definition(table_rows, definition)
        assert len(examples) == 5 and set(examples) <= expected and len(set(examples)) == 5, (
            f"UsageFormatter examples for {source!r} should show five distinct actual matches, got {examples!r}\n"
            + output
        )
        assert remainder_count == 1, f"expected one abbreviated sixth match for {source!r}: {output}"
    assert sum(row[0] == "1 more" for row in table_rows) == len(expected_examples), (
        "each of the three repeated definitions used by six examples should abbreviate its sixth match:\n" + output
    )
    return output


def _assert_single_passing_usage_definition(consumer: Any, report: str) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode == 0, f"the configured usage scenario should pass:\n{output}"
    assert re.search(r"\b1 passed\b", output), output
    messages = _read_messages(consumer, "artifacts/messages.ndjson")
    definitions, counts = _message_definition_records(messages)
    used = [(definition_id, definition) for definition_id, definition in definitions.items() if counts[definition_id]]
    assert len(used) == 1 and counts[used[0][0]] == 1, (definitions, counts)
    _assert_reported_definition(_table_rows(report), used[0][1])


def _assert_no_scenario_started(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    assert not (root / "scenario-started.marker").exists(), "the preflight marker scenario ran unexpectedly"


def _assert_preflight_error(consumer: Any, expected: str) -> str:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, f"usage preflight unexpectedly passed:\n{output}"
    assert expected.lower() in output.lower(), output
    _assert_no_scenario_started(consumer)
    assert "1 passed" not in output, output
    return output


@given("the usage consumer prepares six examples, repeated definition text, and a failing step")
def prepare_usage_identity_consumer(consumer: Any) -> None:
    _prepare_consumer(consumer, _USAGE_FEATURE, feature_name="usage-identities.feature")


@given("the consumer installs the pinned official Cucumber UsageFormatter runtime")
def install_pinned_usage_runtime(consumer: Any) -> None:
    _install_official_usage_runtime(consumer)


@when(parsers.re(r'I run pytest with arguments "(?P<flags>[^"]*)"'))
def run_usage_consumer_pytest(flags: str, consumer: Any) -> None:
    messages_argument = next(
        (argument for argument in shlex.split(flags) if argument.startswith("--cuke-messages-ndjson=")),
        None,
    )
    if messages_argument is not None:
        consumer._usage_messages_relative_path = messages_argument.split("=", 1)[1]
    if getattr(consumer, "_usage_pty_width", None) is None:
        _run_pytest(consumer, flags)
    else:
        _run_pytest_in_pty(consumer, flags, width=consumer._usage_pty_width)


@then("the official usage table should match Messages definition identities and preserve pytest failure")
def usage_report_matches_actual_messages_identities(consumer: Any) -> None:
    consumer._usage_first_report = _assert_usage_matches_messages(consumer)


@then("the displayed Usage durations should match the latest Messages run")
def displayed_usage_durations_match_latest_messages(consumer: Any) -> None:
    report = _usage_stream(consumer)
    _assert_displayed_usage_durations_match_messages(
        report, _read_messages(consumer, _current_usage_messages_path(consumer))
    )


@when("the consumer adds an unused usage definition")
def add_unused_usage_definition(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    plugin = root / "usage_consumer_steps.py"
    assert plugin.is_file(), plugin
    with plugin.open("a", encoding="utf-8") as stream:
        stream.write(
            '\n\n@given("the never exercised usage pattern")\ndef never_exercised_usage_pattern():\n    pass\n'
        )


@then("the official usage output should add the unused definition as UNUSED")
def usage_output_lists_unused_definition(consumer: Any) -> None:
    first_report = getattr(consumer, "_usage_first_report", None)
    assert isinstance(first_report, str), "the first official usage report was not checked"
    output = _assert_pytest_failure(consumer, expected_failures=1, expected_passes=1)
    report = _usage_stream(consumer)
    assert "the never exercised usage pattern" in report and "UNUSED" in report, report
    assert "the never exercised usage pattern" not in first_report, first_report
    assert report != first_report, "adding an unused definition did not change real backend output"
    rows = _table_rows(report)
    unused_rows = [row for row in rows if row[1] == "UNUSED"]
    first_unused_count = sum(row[1] == "UNUSED" for row in _table_rows(first_report))
    added_unused_rows = [row for row in unused_rows if row[0] == "the never exercised usage pattern"]
    assert len(unused_rows) == first_unused_count + 1, (first_unused_count, unused_rows)
    assert len(added_unused_rows) == 1, added_unused_rows
    plugin_lines = (
        (getattr(consumer, "_usage_workspace", _consumer_root(consumer)) / "usage_consumer_steps.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    definition_line = next(
        index for index, line in enumerate(plugin_lines, start=1) if line.startswith("def never_exercised")
    )
    assert f"usage_consumer_steps.py:{definition_line - 1}" in added_unused_rows[0][2].replace("\\", "/"), (
        added_unused_rows[0]
    )
    assert "official usage pytest failure sentinel" in output


@given("the usage consumer prepares one failing scenario for backend finalization")
def prepare_usage_backend_failure_consumer(consumer: Any) -> None:
    _prepare_consumer(consumer, _BACKEND_FAILURE_FEATURE, feature_name="usage-backend-failure.feature")


@given("the usage consumer installs a Node preload that fails during UsageFormatter finalization")
def install_usage_backend_failure_preload(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    preload = root / "usage-backend-finalization-failure.cjs"
    preload.write_text(_USAGE_BACKEND_PRELOAD, encoding="utf-8")
    consumer.env["NODE_OPTIONS"] = f"--require={preload.resolve()}"


@then("the Usage backend failure should remain visible beside the pytest failure")
def usage_backend_failure_preserves_pytest_failure(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "usage backend pytest failure sentinel" in output, output
    assert "usage backend finalization sentinel" in output, output
    assert re.search(r"\b1 failed\b", output), output
    messages = _read_messages(consumer, "artifacts/messages.ndjson")
    assert messages[-1].get("testRunFinished", {}).get("success") is False, messages[-1]


@given("the usage consumer prepares a passing feature with cuke_usage configured as dash")
def prepare_dash_configured_usage_consumer(consumer: Any) -> None:
    _prepare_consumer(consumer, _PASSING_FEATURE, feature_name="configured-usage.feature", usage_setting="-")


@then("configured usage should report the passing definition and its source")
def configured_usage_reports_passing_definition(consumer: Any) -> None:
    report = _usage_stream(consumer)
    assert _table_rows(report)[0] == ["Pattern / Text", "Duration", "Location"]
    _assert_single_passing_usage_definition(consumer, report)
    assert getattr(consumer, "_usage_cucumber_version", None) == "13.3.0"


@given("the usage consumer prepares a passing feature with a configured usage path")
def prepare_path_configured_usage_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _PASSING_FEATURE,
        feature_name="configured-usage-path.feature",
        usage_setting="artifacts/configured usage report.txt",
    )


@then("configured usage should write the report path without terminal output")
def configured_usage_writes_path(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    report_path = root / "artifacts" / "configured usage report.txt"
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode == 0, output
    assert report_path.is_file(), f"configured usage report is missing: {report_path}"
    report = report_path.read_text(encoding="utf-8")
    assert "Pattern / Text" in report and "usage consumer sample scenario passes" in report, report
    assert "Pattern / Text" not in output, f"configured file output also claimed stdout:\n{output}"
    _assert_single_passing_usage_definition(consumer, report)


@given("the usage consumer prepares a passing feature with default configuration")
def prepare_default_usage_consumer(consumer: Any) -> None:
    _prepare_consumer(consumer, _PASSING_FEATURE, feature_name="default-usage.feature")


@given("the usage consumer PATH excludes Node.js and npm")
def hide_node_and_npm_from_usage_consumer(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    empty_bin = root / "empty-path"
    empty_bin.mkdir(exist_ok=True)
    consumer.env["PATH"] = str(empty_bin)
    consumer.env.pop("NODE_PATH", None)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@then("the default run should pass without requesting the usage backend")
def usage_default_is_inert(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    assert result is not None and result.returncode == 0, output
    assert "1 passed" in output, output
    assert "Pattern / Text" not in output and "No step definitions" not in output, output
    assert "@cucumber/cucumber" not in output and "npm install" not in output.lower(), output
    assert not (root / "package.json").exists()
    assert not (root / "node_modules").exists()
    assert (root / "scenario-started.marker").is_file(), "the default scenario should still execute"


@given("the usage consumer prepares a Unicode workspace with spaces and a public terminal formatter")
def prepare_unicode_usage_file_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _PASSING_FEATURE,
        feature_name="usage-file-output.feature",
        workspace="usage workspace 東京 café",
        public_file_formatter=True,
        public_terminal_formatter=True,
    )


@then("the usage file and all independent report outputs should be valid")
def usage_file_coexists_with_independent_outputs(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode == 0, output
    usage_path = root / "artifacts" / "usage report.txt"
    messages_path = root / "artifacts" / "messages.ndjson"
    cucumber_json_path = root / "artifacts" / "cucumber.json"
    junit_path = root / "artifacts" / "junit.xml"
    public_usage_path = root / "artifacts" / "public-usage.json"
    usage_json_path = root / "artifacts" / "usage.json"
    destinations = {
        path.resolve()
        for path in (usage_path, usage_json_path, messages_path, cucumber_json_path, junit_path, public_usage_path)
    }
    assert len(destinations) == 6, destinations

    assert usage_path.is_file(), usage_path
    usage_report = usage_path.read_text(encoding="utf-8")
    assert "Pattern / Text" in usage_report and "Duration" in usage_report and "Location" in usage_report
    assert "usage consumer sample scenario passes" in usage_report, usage_report
    assert "\ufffd" not in usage_report, usage_report
    assert "Pattern / Text" not in output, f"file-selected UsageFormatter also wrote to stdout:\n{output}"

    messages = _read_messages(consumer, "artifacts/messages.ndjson")
    assert messages[-1].get("testRunFinished") is not None
    assert sum("testCase" in row for row in messages) == 1
    assert sum("testStepFinished" in row for row in messages) == 1

    cucumber_json = json.loads(cucumber_json_path.read_text(encoding="utf-8"))
    assert isinstance(cucumber_json, list) and len(cucumber_json) == 1, cucumber_json
    assert cucumber_json[0].get("name") == "Cucumber Usage selected definition", cucumber_json

    junit_root = ET.parse(junit_path).getroot()
    assert junit_root.tag in {"testsuite", "testsuites"}, junit_root.tag
    assert len(list(junit_root.iter("testcase"))) == 1, ET.tostring(junit_root, encoding="unicode")

    public_usage = json.loads(public_usage_path.read_text(encoding="utf-8"))
    assert public_usage["messageCount"] > 0, public_usage
    assert public_usage["testCases"] == 1 and public_usage["finishedSteps"] == 1, public_usage

    usage_json = json.loads(usage_json_path.read_text(encoding="utf-8"))
    assert isinstance(usage_json, list) and all(isinstance(item, dict) for item in usage_json), usage_json
    matched_usage_definitions = [
        item for item in usage_json if item.get("pattern") == "usage consumer sample scenario passes"
    ]
    assert len(matched_usage_definitions) == 1, usage_json
    usage_json_definition = matched_usage_definitions[0]
    assert usage_json_definition["patternType"] == "CucumberExpression", usage_json_definition
    assert usage_json_definition["uri"].replace("\\", "/").endswith("usage_consumer_steps.py"), usage_json_definition
    assert len(usage_json_definition["matches"]) == 1, usage_json_definition
    usage_json_match = usage_json_definition["matches"][0]
    assert usage_json_match["text"] == "usage consumer sample scenario passes", usage_json_match
    assert isinstance(usage_json_match.get("duration"), dict), usage_json_match

    assert (root / "terminal-formatter-started.marker").is_file(), (
        "a file-selected usage formatter must leave the terminal formatter slot available"
    )
    assert output.count("USAGE_PUBLIC_TERMINAL_SENTINEL") == 1, output
    assert getattr(consumer, "_usage_cucumber_version", None) == "13.3.0"


@given("the public Cucumber Usage example is copied into the consumer")
def copy_public_usage_example(consumer: Any) -> None:
    source = _PRODUCT_ROOT / "examples" / "cucumber-usage"
    assert source.is_dir(), f"the public Cucumber Usage example is missing: {source}"
    workspace = _safe_workspace(consumer, "cucumber-usage-example")
    shutil.copytree(source, workspace)
    (workspace / "artifacts").mkdir()
    consumer._usage_workspace = workspace


def _public_usage_example_report(consumer: Any) -> str:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode == 0, output
    assert "2 passed" in output, output
    workspace: Path = Path(consumer._usage_workspace)
    report_path = workspace / "artifacts" / "usage.txt"
    assert report_path.is_file(), f"the public Usage example did not write its report: {report_path}\n{output}"
    report = report_path.read_text(encoding="utf-8")
    assert all(header in report for header in ("Pattern / Text", "Duration", "Location")), report
    assert "\ufffd" not in report, report
    return report


@then("the public Usage example should preserve real matches and its unused definition")
def public_usage_example_preserves_real_matches_and_unused(consumer: Any) -> None:
    report = _public_usage_example_report(consumer)
    messages = _read_messages(consumer, _current_usage_messages_path(consumer))
    run = _latest_complete_test_run(messages)
    definitions, counts = _message_definition_records(run)
    expected_patterns = {
        "the Usage example starts a clean request": 2,
        "the Usage example handles {word}": 2,
        "the Usage example records {word}": 2,
        "the Usage example documents an unused definition": 0,
    }
    assert len(definitions) == len(expected_patterns), definitions
    table_rows = _table_rows(report)
    for pattern, expected_count in expected_patterns.items():
        found = [definition for definition in definitions.values() if definition["pattern"]["source"] == pattern]
        assert len(found) == 1, (pattern, found)
        definition = found[0]
        assert _source_line(definition)[0] == "cucumber_usage_example_steps.py", definition
        assert counts[definition["id"]] == expected_count, (definition, counts)
        row = _assert_reported_definition(table_rows, definition, expected_duration=expected_count > 0)
        assert (row[1] == "UNUSED") is (expected_count == 0), row
    for text in (
        "the Usage example starts a clean request",
        "the Usage example handles alpha",
        "the Usage example handles bravo",
        "the Usage example records alpha",
        "the Usage example records bravo",
    ):
        assert text in report, (text, report)
    assert getattr(consumer, "_usage_cucumber_version", None) == "13.3.0"
    consumer._public_usage_example_first_report = report


@then("the public Usage report durations should match the latest Messages run")
def public_usage_report_durations_match_latest_messages(consumer: Any) -> None:
    report = _public_usage_example_report(consumer)
    messages = _read_messages(consumer, _current_usage_messages_path(consumer))
    _assert_displayed_usage_durations_match_messages(report, messages)


@when("the consumer adds a new unused definition to the public Usage example")
def add_unused_public_usage_definition(consumer: Any) -> None:
    plugin = consumer._usage_workspace / "cucumber_usage_example_steps.py"
    with plugin.open("a", encoding="utf-8") as stream:
        stream.write(
            '\n\n@given("the Usage example introduces another unused definition")\n'
            "def another_unused_definition() -> None:\n"
            '    """This newly added definition must appear as UNUSED."""\n'
        )


@then("the new public Usage definition should change the real report")
def added_unused_public_usage_definition_changes_report(consumer: Any) -> None:
    report = _public_usage_example_report(consumer)
    previous_report = consumer._public_usage_example_first_report
    new_pattern = "the Usage example introduces another unused definition"
    assert report != previous_report, "adding a real unused public definition did not change the report"
    assert new_pattern not in previous_report, previous_report
    table_rows = _table_rows(report)
    run = _latest_complete_test_run(_read_messages(consumer, _current_usage_messages_path(consumer)))
    definitions, counts = _message_definition_records(run)
    found = [definition for definition in definitions.values() if definition["pattern"]["source"] == new_pattern]
    assert len(found) == 1, found
    definition = found[0]
    assert counts[definition["id"]] == 0, (definition, counts)
    row = _assert_reported_definition(table_rows, definition, expected_duration=False)
    assert row[1] == "UNUSED", row
    assert sum(row[1] == "UNUSED" for row in table_rows) == 2, table_rows
    plugin_lines = (
        (consumer._usage_workspace / "cucumber_usage_example_steps.py").read_text(encoding="utf-8").splitlines()
    )
    definition_line = next(
        index for index, line in enumerate(plugin_lines, start=1) if line.startswith("def another_unused_definition")
    )
    assert f"cucumber_usage_example_steps.py:{definition_line - 1}" in row[2].replace("\\", "/"), row


@given("the usage consumer prepares a terminal conflict scenario and a public terminal formatter")
def prepare_usage_terminal_conflict_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _MARKER_FEATURE,
        feature_name="terminal-conflict.feature",
        public_terminal_formatter=True,
    )


@then("a competing stdout formatter should be rejected before formatting or scenario execution")
def competing_stdout_formatter_is_preflighted(consumer: Any) -> None:
    output = _assert_preflight_error(consumer, "Only one live formatter may write to the terminal")
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    assert "usage-public-terminal-probe" in output, output
    assert not (root / "terminal-formatter-started.marker").exists()
    assert "USAGE_PUBLIC_TERMINAL_SENTINEL" not in output


@given("the usage consumer prepares a preflight marker scenario")
def prepare_usage_preflight_consumer(consumer: Any) -> None:
    _prepare_consumer(consumer, _MARKER_FEATURE, feature_name="preflight-marker.feature")


@then("the missing usage parent should fail before tests and before Node lookup")
def missing_usage_parent_is_preflighted(consumer: Any) -> None:
    output = _assert_preflight_error(consumer, "output parent directory does not exist")
    assert "node" not in output.lower() and "npm" not in output.lower(), output
    assert not (_consumer_root(consumer) / "package.json").exists()


@given("the usage consumer prepares a preflight marker scenario with a public file formatter")
def prepare_usage_duplicate_destination_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _MARKER_FEATURE,
        feature_name="duplicate-destination.feature",
        public_file_formatter=True,
    )


@then("the duplicate canonical usage destination should fail before tests or runtime lookup")
def usage_duplicate_canonical_destination_is_preflighted(consumer: Any) -> None:
    output = _assert_preflight_error(consumer, "resolve to the same output path")
    assert "public-usage.json" in output.replace("\\", "/"), output
    assert "node" not in output.lower() and "npm" not in output.lower(), output
    assert not (_consumer_root(consumer) / "package.json").exists()


@given("the usage consumer prepares an unwritable output parent and a marker scenario")
def prepare_usage_unwritable_destination(consumer: Any) -> None:
    root = _prepare_consumer(consumer, _MARKER_FEATURE, feature_name="unwritable-destination.feature")
    directory = root / "read-only"
    directory.mkdir()
    if os.name == "nt":
        icacls = shutil.which("icacls.exe") or shutil.which("icacls")
        whoami = shutil.which("whoami.exe") or shutil.which("whoami")
        assert icacls is not None, "Windows icacls is required to prove an unwritable Usage destination"
        assert whoami is not None, "Windows whoami is required to identify the current ACL principal"
        identity = subprocess.run(
            [whoami, "/user", "/fo", "csv", "/nh"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        assert identity.returncode == 0, f"could not identify the current Windows user:\n{identity.stdout}\n{identity.stderr}"
        rows = list(csv.reader(identity.stdout.splitlines()))
        assert rows and len(rows[0]) >= 2, identity.stdout
        sid = rows[0][-1].strip()
        assert re.fullmatch(r"S-1(?:-\d+)+", sid), identity.stdout
        denied = subprocess.run(
            [icacls, str(directory), "/deny", f"*{sid}:(WD,AD)"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        assert denied.returncode == 0, f"could not deny writes to the Usage output parent:\n{denied.stdout}\n{denied.stderr}"
        state = (directory, None, sid)
        consumer._usage_readonly_directory = state
        try:
            (directory / "write-probe").write_text("probe", encoding="utf-8")
        except PermissionError:
            return
        except OSError as error:
            _restore_readonly_directory(consumer)
            raise AssertionError(f"the Windows Usage ACL probe failed unexpectedly: {error}") from error
        else:
            _restore_readonly_directory(consumer)
            raise AssertionError("the denied Windows Usage ACL still permits creating files")

    original_mode = stat.S_IMODE(directory.stat().st_mode)
    directory.chmod(original_mode & ~0o222)
    probe = directory / "write-probe"
    try:
        probe.write_text("probe", encoding="utf-8")
    except PermissionError:
        consumer._usage_readonly_directory = (directory, original_mode, None)
    except OSError as error:
        directory.chmod(original_mode)
        raise AssertionError(f"the Usage read-only probe failed unexpectedly: {error}") from error
    else:
        probe.unlink(missing_ok=True)
        directory.chmod(original_mode)
        pytest.skip("the current platform or user can still write to a read-only directory")


@then("the unwritable usage destination should fail before scenario execution")
def usage_unwritable_destination_is_preflighted(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert any(text in output.lower() for text in ("not writable", "permission denied", "permissionerror")), output
    assert "node" not in output.lower() and "npm" not in output.lower(), output
    _assert_no_scenario_started(consumer)


@given("the usage consumer exposes an isolated Node executable without npm")
def expose_node_without_npm(consumer: Any) -> None:
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    node_bin = root / "node-only-bin"
    node_bin.mkdir(exist_ok=True)
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
    consumer.env["PATH"] = os.pathsep.join((str(node_bin), str(Path(consumer.python).parent)))
    consumer.env.pop("NODE_PATH", None)
    assert shutil.which("node", path=consumer.env["PATH"]) is not None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@then("missing Node.js usage preflight should be actionable and happen before execution")
def missing_node_usage_preflight(consumer: Any) -> None:
    output = _assert_preflight_error(consumer, "requires executable 'node'")
    assert "not found on path" in output.lower(), output
    assert not (_consumer_root(consumer) / "package.json").exists()


@then("missing npm usage preflight should be actionable and happen before execution")
def missing_npm_usage_preflight(consumer: Any) -> None:
    output = _assert_preflight_error(consumer, "requires executable 'npm'")
    assert "not found on path" in output.lower(), output
    assert not (_consumer_root(consumer) / "package.json").exists()


@given("the usage consumer exposes Node.js and npm without installing the Cucumber package")
def expose_node_and_npm_without_usage_package(consumer: Any) -> None:
    runtime = _node_environment(consumer)
    if runtime is None:
        pytest.skip("the missing Cucumber package preflight lane requires Node.js and npm")
    _, _, environment = runtime
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    assert not (root / "node_modules" / "@cucumber" / "cucumber").exists()
    consumer.env["PATH"] = environment["PATH"]
    consumer.env.pop("NODE_PATH", None)


@then("missing Cucumber package usage preflight should be actionable and happen before execution")
def missing_usage_package_preflight(consumer: Any) -> None:
    output = _assert_preflight_error(consumer, "@cucumber/cucumber")
    assert any(
        text in output.lower() for text in ("requires npm package", "cannot find package", "module_not_found")
    ), output
    assert "npm install" in output.lower(), output
    root = getattr(consumer, "_usage_workspace", _consumer_root(consumer))
    assert not (root / "node_modules" / "@cucumber" / "cucumber").exists()


@given("the usage consumer prepares an undefined feature without step definitions")
def prepare_usage_empty_definitions_consumer(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        _EMPTY_FEATURE,
        feature_name="empty-usage-definitions.feature",
        include_support_plugin=False,
    )


@then("the official usage formatter should report no step definitions and retain pytest failure")
def empty_usage_definitions_preserve_undefined_failure(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode != 0, output
    assert "No step definitions" in output, output
    assert "Pattern / Text" not in output, output
    assert "StepDefinitionNotFoundError" in output or "step definition is not found" in output.lower(), output
    assert re.search(r"(?m)^=+ FAILURES =+$", output), output
    assert re.search(r"(?im)^=+\s*short test summary info\s*=+\s*$", output), output
    assert re.search(r"\b1 failed\b", output), output


@given("the usage consumer prepares a short passing feature for terminal width checks")
def prepare_usage_width_consumer(consumer: Any) -> None:
    _prepare_consumer(consumer, _WIDTH_FEATURE, feature_name="narrow-usage.feature")


@given("the usage consumer sets the terminal width to 48 columns for the next pytest run")
def set_narrow_usage_terminal(consumer: Any) -> None:
    if os.name != "posix":
        pytest.skip("the narrow UsageFormatter TTY contract uses POSIX pseudo-terminals")
    consumer._usage_pty_width = 48


@then("the narrow usage table should retain all columns and fit the terminal width")
def narrow_usage_table_fits_terminal(consumer: Any) -> None:
    result = consumer.pytest_result
    output = _output(consumer)
    assert result is not None and result.returncode == 0, output
    report = _usage_stream(consumer)
    assert all(header in report for header in ("Pattern / Text", "Duration", "Location")), report
    table_lines = _table_lines(report)
    assert table_lines, report
    widths = {line: _display_width(line) for line in table_lines}
    assert max(widths.values()) <= 48, f"usage table exceeded the 48-column terminal: {widths!r}\n{report}"


def _table_lines(output: str) -> list[str]:
    lines = _ANSI.sub("", output).splitlines()
    header_index = next((index for index, line in enumerate(lines) if "Pattern / Text" in line), None)
    assert header_index is not None, output
    start = header_index
    end = header_index
    for index in range(header_index - 1, -1, -1):
        if "┌" in lines[index] or "+---" in lines[index]:
            start = index
            break
    for index in range(header_index + 1, len(lines)):
        if "└" in lines[index] or "+---" in lines[index]:
            end = index
            break
        if lines[index].strip() and not any(character in lines[index] for character in ("│", "|")):
            break
        end = index
    return lines[start : end + 1]


def _display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1 for character in text)
