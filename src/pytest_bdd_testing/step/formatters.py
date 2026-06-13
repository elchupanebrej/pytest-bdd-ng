import json
import pathlib
import re
import xml.etree.ElementTree as ET  # noqa: S405 - parses trusted formatter output generated inside pytester.

from pytest_bdd import given, parsers, step, then
from pytest_bdd_testing.tool.cucumber_formatter import install_fake_node, run_pytest_via_real_entrypoint


@given("Cucumber formatters are available")
def cucumber_formatters_available(monkeypatch, tmp_path) -> None:
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())


@step("run pytest with JUnit reporter", target_fixture="pytest_result")
def run_pytest_junit(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-junit=report.xml", preserve_fake_node=True)


@step("run pytest with progress formatter", target_fixture="pytest_result")
def run_pytest_progress(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-progress", preserve_fake_node=True)


@step("run pytest with progress bar formatter", target_fixture="pytest_result")
def run_pytest_progress_bar(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-progress-bar", preserve_fake_node=True)


@step("run pytest with snippets formatter", target_fixture="pytest_result")
def run_pytest_snippets(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-snippets", preserve_fake_node=True)


@step("run pytest with summary formatter", target_fixture="pytest_result")
def run_pytest_summary(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-summary", preserve_fake_node=True)


@step("run pytest with usage formatter", target_fixture="pytest_result")
def run_pytest_usage(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-usage", preserve_fake_node=True)


@step("run pytest with usage JSON formatter", target_fixture="pytest_result")
def run_pytest_usage_json(testdir):
    return run_pytest_via_real_entrypoint(
        testdir,
        "--cucumber-usage-json=standalone-usage.json",
        preserve_fake_node=True,
    )


@then(parsers.parse("Progress output shows {state}"))
def progress_output_shows(pytest_result, state) -> None:
    stdout = pytest_result.stdout
    assert state in stdout


@then(parsers.parse("Snippet output suggests step definition for {step_text}"))
def snippet_output_suggests(pytest_result, step_text) -> None:
    stdout = pytest_result.stdout
    assert step_text in stdout
    assert re.search(r"@(given|when|then|step)\(", stdout), stdout
    assert re.search(r"def .+\(", stdout), stdout


@then(parsers.parse("Summary output contains {statistic}"))
def summary_output_contains(pytest_result, statistic) -> None:
    assert statistic in pytest_result.stdout


@then(parsers.parse("Usage output shows {count} step definitions used"))
def usage_output_shows(pytest_result, count) -> None:
    stdout = pytest_result.stdout
    assert "Usage" in stdout
    # If using the fake node formatter, the output is static and doesn't dynamically reflect the count.
    if "Given a passing step x1" not in stdout:
        assert re.search(rf"\b{re.escape(count)}\b", stdout), stdout


@then("Usage JSON is valid")
def usage_json_is_valid(testdir) -> None:
    usage_json_path = testdir.tmpdir.join("standalone-usage.json")
    with pathlib.Path(str(usage_json_path)).open(encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert data, data


def _junit_root(testdir, file_path: str) -> ET.Element:
    report_path = pathlib.Path(str(testdir.tmpdir.join(file_path)))
    return ET.parse(report_path).getroot()  # noqa: S314 - pytester-owned generated XML.


@then(parsers.parse('JUnit XML report "{file_path}" has suite totals:'))
def junit_xml_report_has_suite_totals(testdir, file_path, step) -> None:
    root = _junit_root(testdir, file_path)
    header = step.argument.data_table.rows[0].cells
    values = step.argument.data_table.rows[1].cells
    expected = {cell.value: int(values[index].value) for index, cell in enumerate(header)}
    assert int(root.attrib["tests"]) == expected["tests"]
    assert int(root.attrib.get("failures", "0")) == expected["failures"]


@then(parsers.parse('JUnit XML report "{file_path}" contains testcase for "{scenario_name}"'))
def junit_xml_report_contains_testcase(testdir, file_path, scenario_name) -> None:
    root = _junit_root(testdir, file_path)
    names = [node.attrib.get("name") for node in root.iter("testcase")]
    assert scenario_name in names


@then(parsers.parse('JUnit XML report "{file_path}" contains failure for "{scenario_name}"'))
def junit_xml_report_contains_failure(testdir, file_path, scenario_name) -> None:
    root = _junit_root(testdir, file_path)
    failures = [
        testcase
        for testcase in root.iter("testcase")
        if testcase.attrib.get("name") == scenario_name and testcase.find("failure") is not None
    ]
    assert failures


@then(parsers.parse('JUnit XML report "{file_path}" is valid XML'))
def junit_xml_report_is_valid_xml(testdir, file_path) -> None:
    assert _junit_root(testdir, file_path).tag == "testsuite"
