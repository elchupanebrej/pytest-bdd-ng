import json
from pathlib import Path

from pytest_bdd import given, parsers, step, then


@step("run pytest with scenario reporter", target_fixture="pytest_result")
def run_pytest_scenario_reporter(testdir, request):
    try:
        feature_file = request.getfixturevalue("feature_file")
        if feature_file is not None:
            return testdir.runpytest_subprocess("-v", str(feature_file))
    except LookupError:
        pass
    return testdir.runpytest_subprocess("-v", "test_sample.py")


@then(parsers.parse('scenario report contains scenario "{scenario_name}"'))
def scenario_report_contains_scenario(testdir, scenario_name) -> None:
    report_path = Path(str(testdir.tmpdir.join("scenario-reports.jsonl")))
    reports = [json.loads(line) for line in report_path.read_text(encoding="utf-8").splitlines()]
    matching = [report for report in reports if report["name"] == scenario_name]
    assert matching
    assert matching[0]["feature"]["name"]


@given("Scenario with attachment", target_fixture="feature_file")
def scenario_with_attachment(testdir):
    return testdir.makefile(
        ".feature.md",
        attachment="""# Feature: Attach
## Scenario: With attach
Given I attach data
""",
    )
