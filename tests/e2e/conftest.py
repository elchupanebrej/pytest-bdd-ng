"""Provide conftest helpers."""

import json
import os
import re
import shlex
import shutil
import string
import subprocess  # noqa: S404
import sys
from functools import reduce
from operator import attrgetter, itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from cucumber_messages import Envelope  # type:ignore[attr-defined]
from pytest_httpserver import HTTPServer

from pytest_bdd import given, parsers, step, then, when
from pytest_bdd.compatibility.pytest import assert_outcomes
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model import message_converter
from pytest_bdd.util.data_table import data_table_to_dicts
from pytest_bdd.util.toolz_extra import compose, deepattrgetter
from tests.support.cucumber_formatters import (
    install_fake_node,
    requests_terminal_formatter_output,
    run_pytest_via_real_entrypoint,
)
from tests.support.docker import require_docker_daemon
from tests.support.pytest_results import (
    attach_command_result_outputs,
    combined_result_output,
    resolve_pytester_run_mode,
    run_quietly,
)

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir

# Prevent the private fixture feature file from being collected as a standalone test.
# It is only exercised via @scenario in test_xdist_html_reporting.py.
collect_ignore_glob = ["_*.feature"]

_CUCUMBER_FORMATTER_REPORT_FEATURE_URI = "file:07 Report/09 Cucumber formatter reports.feature.md"
_HTML_REPORT_FEATURE_URIS = (
    "file:07 Report/02 Gathering.feature.md",
    "file:07 Report/07 xdist HTML reporting.feature.md",
    "../tests/e2e/_xdist_html_reporting.feature",
)

try:
    import jq  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - platform-specific availability
    jq = None


@pytest.fixture
def httpserver_port(httpserver):
    """Handle httpserver port."""
    return httpserver.port


@pytest.fixture(autouse=True)
def ensure_fake_node_for_cucumber_formatter_report_docs(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> None:
    """Ensure fake node for cucumber formatter report docs."""
    nodeid = getattr(request.node, "nodeid", "")
    if _CUCUMBER_FORMATTER_REPORT_FEATURE_URI in nodeid:
        install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())
        return
    if any(feature_uri in nodeid for feature_uri in _HTML_REPORT_FEATURE_URIS):
        install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())


@given(re.compile(r"File \"(?P<name>(\.|\w)+)(?P<extension>\.\w+)\" with (?P<extra_opts>.*|\s)content:"))
def write_file_with_extras(name, extension, testdir, step, request, extra_opts):
    """Write file with extras."""
    doc_string = deepattrgetter("argument.doc_string", default=None)(step)[0]
    content = doc_string.content if doc_string else ""
    is_fixture_templated = "fixture templated" in extra_opts
    if is_fixture_templated:
        template_fields = [field_name for _, field_name, _, _ in string.Formatter().parse(content) if field_name]

        format_options = {fixture_name: str(request.getfixturevalue(fixture_name)) for fixture_name in template_fields}
    file_data = str(content).format_map(format_options) if is_fixture_templated else content
    (Path(testdir.tmpdir.strpath) / f"{name}{extension}").write_text(file_data, encoding="utf-8")


@given(
    re.compile(r'File "(?P<name>\w+)(?P<extension>\.\w+)" in the temporary path with content:'),
)
def write_file(name, extension, tmp_path: Path, step):
    """Write file."""
    doc_string = deepattrgetter("argument.doc_string", default=None)(step)[0]
    content = doc_string.content if doc_string else ""
    (tmp_path / f"{name}{extension}").write_text(content)


def _resolve_test_output_path(testdir: "Testdir", file_path: Path) -> Path:
    if file_path.is_absolute():
        return file_path
    return Path(str(testdir.tmpdir)) / file_path


@given(
    re.compile(r'Localserver endpoint "(?P<endpoint>.+)" responding content:'),
)
def test_feature_load_by_http_with_base_url(endpoint, httpserver: HTTPServer, step):
    """
    Verify feature load by http with base url.

    Yields:
        Generated values.

    """
    httpserver.expect_request(endpoint).respond_with_data(
        step.argument.doc_string.content,
        content_type=Mimetype.gherkin_plain.value,
    )
    yield


@given(re.compile(r"Set pytest.ini content to:"))
def _(testdir, step):
    doc_string = getattr(step.argument, "doc_string", None) if getattr(step, "argument", None) else None
    content = doc_string.content if doc_string else ""
    testdir.makeini(content)


@step("run pytest", target_fixture="pytest_result")
def run_pytest(testdir: "Testdir", step, attach):
    """
    Run pytest.

    Yields:
        Generated values.

    """
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    options_dict = data_table_to_dicts(data_table)
    cli_args = list(options_dict.get("cli_args", []))
    run_mode = resolve_pytester_run_mode(options_dict)
    # Most e2e scenarios validate nested pytest output after the fact. Running those
    # child sessions as captured subprocesses keeps the outer live formatter as the
    # only terminal writer while still exposing stdout/stderr through attachments.
    if run_mode == "subprocess" and requests_terminal_formatter_output(*cli_args):
        outcome = run_pytest_via_real_entrypoint(testdir, *cli_args)
        harness_stdout = ""
        harness_stderr = ""
    else:
        testrunner = testdir.runpytest_inprocess if run_mode == "inprocess" else testdir.runpytest_subprocess
        outcome, harness_stdout, harness_stderr = run_quietly(testrunner, *cli_args)

    attach_command_result_outputs(
        attach,
        outcome,
        label="nested-pytest",
        command="pytest " + " ".join(cli_args),
        harness_stdout=harness_stdout,
        harness_stderr=harness_stderr,
    )

    yield outcome


def _coerce_pytest_return_code(pytest_result) -> int:
    return_code = getattr(pytest_result, "ret", None)
    if return_code is None:
        return_code = pytest_result.returncode
    return int(return_code)


def _coerce_pytest_stream_text(stream) -> str:
    if isinstance(stream, str):
        return stream
    str_method = getattr(stream, "str", None)
    if callable(str_method):
        return str_method()
    lines = getattr(stream, "lines", None)
    if isinstance(lines, list):
        return "\n".join(lines)
    return str(stream)


def _parse_outcome_counts(pytest_result) -> dict[str, int]:
    counts: dict[str, int] = {}
    for raw_count, raw_status in re.findall(
        r"(\d+)\s+(passed|failed|skipped|error|errors|xpassed|xfailed)",
        combined_result_output(pytest_result),
    ):
        status = "errors" if raw_status in {"error", "errors"} else raw_status
        counts[status] = max(counts.get(status, 0), int(raw_count))
    return counts


@given("Install npm packages")
def _(testdir: "Testdir", step, attach):
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    options_dict = data_table_to_dicts(data_table)
    packages = list(options_dict.get("packages", []))
    result, harness_stdout, harness_stderr = run_quietly(
        testdir.run,
        shutil.which("npm"),
        "install",
        "--silent",
        *packages,
    )
    attach_command_result_outputs(
        attach,
        result,
        label="npm-install",
        command="npm install --silent " + " ".join(packages),
        harness_stdout=harness_stdout,
        harness_stderr=harness_stderr,
    )
    yield result


@given("pytest-xdist is available")
def _require_xdist():
    pytest.importorskip("xdist")


_REMOTE_XDIST_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "remote_xdist"
_REMOTE_XDIST_REPORT_NAME = "remote-xdist.ndjson"
# Human-friendly aliases for execnet gateway mode names.
# The feature files use the alias; docker-compose receives the canonical execnet keyword.
_REMOTE_MODE_ALIASES: dict[str, str] = {
    "relay": "via",  # 'relay' is the readable name for execnet's 'via' proxy-chain topology
}


@step("Docker is available")
def _require_docker():
    require_docker_daemon()


@step(
    re.compile(r"run pytest across xdist workers over (?P<remote_mode>\w+) gateway"),
    target_fixture="remote_xdist_result",
)
def _run_remote_xdist(remote_mode: str, tmp_path: Path, attach):
    from tests.e2e.test_xdist_remote_message_aggregation import _run_remote_xdist_compose

    execnet_mode = _REMOTE_MODE_ALIASES.get(remote_mode, remote_mode)

    result = _run_remote_xdist_compose(
        tmp_path,
        remote_mode=execnet_mode,
        verify_mode="success",
        fail_transport_workers="",
    )

    attach_command_result_outputs(
        attach,
        result,
        label=f"remote-xdist-{execnet_mode}",
        command="pytest xdist remote execution",
    )

    dest = tmp_path / _REMOTE_XDIST_REPORT_NAME
    return {"result": result, "report": dest, "remote_mode": execnet_mode}


@then("the distributed run succeeds and a consolidated NDJSON report is produced")
def _assert_remote_run_succeeds(remote_xdist_result):
    from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

    from pytest_bdd.model.message_validation import validate_message_stream
    from tests.messages.message_stream_assertions import (
        count_payload_kinds,
        gateway_modes_for_payloads,
        parse_ndjson_messages,
        worker_ids_for_payloads,
    )

    result = remote_xdist_result["result"]
    report = remote_xdist_result["report"]
    remote_mode = remote_xdist_result["remote_mode"]

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert report.exists(), f"NDJSON report not found at {report}"

    messages = parse_ndjson_messages(report)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)
    worker_ids = worker_ids_for_payloads(messages, CucumberTestCaseStarted)
    gateway_modes = gateway_modes_for_payloads(messages, CucumberTestCaseStarted)

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert len(worker_ids) >= 2
    assert remote_mode in gateway_modes


@step("pytest outcome must contain tests with statuses:")
def check_pytest_test_statuses(pytest_result, step):
    """Check pytest test statuses."""
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    outcomes_kwargs = map(attrgetter("value"), data_table.rows[0].cells)
    outcomes_kwargs_values = map(compose(int, attrgetter("value")), data_table.rows[1].cells)
    outcome_result = dict(zip(outcomes_kwargs, outcomes_kwargs_values, strict=False))

    if hasattr(pytest_result, "assert_outcomes"):
        assert_outcomes(pytest_result, **outcome_result)
        return

    parsed_counts = _parse_outcome_counts(pytest_result)
    for outcome_name, expected_count in outcome_result.items():
        assert parsed_counts.get(outcome_name, 0) == expected_count, combined_result_output(pytest_result)


@step("pytest exits with test failures")
def check_pytest_test_failures(pytest_result):
    """Check pytest test failures."""
    assert _coerce_pytest_return_code(pytest_result) == pytest.ExitCode.TESTS_FAILED


@step("pytest outcome must match lines:")
def check_pytest_stdout_lines(pytest_result, step):
    """Check pytest stdout lines."""
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    lines = list(
        map(
            compose(attrgetter("value"), itemgetter(0)),
            map(attrgetter("cells"), data_table.rows),
        ),
    )

    stdout_text = _coerce_pytest_stream_text(getattr(pytest_result, "stdout", ""))
    fnmatch_lines = getattr(getattr(pytest_result, "stdout", None), "fnmatch_lines", None)
    if callable(fnmatch_lines):
        fnmatch_lines(lines)
        return
    for line in lines:
        assert re.search(re.escape(line).replace("\\*", ".*"), stdout_text), stdout_text


@when(parsers.parse("run `{command}`"), target_fixture="renderer_result")
def run_command(testdir, command: str, attach) -> subprocess.CompletedProcess[str]:
    """Run command."""
    command_args = shlex.split(command)
    if command_args and command_args[0] == "python":
        command_args[0] = sys.executable
    env = dict(os.environ)
    repo_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(repo_root / "src"), env.get("PYTHONPATH", "")]))
    result = subprocess.run(  # noqa: S603
        command_args,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(testdir.tmpdir),
        env=env,
    )
    attach_command_result_outputs(attach, result, label="standalone-renderer", command=command)
    return result


@then("the renderer terminal output includes:")
def renderer_terminal_output_includes(request: pytest.FixtureRequest, step) -> None:
    """Handle renderer terminal output includes."""
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    lines = [row.cells[0].value for row in data_table.rows]
    output_fragments: list[str] = []

    if "renderer_result" in request.fixturenames:
        renderer_result = request.getfixturevalue("renderer_result")
        output_fragments.extend([renderer_result.stdout, renderer_result.stderr])
    if "pytest_result" in request.fixturenames:
        pytest_result = request.getfixturevalue("pytest_result")
        output_fragments.extend(
            [
                _coerce_pytest_stream_text(getattr(pytest_result, "stdout", "")),
                _coerce_pytest_stream_text(getattr(pytest_result, "stderr", "")),
            ],
        )

    combined_output = "\n".join(fragment for fragment in output_fragments if fragment)
    for line in lines:
        assert re.search(re.escape(line).replace("\\*", ".*"), combined_output), combined_output


@given(re.compile(r'Copy path from "(?P<initial_path>[^"]+)" to test path "(?P<final_path>[^"]+)"'))
def copy_path(request, testdir: "Testdir", initial_path, final_path):
    """Handle copy path."""
    full_initial_path = (Path(request.config.rootdir) / Path(initial_path).as_posix()).resolve(strict=True)
    full_final_path = Path(testdir.tmpdir) / Path(final_path).as_posix()
    if full_initial_path.is_file():
        full_final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(full_initial_path, full_final_path)
    else:
        shutil.copytree(full_initial_path, full_final_path, dirs_exist_ok=True)


@then(
    re.compile(r'File "(?P<file_path>[^"]+)" has "(?P<line_count>\d+)" lines'),
    converters={"line_count": int, "file_path": Path},
)
def _(file_path: Path, line_count: int, testdir: "Testdir"):
    output_path = _resolve_test_output_path(testdir, file_path)
    with output_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)  # type: ignore[no-any-return]
    assert line_count == real_line_count


@then(
    re.compile(r'File "(?P<file_path>[^"]+)" has at least "(?P<line_count>\d+)" lines'),
    converters={"line_count": int, "file_path": Path},
)
def _(file_path: Path, line_count: int, testdir: "Testdir"):
    output_path = _resolve_test_output_path(testdir, file_path)
    with output_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)  # type: ignore[no-any-return]
    assert real_line_count >= line_count


@then(
    re.compile(r'File "(?P<file_path>[^"]+)" is not empty'),
    converters={"file_path": Path},
)
def _(file_path: Path, testdir):
    assert _resolve_test_output_path(testdir, file_path).stat().st_size != 0


@then(parsers.parse('File "{file_path}" contains the line "{line}"'))
def file_contains_line(testdir, file_path: str, line: str) -> None:
    """Handle file contains line."""
    output_path = _resolve_test_output_path(testdir, Path(file_path))
    assert line in output_path.read_text(encoding="utf-8")


@then(
    re.compile(r'Report "(?P<file_path>[^"]+)" parsable into messages'),
    converters={"file_path": Path},
)
def _(file_path: Path, testdir: "Testdir"):
    output_path = _resolve_test_output_path(testdir, file_path)
    with output_path.open(mode="r") as ast_file:
        try:
            for raw_datum in ast_file:
                message_converter.from_dict(json.loads(raw_datum), Envelope)
        except Exception as e:
            raise AssertionError from e


@then(
    re.compile(
        r'JSON file "(?P<file_path>.+)" jq query "(?P<query>.+)" returns "(?P<expected>.+)"',
    ),
    converters={"file_path": Path},
)
def _(file_path: Path, query: str, expected: str, testdir):
    if jq is None:
        pytest.skip("jq package is unavailable on this platform")
    payload = json.loads((Path(str(testdir.tmpdir)) / file_path).read_text(encoding="utf-8"))
    actual = jq.compile(query).input(payload).first()
    assert str(actual) == expected
