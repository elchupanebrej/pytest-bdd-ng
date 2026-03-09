import json
import os
import re
import shutil
import subprocess  # noqa: S404
import string
import tempfile
from functools import reduce
from operator import attrgetter, itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

# Prevent the private fixture feature file from being collected as a standalone test.
# It is only exercised via @scenario in test_xdist_html_reporting.py.
collect_ignore_glob = ["_*.feature"]

import pytest
from cucumber_messages import Envelope  # type:ignore[attr-defined]
from pytest_httpserver import HTTPServer

from pytest_bdd import given, step, then
from pytest_bdd.compatibility.pytest import assert_outcomes
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model import message_converter
from pytest_bdd.util.data_table import data_table_to_dicts
from pytest_bdd.util.toolz_extra import compose

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir

try:
    import jq  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - platform-specific availability
    jq = None


@pytest.fixture
def httpserver_port(httpserver):
    return httpserver.port


@given(re.compile(r"File \"(?P<name>(\.|\w)+)(?P<extension>\.\w+)\" with (?P<extra_opts>.*|\s)content:"))
def write_file_with_extras(name, extension, testdir, step, request, extra_opts):
    content = step.doc_string.content
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
    content = step.doc_string.content
    (tmp_path / f"{name}{extension}").write_text(content)


@given(
    re.compile(r'Localserver endpoint "(?P<endpoint>.+)" responding content:'),
)
def test_feature_load_by_http_with_base_url(endpoint, httpserver: HTTPServer, step):
    httpserver.expect_request(endpoint).respond_with_data(
        step.doc_string.content,
        content_type=Mimetype.gherkin_plain.value,
    )
    yield


@given(re.compile(r"Set pytest.ini content to:"))
def _(testdir, step):
    content = step.doc_string.content
    testdir.makeini(content)


@step("run pytest", target_fixture="pytest_result")
def run_pytest(testdir: "Testdir", step):
    options_dict = data_table_to_dicts(step.data_table)
    testrunner = (
        testdir.runpytest_inprocess if options_dict.get("subprocess", [False])[0] == "true" else testdir.runpytest
    )

    outcome = testrunner(*options_dict.get("cli_args", []))

    yield outcome


@given("Install npm packages")
def _(testdir: "Testdir", step):
    options_dict = data_table_to_dicts(step.data_table)
    yield testdir.run(shutil.which("npm"), "install", "--silent", *options_dict.get("packages", []))


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
    if shutil.which("docker") is None:
        pytest.skip("Docker is unavailable.")


@step(
    re.compile(r'run pytest across xdist workers over (?P<remote_mode>\w+) gateway'),
    target_fixture="remote_xdist_result",
)
def _run_remote_xdist(remote_mode: str, tmp_path: Path):
    execnet_mode = _REMOTE_MODE_ALIASES.get(remote_mode, remote_mode)
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="pytest-bdd-remote-artifacts-", dir=repo_root) as artifact_dir:
        env = {
            **os.environ,
            "BUILDKIT_PROGRESS": "plain",
            "REPO_ROOT": str(repo_root),
            "ARTIFACT_DIR": artifact_dir,
            "REPORT_NAME": _REMOTE_XDIST_REPORT_NAME,
            "VERIFY_REPORT_MODE": "success",
            "PYTEST_REMOTE_MODE": execnet_mode,
            "PYTEST_BDD_MESSAGES_FAIL_WORKERS": "",
            "COMPOSE_PROJECT_NAME": (
                f"pytestbddremote{execnet_mode}{tmp_path.name.replace('-', '').replace('_', '')}"
            ).lower(),
        }
        compose_cmd = [
            "docker",
            "compose",
            "-f",
            str(_REMOTE_XDIST_FIXTURE_DIR / "docker-compose.yml"),
        ]
        try:
            result = subprocess.run(  # noqa: S603
                [*compose_cmd, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "controller"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
        finally:
            subprocess.run(  # noqa: S603
                [*compose_cmd, "down", "--volumes", "--remove-orphans"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )

        artifact_report = Path(artifact_dir, _REMOTE_XDIST_REPORT_NAME)
        dest = tmp_path / _REMOTE_XDIST_REPORT_NAME
        if artifact_report.exists():
            shutil.copy2(artifact_report, dest)
    return {"result": result, "report": dest, "remote_mode": execnet_mode}


@then("the distributed run succeeds and a consolidated NDJSON report is produced")
def _assert_remote_run_succeeds(remote_xdist_result):
    from tests.messages.message_stream_assertions import (
        count_payload_kinds,
        gateway_modes_for_payloads,
        parse_ndjson_messages,
        worker_ids_for_payloads,
    )
    from pytest_bdd.model.message_validation import validate_message_stream
    from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

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
    outcomes_kwargs = map(attrgetter("value"), step.data_table.rows[0].cells)
    outcomes_kwargs_values = map(compose(int, attrgetter("value")), step.data_table.rows[1].cells)
    outcome_result = dict(zip(outcomes_kwargs, outcomes_kwargs_values, strict=False))

    assert_outcomes(pytest_result, **outcome_result)


@step("pytest outcome must match lines:")
def check_pytest_stdout_lines(pytest_result, step):
    lines = list(
        map(
            compose(attrgetter("value"), itemgetter(0)),
            map(attrgetter("cells"), step.data_table.rows),
        )
    )

    pytest_result.stdout.fnmatch_lines(lines)


@given(re.compile(r"Copy path from \"(?P<initial_path>(\w|\\|.)+)\" to test path \"(?P<final_path>(\w|\\|.)+)\""))
def copy_path(request, testdir: "Testdir", initial_path, final_path):
    full_initial_path = (Path(request.config.rootdir) / Path(initial_path).as_posix()).resolve(strict=True)
    full_final_path = Path(testdir.tmpdir) / Path(final_path).as_posix()
    if full_initial_path.is_file():
        full_final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(full_initial_path, full_final_path)
    else:
        shutil.copytree(full_initial_path, full_final_path, dirs_exist_ok=True)


@then(
    re.compile(r"File \"(?P<file_path>(\w|\\|.)+)\" has \"(?P<line_count>(\w|\\|.)+)\" lines"),
    converters={"line_count": int, "file_path": Path},
)
def _(file_path: Path, line_count: int):
    with file_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)  # type: ignore[no-any-return]
    assert line_count == real_line_count


@then(
    re.compile(r"File \"(?P<file_path>(\w|\\|.)+)\" has at least \"(?P<line_count>(\w|\\|.)+)\" lines"),
    converters={"line_count": int, "file_path": Path},
)
def _(file_path: Path, line_count: int):
    with file_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)  # type: ignore[no-any-return]
    assert real_line_count >= line_count


@then(
    re.compile(r"File \"(?P<file_path>(\w|\\|.)+)\" is not empty"),
    converters={"file_path": Path},
)
def _(file_path: Path, testdir):
    assert (Path(str(testdir.tmpdir)) / file_path).stat().st_size != 0


@then(
    re.compile(r"Report \"(?P<file_path>(\w|\\|.)+)\" parsable into messages"),
    converters={"file_path": Path},
)
def _(file_path: Path):
    with file_path.open(mode="r") as ast_file:
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
