import json
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "options,expected_wip,expected_skip",
    [
        ((), "skipped", "skipped"),
        (("--cuke-wip-as-failed",), "failed", "skipped"),
        (("--cuke-skip-as-failed",), "skipped", "failed"),
        (("--cuke-report-policy=diagnostic",), "failed", "failed"),
        (("--cuke-report-policy=diagnostic", "--cuke-no-wip-as-failed"), "skipped", "failed"),
    ],
)
def test_wip_report_policy_is_independent_of_ordinary_skip(pytester, options, expected_wip, expected_skip):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        example="Feature: Example\n  Scenario: Wip\n    Given pending work\n  Scenario: Ordinary\n    Given pending work\n",
    )
    pytester.makeconftest("""
from pytest_cuke import given
from pytest_cuke.steps.decorators import not_implemented
@given("pending work")
@not_implemented
def pending():
    raise AssertionError("must not execute")
""")
    pytester.makepyfile(
        test_cases="""
import pytest
from pytest_cuke import scenario
@scenario("example.feature", "Wip", features_base_dir=".")
def test_wip():
    pass
@pytest.mark.skip(reason="ordinary skip")
@scenario("example.feature", "Ordinary", features_base_dir=".")
def test_skip():
    pass
"""
    )
    live = pytester.runpytest_subprocess(
        "--cuke-wip-status=skipped", "--cuke-allure=live", "--cuke-messages-ndjson=messages.ndjson", *options, "-q"
    )
    live.assert_outcomes(skipped=2)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    wip_metadata = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.step-outcome+json"
    ]
    assert len(wip_metadata) == 1 and wip_metadata[0]["outcome"] == "wip-skipped"
    assert "actualResult" not in wip_metadata[0]
    assert all(
        event["testStepFinished"]["testStepResult"]["status"] == "SKIPPED"
        for event in events
        if "testStepFinished" in event
    )
    replay = pytester.runpytest_subprocess(
        "--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replay", *options, "-q"
    )
    assert replay.ret == 0
    cli = subprocess.run(
        [
            sys.executable,
            "-c",
            "from pytest_cuke.cli import main; raise SystemExit(main())",
            "convert",
            "allure",
            "messages.ndjson",
            "--output=converted",
            *(option.replace("--cuke-", "--", 1) for option in options),
        ],
        cwd=pytester.path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
    for directory in ("live", "replay", "converted"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert {report["name"]: report["status"] for report in reports} == {
            "Wip": expected_wip,
            "Ordinary": expected_skip,
        }
    if options == ("--cuke-wip-as-failed",):
        pytest.importorskip("xdist")
        parallel = pytester.runpytest_subprocess(
            "-n",
            "2",
            "--cuke-wip-status=skipped",
            "--cuke-wip-as-failed",
            "--cuke-allure=parallel",
            "--cuke-messages-ndjson=parallel.ndjson",
            "-q",
        )
        parallel.assert_outcomes(skipped=2)
        reports = [json.loads(path.read_text()) for path in (pytester.path / "parallel").glob("*-result.json")]
        assert {report["name"]: report["status"] for report in reports} == {"Wip": "failed", "Ordinary": "skipped"}


@pytest.mark.parametrize("arguments,expected", [((), "failed"), (("--cuke-wip-status=skipped",), "skipped")])
def test_not_implemented_never_executes_body(pytester, arguments, expected):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Pending\n    Given pending work\n")
    pytester.makeconftest("""
from pathlib import Path
from pytest_cuke import given
from pytest_cuke.steps.decorators import not_implemented
@given("pending work")
@not_implemented
def pending():
    Path("body-executed").touch()
""")
    pytester.makepyfile(
        test_pending="""
from pytest_cuke import scenario
@scenario("example.feature", "Pending", features_base_dir=".")
def test_pending():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", *arguments, "-q")
    result.assert_outcomes(**{expected: 1})
    assert not (pytester.path / "body-executed").exists()
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    finished = [event["testStepFinished"] for event in events if "testStepFinished" in event]
    assert len(finished) == 1
    assert finished[0]["testStepResult"]["status"] == expected.upper()


def test_invalid_local_wip_policy_is_an_error(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Pending\n    Given pending work\n")
    pytester.makeconftest("""
from pytest_cuke import given
from pytest_cuke.steps.decorators import not_implemented
@given("pending work")
@not_implemented
def pending():
    pass
""")
    pytester.makepyfile(
        test_pending="""
import pytest
from pytest_cuke import scenario
@pytest.mark.wip_status("invalid")
@scenario("example.feature", "Pending", features_base_dir=".")
def test_pending():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-wip-status=skipped", "-q")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*Invalid*wip_status*invalid*"])


def test_successful_wip_policy_is_rejected(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\n")
    result = pytester.runpytest_subprocess("--cuke-wip-status=passed", "-q")
    assert result.ret == 4
    result.stderr.fnmatch_lines(["*invalid choice*passed*"])


def test_local_wip_policy_overrides_cli(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Pending\n    Given pending work\n")
    pytester.makeconftest("""
from pathlib import Path
from pytest_cuke import given
from pytest_cuke.steps.decorators import not_implemented
@given("pending work")
@not_implemented
def pending():
    Path("body-executed").touch()
""")
    pytester.makepyfile(
        test_pending="""
import pytest
from pytest_cuke import scenario
@pytest.mark.wip_status("failed")
@scenario("example.feature", "Pending", features_base_dir=".")
def test_pending():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-wip-status=skipped", "-q")
    result.assert_outcomes(failed=1)
    assert not (pytester.path / "body-executed").exists()
