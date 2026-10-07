"""BDD steps for standalone rendering of saved Cucumber Messages streams."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pytest_cuke import given, parsers, then, when


_PROBE_RENDERER = """\
import json
import sys


for line in sys.stdin:
    envelope = json.loads(line)
    event_name, payload = next(iter(envelope.items()))
    rendered = {"event": event_name, "message": payload}
    sys.stdout.write(json.dumps(rendered, sort_keys=True, separators=(",", ":")) + "\\n")
    sys.stdout.flush()
"""

_PROBE_FORMATTER_PLUGIN = """\
import sys
from pathlib import Path

from pytest_cuke import FormatterRequest


def _request(selection):
    working_directory = Path(selection.working_directory)
    return FormatterRequest(
        name=selection.name,
        command=(sys.executable, str(working_directory / "formatter_probe.py")),
        output_path=selection.destination,
        working_directory=working_directory,
        timeout_seconds=5.0,
    )


def probe_request(selection):
    return _request(selection)


def probe_copy_request(selection):
    return _request(selection)
"""

_PROBE_DISTRIBUTION_METADATA = """\
Metadata-Version: 2.1
Name: pytest-cuke-offline-probe
Version: 0.0.1
"""

_PROBE_ENTRY_POINTS = """\
[pytest_cuke.formatters]
probe = offline_probe_formatter:probe_request
probe-copy = offline_probe_formatter:probe_copy_request
"""

_FAILING_FORMATTER_PLUGIN = """\
import sys
from pathlib import Path

from pytest_cuke import FormatterRequest


def failure_request(selection):
    working_directory = Path(selection.working_directory)
    return FormatterRequest(
        name=selection.name,
        command=(sys.executable, str(working_directory / "formatter_failure.py")),
        output_path=selection.destination,
        working_directory=working_directory,
        timeout_seconds=5.0,
    )
"""

_FAILING_FORMATTER_PROGRAM = """\
import sys


sys.stdin.read()
print("formatter failure sentinel", file=sys.stderr, flush=True)
raise SystemExit(23)
"""

_MISSING_NPM_PACKAGE = "pytest-cuke-definitely-missing-package"

_TRAP_MARKERS = (
    "conftest-imported.marker",
    "fixture-executed.marker",
    "feature-step-executed.marker",
    "test-source-imported.marker",
    "test-body-executed.marker",
)
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _consumer_path(consumer: Any, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("consumer formatter files must stay inside the consumer project")
    root = _consumer_root(consumer)
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("consumer formatter files must stay inside the consumer project") from exc
    return path


def _write_consumer_file(consumer: Any, relative_path: str, content: str) -> Path:
    path = _consumer_path(consumer, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _consumer_site_packages(consumer: Any) -> Path:
    result = subprocess.run(
        [
            str(consumer.python),
            "-c",
            "import sysconfig; print(sysconfig.get_paths()['purelib'])",
        ],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"could not locate consumer site-packages:\n{result.stdout}\n{result.stderr}"
    site_packages = Path(result.stdout.strip())
    assert site_packages.is_dir(), f"consumer site-packages does not exist: {site_packages}"
    return site_packages


def _register_probe_entry_points(consumer: Any) -> None:
    site_packages = _consumer_site_packages(consumer)
    _write_consumer_file(consumer, "formatter_probe.py", _PROBE_RENDERER)
    plugin_module = site_packages / "offline_probe_formatter.py"
    plugin_module.write_text(_PROBE_FORMATTER_PLUGIN, encoding="utf-8")
    distribution = site_packages / "pytest_cuke_offline_probe-0.0.1.dist-info"
    distribution.mkdir(parents=True, exist_ok=True)
    (distribution / "METADATA").write_text(_PROBE_DISTRIBUTION_METADATA, encoding="utf-8")
    (distribution / "entry_points.txt").write_text(_PROBE_ENTRY_POINTS, encoding="utf-8")


@given('the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"')
def register_saved_stream_probe_formatters(consumer: Any) -> None:
    _register_probe_entry_points(consumer)


@given("the consumer registers a formatter that reports an error and exits with status 23")
def register_saved_stream_failing_formatter(consumer: Any) -> None:
    site_packages = _consumer_site_packages(consumer)
    (site_packages / "offline_failing_formatter.py").write_text(_FAILING_FORMATTER_PLUGIN, encoding="utf-8")
    distribution = site_packages / "pytest_cuke_offline_probe-0.0.1.dist-info"
    entry_points = distribution / "entry_points.txt"
    contents = entry_points.read_text(encoding="utf-8")
    entry_points.write_text(
        contents + "probe-failure = offline_failing_formatter:failure_request\n",
        encoding="utf-8",
    )
    _write_consumer_file(consumer, "formatter_failure.py", _FAILING_FORMATTER_PROGRAM)


@given("the consumer registers a formatter that requires a missing npm package")
def register_saved_stream_missing_npm_package_formatter(consumer: Any) -> None:
    node = shutil.which("node", path=consumer.env.get("PATH"))
    if node is None:
        node = getattr(consumer, "_cucumber_node", None)
    assert isinstance(node, str), "the missing-package formatter requires the installed Node.js runtime"

    plugin = f"""\
from pathlib import Path

from pytest_cuke import FormatterRequest


def missing_package_request(selection):
    return FormatterRequest(
        name=selection.name,
        command=({node!r}, "-e", "process.stdin.resume()"),
        output_path=selection.destination,
        working_directory=Path(selection.working_directory),
        required_executables=({node!r},),
        required_npm_packages=({_MISSING_NPM_PACKAGE!r},),
        timeout_seconds=5.0,
    )
"""
    site_packages = _consumer_site_packages(consumer)
    (site_packages / "offline_missing_npm_formatter.py").write_text(plugin, encoding="utf-8")
    distribution = site_packages / "pytest_cuke_offline_probe-0.0.1.dist-info"
    entry_points = distribution / "entry_points.txt"
    contents = entry_points.read_text(encoding="utf-8")
    entry_points.write_text(
        contents + "missing-npm = offline_missing_npm_formatter:missing_package_request\n",
        encoding="utf-8",
    )


@given("the consumer registers an official Cucumber PrettyPrinter replay formatter")
def register_official_pretty_replay_formatter(consumer: Any) -> None:
    node = shutil.which("node", path=consumer.env.get("PATH"))
    if node is None:
        node = getattr(consumer, "_cucumber_node", None)
    assert isinstance(node, str), "the pinned Cucumber PrettyPrinter packages were not installed"

    adapter = """\
import { createInterface } from "node:readline";
import { Writable } from "node:stream";

import { PrettyPrinter } from "@cucumber/pretty-formatter";

const outputStream = new Writable({
  write(chunk, encoding, callback) {
    process.stdout.write(chunk.toString("utf8"));
    callback();
  },
});
const printer = new PrettyPrinter({ stream: outputStream });
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of input) {
  printer.update(JSON.parse(line));
}
"""
    plugin = f"""\
from pathlib import Path

from pytest_cuke import FormatterRequest


def official_pretty_request(selection):
    return FormatterRequest(
        name=selection.name,
        command=({node!r}, "pretty-replay.mjs"),
        output_path=selection.destination,
        working_directory=Path(selection.working_directory),
        required_executables=({node!r},),
        required_npm_packages=("@cucumber/pretty-formatter",),
        timeout_seconds=15.0,
    )
"""
    site_packages = _consumer_site_packages(consumer)
    (site_packages / "offline_pretty_formatter.py").write_text(plugin, encoding="utf-8")
    distribution = site_packages / "pytest_cuke_offline_probe-0.0.1.dist-info"
    entry_points = distribution / "entry_points.txt"
    contents = entry_points.read_text(encoding="utf-8")
    entry_points.write_text(
        contents + "official-pretty = offline_pretty_formatter:official_pretty_request\n",
        encoding="utf-8",
    )
    _write_consumer_file(consumer, "pretty-replay.mjs", adapter)


@given('consumer Messages file "messages.ndjson" contains a valid saved run')
def write_valid_saved_messages(consumer: Any) -> None:
    product = {"name": "pytest-cuke", "version": "2.3.1"}
    messages = (
        {
            "meta": {
                "protocolVersion": "28.0.0",
                "implementation": product,
                "runtime": product,
                "os": product,
                "cpu": product,
            }
        },
        {"testRunStarted": {"timestamp": {"seconds": 100, "nanos": 0}}},
        {
            "testRunFinished": {
                "timestamp": {"seconds": 101, "nanos": 0},
                "success": True,
            }
        },
    )
    contents = "\n".join(json.dumps(message, separators=(",", ":")) for message in messages) + "\n"
    _write_consumer_file(consumer, "messages.ndjson", contents)


@given("the consumer removes Node.js from PATH")
def remove_node_from_consumer_path(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None


@then('consumer Messages artifact "messages.ndjson" should capture a successful live run with the trap sources')
def consumer_saved_messages_stream_has_live_trap_sources(consumer: Any) -> None:
    root = _consumer_root(consumer)
    artifact = root / "messages.ndjson"
    assert artifact.is_file(), f"pytest did not publish its saved Messages stream: {artifact}"
    source_markers = (
        "conftest-imported.marker",
        "fixture-executed.marker",
        "feature-step-executed.marker",
        "test-source-imported.marker",
        "test-body-executed.marker",
    )
    missing_markers = [name for name in source_markers if not (root / name).is_file()]
    assert not missing_markers, f"the live pytest run did not execute its trap sources: {missing_markers!r}"

    raw_messages = artifact.read_bytes()
    lines = [line for line in raw_messages.splitlines() if line.strip()]
    assert lines, "the saved Messages artifact is empty"
    records = [json.loads(line) for line in lines]
    assert all(isinstance(record, dict) and len(record) == 1 for record in records), records
    event_names = {next(iter(record)) for record in records}
    expected_events = {
        "meta",
        "source",
        "gherkinDocument",
        "pickle",
        "testCase",
        "testRunStarted",
        "testCaseStarted",
        "testCaseFinished",
        "testRunFinished",
    }
    assert expected_events <= event_names, f"saved artifact is not a real completed Messages run: {event_names!r}"
    finished = next(record["testRunFinished"] for record in records if "testRunFinished" in record)
    assert finished.get("success") is True, finished

    live_outputs = {}
    for name in ("probe", "probe-copy"):
        output = root / f"live-{name}.ndjson"
        assert output.is_file(), f"live formatter {name!r} did not publish output: {output}"
        rendered = output.read_bytes()
        rendered_records = [json.loads(line) for line in rendered.splitlines() if line.strip()]
        rendered_events = {record.get("event") for record in rendered_records if isinstance(record, dict)}
        assert expected_events <= rendered_events, (name, rendered_events)
        live_outputs[name] = rendered

    consumer._saved_messages_snapshot = raw_messages
    consumer._saved_messages_live_outputs = live_outputs


@when("I clear the consumer trap source markers")
def clear_consumer_trap_source_markers(consumer: Any) -> None:
    for marker in _TRAP_MARKERS:
        _consumer_path(consumer, marker).unlink(missing_ok=True)


@then(
    'consumer replay artifacts "rendered-one.ndjson" and "rendered-two.ndjson" should match both live formatter outputs'
)
def consumer_saved_stream_replay_matches_live_formatter_outputs(consumer: Any) -> None:
    root = _consumer_root(consumer)
    live_outputs = getattr(consumer, "_saved_messages_live_outputs", None)
    assert isinstance(live_outputs, dict), "the live formatter output snapshot is missing"
    rendered_one = root / "rendered-one.ndjson"
    rendered_two = root / "rendered-two.ndjson"
    assert rendered_one.is_file(), f"first replay formatter output was not published: {rendered_one}"
    assert rendered_two.is_file(), f"second replay formatter output was not published: {rendered_two}"

    expected_one = live_outputs["probe"]
    expected_two = live_outputs["probe-copy"]
    actual_one = rendered_one.read_bytes()
    actual_two = rendered_two.read_bytes()
    assert actual_one == expected_one, "the first saved-stream rendering differs from its live rendering"
    assert actual_two == expected_two, "the second saved-stream rendering differs from its live rendering"
    assert actual_one == actual_two, "the two replay formatter destinations differ"

    expected_events = {"meta", "source", "gherkinDocument", "pickle", "testCase", "testRunStarted", "testRunFinished"}
    for name, contents in ((rendered_one.name, actual_one), (rendered_two.name, actual_two)):
        records = [json.loads(line) for line in contents.splitlines() if line.strip()]
        assert records and all(isinstance(record, dict) for record in records), (name, records)
        events = {record.get("event") for record in records}
        assert expected_events <= events, (name, events)


@then(
    'consumer replay artifacts "rendered-one-again.ndjson" and "rendered-two-again.ndjson" '
    "should match the first replay byte for byte"
)
def repeated_saved_stream_replay_is_byte_identical(consumer: Any) -> None:
    root = _consumer_root(consumer)
    pairs = (
        (root / "rendered-one.ndjson", root / "rendered-one-again.ndjson"),
        (root / "rendered-two.ndjson", root / "rendered-two-again.ndjson"),
    )
    for first, repeated in pairs:
        assert first.is_file(), f"first replay formatter output was not published: {first}"
        assert repeated.is_file(), f"repeated replay formatter output was not published: {repeated}"
        assert repeated.read_bytes() == first.read_bytes(), f"replay output changed on the second render: {first.name}"


@then('consumer Messages artifact "messages.ndjson" should remain byte-identical to the captured saved stream')
def consumer_saved_messages_input_is_unchanged(consumer: Any) -> None:
    expected = getattr(consumer, "_saved_messages_snapshot", None)
    assert isinstance(expected, bytes), "the original saved Messages bytes were not captured"
    actual = (_consumer_root(consumer) / "messages.ndjson").read_bytes()
    assert actual == expected, "standalone rendering modified the saved Messages input"


@then("standalone Messages rendering should not import conftest or run test fixtures")
def standalone_saved_messages_rendering_skips_trap_sources(consumer: Any) -> None:
    root = _consumer_root(consumer)
    assert not (root / "conftest.py").exists(), "the trap conftest source was not removed before rendering"
    assert not (root / "test_trap.py").exists(), "the trap test source was not removed before rendering"
    assert not (root / "features" / "trapped-saved-run.feature").exists(), (
        "the trap feature source was not removed before rendering"
    )
    created = [name for name in _TRAP_MARKERS if (root / name).exists()]
    assert not created, f"standalone rendering imported test sources or ran fixtures: {created!r}"


@then(
    parsers.parse(
        'the replay output conflict should name formatters "probe" and "probe-copy" and destination "{destination}"'
    )
)
def replay_output_conflict_is_actionable(destination: str, consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"duplicate formatter outputs unexpectedly passed:\n{output}"
    assert "Replay formatters 'probe' and 'probe-copy' resolve to the same output path" in output, output
    resolved_destination = _consumer_path(consumer, destination).resolve()
    assert str(resolved_destination) in output, (str(resolved_destination), output)
    assert not resolved_destination.exists(), f"conflicting output was published: {resolved_destination}"


@then(parsers.parse('the missing saved Messages diagnostic should name "{input_path}"'))
def missing_saved_messages_error_names_path(input_path: str, consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"replay unexpectedly accepted a missing input:\n{output}"
    assert input_path in output, (input_path, output)
    assert "not found" in output.lower() or "does not exist" in output.lower(), output


@given(parsers.parse('consumer Messages file "{input_path}" contains malformed case "{case}"'))
def write_malformed_saved_messages(input_path: str, case: str, consumer: Any) -> None:
    valid_meta = {
        "meta": {
            "protocolVersion": "28.0.0",
            "implementation": {"name": "pytest-cuke", "version": "2.3.1"},
            "runtime": {"name": "pytest-cuke", "version": "2.3.1"},
            "os": {"name": "pytest-cuke", "version": "2.3.1"},
            "cpu": {"name": "pytest-cuke", "version": "2.3.1"},
        }
    }
    valid_meta_line = json.dumps(valid_meta, separators=(",", ":"))
    if case == "invalid-json":
        contents = f"{valid_meta_line}\n{{not json\n"
    elif case == "invalid-envelope":
        contents = f"{valid_meta_line}\nnull\n"
    elif case == "invalid-schema":
        invalid_schema = {
            "meta": {
                **valid_meta["meta"],
                "runtime": {"name": 42},
            }
        }
        contents = f"{valid_meta_line}\n{json.dumps(invalid_schema, separators=(',', ':'))}\n"
    elif case == "orphan-reference":
        run_started = {"testRunStarted": {"timestamp": {"seconds": 100, "nanos": 0}}}
        case_started = {
            "testCaseStarted": {
                "id": "attempt-1",
                "testCaseId": "missing-case",
                "attempt": 0,
                "timestamp": {"seconds": 101, "nanos": 0},
            }
        }
        contents = (
            "\n".join(json.dumps(message, separators=(",", ":")) for message in (valid_meta, run_started, case_started))
            + "\n"
        )
    else:
        raise ValueError(f"unknown malformed Messages case: {case!r}")
    _write_consumer_file(consumer, input_path, contents)


@then(
    parsers.parse(
        'the malformed saved Messages diagnostic should identify "{input_path}" at line {line} '
        'with error "{expected_error}"'
    )
)
def malformed_saved_messages_error_identifies_line(
    input_path: str, line: str, expected_error: str, consumer: Any
) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"replay unexpectedly accepted malformed input:\n{output}"
    assert input_path in output, (input_path, output)
    assert f"line {line}" in output.lower(), output
    assert expected_error.lower() in output.lower(), output


@then(parsers.parse('the replay output parent diagnostic should name "{output_parent}"'))
def replay_output_parent_error_names_directory(output_parent: str, consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"replay unexpectedly accepted a missing output parent:\n{output}"
    assert "output parent directory does not exist" in output.lower(), output
    assert str(_consumer_path(consumer, output_parent).resolve()) in output, output


@then("the replay formatter failure should report its stderr and exit status")
def replay_formatter_failure_reports_stderr_and_exit_status(consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    assert result.returncode != 0, (
        f"the failing replay formatter unexpectedly passed:\n{result.stdout}\n{result.stderr}"
    )
    assert "formatter failure sentinel" in result.stderr, result.stderr
    assert "Replay formatter 'probe-failure' exited with status 23." in result.stderr, result.stderr


@then('the replay terminal conflict should name formatters "probe" and "probe-copy"')
def replay_terminal_conflict_names_both_formatters(consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    assert result.returncode != 0, f"two terminal formatters unexpectedly passed:\n{result.stdout}\n{result.stderr}"
    assert "Only one replay formatter may write to the terminal" in result.stderr, result.stderr
    assert "'probe'" in result.stderr and "'probe-copy'" in result.stderr, result.stderr


@then("the missing npm package replay diagnostic should be actionable")
def missing_npm_package_replay_diagnostic_is_actionable(consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    assert result.returncode != 0, f"the missing npm package unexpectedly passed:\n{result.stdout}\n{result.stderr}"
    assert f"requires npm package '{_MISSING_NPM_PACKAGE}'" in result.stderr, result.stderr
    assert f"npm install {_MISSING_NPM_PACKAGE}" in result.stderr, result.stderr


@then("the missing Node replay diagnostic should explain the requirement")
def missing_node_replay_error_is_actionable(consumer: Any) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone formatter command has not run"
    assert result.returncode != 0, (
        f"the Node formatter unexpectedly ran without Node on PATH:\n{result.stdout}\n{result.stderr}"
    )
    assert "requires Node.js to load npm package(s): @cucumber/pretty-formatter" in result.stderr, result.stderr


@then(parsers.parse('consumer artifact "{output_path}" should not be published by replay'))
def replay_does_not_publish_output_on_failure(output_path: str, consumer: Any) -> None:
    artifact = _consumer_path(consumer, output_path)
    assert not artifact.exists(), f"replay published output despite an input error: {artifact}"


@then('consumer replay artifact "pretty-replay.txt" should match the pinned official Cucumber formatter output')
def official_pretty_replay_output_is_recorded(consumer: Any) -> None:
    artifact = _consumer_path(consumer, "pretty-replay.txt")
    assert artifact.is_file(), f"the official Cucumber PrettyPrinter did not publish its replay: {artifact}"
    rendered = _ANSI_ESCAPE.sub("", artifact.read_text(encoding="utf-8"))
    selected_lines: list[str] = []
    for line in rendered.replace("\r\n", "\n").splitlines():
        normalized_line = line.strip()
        if normalized_line.startswith(("Feature: ", "Scenario: ", "✔ ")):
            selected_lines.append(re.split(r"\s+#\s+", normalized_line, maxsplit=1)[0])
    normalized = "\n".join(selected_lines) + "\n"
    expected_output = Path(__file__).parents[1] / "data" / "offline-formatter-replay" / "official-pretty.normalized.txt"
    expected = expected_output.read_text(encoding="utf-8")
    assert normalized == expected, f"the pinned Cucumber PrettyPrinter output changed:\n{normalized}"
    consumer._official_pretty_replay_normalized_output = normalized
