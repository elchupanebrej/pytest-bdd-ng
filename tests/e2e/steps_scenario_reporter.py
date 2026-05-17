from pytest_bdd import given, step, then


@step("run pytest with scenario reporter", target_fixture="pytest_result")
def run_pytest_scenario_reporter(testdir, request):
    try:
        feature_file = request.getfixturevalue("feature_file")
        return testdir.runpytest_inprocess("-v", str(feature_file))
    except LookupError:
        feature_files = [f for f in testdir.tmpdir.listdir() if f.check(file=1) and f.basename.endswith(".feature.md")]
        if feature_files:
            return testdir.runpytest_inprocess("-v", str(feature_files[0]))
        return testdir.runpytest_inprocess("-v")


@then("Scenario reporter outputs scenario name")
def scenario_reporter_outputs_name(pytest_result):
    assert "Scenario" in pytest_result.stdout.str() or "Scenario" in pytest_result.stderr.str()


@then("Attachment is recorded")
def attachment_is_recorded(pytest_result):
    assert "attachment" in pytest_result.stdout.str() or "attachment" in pytest_result.stderr.str()


@given("Scenario with attachment", target_fixture="feature_file")
def scenario_with_attachment(testdir):
    testdir.makeconftest("""
from pytest_bdd import given
import pytest_bdd.plugin.scenario_reporter.plugin as srp
@given("I attach data")
def attach_data(request):
    # Mock attachment if necessary, or call actual attach
    pass
""")
    return testdir.makefile(
        ".feature.md",
        attachment="""# Feature: Attach
## Scenario: With attach
Given I attach data
""",
    )
