"""E2E BDD step definitions extracted from conftest."""

import json
import os
import re
import shlex
import shutil
import string
import subprocess
import sys
from functools import reduce
from html.parser import HTMLParser
from operator import attrgetter, itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from cucumber_messages import Envelope  # type:ignore[attr-defined]  # cucumber_messages has no py.typed marker
from pytest_httpserver import HTTPServer

from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    greater_than_or_equal_to,
    is_,
    is_not,
)
from pytest_bdd import given, parsers, step, then, when
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model import message_converter
from pytest_bdd.util.data_table import data_table_to_dicts
from pytest_bdd.util.toolz_extra import compose, deepattrgetter
from pytest_bdd_testing.tool.cucumber_formatter import (
    install_fake_node,
    requests_terminal_formatter_output,
    run_pytest_via_real_entrypoint,
)
from pytest_bdd_testing.tool.docker.docker import require_docker_daemon
from pytest_bdd_testing.tool.pytest_results import (
    attach_command_result_outputs,
    combined_result_output,
    resolve_pytester_run_mode,
    run_quietly,
)

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Testdir

try:
    import jq  # type: ignore[import-untyped]  # jq has no inline type stubs
except ImportError:
    jq = None

_CUCUMBER_FORMATTER_REPORT_FEATURE_URI = "file:07 Report/09 Cucumber formatter reports.feature.md"
_HTML_REPORT_FEATURE_URIS = (
    "file:07 Report/02 Gathering.feature.md",
    "file:07 Report/07 xdist HTML reporting.feature.md",
    "../../e2e/_xdist_html_reporting.feature",
)

_REMOTE_XDIST_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "assets" / "docker" / "remote_xdist"
_REMOTE_XDIST_REPORT_NAME = "remote-xdist.ndjson"
_REMOTE_MODE_ALIASES: dict[str, str] = {"relay": "via"}


# ── pytest fixtures ──────────────────────────────────────────────────


@pytest.fixture
def httpserver_port(httpserver):
    return httpserver.port


@pytest.fixture(autouse=True)
def ensure_fake_node_for_cucumber_formatter_report_docs(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> None:
    nodeid = getattr(request.node, "nodeid", "")
    if _CUCUMBER_FORMATTER_REPORT_FEATURE_URI in nodeid:
        install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())
        return
    if any(feature_uri in nodeid for feature_uri in _HTML_REPORT_FEATURE_URIS):
        install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())


# ── helpers ───────────────────────────────────────────────────────────


def _resolve_test_output_path(testdir: "Testdir", file_path: Path) -> Path:
    if file_path.is_absolute():
        return file_path
    return Path(str(testdir.tmpdir)) / file_path


class _HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)

    @property
    def text(self) -> str:
        return "\n".join(self.text_parts)


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


def _fake_node_runtime_installed() -> bool:
    return any(
        key in os.environ
        for key in (
            "PYTEST_BDD_FAKE_NODE_CAPTURE_DIR",
            "NODE_PATH",
            "FAKE_GLOBAL_NODE_MODULES_ROOT",
        )
    )


# ── step definitions ─────────────────────────────────────────────────


@given(re.compile(r"File \"(?P<name>(\.|\w)+)(?P<extension>\.\w+)\" with (?P<extra_opts>.*|\s)content:"))
def write_file_with_extras(name, extension, testdir, step, request, extra_opts):
    doc_string = deepattrgetter("argument.doc_string", default=None)(step)[0]
    content = doc_string.content if doc_string else ""
    is_fixture_templated = "fixture templated" in extra_opts
    if is_fixture_templated:
        template_fields = [field_name for _, field_name, _, _ in string.Formatter().parse(content) if field_name]
        format_options = {fixture_name: str(request.getfixturevalue(fixture_name)) for fixture_name in template_fields}
    file_data = str(content).format_map(format_options) if is_fixture_templated else content
    (Path(testdir.tmpdir.strpath) / f"{name}{extension}").write_text(file_data, encoding="utf-8")


@given(re.compile(r'File "(?P<name>\w+)(?P<extension>\.\w+)" in the temporary path with content:'))
def write_file(name, extension, tmp_path: Path, step):
    doc_string = deepattrgetter("argument.doc_string", default=None)(step)[0]
    content = doc_string.content if doc_string else ""
    (tmp_path / f"{name}{extension}").write_text(content)


@given(re.compile(r'Localserver endpoint "(?P<endpoint>.+)" responding content:'))
def test_feature_load_by_http_with_base_url(endpoint, httpserver: HTTPServer, step):
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
def run_pytest(testdir: "Testdir", step, attach):  # pylint: disable=E0102  # intentional redefinition for step type
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    options_dict = data_table_to_dicts(data_table)
    cli_args = list(options_dict.get("cli_args", []))
    run_mode = resolve_pytester_run_mode(options_dict)
    if run_mode == "subprocess" and requests_terminal_formatter_output(*cli_args):
        outcome = run_pytest_via_real_entrypoint(
            testdir,
            *cli_args,
            preserve_fake_node=_fake_node_runtime_installed(),
        )
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
        harness_outputs=(harness_stdout, harness_stderr),
    )
    yield outcome


@given("Install npm packages")
def _(testdir: "Testdir", step, attach):  # pylint: disable=E0102  # intentional redefinition for step type
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
        harness_outputs=(harness_stdout, harness_stderr),
    )
    yield result


@given("pytest-xdist is available")
def _require_xdist():
    pytest.importorskip("xdist")


@step("Docker is available")
def _require_docker():
    require_docker_daemon()


@step(
    re.compile(r"run pytest across xdist workers over (?P<remote_mode>\w+) gateway(?: with CLI options:)?"),
    target_fixture="remote_xdist_result",
)
def _run_remote_xdist(remote_mode: str, tmp_path: Path, attach):
    from pytest_bdd_testing.case.external.test_xdist_remote_message_aggregation import (
        run_remote_xdist_compose,
    )

    execnet_mode = _REMOTE_MODE_ALIASES.get(remote_mode, remote_mode)
    result = run_remote_xdist_compose(
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
@then("the distributed run succeeds and a consolidated NDJSON report is produced:")
def _assert_remote_run_succeeds(remote_xdist_result, step=None):
    from cucumber_messages import (
        TestCaseStarted as CucumberTestCaseStarted,  # type: ignore[attr-defined]  # cucumber_messages lacks py.typed
    )

    from pytest_bdd.model.message_validation import validate_message_stream
    from pytest_bdd_testing.tool.message.stream_assertions import (
        count_payload_kinds,
        gateway_modes_for_payloads,
        parse_ndjson_messages,
        worker_ids_for_payloads,
    )

    result = remote_xdist_result["result"]
    report = remote_xdist_result["report"]
    remote_mode = remote_xdist_result["remote_mode"]
    assert_that(result.returncode, equal_to(0), result.stdout + "\n" + result.stderr)
    assert_that(report.exists(), is_(True), f"NDJSON report not found at {report}")
    messages = parse_ndjson_messages(report)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)
    worker_ids = worker_ids_for_payloads(messages, CucumberTestCaseStarted)
    gateway_modes = gateway_modes_for_payloads(messages, CucumberTestCaseStarted)
    expected: dict[str, int] = {}
    data_table = (
        getattr(step.argument, "data_table", None) if step is not None and getattr(step, "argument", None) else None
    )
    if data_table is not None:
        header = [cell.value for cell in data_table.rows[0].cells]
        values = [int(cell.value) for cell in data_table.rows[1].cells]
        expected = dict(zip(header, values, strict=True))
    assert_that(validation_result.status, equal_to("pass"))
    assert_that(payload_counts["meta"], equal_to(1))
    assert_that(payload_counts["test_run_started"], equal_to(1))
    assert_that(payload_counts["test_run_finished"], equal_to(1))
    if "tests" in expected:
        assert_that(payload_counts["test_case_started"], equal_to(expected["tests"]))
    assert_that(len(worker_ids), greater_than_or_equal_to(2))
    assert_that(remote_mode in gateway_modes, is_(True))


@step("pytest outcome must contain tests with statuses:")
def check_pytest_test_statuses(pytest_result, step):
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    outcomes_kwargs = map(attrgetter("value"), data_table.rows[0].cells)
    outcomes_kwargs_values = map(compose(int, attrgetter("value")), data_table.rows[1].cells)
    outcome_result = dict(zip(outcomes_kwargs, outcomes_kwargs_values, strict=False))
    if hasattr(pytest_result, "assert_outcomes"):
        pytest_result.assert_outcomes(**outcome_result)
        return
    parsed_counts = _parse_outcome_counts(pytest_result)
    for outcome_name, expected_count in outcome_result.items():
        assert_that(
            parsed_counts.get(outcome_name, 0),
            equal_to(expected_count),
            combined_result_output(pytest_result),
        )


@step("pytest exits with test failures")
def check_pytest_test_failures(pytest_result):
    assert_that(_coerce_pytest_return_code(pytest_result), equal_to(pytest.ExitCode.TESTS_FAILED))


@step("pytest outcome must match lines:")
def check_pytest_stdout_lines(pytest_result, step):
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    lines = list(map(compose(attrgetter("value"), itemgetter(0)), map(attrgetter("cells"), data_table.rows)))
    stdout_text = _coerce_pytest_stream_text(getattr(pytest_result, "stdout", ""))
    fnmatch_lines = getattr(getattr(pytest_result, "stdout", None), "fnmatch_lines", None)
    if callable(fnmatch_lines):
        fnmatch_lines(lines)
        return
    for line in lines:
        assert_that(re.search(re.escape(line).replace("\\*", ".*"), stdout_text), is_(True), stdout_text)


@when(parsers.parse("run `{command}`"), target_fixture="renderer_result")
def run_command(testdir, command: str, attach) -> subprocess.CompletedProcess[str]:
    command_args = shlex.split(command)
    if command_args and command_args[0] == "python":
        command_args[0] = sys.executable
    env = dict(os.environ)
    repo_root = Path(__file__).resolve().parents[3]
    if len(command_args) > 1 and command_args[0] in {"bash", "sh"}:
        script_path = Path(command_args[1])
        repo_script_path = repo_root / script_path
        env["UV"] = "uv"
        env["UV_PROJECT_ENVIRONMENT"] = "/tmp/pytest-bdd-messages-audit-venv"  # noqa: S108 - WSL bash needs a POSIX venv path outside the Windows project .venv.
        env.pop("VIRTUAL_ENV", None)
        if not script_path.is_absolute() and repo_script_path.exists():
            script_arg = repo_script_path.as_posix()
            if len(script_arg) > 2 and script_arg[1:3] == ":/":
                script_arg = f"/mnt/{script_arg[0].lower()}{script_arg[2:]}"
            command_args[1] = script_arg
        bash_command = " ".join(shlex.quote(arg) for arg in command_args[1:])
        bash_command = f"UV=uv UV_PROJECT_ENVIRONMENT=/tmp/pytest-bdd-messages-audit-venv VIRTUAL_ENV= {bash_command}"
        command_args = [command_args[0], "-lc", bash_command]
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(repo_root / "src"), env.get("PYTHONPATH", "")]))
    result = subprocess.run(command_args, check=False, capture_output=True, text=True, cwd=str(testdir.tmpdir), env=env)
    attach_command_result_outputs(attach, result, label="standalone-renderer", command=command)
    return result


@then("the renderer terminal output includes:")
def renderer_terminal_output_includes(request: pytest.FixtureRequest, step) -> None:  # pylint: disable=E0102  # intentional redefinition for step type
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    lines = [row.cells[0].value for row in data_table.rows]
    output_fragments: list[str] = []
    if "renderer_result" in request.fixturenames:
        renderer_result = request.getfixturevalue("renderer_result")
        output_fragments.extend([renderer_result.stdout, renderer_result.stderr])
    if "pytest_result" in request.fixturenames:
        pytest_result = request.getfixturevalue("pytest_result")
        output_fragments.extend([
            _coerce_pytest_stream_text(getattr(pytest_result, "stdout", "")),
            _coerce_pytest_stream_text(getattr(pytest_result, "stderr", "")),
        ])
    combined_output = "\n".join(fragment for fragment in output_fragments if fragment)
    for line in lines:
        assert_that(bool(re.search(re.escape(line).replace("\\*", ".*"), combined_output)), is_(True), combined_output)


@given(re.compile(r'Copy path from "(?P<initial_path>[^"]+)" to test path "(?P<final_path>[^"]+)"'))
def copy_path(request, testdir: "Testdir", initial_path, final_path):
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
def _(file_path: Path, line_count: int, testdir: "Testdir"):  # pylint: disable=E0102  # intentional redefinition for step type
    output_path = _resolve_test_output_path(testdir, file_path)
    with output_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)
    assert_that(line_count, equal_to(real_line_count))


@then(
    re.compile(r'File "(?P<file_path>[^"]+)" has at least "(?P<line_count>\d+)" lines'),
    converters={"line_count": int, "file_path": Path},
)
def _(file_path: Path, line_count: int, testdir: "Testdir"):  # pylint: disable=E0102  # intentional redefinition for step type
    output_path = _resolve_test_output_path(testdir, file_path)
    with output_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)
    assert_that(real_line_count, greater_than_or_equal_to(line_count))


@then(re.compile(r'File "(?P<file_path>[^"]+)" is not empty'), converters={"file_path": Path})
def _(file_path: Path, testdir):  # pylint: disable=E0102  # intentional redefinition for step type
    assert_that(_resolve_test_output_path(testdir, file_path).stat().st_size, is_not(0))


@then(re.compile(r'HTML report "(?P<file_path>[^"]+)" contains scenario outcomes:'), converters={"file_path": Path})
def _(file_path: Path, testdir, step):  # pylint: disable=E0102  # intentional redefinition for step type
    report_path = _resolve_test_output_path(testdir, file_path)
    parser = _HTMLTextParser()
    parser.feed(report_path.read_text(encoding="utf-8"))
    report_text = parser.text.lower()
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value.lower()
        status = row.cells[1].value.lower()
        assert_that(report_text, contains_string(scenario), parser.text)
        assert_that(report_text, contains_string(status), parser.text)


@then(parsers.parse('File "{file_path}" contains the line "{line}"'))
def file_contains_line(testdir, file_path: str, line: str) -> None:
    output_path = _resolve_test_output_path(testdir, Path(file_path))
    assert_that(output_path.read_text(encoding="utf-8"), contains_string(line))


@then(re.compile(r'Report "(?P<file_path>[^"]+)" parsable into messages'), converters={"file_path": Path})
def _(file_path: Path, testdir: "Testdir"):  # pylint: disable=E0102  # intentional redefinition for step type
    output_path = _resolve_test_output_path(testdir, file_path)
    with output_path.open(mode="r") as ast_file:
        try:
            for raw_datum in ast_file:
                message_converter.from_dict(json.loads(raw_datum), Envelope)
        except Exception as e:
            raise AssertionError from e


@then(
    re.compile(r'JSON file "(?P<file_path>.+)" jq query "(?P<query>.+)" returns "(?P<expected>.+)"'),
    converters={"file_path": Path},
)
def _(file_path: Path, query: str, expected: str, testdir):  # pylint: disable=E0102  # intentional redefinition for step type
    if jq is None:
        pytest.skip("jq package is unavailable on this platform")
    payload = json.loads((Path(str(testdir.tmpdir)) / file_path).read_text(encoding="utf-8"))
    actual = jq.compile(query).input(payload).first()
    assert_that(str(actual), equal_to(expected))


# Backward-compatible re-exports for conftest
collect_ignore_glob = ["_*.feature"]
