from __future__ import annotations

import pytest
import textwrap
from pathlib import Path
from pytest_bdd import given, when, then, scenario

@scenario("../tests/e2e/_xdist_html_reporting.feature", "Generate consolidated HTML report from xdist run")
def test_generate_html_report_xdist():
    pass

@given("a test suite with multiple passing and failing scenarios", target_fixture="test_suite")
def setup_test_suite(testdir, tmp_path):
    pytest.importorskip("xdist")
    testdir.makefile(
        ".feature",
        test_suite=textwrap.dedent(
            """
            Feature: example suite
              Scenario: pass one
                Given a passing step
              Scenario: pass two
                Given a passing step
              Scenario: pass three
                Given a passing step
              Scenario: fail four
                Given a failing step
            """
        )
    )
    testdir.makeconftest(
        textwrap.dedent(
            """
            from pytest_bdd import given
    
            @given("a passing step")
            def _pass():
                return "ok"
    
            @given("a failing step")
            def _fail():
                raise RuntimeError("boom")
            """
        )
    )
    html_report_path = tmp_path / "report.html"
    return html_report_path


@when("I run the test suite with pytest-xdist and request an HTML report", target_fixture="run_xdist_with_html")
def execute_xdist(testdir, test_suite):
    html_report_path = test_suite
    result = testdir.runpytest_subprocess(
        "-n", "2",
        "--cucumber-html", str(html_report_path),
    )
    result.assert_outcomes(passed=3, failed=1)
    return html_report_path


@then("a single HTML report is generated")
def verify_html_report_generated(run_xdist_with_html):
    html_report_path = run_xdist_with_html
    assert html_report_path.exists(), "HTML report was not generated"
    assert html_report_path.stat().st_size > 0, "HTML report is empty"


@then("the HTML report contains results from all executed scenarios")
def verify_html_content(run_xdist_with_html):
    html_report_path = run_xdist_with_html
    content = html_report_path.read_text(encoding="utf-8")
    
    # We expect the HTML report to contain references to the scenarios
    assert "pass one" in content, "Missing 'pass one' scenario in HTML report"
    assert "pass two" in content, "Missing 'pass two' scenario in HTML report"
    assert "pass three" in content, "Missing 'pass three' scenario in HTML report"
    assert "fail four" in content, "Missing 'fail four' scenario in HTML report"
