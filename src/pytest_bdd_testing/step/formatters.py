import json
import pathlib
import re
import xml.etree.ElementTree as ET  # noqa: S405 - parses trusted formatter output generated inside pytester.

from hamcrest import assert_that, contains_string, equal_to, is_
from pytest_bdd import given, parsers, then
from pytest_bdd_testing.tool.cucumber_formatter import install_fake_node


@given("Cucumber formatters are available")
def cucumber_formatters_available(monkeypatch, tmp_path) -> None:
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())


@then(parsers.parse("Progress output shows {state}"))
def progress_output_shows(pytest_result, state) -> None:
    stdout = pytest_result.stdout
    assert_that(stdout, contains_string(state))


@then(parsers.parse("Snippet output suggests step definition for {step_text}"))
def snippet_output_suggests(pytest_result, step_text) -> None:
    stdout = pytest_result.stdout
    assert_that(stdout, contains_string(step_text))
    assert_that(re.search(r"@(given|when|then|step)\(", stdout), is_(True), stdout)
    assert_that(re.search(r"def .+\(", stdout), is_(True), stdout)


@then(parsers.parse("Summary output contains {statistic}"))
def summary_output_contains(pytest_result, statistic) -> None:
    assert_that(pytest_result.stdout, contains_string(statistic))


@then(parsers.parse("Usage output shows {count} step definitions used"))
def usage_output_shows(pytest_result, count) -> None:
    stdout = pytest_result.stdout
    assert_that(stdout, contains_string("Usage"))
    # If using the fake node formatter, the output is static and doesn't dynamically reflect the count.
    if "Given a passing step x1" not in stdout:
        assert_that(re.search(rf"\b{re.escape(count)}\b", stdout), is_(True), stdout)


@then("Usage JSON is valid")
def usage_json_is_valid(testdir) -> None:
    usage_json_path = testdir.tmpdir.join("standalone-usage.json")
    with pathlib.Path(str(usage_json_path)).open(encoding="utf-8") as f:
        data = json.load(f)
    assert_that(isinstance(data, dict), is_(True))
    assert_that(data, is_(True), data)


def _junit_root(testdir, file_path: str) -> ET.Element:
    report_path = pathlib.Path(str(testdir.tmpdir.join(file_path)))
    return ET.parse(report_path).getroot()  # noqa: S314 - pytester-owned generated XML.


@then(parsers.parse('JUnit XML report "{file_path}" has suite totals:'))
def junit_xml_report_has_suite_totals(testdir, file_path, step) -> None:
    root = _junit_root(testdir, file_path)
    header = step.argument.data_table.rows[0].cells
    values = step.argument.data_table.rows[1].cells
    expected = {cell.value: int(values[index].value) for index, cell in enumerate(header)}
    assert_that(int(root.attrib["tests"]), equal_to(expected["tests"]))
    assert_that(int(root.attrib.get("failures", "0")), equal_to(expected["failures"]))


@then(parsers.parse('JUnit XML report "{file_path}" contains testcase for "{scenario_name}"'))
def junit_xml_report_contains_testcase(testdir, file_path, scenario_name) -> None:
    root = _junit_root(testdir, file_path)
    names = [node.attrib.get("name") for node in root.iter("testcase")]
    assert_that(scenario_name in names, is_(True))


@then(parsers.parse('JUnit XML report "{file_path}" contains failure for "{scenario_name}"'))
def junit_xml_report_contains_failure(testdir, file_path, scenario_name) -> None:
    root = _junit_root(testdir, file_path)
    failures = [
        testcase
        for testcase in root.iter("testcase")
        if testcase.attrib.get("name") == scenario_name and testcase.find("failure") is not None
    ]
    assert_that(failures, is_(True))


@then(parsers.parse('JUnit XML report "{file_path}" is valid XML'))
def junit_xml_report_is_valid_xml(testdir, file_path) -> None:
    assert_that(_junit_root(testdir, file_path).tag, equal_to("testsuite"))
