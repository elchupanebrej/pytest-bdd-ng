"""BDD steps for the public live formatter extension contract."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, then
from pytest_cuke.model.message_types import message_from_dict
from pytest_cuke.model.message_stream_validation import validate_message_stream
from pytest_cuke.model.message_validation import validate_envelope


_FORMATTER_PROBE = '''\
import json
import sys
from pathlib import Path

mode = sys.argv[1]
for line in sys.stdin:
    envelope = json.loads(line)
    if mode == "fail-first":
        print("formatter first-envelope failure sentinel", file=sys.stderr, flush=True)
        raise SystemExit(23)
    if mode == "fail" and "testCaseStarted" in envelope:
        print("formatter child failure sentinel", file=sys.stderr, flush=True)
        raise SystemExit(19)
    if "testCaseStarted" in envelope:
        marker = Path(f"live-{mode}.marker")
        marker.write_text(json.dumps(envelope["testCaseStarted"]), encoding="utf-8")
    sys.stdout.write(line)
    sys.stdout.flush()
'''

_FORMATTER_SUPPORT = '''\
import json
import os
import time
import uuid
from pathlib import Path

from pytest_cuke import given, parsers

ROOT = Path(__file__).parent
expected_markers = json.loads((ROOT / "expected-live-markers.json").read_text(encoding="utf-8"))


def _wait_for_live_markers(names):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if all((ROOT / f"live-{name}.marker").is_file() for name in names):
            return
        time.sleep(0.01)
    missing = [name for name in names if not (ROOT / f"live-{name}.marker").is_file()]
    assert not missing, f"formatters did not receive TestCaseStarted live: {missing!r}"


@given("the selected formatter has received the scenario start")
def selected_formatter_received_scenario_start():
    _wait_for_live_markers(expected_markers)


@given("every selected formatter has received the scenario start")
def every_selected_formatter_received_scenario_start():
    _wait_for_live_markers(expected_markers)


@given("the formatter scenario records that it started")
def formatter_scenario_records_that_it_started():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")


@given(parsers.parse("formatter worker scenario {case} reaches the bridge"))
def formatter_worker_scenario_reaches_bridge(case):
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    assert worker_id, "the formatter worker scenario must run in an xdist worker"
    observations = ROOT / "formatter-worker-observations"
    observations.mkdir(exist_ok=True)
    observation = observations / f"{case}-{uuid.uuid4().hex}.json"
    observation.write_text(json.dumps({"case": case, "worker_id": worker_id}), encoding="utf-8")

    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        workers = {
            json.loads(path.read_text(encoding="utf-8"))["worker_id"]
            for path in observations.glob("*.json")
        }
        if len(workers) >= 2:
            return
        time.sleep(0.01)
    raise AssertionError("the formatter run did not execute scenarios on two xdist workers")


@given("the official formatter has rendered its scenario title")
def official_formatter_has_rendered_scenario_title():
    marker = ROOT / "pretty-live.marker"
    expected = "The official Cucumber formatter renders this scenario live"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if marker.is_file() and expected in marker.read_text(encoding="utf-8"):
            return
        time.sleep(0.01)
    observed = marker.read_text(encoding="utf-8") if marker.is_file() else "<no formatter output>"
    assert expected in observed, f"official PrettyPrinter had not rendered the scenario live: {observed!r}"
'''


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _write_consumer_file(consumer: Any, relative_path: str, content: str) -> Path:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer formatter files must stay inside the consumer project")
    path = _consumer_root(consumer) / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _plugin_source(requests: list[dict[str, Any]]) -> str:
    request_lines = []
    for request in requests:
        output_expression = request.get("output_expression")
        if output_expression is None:
            output_expression = "None" if request["output"] is None else f"Path({request['output']!r})"
        request_lines.append(
            "        FormatterRequest(\n"
            f"            name={request['name']!r},\n"
            "            command=(sys.executable, 'formatter_probe.py', "
            f"{request['mode']!r}),\n"
            f"            output_path={output_expression},\n"
            "            working_directory=Path(__file__).parent,\n"
            "            timeout_seconds=5.0,\n"
            "        ),"
        )
    return (
        "from pathlib import Path\n"
        "import sys\n\n"
        "from pytest_cuke.formatter_api import FormatterRequest\n\n\n"
        "def pytest_cuke_formatter_requests(config):\n"
        "    del config\n"
        "    return [\n"
        + "\n".join(request_lines)
        + "\n    ]\n"
    )


def _install_formatter_plugins(consumer: Any, plugins: dict[str, str], markers: list[str]) -> None:
    _write_consumer_file(consumer, "formatter_probe.py", _FORMATTER_PROBE)
    _write_consumer_file(consumer, "formatter_bridge_support.py", _FORMATTER_SUPPORT)
    _write_consumer_file(consumer, "expected-live-markers.json", json.dumps(markers))
    plugin_names = [*plugins, "formatter_bridge_support"]
    _write_consumer_file(consumer, "conftest.py", f"pytest_plugins = {plugin_names!r}\n")
    for name, source in plugins.items():
        _write_consumer_file(consumer, f"{name}.py", source)


@given(
    re.compile(
        r'the consumer registers live formatter plugin "(?P<name>[^"]+)" writing "(?P<output>[^"]+)"'
    )
)
def register_live_formatter_plugin(name: str, output: str, consumer: Any) -> None:
    source = _plugin_source([{"name": name, "mode": name, "output": output}])
    _install_formatter_plugins(consumer, {f"{name}_formatter": source}, [name])


@given("the installed consumer has pytest-xdist available or skips this scenario")
def require_consumer_xdist_or_skip(consumer: Any) -> None:
    probe = subprocess.run(
        [str(consumer.python), "-c", "import xdist"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        return

    uv_executable = shutil.which("uv")
    if uv_executable is None:
        pytest.skip("pytest-xdist is not installed in this consumer and uv is unavailable")
    install = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(consumer.python), "pytest-xdist"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if install.returncode != 0:
        pytest.skip(f"pytest-xdist is not available in this consumer:\n{install.stdout}\n{install.stderr}")
    probe = subprocess.run(
        [str(consumer.python), "-c", "import xdist"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("pytest-xdist could not be imported in this consumer")


@given("the consumer installs the pinned Cucumber pretty formatter packages")
def install_pinned_cucumber_pretty_formatter_packages(consumer: Any) -> None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        pytest.skip("the official Cucumber formatter BDD requires both Node.js and npm")

    package_json = {
        "name": "pytest-cuke-live-formatter-consumer",
        "private": True,
        "type": "module",
        "dependencies": {
            "@cucumber/messages": "34.2.1",
            "@cucumber/pretty-formatter": "4.0.2",
            "@cucumber/query": "16.1.1",
            "luxon": "3.7.2",
        },
    }
    _write_consumer_file(consumer, "package.json", json.dumps(package_json, indent=2) + "\n")

    node_environment = dict(consumer.env)
    path_entries = (
        str(Path(node).parent),
        str(Path(npm).parent),
        str(Path(consumer.python).parent),
        os.defpath,
    )
    node_environment["PATH"] = os.pathsep.join(dict.fromkeys(path_entries))
    result = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=consumer.path,
        env=node_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"could not install pinned Cucumber formatter packages:\n{result.stdout}\n{result.stderr}"
    consumer.env["PATH"] = node_environment["PATH"]
    consumer._cucumber_node = node


@given("the consumer registers the official PrettyPrinter as a live formatter")
def register_official_pretty_printer(consumer: Any) -> None:
    node = getattr(consumer, "_cucumber_node", None)
    assert isinstance(node, str), "the pinned Cucumber formatter packages were not installed"
    adapter = '''\
import { appendFileSync } from "node:fs";
import { createInterface } from "node:readline";
import { Writable } from "node:stream";

import { PrettyPrinter } from "@cucumber/pretty-formatter";

const markerPath = new URL("./pretty-live.marker", import.meta.url);
const outputStream = new Writable({
  write(chunk, encoding, callback) {
    const text = chunk.toString("utf8");
    process.stdout.write(text);
    if (text) appendFileSync(markerPath, text, "utf8");
    callback();
  },
});
const printer = new PrettyPrinter({ stream: outputStream });
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of input) {
  printer.update(JSON.parse(line));
}
'''
    plugin = f'''\
from pathlib import Path

from pytest_cuke.formatter_api import FormatterRequest


def pytest_cuke_formatter_requests(config):
    del config
    return (
        FormatterRequest(
            name="official-cucumber-pretty",
            command=({node!r}, "pretty-formatter.mjs"),
            output_path=Path("pretty-output.txt"),
            working_directory=Path(__file__).parent,
            required_executables=("node",),
            required_npm_packages=("@cucumber/pretty-formatter",),
            timeout_seconds=15.0,
        ),
    )
'''
    _install_formatter_plugins(consumer, {"official_pretty_formatter": plugin}, [])
    _write_consumer_file(consumer, "pretty-formatter.mjs", adapter)


@given('the consumer registers independent formatter plugins "zeta" and "alpha"')
def register_independent_formatter_plugins(consumer: Any) -> None:
    plugin_specs = {
        "zeta_formatter": [{"name": "zeta", "mode": "zeta", "output": "zeta.ndjson"}],
        "alpha_formatter": [{"name": "alpha", "mode": "alpha", "output": "alpha.ndjson"}],
    }
    plugins = {name: _plugin_source(requests) for name, requests in plugin_specs.items()}
    # Loading in reverse name order proves resolution does not depend on plugin registration order.
    _install_formatter_plugins(consumer, plugins, ["alpha", "zeta"])


def _destination_case_plugins(case: str) -> dict[str, str]:
    if case == "duplicate":
        return {
            "zeta_formatter": _plugin_source(
                [{"name": "zeta", "mode": "zeta", "output": "shared.ndjson"}]
            ),
            "alpha_formatter": _plugin_source(
                [
                    {
                        "name": "alpha",
                        "mode": "alpha",
                        "output": None,
                        "output_expression": 'Path(__file__).parent / "shared.ndjson"',
                    }
                ]
            ),
        }
    if case == "missing-parent":
        return {
            "missing_parent_formatter": _plugin_source(
                [{"name": "missing-parent", "mode": "missing", "output": "missing-parent/output.ndjson"}]
            )
        }
    if case == "multiple-terminal":
        return {
            "zeta_formatter": _plugin_source(
                [{"name": "zeta-terminal", "mode": "zeta", "output": None}]
            ),
            "alpha_formatter": _plugin_source(
                [{"name": "alpha-terminal", "mode": "alpha", "output": None}]
            ),
        }
    raise ValueError(f"unknown formatter destination case: {case}")


@given(re.compile(r'the consumer registers formatter destination case "(?P<case>duplicate|missing-parent|multiple-terminal)"'))
def register_formatter_destination_case(case: str, consumer: Any) -> None:
    plugins = _destination_case_plugins(case)
    markers = []
    _install_formatter_plugins(consumer, plugins, markers)
    consumer._formatter_destination_case = case


@then("the formatter destination conflict should be rejected before the scenario starts")
def formatter_destination_conflict_is_preflighted(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None, "installed pytest has not run"
    combined_output = result.stdout + result.stderr
    case = consumer._formatter_destination_case
    expected_text = {
        "duplicate": "resolve to the same output path",
        "missing-parent": "output parent directory does not exist",
        "multiple-terminal": "Only one live formatter may write to the terminal",
    }[case]
    assert result.returncode != 0, f"conflicting formatter requests unexpectedly passed:\n{combined_output}"
    assert expected_text in combined_output, (expected_text, combined_output)
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the scenario executed before formatter destination validation"
    )


@given(
    'the consumer registers an optional formatter that requires Node and "@cucumber/pretty-formatter" when selected'
)
def register_unselected_optional_formatter(consumer: Any) -> None:
    source = '''\
import sys
from pathlib import Path

from pytest_cuke.formatter_api import FormatterRequest


def pytest_addoption(parser):
    parser.addoption("--select-optional-formatter", action="store_true")


def pytest_cuke_formatter_requests(config):
    if not config.getoption("--select-optional-formatter"):
        return ()
    return (
        FormatterRequest(
            name="optional",
            command=(sys.executable, "formatter_probe.py", "optional"),
            output_path=Path("optional.ndjson"),
            required_executables=("node",),
            required_npm_packages=("@cucumber/pretty-formatter",),
        ),
    )
'''
    _install_formatter_plugins(consumer, {"optional_formatter": source}, [])


@given('the installed consumer has no Node or "@cucumber/pretty-formatter" package available')
def remove_optional_node_runtime(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert not (_consumer_root(consumer) / "node_modules" / "@cucumber" / "pretty-formatter").exists()


@then(re.compile(r'the formatter scenario should have started without creating "(?P<output>[^"]+)"'))
def formatter_scenario_started_without_optional_output(output: str, consumer: Any) -> None:
    assert (_consumer_root(consumer) / "scenario-started.marker").is_file()
    assert not (_consumer_root(consumer) / output).exists()


@given("the consumer registers a formatter process that fails after receiving a message")
def register_failing_formatter(consumer: Any) -> None:
    source = _plugin_source([{"name": "broken", "mode": "fail", "output": "broken.ndjson"}])
    _install_formatter_plugins(consumer, {"failing_formatter": source}, ["fail"])


@given("the consumer registers a healthy formatter alongside one that fails")
def register_failing_formatter_with_healthy_sibling(consumer: Any) -> None:
    plugins = {
        "healthy_formatter": _plugin_source(
            [{"name": "healthy", "mode": "healthy", "output": "healthy.ndjson"}]
        ),
        "failing_formatter": _plugin_source(
            [{"name": "broken", "mode": "fail", "output": "broken.ndjson"}]
        ),
    }
    _install_formatter_plugins(consumer, plugins, ["healthy", "fail"])


@given("the consumer registers a formatter process that fails on its first Messages envelope")
def register_first_envelope_failing_formatter(consumer: Any) -> None:
    source = _plugin_source(
        [{"name": "first-message", "mode": "fail-first", "output": "first-message.ndjson"}]
    )
    _install_formatter_plugins(consumer, {"first_message_formatter": source}, ["fail-first"])


@then(re.compile(r'the selected formatter failure should be visible and "(?P<output>[^"]+)" should not be published'))
def selected_formatter_failure_is_reported(output: str, consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None, "installed pytest has not run"
    combined_output = result.stdout + result.stderr
    assert result.returncode != 0, f"a failing formatter unexpectedly passed:\n{combined_output}"
    assert (
        "formatter child failure sentinel" in combined_output
        or "Live formatter 'broken' exited before the Messages stream finished" in combined_output
    ), combined_output
    target = _consumer_root(consumer) / output
    assert not target.exists(), f"failed formatter published a success-looking artifact: {target}"
    leftovers = list(target.parent.glob(f".{target.name}.*.pytest-cuke-tmp"))
    assert not leftovers, f"failed formatter left staged output files behind: {leftovers}"


@then("the formatter failure should prevent every selected output from being published")
def failed_formatter_prevents_sibling_output_publication(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None, "installed pytest has not run"
    combined_output = result.stdout + result.stderr
    assert result.returncode != 0, f"a failing formatter unexpectedly passed:\n{combined_output}"
    assert (
        "formatter child failure sentinel" in combined_output
        or "Live formatter 'broken' exited before the Messages stream finished" in combined_output
    ), combined_output
    for output in ("healthy.ndjson", "broken.ndjson"):
        target = _consumer_root(consumer) / output
        assert not target.exists(), f"failed shared session published an artifact: {target}"
        leftovers = list(target.parent.glob(f".{target.name}.*.pytest-cuke-tmp"))
        assert not leftovers, f"failed shared session left staged output files behind: {leftovers}"


@then(re.compile(r'the first-envelope formatter failure should fail pytest and leave no "(?P<output>[^"]+)" output'))
def first_envelope_formatter_failure_is_not_published(output: str, consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None, "installed pytest has not run"
    combined_output = result.stdout + result.stderr
    assert result.returncode != 0, f"first-envelope formatter failure did not fail pytest:\n{combined_output}"
    assert (
        "formatter first-envelope failure sentinel" in combined_output
        or "Live formatter 'first-message' exited before the Messages stream finished" in combined_output
    ), combined_output
    target = _consumer_root(consumer) / output
    assert not target.exists(), f"first-envelope failure published an output artifact: {target}"
    leftovers = list(target.parent.glob(f".{target.name}.*.pytest-cuke-tmp"))
    assert not leftovers, f"first-envelope failure left staged output files behind: {leftovers}"


def _messages_artifact(relative_path: str, consumer: Any) -> tuple[Path, list[dict[str, Any]]]:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("consumer formatter artifacts must stay inside the consumer project")
    path = _consumer_root(consumer) / relative
    assert path.is_file(), f"consumer formatter artifact does not exist: {path}"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and all(isinstance(row, dict) for row in rows), rows
    envelopes = []
    for index, row in enumerate(rows, start=1):
        envelope = message_from_dict(row)
        diagnostics = validate_envelope(envelope)
        assert not diagnostics, f"invalid Messages envelope at line {index}: {diagnostics!r}"
        envelopes.append(envelope)
    stream_diagnostics = validate_message_stream(envelopes)
    assert not stream_diagnostics, f"invalid Messages stream lifecycle: {stream_diagnostics!r}"
    return path, rows


def _assert_one_successful_messages_stream(relative_path: str, consumer: Any) -> tuple[Path, list[dict[str, Any]]]:
    path, rows = _messages_artifact(relative_path, consumer)
    run_starts = [row["testRunStarted"] for row in rows if "testRunStarted" in row]
    run_finishes = [row["testRunFinished"] for row in rows if "testRunFinished" in row]
    case_starts = [row["testCaseStarted"] for row in rows if "testCaseStarted" in row]
    case_finishes = [row["testCaseFinished"] for row in rows if "testCaseFinished" in row]
    test_cases = [row["testCase"] for row in rows if "testCase" in row]
    assert len(run_starts) == len(run_finishes) == 1, (run_starts, run_finishes)
    assert len(case_starts) == len(case_finishes) == len(test_cases) == 1, (case_starts, case_finishes, test_cases)
    assert run_finishes[0].get("success") is True, run_finishes[0]
    assert case_finishes[0].get("testCaseStartedId") == case_starts[0].get("id"), case_finishes[0]
    return path, rows


@then(re.compile(r'consumer formatter artifact "(?P<output>[^"]+)" should be one valid successful Messages stream'))
def single_formatter_artifact_is_valid(output: str, consumer: Any) -> None:
    path, _ = _assert_one_successful_messages_stream(output, consumer)
    assert (_consumer_root(consumer) / "live-probe.marker").is_file(), (
        f"formatter artifact {path.name!r} exists, but the scenario did not observe its live event"
    )


@then(
    re.compile(
        r'consumer formatter artifacts "(?P<first>[^"]+)" and "(?P<second>[^"]+)" '
        r'should be identical valid successful Messages streams'
    )
)
def independent_formatter_artifacts_are_identical(first: str, second: str, consumer: Any) -> None:
    first_path, _ = _assert_one_successful_messages_stream(first, consumer)
    second_path, _ = _assert_one_successful_messages_stream(second, consumer)
    assert first_path.read_bytes() == second_path.read_bytes(), (
        "independent formatter plugins received different ordered Messages streams"
    )
    for name in ("alpha", "zeta"):
        assert (_consumer_root(consumer) / f"live-{name}.marker").is_file(), (
            f"formatter {name!r} did not observe the scenario start live"
        )


def _message_identifier_graph(value: object) -> tuple[list[str], list[str]]:
    object_ids: list[str] = []
    references: list[str] = []

    def collect(current: object) -> None:
        if isinstance(current, dict):
            for key, nested in current.items():
                if key == "workerId":
                    continue
                if key == "id":
                    assert isinstance(nested, str) and nested, (key, nested)
                    object_ids.append(nested)
                elif key.endswith(("Id", "Ids", "_id", "_ids")):
                    values = nested if isinstance(nested, list) else [nested]
                    for identifier in values:
                        assert isinstance(identifier, str) and identifier, (key, identifier)
                        references.append(identifier)
                collect(nested)
        elif isinstance(current, list):
            for nested in current:
                collect(nested)

    collect(value)
    return object_ids, references


@then(re.compile(r'consumer formatter artifact "(?P<output>[^"]+)" should be one normalized stream for two xdist scenarios'))
def formatter_xdist_artifact_is_one_normalized_stream(output: str, consumer: Any) -> None:
    _, rows = _messages_artifact(output, consumer)
    metas = [row["meta"] for row in rows if "meta" in row]
    run_starts = [row["testRunStarted"] for row in rows if "testRunStarted" in row]
    run_finishes = [row["testRunFinished"] for row in rows if "testRunFinished" in row]
    sources = [row["source"] for row in rows if "source" in row]
    documents = [row["gherkinDocument"] for row in rows if "gherkinDocument" in row]
    pickles = [row["pickle"] for row in rows if "pickle" in row]
    cases = [row["testCase"] for row in rows if "testCase" in row]
    attempts = [row["testCaseStarted"] for row in rows if "testCaseStarted" in row]
    case_finishes = [row["testCaseFinished"] for row in rows if "testCaseFinished" in row]
    step_starts = [row["testStepStarted"] for row in rows if "testStepStarted" in row]
    step_finishes = [row["testStepFinished"] for row in rows if "testStepFinished" in row]

    assert len(metas) == len(run_starts) == len(run_finishes) == 1, (metas, run_starts, run_finishes)
    assert sources and documents, (sources, documents)
    assert len(pickles) == len(cases) == 2, (pickles, cases)
    assert len(attempts) == len(case_finishes) == len(step_starts) == len(step_finishes) == 2
    assert run_finishes[0].get("success") is True, run_finishes[0]
    assert rows[-1].get("testRunFinished") == run_finishes[0], "testRunFinished must close the live xdist stream"

    expected_steps = {
        "formatter worker scenario north reaches the bridge",
        "formatter worker scenario south reaches the bridge",
    }
    pickle_ids = {pickle["id"] for pickle in pickles}
    case_ids = {case["id"] for case in cases}
    attempt_ids = {attempt["id"] for attempt in attempts}
    assert len(pickle_ids) == len(case_ids) == len(attempt_ids) == 2
    assert {pickle["steps"][0]["text"] for pickle in pickles} == expected_steps
    pickles_by_id = {pickle["id"]: pickle for pickle in pickles}
    cases_by_id = {case["id"]: case for case in cases}
    cases_by_pickle_id = {case["pickleId"]: case for case in cases}
    attempts_by_id = {attempt["id"]: attempt for attempt in attempts}
    assert {case["pickleId"] for case in cases} == pickle_ids
    assert {attempt["testCaseId"] for attempt in attempts} == case_ids
    assert {item["testCaseStartedId"] for item in case_finishes} == attempt_ids
    assert {item["testCaseStartedId"] for item in step_starts} == attempt_ids
    assert {item["testCaseStartedId"] for item in step_finishes} == attempt_ids
    assert {item["testStepId"] for item in step_starts} == {
        case["testSteps"][0]["id"] for case in cases
    }
    assert {item["testStepId"] for item in step_finishes} == {
        case["testSteps"][0]["id"] for case in cases
    }
    assert all(item["testStepResult"]["status"] == "PASSED" for item in step_finishes)
    assert all(
        [step["pickleStepId"] for step in cases_by_pickle_id[pickle["id"]]["testSteps"]]
        == [step["id"] for step in pickle["steps"]]
        for pickle in pickles
    )

    workers = {attempt.get("workerId") for attempt in attempts}
    assert len(workers) == 2 and all(isinstance(worker, str) and worker for worker in workers), attempts
    worker_prefixes = tuple(f"{worker}:" for worker in workers)
    observations_path = _consumer_root(consumer) / "formatter-worker-observations"
    observations = [json.loads(path.read_text(encoding="utf-8")) for path in observations_path.glob("*.json")]
    assert {item.get("case") for item in observations} == {"north", "south"}, observations
    assert {item.get("worker_id") for item in observations} == workers, observations

    object_ids, references = _message_identifier_graph(rows)
    assert len(object_ids) == len(set(object_ids)), f"worker-scoped Messages IDs were duplicated: {object_ids}"
    assert set(references) <= set(object_ids), f"Messages references have no target: {set(references) - set(object_ids)}"
    assert set(cases_by_id) == {attempt["testCaseId"] for attempt in attempts_by_id.values()}
    assert set(pickles_by_id) == {case["pickleId"] for case in cases_by_id.values()}
    for attempt in attempts:
        worker_prefix = f"{attempt['workerId']}:"
        case = cases_by_id[attempt["testCaseId"]]
        pickle = pickles_by_id[case["pickleId"]]
        assert attempt["id"].startswith(worker_prefix), attempt
        assert case["id"].startswith(worker_prefixes), case
        assert pickle["id"].startswith(worker_prefixes), pickle
        assert all(step["id"].startswith(worker_prefixes) for step in pickle["steps"]), pickle
        assert all(step["id"].startswith(worker_prefixes) for step in case["testSteps"]), case
        for event in (*step_starts, *step_finishes):
            if event["testCaseStartedId"] == attempt["id"]:
                assert event["testCaseStartedId"].startswith(worker_prefix), event
                assert event["testStepId"].startswith(worker_prefixes), event


@then("consumer artifact \"pretty-output.txt\" should contain the official Cucumber formatter output")
def official_pretty_formatter_artifact_contains_live_scenario(consumer: Any) -> None:
    expected = "The official Cucumber formatter renders this scenario live"
    artifact = _consumer_root(consumer) / "pretty-output.txt"
    assert artifact.is_file(), f"official PrettyPrinter output was not published: {artifact}"
    output = artifact.read_text(encoding="utf-8")
    assert expected in output, f"official PrettyPrinter artifact omitted the scenario title: {output!r}"
    live_marker = _consumer_root(consumer) / "pretty-live.marker"
    assert live_marker.is_file(), "official PrettyPrinter output was not observed during the scenario"
    live_output = live_marker.read_text(encoding="utf-8")
    assert expected in live_output, f"the scenario did not observe the official formatter's live output: {live_output!r}"
