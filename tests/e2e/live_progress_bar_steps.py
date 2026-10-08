"""Installed-consumer BDD steps for the live Cucumber progress bar."""

from __future__ import annotations

import json
import os
import re
import select
import shutil
import struct
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
from pytest_cuke import given, then, when
from pytest_cuke.model.message_stream_validation import validate_message_stream
from pytest_cuke.model.message_types import message_from_dict
from pytest_cuke.model.message_validation import validate_envelope


_SUPPORT_PLUGIN = '''\
from pathlib import Path
import time

import pytest
from pytest_cuke import given, when, then

ROOT = Path(__file__).parent


@given("a progress-bar scenario records execution")
def progress_bar_scenario_records_execution():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")


@given("a progress-bar scenario passes")
def progress_bar_scenario_passes():
    pass


@given("a progress-bar scenario fails before its following step")
def progress_bar_scenario_fails_before_following_step():
    raise AssertionError("progress-bar failure sentinel")


@then("the following progress-bar step remains skipped")
def following_progress_bar_step_remains_skipped():
    pass


@given("a progress-bar scenario deliberately skips")
def progress_bar_scenario_deliberately_skips():
    pytest.skip("progress-bar skip sentinel")


@given("the progress-bar scenario fails once and then passes")
def retryable_progress_bar_scenario():
    counter = ROOT / "retry-attempt-count.txt"
    attempt = int(counter.read_text(encoding="utf-8")) if counter.exists() else 0
    counter.write_text(str(attempt + 1), encoding="utf-8")
    if attempt == 0:
        raise AssertionError("progress-bar first retry attempt sentinel")


@when("the final progress-bar scenario waits for release")
def final_progress_bar_scenario_waits_for_release():
    (ROOT / "gated-started.marker").write_text("started", encoding="utf-8")
    deadline = time.monotonic() + 45
    release = ROOT / "release-gated-scenario.marker"
    while time.monotonic() < deadline and not release.is_file():
        time.sleep(0.01)
    assert release.is_file(), "the live progress-bar observer did not release the final scenario"
    (ROOT / "gated-finished.marker").write_text("finished", encoding="utf-8")


@then("the final progress-bar scenario is released")
def final_progress_bar_scenario_is_released():
    assert (ROOT / "gated-finished.marker").is_file()
'''

_OUTCOME_FEATURE = '''\
Feature: Piped progress-bar outcomes
  Scenario: A failure remains worse than its skipped continuation
    Given a progress-bar scenario fails before its following step
    Then the following progress-bar step remains skipped

  Scenario: A progress-bar scenario is skipped
    Given a progress-bar scenario deliberately skips

  Scenario: A progress-bar scenario passes
    Given a progress-bar scenario passes
'''

_RETRY_FEATURE = '''\
Feature: TTY progress-bar retries
  Scenario: A progress-bar Pickle fails once and then passes
    Given the progress-bar scenario fails once and then passes

  Scenario: A progress-bar Pickle is skipped
    Given a progress-bar scenario deliberately skips

  Scenario: The final progress-bar Pickle waits for release
    When the final progress-bar scenario waits for release
    Then the final progress-bar scenario is released
'''

_OFFICIAL_PACKAGES = {
    "@cucumber/messages": "34.2.1",
    "@cucumber/pretty-formatter": "4.0.2",
    "@cucumber/query": "16.1.1",
    "luxon": "3.7.2",
}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_CURSOR_CONTROL = re.compile(r"\x1b\[[0-?]*[ -/]*[ABCDEFGHJKSTf]|\r")
_RATIO = re.compile(r"(?P<completed>\d+)\s*/\s*(?P<total>\d+)")
_PROGRESS_BAR_ROW = re.compile(r"\d+/\d+ scenarios \[[#-]*\] [A-Z?.-]")
_MARKERS = {"FAILED": "F", "PASSED": ".", "SKIPPED": "-"}
_SEVERITY = {"PASSED": 1, "SKIPPED": 2, "PENDING": 3, "UNDEFINED": 4, "AMBIGUOUS": 5, "FAILED": 6}


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _safe_workspace(consumer: Any, workspace: str | None = None) -> Path:
    root = _consumer_root(consumer)
    destination = Path(workspace) if workspace else Path(".")
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("progress-bar workspace must stay inside the consumer project")
    return root / destination


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("progress-bar consumer files must stay inside the consumer project")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _prepare_consumer(
    consumer: Any,
    feature: str,
    *,
    feature_name: str,
    workspace: str | None = None,
    ini_enabled: bool = False,
) -> Path:
    root = _safe_workspace(consumer, workspace)
    config = "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n"
    if ini_enabled:
        config += "cuke_progress_bar = true\n"
    _write_file(root, "pyproject.toml", config)
    _write_file(root, "conftest.py", 'pytest_plugins = ["progress_bar_consumer_steps"]\n')
    _write_file(root, "progress_bar_consumer_steps.py", _SUPPORT_PLUGIN)
    _write_file(root, f"features/{feature_name}", feature)
    consumer._progress_bar_workspace = root
    return root


def _node_runtime(consumer: Any) -> tuple[str, str, dict[str, str]] | None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None
    environment = dict(consumer.env)
    environment["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), str(Path(consumer.python).parent), os.defpath))
    )
    return node, npm, environment


def _install_formatter(consumer: Any) -> None:
    runtime = _node_runtime(consumer)
    if runtime is None:
        pytest.skip("the real Cucumber formatter lane requires Node.js and npm")
    _, npm, environment = runtime
    root = getattr(consumer, "_progress_bar_workspace", _consumer_root(consumer))
    package_json = {
        "name": "pytest-cuke-progress-bar-consumer",
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
    assert install.returncode == 0, (
        f"could not install the pinned Cucumber formatter packages:\n{install.stdout}\n{install.stderr}"
    )
    consumer.env["PATH"] = environment["PATH"]


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this consumer"
    return f"{result.stdout}\n{result.stderr}"


def _message_rows(consumer: Any, relative_path: str) -> list[dict[str, Any]]:
    root = getattr(consumer, "_progress_bar_workspace", _consumer_root(consumer))
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


def _attempts(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    pickle_names = {row["pickle"]["id"]: row["pickle"]["name"] for row in rows if "pickle" in row}
    test_case_pickles = {row["testCase"]["id"]: row["testCase"]["pickleId"] for row in rows if "testCase" in row}
    started = {row["testCaseStarted"]["id"]: row["testCaseStarted"] for row in rows if "testCaseStarted" in row}
    step_statuses: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        finished_step = row.get("testStepFinished")
        if finished_step is not None:
            step_statuses[finished_step["testCaseStartedId"]].append(finished_step["testStepResult"]["status"])

    attempts = []
    for row in rows:
        finished_case = row.get("testCaseFinished")
        if finished_case is None:
            continue
        started_id = finished_case["testCaseStartedId"]
        pickle_id = test_case_pickles[started[started_id]["testCaseId"]]
        statuses = step_statuses[started_id]
        status = max(statuses, key=lambda item: _SEVERITY.get(item, 0), default="PASSED")
        attempts.append({"id": started_id, "pickle_id": pickle_id, "name": pickle_names[pickle_id], "status": status})
    return attempts


def _progress_marker_lines(output: str) -> list[str]:
    return [line.strip() for line in _ANSI.sub("", output).replace("\r", "\n").splitlines() if line.strip()]


def _ratio_updates(output: str) -> list[tuple[int, int]]:
    return [(int(match["completed"]), int(match["total"])) for match in _RATIO.finditer(_ANSI.sub("", output))]


def _progress_rows(output: str) -> list[str]:
    return _PROGRESS_BAR_ROW.findall(_ANSI.sub("", output))


@given("the consumer prepares a progress-bar scenario that records execution")
def prepare_progress_bar_preflight_scenario(consumer: Any) -> None:
    _prepare_consumer(
        consumer,
        "Feature: Progress-bar preflight\n  Scenario: The consumer scenario starts only after preflight\n    Given a progress-bar scenario records execution\n",
        feature_name="progress-bar-preflight.feature",
    )


@given("the consumer prepares failing, skipped, and passing progress-bar scenarios in a Unicode workspace with spaces")
def prepare_progress_bar_outcomes_in_unicode_workspace(consumer: Any) -> None:
    root = _prepare_consumer(
        consumer,
        _OUTCOME_FEATURE,
        feature_name="progress-bar-outcomes.feature",
        workspace="progress workspace café",
        ini_enabled=True,
    )
    (root / "artifacts").mkdir()


@given("the consumer installs pinned official Cucumber progress formatter packages in that workspace")
def install_progress_formatter_in_unicode_workspace(consumer: Any) -> None:
    _install_formatter(consumer)


@given("the consumer PATH has no Node.js or npm executables")
def hide_node_and_npm_from_consumer_path(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("npm", path=consumer.env["PATH"]) is None


@given("Node and npm are available but the official progress formatter package is absent")
def expose_node_and_npm_without_progress_formatter(consumer: Any) -> None:
    runtime = _node_runtime(consumer)
    if runtime is None:
        pytest.skip("the missing-backend preflight lane requires Node.js and npm")
    _, _, environment = runtime
    root = getattr(consumer, "_progress_bar_workspace", _consumer_root(consumer))
    package = root / "node_modules" / "@cucumber" / "pretty-formatter"
    assert not package.exists(), f"fresh consumer unexpectedly contains {package}"
    environment["npm_config_prefix"] = str(root / ".isolated-npm-prefix")
    environment.pop("NODE_PATH", None)
    consumer.env.update(environment)


@given("the consumer prepares a retry, a skipped case, and a gated progress-bar scenario")
def prepare_tty_progress_bar_scenarios(consumer: Any) -> None:
    root = _prepare_consumer(
        consumer,
        _RETRY_FEATURE,
        feature_name="progress-bar-retries.feature",
        workspace="progress workspace café",
    )
    (root / "artifacts").mkdir()
    for marker in ("retry-attempt-count.txt", "gated-started.marker", "gated-finished.marker", "release-gated-scenario.marker"):
        (root / marker).unlink(missing_ok=True)


@given("a POSIX pseudo-terminal with 32 columns is available")
def posix_pty_with_terminal_width_is_available() -> None:
    # Windows and POSIX builds without PTY support cannot exercise a real TTY; skip this scenario only.
    if os.name != "posix":
        pytest.skip("the live progress-bar case requires a POSIX pseudo-terminal")
    try:
        import fcntl
        import pty
        import termios

        if not hasattr(pty, "openpty") or not hasattr(termios, "TIOCSWINSZ") or not hasattr(fcntl, "ioctl"):
            pytest.skip("this POSIX platform does not provide pseudo-terminal window sizing")
    except ImportError:
        pytest.skip("this POSIX platform does not provide pseudo-terminal support")


@given("the consumer installs pinned official Cucumber progress formatter packages")
def install_progress_formatter(consumer: Any) -> None:
    _install_formatter(consumer)


@given("the consumer installs pytest-rerunfailures in the installed consumer")
def install_rerunfailures(consumer: Any) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("the TTY retry lane requires uv to install pytest-rerunfailures")
    install = subprocess.run(
        [uv, "pip", "install", "--python", str(consumer.python), "pytest-rerunfailures"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert install.returncode == 0, f"could not install pytest-rerunfailures:\n{install.stdout}\n{install.stderr}"


@then("progress bar should remain disabled while the scenario runs")
def progress_bar_is_disabled_by_default(consumer: Any) -> None:
    assert (_consumer_root(consumer) / "scenario-started.marker").is_file(), _output(consumer)
    output = _output(consumer)
    assert "1 passed" in output, f"the ordinary pytest summary was not preserved:\n{output}"
    output = output.lower()
    assert "@cucumber/pretty-formatter" not in output, output
    assert "npm install" not in output, output


@then(re.compile(r'piped progress-bar markers should match completed Messages attempts in "(?P<relative_path>[^"]+)"'))
def piped_progress_markers_match_messages(relative_path: str, consumer: Any) -> None:
    attempts = _attempts(_message_rows(consumer, relative_path))
    assert [attempt["status"] for attempt in attempts] == ["FAILED", "SKIPPED", "PASSED"], attempts
    assert len({attempt["pickle_id"] for attempt in attempts}) == 3, attempts
    expected = "".join(_MARKERS[attempt["status"]] for attempt in attempts)
    output = _output(consumer)
    lines = _progress_marker_lines(output)
    marker_indexes = [index for index, line in enumerate(lines) if expected in line]
    assert marker_indexes, (expected, output)
    summary_rows = [(index, line.lower()) for index, line in enumerate(lines) if re.search(r"\b3 scenarios?\b", line, re.I)]
    assert summary_rows, f"Cucumber's final scenario statistics are missing:\n{output}"
    summary_index, summary = summary_rows[-1]
    assert summary_index > marker_indexes[-1], f"Cucumber's final summary should follow the progress markers:\n{output}"
    for expected_result in ("1 passed", "1 failed", "1 skipped"):
        assert expected_result in summary, f"Cucumber's final summary omitted {expected_result!r}: {summary!r}"
    assert "AssertionError" in output and "progress-bar failure sentinel" in output, (
        f"the standard pytest failure traceback was not preserved:\n{output}"
    )
    failure_section = re.search(r"(?m)^=+ FAILURES =+$", output)
    assert failure_section is not None, f"the standard pytest failure section was not preserved:\n{output}"
    pytest_summary = re.search(r"(?im)^=+\s*short test summary info\s*=+\s*$", output)
    assert pytest_summary is not None, f"the standard pytest short summary was not preserved:\n{output}"
    pytest_summary_output = output[pytest_summary.end() :]
    assert re.search(r"(?m)^\s*features/progress-bar-outcomes\.feature::test_scenarios", pytest_summary_output), (
        f"the pytest short summary omitted the failing BDD scenario:\n{pytest_summary_output}"
    )
    assert "AssertionError: progress-bar failure sentinel" in output[failure_section.end() : pytest_summary.start()], (
        f"the pytest failure section omitted the sentinel traceback:\n{output}"
    )


@then("progress-bar output should have no cursor controls and both file reports should be valid")
def piped_progress_bar_has_readable_output_and_file_reports(consumer: Any) -> None:
    output = _output(consumer)
    assert not _CURSOR_CONTROL.search(output), f"piped progress output used terminal cursor controls:\n{output!r}"
    root = getattr(consumer, "_progress_bar_workspace", _consumer_root(consumer))
    messages_path = root / "artifacts" / "messages.ndjson"
    report_path = root / "artifacts" / "report.json"
    assert messages_path.is_file(), f"Messages file is missing: {messages_path}"
    assert report_path.is_file(), f"JSON file is missing: {report_path}"
    assert isinstance(json.loads(report_path.read_text(encoding="utf-8")), (dict, list))


@then("missing progress-bar backend should fail before the scenario starts")
def missing_progress_bar_backend_is_actionable(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "@cucumber/pretty-formatter" in output, output
    assert "npm install" in output.lower(), output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the progress-bar scenario started before the missing formatter package was rejected"
    )


@then("missing Node progress-bar preflight should fail before the scenario starts")
def missing_node_progress_bar_preflight_is_actionable(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "requires executable 'node', but it was not found on PATH" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the progress-bar scenario started before missing Node.js was rejected"
    )


@then("the progress-bar and pretty conflict should fail before the scenario starts")
def progress_bar_conflicts_with_pretty_before_execution(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "Only one live formatter may write to the terminal" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the progress-bar scenario started before terminal formatter conflict validation"
    )


@when("I run installed pytest in a 32-column terminal until the first live progress update")
def run_progress_bar_in_pty_until_live_update(consumer: Any) -> None:
    try:
        import fcntl
        import pty
        import termios
    except ImportError:
        pytest.skip("this POSIX platform does not provide pseudo-terminal support")

    root = getattr(consumer, "_progress_bar_workspace", _consumer_root(consumer))
    command = [
        str(consumer.pytest),
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-progress-bar",
        "--cuke-messages-ndjson=artifacts/messages.ndjson",
        "--reruns=1",
        "--capture=tee-sys",
        "-v",
        "--tb=no",
        "--color=no",
    ]
    try:
        master_fd, slave_fd = pty.openpty()
    except OSError as error:
        pytest.skip(f"the operating system did not provide a pseudo-terminal: {error}")
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 32, 0, 0))
    process = subprocess.Popen(
        command,
        cwd=root,
        env=consumer.env,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)
    chunks: list[bytes] = []
    deadline = time.monotonic() + 45
    observed_live = False
    release_path = root / "release-gated-scenario.marker"
    try:
        while time.monotonic() < deadline:
            readable, _, _ = select.select([master_fd], [], [], 0.05)
            if readable:
                try:
                    chunks.append(os.read(master_fd, 4096))
                except OSError:
                    break
            text = b"".join(chunks).decode("utf-8", errors="replace")
            if (root / "gated-started.marker").is_file() and (1, 3) in _ratio_updates(text):
                assert not (root / "gated-finished.marker").exists(), (
                    "the gated progress-bar scenario finished before its live update was observed"
                )
                observed_live = True
                release_path.write_text("release", encoding="utf-8")
                break
            if process.poll() is not None:
                break
        assert observed_live, (
            "the 1/3 progress update did not arrive while the final scenario was waiting:\n"
            + b"".join(chunks).decode("utf-8", errors="replace")
        )
        return_code = process.wait(timeout=45)
        while True:
            readable, _, _ = select.select([master_fd], [], [], 0)
            if not readable:
                break
            try:
                chunks.append(os.read(master_fd, 4096))
            except OSError:
                break
    except BaseException:
        release_path.write_text("release", encoding="utf-8")
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        os.close(master_fd)

    output = b"".join(chunks).decode("utf-8", errors="replace")
    consumer._progress_bar_live_update_observed = observed_live
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")


def _run_progress_bar_geometry_replay(consumer: Any, *, columns: int | None) -> str:
    import fcntl
    import pty
    import termios

    root = getattr(consumer, "_progress_bar_workspace", _consumer_root(consumer))
    release_path = root / "release-gated-scenario.marker"
    for marker in ("retry-attempt-count.txt", "gated-started.marker", "gated-finished.marker", "release-gated-scenario.marker"):
        (root / marker).unlink(missing_ok=True)
    release_path.write_text("release", encoding="utf-8")

    master_fd, slave_fd = pty.openpty()
    expected_columns = columns if columns is not None else 0
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, expected_columns, 0, 0))
    assert os.get_terminal_size(slave_fd).columns == expected_columns

    environment = dict(consumer.env)
    environment.pop("COLUMNS", None)
    assert "COLUMNS" not in environment
    command = [
        str(consumer.pytest),
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-progress-bar",
        "--reruns=1",
        "--capture=tee-sys",
        "-v",
        "--tb=no",
        "--color=no",
    ]
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=environment,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )
    finally:
        os.close(slave_fd)

    chunks: list[bytes] = []
    deadline = time.monotonic() + 45
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"the {columns or 80}-column progress-bar replay did not finish")
            readable, _, _ = select.select([master_fd], [], [], min(remaining, 0.05))
            if readable:
                try:
                    chunks.append(os.read(master_fd, 4096))
                except OSError:
                    break
            if process.poll() is not None and not readable:
                break
        return_code = process.wait(timeout=5)
    except BaseException:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        os.close(master_fd)

    output = b"".join(chunks).decode("utf-8", errors="replace")
    assert return_code == 0, f"the {columns or 80}-column progress-bar replay failed:\n{output}"
    return output


@then("the terminal progress updates should be live, width-aware, and capped at the unique Pickle total")
def terminal_progress_updates_fit_width_and_cap_counts(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _output(consumer)
    assert getattr(consumer, "_progress_bar_live_update_observed", False), _output(consumer)
    output = _output(consumer)
    attempts = _attempts(_message_rows(consumer, "artifacts/messages.ndjson"))
    unique_pickles = {attempt["pickle_id"] for attempt in attempts}
    assert len(unique_pickles) == 3, attempts
    assert len(attempts) == 4, attempts
    ratios = _ratio_updates(output)
    assert ratios.count((1, 3)) >= 2, f"retry completion did not update the live count:\n{output}"
    assert ratios[-1] == (3, 3), f"final progress count should be 3/3:\n{output}"
    assert all(total == len(unique_pickles) and 0 <= completed <= total for completed, total in ratios), ratios
    progress_rows = _progress_rows(output)
    assert progress_rows, output
    assert all(len(line) <= 32 for line in progress_rows), progress_rows

    wide_rows = _progress_rows(_run_progress_bar_geometry_replay(consumer, columns=100))
    assert wide_rows and max(len(line) for line in wide_rows) == 100, wide_rows

    fallback_rows = _progress_rows(_run_progress_bar_geometry_replay(consumer, columns=None))
    assert fallback_rows and max(len(line) for line in fallback_rows) == 80, fallback_rows
