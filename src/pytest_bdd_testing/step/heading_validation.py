from pathlib import Path

from pytest_bdd import given, parsers, step, then


@given("Feature file has empty heading")
def feature_file_empty_heading(testdir) -> None:
    content = "# Feature:\n"
    testdir.makefile(".feature.md", empty_heading=content)


@given("Feature file has empty scenario heading")
def feature_file_empty_scenario_heading(testdir) -> None:
    content = "# Feature: Valid\n\n## Scenario:\n"
    testdir.makefile(".feature.md", empty_scenario_heading=content)


@then("heading validation skips invalid heading")
def heading_validation_skips_invalid_heading(pytest_result) -> None:
    pytest_result.assert_outcomes(skipped=1)


@step("collect feature files", target_fixture="pytest_result")
def collect_feature_files(testdir):
    return testdir.runpytest_inprocess()


@given(parsers.parse('File "{filename}" with content:'))
def file_with_content_heading(testdir, filename, step) -> None:
    doc_string = getattr(step.argument, "doc_string", None) if getattr(step, "argument", None) else None
    content = doc_string.content if doc_string else ""
    target = Path(str(testdir.tmpdir)) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    testdir.makeini("""
[pytest]
bdd_features_base_dir = .
    """)
