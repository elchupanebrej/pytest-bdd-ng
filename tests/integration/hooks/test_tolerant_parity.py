import json
import subprocess
import sys

import pytest
from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.formatter_replay import replay_messages


def test_ignored_tolerant_failure_preserves_diagnostics_without_failing_report(pytester):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        example="Feature: Example\n  Scenario: Tolerated\n    Given a failing tolerant step\n    Then a later step\n",
    )
    pytester.makeconftest("""
from pytest_cuke import given, then
from pytest_cuke.steps.decorators import tolerant
@given("a failing tolerant step")
@tolerant
def first():
    raise AssertionError("tolerated failure details")
@then("a later step")
def later():
    pass
""")
    pytester.makepyfile(
        test_case="""
from pytest_cuke import scenario
@scenario("example.feature", "Tolerated", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess(
        "--cuke-tolerant-status=ignored", "--cuke-allure=live", "--cuke-messages-ndjson=messages.ndjson", "-q"
    )
    result.assert_outcomes(passed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert [
        event["testStepFinished"]["testStepResult"]["status"] for event in events if "testStepFinished" in event
    ] == ["PASSED", "PASSED"]
    assert "tolerated failure details" in json.dumps(events)
    metadata = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.step-outcome+json"
    ]
    assert len(metadata) == 1
    assert metadata[0]["actualResult"]["status"] == "FAILED"
    assert "tolerated failure details" in metadata[0]["actualResult"]["exception"]["stackTrace"]
    assert metadata[0]["testStepId"] == next(
        event["testStepFinished"]["testStepId"] for event in events if "testStepFinished" in event
    )
    reports = [json.loads(path.read_text()) for path in (pytester.path / "live").glob("*-result.json")]
    assert len(reports) == 1
    assert reports[0]["status"] == "passed"
    assert "tolerated failure details" in reports[0]["steps"][0]["statusDetails"]["message"]
    replay = pytester.runpytest_subprocess("--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replayed", "-q")
    assert replay.ret == 0
    replayed = [json.loads(path.read_text()) for path in (pytester.path / "replayed").glob("*-result.json")]
    assert len(replayed) == 1 and replayed[0]["status"] == "passed"
    diagnostic = pytester.runpytest_subprocess(
        "--cuke-tolerant-status=ignored", "--cuke-tolerated-as-failed", "--cuke-allure=diagnostic", "-q"
    )
    diagnostic.assert_outcomes(passed=1)
    replay_diagnostic = pytester.runpytest_subprocess(
        "--cuke-allure-messages-in=messages.ndjson",
        "--cuke-allure=diagnostic-replay",
        "--cuke-tolerated-as-failed",
        "-q",
    )
    assert replay_diagnostic.ret == 0
    for directory in ("diagnostic", "diagnostic-replay"):
        output = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert len(output) == 1 and output[0]["status"] == "failed"
        assert output[0]["steps"][0]["status"] == "failed"

    source = pytester.path / "messages.ndjson"
    original = source.read_bytes()
    for diagnostic_mode, expected in ((False, "PASSED"), (True, "FAILED")):
        destination = pytester.path / f"formatter-{diagnostic_mode}.ndjson"
        replay_messages(
            source,
            (
                FormatterRequest(
                    name="probe",
                    command=(sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"),
                    output_path=destination,
                    working_directory=pytester.path,
                    timeout_seconds=5,
                ),
            ),
            tolerated_as_failed=diagnostic_mode,
        )
        formatted = [json.loads(line) for line in destination.read_text().splitlines()]
        results = [
            event["testStepFinished"]["testStepResult"]["status"] for event in formatted if "testStepFinished" in event
        ]
        assert results == [expected, "PASSED"]
        assert source.read_bytes() == original

    for name, options, expected_status in (
        ("preset-diagnostic", ("--cuke-report-policy=diagnostic",), "failed"),
        ("preset-override", ("--cuke-report-policy=diagnostic", "--cuke-no-tolerated-as-failed"), "passed"),
        ("normal-override", ("--cuke-report-policy=normal", "--cuke-tolerated-as-failed"), "failed"),
    ):
        result = pytester.runpytest_subprocess(
            "--cuke-allure-messages-in=messages.ndjson", f"--cuke-allure={name}", *options, "-q"
        )
        assert result.ret == 0
        reports = [json.loads(path.read_text()) for path in (pytester.path / name).glob("*-result.json")]
        assert len(reports) == 1 and reports[0]["status"] == expected_status
    assert source.read_bytes() == original

    for name, options, expected_status in (
        ("live-preset", ("--cuke-report-policy=diagnostic",), "failed"),
        ("live-override", ("--cuke-report-policy=diagnostic", "--cuke-no-tolerated-as-failed"), "passed"),
    ):
        result = pytester.runpytest_subprocess(
            "--cuke-tolerant-status=ignored", f"--cuke-allure={name}", *options, "-q"
        )
        result.assert_outcomes(passed=1)
        reports = [json.loads(path.read_text()) for path in (pytester.path / name).glob("*-result.json")]
        assert len(reports) == 1 and reports[0]["status"] == expected_status

    metadata_dir = pytester.path / "probe_formatter-0.0.1.dist-info"
    metadata_dir.mkdir()
    (metadata_dir / "METADATA").write_text("Metadata-Version: 2.1\nName: probe-formatter\nVersion: 0.0.1\n")
    (metadata_dir / "entry_points.txt").write_text("[pytest_cuke.formatters]\nprobe = probe_formatter:request\n")
    (pytester.path / "probe_formatter.py").write_text("""
import sys
from pytest_cuke.formatter_api import FormatterRequest
def request(selection):
    return FormatterRequest(name=selection.name, command=(sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"), output_path=selection.destination, working_directory=selection.working_directory, timeout_seconds=5)
""")
    for name, options, expected in (
        ("cli-preset", ("--report-policy=diagnostic",), "FAILED"),
        ("cli-override", ("--report-policy=diagnostic", "--no-tolerated-as-failed"), "PASSED"),
    ):
        destination = pytester.path / f"{name}.ndjson"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from pytest_cuke.cli import main; raise SystemExit(main())",
                "replay",
                str(source),
                f"--formatter=probe={destination}",
                *options,
            ],
            cwd=pytester.path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        events = [json.loads(line) for line in destination.read_text().splitlines()]
        statuses = [
            event["testStepFinished"]["testStepResult"]["status"] for event in events if "testStepFinished" in event
        ]
        assert statuses == [expected, "PASSED"]
    for name, options, expected_status in (
        ("convert-preset", ("--report-policy=diagnostic",), "failed"),
        ("convert-override", ("--report-policy=diagnostic", "--no-tolerated-as-failed"), "passed"),
    ):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from pytest_cuke.cli import main; raise SystemExit(main())",
                "convert",
                "allure",
                str(source),
                "--output",
                name,
                *options,
            ],
            cwd=pytester.path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        reports = [json.loads(path.read_text()) for path in (pytester.path / name).glob("*-result.json")]
        assert len(reports) == 1 and reports[0]["status"] == expected_status
    assert source.read_bytes() == original

    pytest.importorskip("xdist")
    parallel = pytester.runpytest_subprocess(
        "-n",
        "2",
        "--cuke-tolerant-status=ignored",
        "--cuke-tolerated-as-failed",
        "--cuke-messages-ndjson=parallel.ndjson",
        "--cuke-allure=parallel",
        "-q",
    )
    parallel.assert_outcomes(passed=1)
    parallel_events = [json.loads(line) for line in (pytester.path / "parallel.ndjson").read_text().splitlines()]
    parallel_metadata = [
        json.loads(event["attachment"]["body"])
        for event in parallel_events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.step-outcome+json"
    ]
    assert len(parallel_metadata) == 1
    assert any(
        event.get("testStepFinished", {}).get("testStepId") == parallel_metadata[0]["testStepId"]
        and event["testStepFinished"]["testCaseStartedId"] == parallel_metadata[0]["testCaseStartedId"]
        for event in parallel_events
    )
    parallel_reports = [json.loads(path.read_text()) for path in (pytester.path / "parallel").glob("*-result.json")]
    assert len(parallel_reports) == 1 and parallel_reports[0]["status"] == "failed"
