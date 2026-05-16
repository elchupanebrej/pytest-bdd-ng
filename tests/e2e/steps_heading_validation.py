from pytest_bdd import given, step, then
from pytest_bdd.model.heading_validation import EMPTY_HEADING_TITLE_CODE


@given("Feature file has empty heading")
def feature_file_empty_heading(testdir):
    content = "# Feature:\n"
    testdir.makefile(".feature.md", empty_heading=content)


@given("Feature file has empty scenario heading")
def feature_file_empty_scenario_heading(testdir):
    content = "# Feature: Valid\n\n## Scenario:\n"
    testdir.makefile(".feature.md", empty_scenario_heading=content)


@then("Heading validation reports EMPTY_HEADING_TITLE")
def heading_validation_reports(pytest_result):
    stdout = pytest_result.stdout.str()
    assert EMPTY_HEADING_TITLE_CODE in stdout


@step("run heading validation", target_fixture="pytest_result")
def run_heading_validation(testdir):
    return testdir.runpytest_inprocess()
