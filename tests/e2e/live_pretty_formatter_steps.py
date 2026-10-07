"""Installed-consumer acceptance steps for the live Cucumber Pretty formatter."""

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


_SUPPORT_PLUGIN = """\
import time
from pathlib import Path

import pytest
from pytest_cuke import given, parsers, then, when

ROOT = Path(__file__).parent


@given("a Unicode account context is loaded:")
def unicode_account_context_is_loaded(step):
    assert "déjà vu" in step.doc_string.content
    assert "東京" in step.doc_string.content
    assert "🧪" in step.doc_string.content


@given("the account has this balance table:")
def account_has_balance_table(step):
    rows = [[cell.value for cell in row.cells] for row in step.data_table.rows]
    assert rows == [["item", "amount"], ["café", "12.50"], ["茶", "4.00"]]


@when(parsers.parse('the account owner "{person}" reads this message:'))
def account_owner_reads_message(person, step):
    assert person
    if person in {"Zoë", "李雷"}:
        assert "mañana" in step.doc_string.content
        assert "🪁" in step.doc_string.content


@then("the account story is recorded")
def account_story_is_recorded():
    print("pretty capture sentinel")


@then("the requested details are checked:")
def requested_details_are_checked(step):
    rows = [[cell.value for cell in row.cells] for row in step.data_table.rows]
    assert rows == [["field", "value"], ["language", "日本語"], ["status", "ready"]]


@then("the record raises a deliberate failure")
def record_raises_deliberate_failure():
    raise AssertionError("pretty failure sentinel")


@then("the step after the failure remains visible")
def step_after_failure_remains_visible():
    pass


@then("the record is deliberately skipped")
def record_is_deliberately_skipped():
    pytest.skip("pretty skip sentinel")


@when("the long operation starts and waits for release")
def long_operation_waits_for_release():
    (ROOT / "gated-step-started.marker").write_text("started", encoding="utf-8")
    deadline = time.monotonic() + 25
    release = ROOT / "release-gated-step.marker"
    while time.monotonic() < deadline and not release.is_file():
        time.sleep(0.01)
    assert release.is_file(), "the live pretty output observer did not release the gated step"
    (ROOT / "gated-step-finished.marker").write_text("finished", encoding="utf-8")


@then("the long operation is complete")
def long_operation_is_complete():
    assert (ROOT / "gated-step-finished.marker").is_file()


@then("the pretty consumer records that its scenario started")
def pretty_consumer_records_scenario_start():
    (ROOT / "scenario-started.marker").write_text("started", encoding="utf-8")
"""

_ACCOUNT_DOC = """Feature: Live Cucumber Pretty contract
  Background:
    Given a Unicode account context is loaded:
      \"\"\"text/plain
      Notes for Zoë: déjà vu from 東京 — 🧪 keeps the source readable.
      The second line remains part of the same docstring.
      \"\"\"
    And the account has this balance table:
      | item | amount |
      | café | 12.50  |
      | 茶   | 4.00   |

  Scenario Outline: A passing account story for <person>
    When the account owner \"<person>\" reads this message:
      \"\"\"text/plain
      Bonjour, mañana — 🪁 and 東京 stay in the output.
      \"\"\"
    Then the account story is recorded
    And the requested details are checked:
      | field    | value   |
      | language | 日本語  |
      | status   | ready   |

    Examples:
      | person |
      | Zoë    |
      | 李雷   |

  Scenario: A failing account story keeps its source visible
    When the account owner \"Élodie\" reads this message:
      \"\"\"text/plain
      A failure still carries readable source.
      \"\"\"
    Then the record raises a deliberate failure
    And the step after the failure remains visible

  Scenario: A skipped account story keeps its source visible
    When the account owner \"Miyuki\" reads this message:
      \"\"\"text/plain
      A skip still carries readable source.
      \"\"\"
    Then the record is deliberately skipped
"""

_PROGRESS_FEATURE = """Feature: Pretty output arrives before a later step finishes
  Scenario: The formatter reports the scenario while an operation is gated
    When the long operation starts and waits for release
    Then the long operation is complete
"""

_START_MARKER_FEATURE = """Feature: Pretty formatter selection preflight
  Scenario: The scenario must not start when terminal outputs conflict
    Then the pretty consumer records that its scenario started
"""

_PACKAGE_PREFLIGHT_FEATURE = """Feature: Pretty formatter package preflight
  Scenario: The selected PrettyPrinter must be checked before execution
    Then the pretty consumer records that its scenario started
"""

_SIMPLE_FEATURE = """Feature: Live pretty output portability
  Scenario: A passing account story for Zoë
    Given a Unicode account context is loaded:
      \"\"\"text/plain
      Notes for Zoë: déjà vu from 東京 — 🧪.
      \"\"\"
    Then the account story is recorded
"""

_CLEAN_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_USAGE_JSON_PLUGIN = """\
import sys
from pathlib import Path

from pytest_cuke import FormatterRequest


def pytest_cuke_formatter_requests(config):
    command = (
        sys.executable,
        "-c",
        "import collections,json,sys; counts=collections.Counter(); "
        "[counts.update(json.loads(line).keys()) for line in sys.stdin if line.strip()]; "
        "print(json.dumps({'event_counts': dict(counts)}))",
    )
    return (FormatterRequest(
        name="usage-json-probe",
        command=command,
        output_path=Path("artifacts/usage.json"),
        working_directory=Path(__file__).parent,
    ),)
"""


def _consumer_root(consumer: Any) -> Path:
    return Path(consumer.path).resolve()


def _safe_workspace(consumer: Any, workspace: str | None = None) -> Path:
    root = _consumer_root(consumer)
    destination = Path(workspace) if workspace else Path(".")
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("pretty consumer workspace must stay inside the consumer project")
    workspace_root = (root / destination).resolve()
    if root not in workspace_root.parents and workspace_root != root:
        raise ValueError("pretty consumer workspace must stay inside the consumer project")
    return workspace_root


def _write_file(root: Path, relative_path: str, content: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("pretty consumer files must stay inside the consumer project")
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _prepare_consumer(root: Path, feature: str, *, feature_name: str) -> None:
    _write_file(root, "conftest.py", 'pytest_plugins = ["pretty_consumer_steps"]\n')
    _write_file(root, "pretty_consumer_steps.py", _SUPPORT_PLUGIN)
    _write_file(root, f"features/{feature_name}", feature)


def _pin_node_environment(consumer: Any, workspace_root: Path) -> None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        pytest.skip("the official Cucumber PrettyPrinter acceptance lane requires Node.js and npm")

    package_json = {
        "name": "pytest-cuke-live-pretty-consumer",
        "private": True,
        "type": "module",
        "dependencies": {
            "@cucumber/messages": "34.2.1",
            "@cucumber/pretty-formatter": "4.0.2",
            "@cucumber/query": "16.1.1",
            "luxon": "3.7.2",
        },
    }
    _write_file(workspace_root, "package.json", json.dumps(package_json, indent=2) + "\n")
    environment = dict(consumer.env)
    path_entries = (
        str(Path(node).parent),
        str(Path(npm).parent),
        str(Path(consumer.python).parent),
        os.defpath,
    )
    environment["PATH"] = os.pathsep.join(dict.fromkeys(path_entries))
    install = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=workspace_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert install.returncode == 0, (
        f"could not install pinned Cucumber PrettyPrinter packages:\n{install.stdout}\n{install.stderr}"
    )
    consumer.env["PATH"] = environment["PATH"]
    consumer._live_pretty_node = node


def _prepare_simple_workspace(consumer: Any, *, workspace: str | None = None, feature: str = _SIMPLE_FEATURE) -> Path:
    root = _safe_workspace(consumer, workspace)
    _prepare_consumer(root, feature, feature_name="live-pretty-portable.feature")
    return root


def _output(consumer: Any) -> str:
    result = getattr(consumer, "pytest_result", None)
    assert result is not None, "installed pytest has not run in this consumer"
    return _CLEAN_ANSI.sub("", f"{result.stdout}\n{result.stderr}")


def _run_with_pipe(consumer: Any, *, arguments: list[str], timeout_seconds: float = 30) -> None:
    command = [str(consumer.pytest), *arguments]
    process = subprocess.run(
        command,
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout_seconds,
    )
    consumer.pytest_result = process


@given("the consumer installs the pinned official PrettyPrinter packages for live output")
def install_official_pretty_packages(consumer: Any) -> None:
    _pin_node_environment(consumer, _consumer_root(consumer))


@given("the consumer prepares a Unicode feature with a Background, two outline rows, a failure, and a skip")
def prepare_full_pretty_feature(consumer: Any) -> None:
    _prepare_consumer(_consumer_root(consumer), _ACCOUNT_DOC, feature_name="live-pretty-contract.feature")


@then("the live pretty output should preserve the feature source, Unicode, tables, and outcomes")
def full_live_pretty_output_is_readable(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, result
    output = _output(consumer)
    for expected in (
        "Live Cucumber Pretty contract",
        "A passing account story for <person>",
        "A failing account story keeps its source visible",
        "A skipped account story keeps its source visible",
        "déjà vu",
        "東京",
        "🧪",
        "mañana",
        "🪁",
        "café",
        "日本語",
        "When the account owner",
        "Then the record raises a deliberate failure",
        "the step after the failure remains visible",
        "pretty failure sentinel",
        "pretty skip sentinel",
    ):
        assert expected in output, f"live PrettyPrinter output omitted {expected!r}:\n{output}"
    failure_location = next(
        f"pretty_consumer_steps.py:{line_number}"
        for line_number, source_line in enumerate(_SUPPORT_PLUGIN.splitlines(), start=1)
        if 'raise AssertionError("pretty failure sentinel")' in source_line
    )
    assert f"✘ Then the record raises a deliberate failure" in output, output
    assert failure_location in output, f"failing step source location was omitted: {output}"
    assert "↷ And the step after the failure remains visible" in output, output
    assert "✔ And the step after the failure remains visible" not in output, output
    assert "↷ Then the record is deliberately skipped" in output, output
    outline_title = "Scenario Outline: A passing account story for <person>"
    assert output.count(outline_title) == 2, f"each executed outline row must render once: {output}"
    for person in ("Zoë", "李雷"):
        expanded_step = f'When the account owner "{person}" reads this message:'
        assert output.count(expanded_step) == 1, (
            f"live PrettyPrinter output did not render exactly one expanded outline row for {person!r}:\n{output}"
        )
    assert output.count("a Unicode account context is loaded") == 4, output
    assert re.search(r"live-pretty-contract\.feature:\d+", output), output
    assert re.search(r"(?s)(?=.*\b2 passed\b)(?=.*\b1 failed\b)(?=.*\b1 skipped\b)", output), output


@given("the consumer prepares a feature with a deliberately gated later step")
def prepare_gated_pretty_feature(consumer: Any) -> None:
    root = _consumer_root(consumer)
    _prepare_consumer(root, _PROGRESS_FEATURE, feature_name="live-pretty-progress.feature")
    for marker in ("gated-step-started.marker", "gated-step-finished.marker", "release-gated-step.marker"):
        (root / marker).unlink(missing_ok=True)


@when("I release the gated step only after its scenario title appears in live pretty output")
def run_until_live_pretty_title_releases_gated_step(consumer: Any) -> None:
    root = _consumer_root(consumer)
    command = [
        str(consumer.pytest),
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-pretty",
        "-s",
        "-q",
        "--color=no",
    ]
    environment = dict(consumer.env)
    environment.update({"COLUMNS": "48", "TERM": "dumb"})
    process = subprocess.Popen(
        command,
        cwd=root,
        env=environment,
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

    reader = threading.Thread(target=read_output, name="live-pretty-output-reader", daemon=True)
    reader.start()
    title = "The formatter reports the scenario while an operation is gated"
    deadline = time.monotonic() + 20
    observed = False
    try:
        while time.monotonic() < deadline:
            text = b"".join(chunks).decode("utf-8", errors="replace")
            started = (root / "gated-step-started.marker").is_file()
            finished = (root / "gated-step-finished.marker").is_file()
            if title in text and started:
                assert not finished, "the later step finished before live pretty output was observed"
                observed = True
                break
            if process.poll() is not None:
                break
            time.sleep(0.01)
        assert observed, (
            "the pretty scenario title did not reach the piped terminal before the gated step finished:\n"
            + b"".join(chunks).decode("utf-8", errors="replace")
        )
        (root / "release-gated-step.marker").write_text("release", encoding="utf-8")
        return_code = process.wait(timeout=30)
    except BaseException:
        (root / "release-gated-step.marker").write_text("release", encoding="utf-8")
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        reader.join(timeout=5)

    output = b"".join(chunks).decode("utf-8", errors="replace")
    consumer._live_pretty_gate_observed = observed
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")


@then("the installed pytest run should finish after the live output gate is released")
def gated_pretty_run_finishes_after_output(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _output(consumer)
    assert getattr(consumer, "_live_pretty_gate_observed", False)
    assert (_consumer_root(consumer) / "gated-step-finished.marker").is_file()


@given("a portable workspace café enables cuke_pretty and contains one Unicode feature")
def prepare_portable_pretty_workspace(consumer: Any) -> None:
    root = _prepare_simple_workspace(consumer, workspace="portable workspace café")
    _write_file(root, "pretty_usage_json_formatter.py", _USAGE_JSON_PLUGIN)
    _write_file(
        root,
        "conftest.py",
        'pytest_plugins = ["pretty_consumer_steps", "pretty_usage_json_formatter"]\n',
    )
    _write_file(
        root,
        "pyproject.toml",
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\ncuke_pretty = true\n",
    )
    (root / "artifacts").mkdir()
    consumer._live_pretty_workspace = root


@given("the consumer installs the pinned official PrettyPrinter packages in its portable workspace")
def install_official_pretty_packages_in_workspace(consumer: Any) -> None:
    workspace = getattr(consumer, "_live_pretty_workspace", None)
    assert isinstance(workspace, Path), "the portable workspace must be prepared before installing npm packages"
    _pin_node_environment(consumer, workspace)


@then("pretty, Messages, JSON, and JUnit outputs should coexist in the portable consumer workspace")
def pretty_and_file_formatters_coexist(consumer: Any) -> None:
    root = getattr(consumer, "_live_pretty_workspace", None)
    assert isinstance(root, Path)
    output = _output(consumer)
    assert "Live pretty output portability" in output, output
    messages_path = root / "artifacts" / "messages.ndjson"
    json_path = root / "artifacts" / "report.json"
    junit_path = root / "artifacts" / "junit.xml"
    usage_path = root / "artifacts" / "usage.json"
    assert messages_path.is_file(), f"Messages output was not written at the relative path {messages_path}"
    assert json_path.is_file(), f"JSON output was not written at the relative path {json_path}"
    assert junit_path.is_file(), f"JUnit output was not written at the relative path {junit_path}"
    assert usage_path.is_file(), f"usage JSON output was not written at the relative path {usage_path}"
    messages = [json.loads(line) for line in messages_path.read_text(encoding="utf-8").splitlines() if line]
    assert messages and any("testRunFinished" in row for row in messages), messages
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(report, (dict, list)), report
    usage_report = json.loads(usage_path.read_text(encoding="utf-8"))
    assert usage_report["event_counts"]["testRunFinished"] == 1, usage_report


@then("verbose tee-sys output should retain its normal forwarding and capture behavior")
def verbose_tee_sys_output_is_preserved(consumer: Any) -> None:
    output = _output(consumer)
    assert "PASSED" in output, output
    assert "pretty capture sentinel" in output, "tee-sys should forward passing step stdout"


@given("the piped pretty consumer has a Unicode scenario and a narrow terminal width")
def prepare_narrow_piped_pretty_consumer(consumer: Any) -> None:
    _prepare_simple_workspace(consumer)
    consumer.env.update({"COLUMNS": "42", "TERM": "dumb"})


@then("the piped pretty output should contain readable Unicode and the scenario source")
def piped_pretty_output_is_readable(consumer: Any) -> None:
    assert consumer.pytest_result is not None and consumer.pytest_result.returncode == 0, _output(consumer)
    output = _output(consumer)
    for expected in (
        "Live pretty output portability",
        "A passing account story for Zoë",
        "a Unicode account context is loaded",
        "東京",
    ):
        assert expected in output, f"piped output omitted {expected!r}:\n{output}"
    assert "\ufffd" not in output, output
    assert "PASSED" not in output, "quiet pytest output should not contain verbose progress labels"
    assert "pretty capture sentinel" not in output, "passing step stdout should remain captured by pytest"


@given("the terminal pretty consumer has a Unicode scenario")
def prepare_tty_pretty_consumer(consumer: Any) -> None:
    if os.name == "nt":
        pytest.skip("the standard-library pseudo-terminal API is not available on Windows")
    _prepare_simple_workspace(consumer)


@when("I run installed pytest in a narrow terminal with pretty output enabled")
def run_consumer_pytest_in_narrow_terminal(consumer: Any) -> None:
    if os.name == "nt":
        pytest.skip("the standard-library pseudo-terminal API is not available on Windows")

    import fcntl
    import pty
    import struct
    import termios

    root = _consumer_root(consumer)
    command = [
        str(consumer.pytest),
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-pretty",
        "-s",
        "-q",
        "--color=yes",
    ]
    environment = dict(consumer.env)
    environment.update({"COLUMNS": "46", "TERM": "xterm"})
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 46, 0, 0))
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
    chunks: list[bytes] = []

    def read_terminal() -> None:
        while True:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                return
            if not chunk:
                return
            chunks.append(chunk)

    reader = threading.Thread(target=read_terminal, name="pretty-terminal-reader", daemon=True)
    reader.start()
    try:
        return_code = process.wait(timeout=30)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait(timeout=5)
        raise AssertionError("installed pytest did not finish in the narrow pseudo-terminal") from error
    finally:
        reader.join(timeout=5)
        os.close(master)
    output = b"".join(chunks).decode("utf-8", errors="replace")
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
    consumer._live_pretty_tty_output = output


@then("the narrow terminal pretty output should contain readable Unicode and the scenario source")
def tty_pretty_output_is_readable(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _output(consumer)
    output = _CLEAN_ANSI.sub("", getattr(consumer, "_live_pretty_tty_output", ""))
    for expected in (
        "Live pretty output portability",
        "A passing account story for Zoë",
        "a Unicode account context is loaded",
        "東京",
    ):
        assert expected in output, f"TTY output omitted {expected!r}:\n{output}"
    assert "\ufffd" not in output, output


@given("the consumer prepares a scenario that records whether it started")
def prepare_terminal_conflict_consumer(consumer: Any) -> None:
    root = _consumer_root(consumer)
    _prepare_consumer(root, _START_MARKER_FEATURE, feature_name="pretty-terminal-conflict.feature")
    _write_file(
        root,
        "extra_terminal_formatter.py",
        "import sys\n"
        "from pathlib import Path\n\n"
        "from pytest_cuke import FormatterRequest\n\n\n"
        "def pytest_cuke_formatter_requests(config):\n"
        "    del config\n"
        "    return (FormatterRequest(\n"
        "        name='extra-terminal-probe',\n"
        "        command=(sys.executable, 'terminal_probe.py'),\n"
        "        output_path=None,\n"
        "        working_directory=Path(__file__).parent,\n"
        "    ),)\n",
    )
    _write_file(root, "terminal_probe.py", "import sys\nsys.stdin.read()\nprint('unexpected terminal probe start')\n")
    _write_file(
        root,
        "conftest.py",
        'pytest_plugins = ["pretty_consumer_steps", "extra_terminal_formatter"]\n',
    )


@then("the terminal formatter conflict should be rejected before the scenario starts")
def terminal_pretty_conflict_is_preflighted(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "Only one live formatter may write to the terminal" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the scenario began before terminal formatter conflicts were validated"
    )


@given("the consumer prepares a normal feature without installing Node or Cucumber packages")
def prepare_unselected_pretty_consumer(consumer: Any) -> None:
    _prepare_simple_workspace(consumer)


@given("Node is absent from the installed consumer PATH")
def remove_node_from_consumer_path(consumer: Any) -> None:
    consumer.env["PATH"] = str(Path(consumer.python).parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert not (_consumer_root(consumer) / "node_modules" / "@cucumber" / "pretty-formatter").exists()


@then("the normal scenario should pass without creating pretty output")
def normal_consumer_run_ignores_pretty_dependencies(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _output(consumer)
    assert "1 passed" in _output(consumer)
    assert not (_consumer_root(consumer) / "pretty-output.txt").exists()
    assert not (_consumer_root(consumer) / "node_modules").exists()


@given("Node and npm are available but the official PrettyPrinter package is absent")
def require_node_without_pretty_package(consumer: Any) -> None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        pytest.skip("the missing-package preflight case requires both Node.js and npm on PATH")
    root = _consumer_root(consumer)
    package = root / "node_modules" / "@cucumber" / "pretty-formatter"
    assert not package.exists(), f"fresh consumer unexpectedly contains {package}"
    consumer.env["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), str(Path(consumer.python).parent), os.defpath))
    )


@given("the consumer prepares a scenario marker for pretty package preflight")
def prepare_pretty_package_preflight_marker(consumer: Any) -> None:
    _prepare_consumer(
        _consumer_root(consumer),
        _PACKAGE_PREFLIGHT_FEATURE,
        feature_name="pretty-package-preflight.feature",
    )


@then("missing PrettyPrinter package preflight should fail before the scenario starts")
def missing_pretty_package_fails_preflight(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "requires npm package '@cucumber/pretty-formatter'" in output, output
    assert "npm install @cucumber/pretty-formatter" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the scenario ran before the missing PrettyPrinter package was rejected"
    )


@then("missing Node preflight should fail before the scenario starts")
def missing_node_fails_preflight(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "requires executable 'node', but it was not found on PATH" in output, output
    assert not (_consumer_root(consumer) / "scenario-started.marker").exists(), (
        "the scenario ran before missing Node was rejected"
    )


@given("the consumer prepares a bounded fake PrettyPrinter package and a Unicode feature")
def prepare_bounded_fake_pretty_printer(consumer: Any) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("the bounded Node formatter lane requires a Node executable")
    root = _consumer_root(consumer)
    _prepare_simple_workspace(consumer)
    fake_packages = {
        "@cucumber/pretty-formatter": (
            "export class PrettyPrinter {\n"
            "  constructor({ stream }) { this.stream = stream; }\n"
            "  update(message) {\n"
            "    if (message.testRunStarted) this.stream.write('FAKE_PRETTY_RUNTIME_RECEIVED_LIVE_MESSAGES\\n');\n"
            "  }\n"
            "}\n"
        ),
        "@cucumber/messages": "export {};\n",
        "@cucumber/query": "export {};\n",
        "luxon": "export {};\n",
    }
    for name, module_source in fake_packages.items():
        package_root = Path("node_modules") / name
        _write_file(
            root,
            str(package_root / "package.json"),
            json.dumps(
                {
                    "name": name,
                    "version": "0.0.0-test",
                    "type": "module",
                    "exports": "./index.js",
                },
                indent=2,
            )
            + "\n",
        )
        _write_file(root, str(package_root / "index.js"), module_source)
    consumer.env["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(consumer.python).parent), os.defpath))
    )


@when("I run installed pytest with the fake PrettyPrinter and a 20-second bound")
def run_fake_pretty_printer_bounded(consumer: Any) -> None:
    _run_with_pipe(
        consumer,
        arguments=[
            "--rootdir=.",
            "--cuke-autoload",
            "--cuke-features-dir=features",
            "--cuke-pretty",
            "-q",
            "--color=no",
        ],
        timeout_seconds=20,
    )


@then("the fake pretty runtime should finish and report that it received live Messages")
def fake_pretty_runtime_finishes_bounded(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode == 0, _output(consumer)
    assert "FAKE_PRETTY_RUNTIME_RECEIVED_LIVE_MESSAGES" in _output(consumer), _output(consumer)


@given("the consumer prepares a PrettyPrinter backend that exits with an error after final Messages")
def prepare_failing_pretty_printer(consumer: Any) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("the bounded Node formatter lane requires a Node executable")
    root = _consumer_root(consumer)
    _prepare_simple_workspace(consumer)
    fake_packages = {
        "@cucumber/pretty-formatter": (
            "export class PrettyPrinter {\n"
            "  constructor({ stream }) { this.stream = stream; }\n"
            "  update(message) {\n"
            "    if (message.testRunFinished) {\n"
            "      this.stream.write('FAKE_PRETTY_BACKEND_EXITING_23\\n');\n"
            "      process.exitCode = 23;\n"
            "    }\n"
            "  }\n"
            "}\n"
        ),
        "@cucumber/messages": "export {};\n",
        "@cucumber/query": "export {};\n",
        "luxon": "export {};\n",
    }
    for name, module_source in fake_packages.items():
        package_root = Path("node_modules") / name
        _write_file(
            root,
            str(package_root / "package.json"),
            json.dumps(
                {
                    "name": name,
                    "version": "0.0.0-test",
                    "type": "module",
                    "exports": "./index.js",
                },
                indent=2,
            )
            + "\n",
        )
        _write_file(root, str(package_root / "index.js"), module_source)
    consumer.env["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(consumer.python).parent), os.defpath))
    )


@then("the pretty backend failure should be reported with the pytest run status")
def pretty_backend_failure_is_reported(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, _output(consumer)
    output = _output(consumer)
    assert "FAKE_PRETTY_BACKEND_EXITING_23" in output, output
    assert "cucumber-pretty" in output and "status 23" in output, output
    assert "1 passed" in output, output
