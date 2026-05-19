"""Provide test xdist html reporting helpers."""

from __future__ import annotations

import textwrap
from types import SimpleNamespace

import pytest

from pytest_bdd import given, scenario, then, when

from tests.cases.e2e.e2e.test_e2e import _exclude_default_bdd_features

pytestmark = [pytest.mark.xdist, pytest.mark.slow]


@scenario("../../../../tests/e2e/_xdist_html_reporting.feature", "Generate consolidated HTML report from xdist run")
def test_generate_html_report_xdist():
    """Verify generate html report xdist."""


def test_public_xdist_html_report_doc_stays_in_broad_sweep() -> None:
    """Verify public xdist html report doc stays in broad sweep."""
    feature = SimpleNamespace(
        uri="file:07 Report/07 xdist HTML reporting.feature.md",
        feature=SimpleNamespace(name="xdist html reporting", tags=[]),
    )
    pickle = SimpleNamespace(name="single consolidated html report is produced from a distributed xdist run", tags=[])

    assert _exclude_default_bdd_features(None, feature, pickle) is True


@given("a test suite with multiple passing and failing scenarios", target_fixture="test_suite")
def setup_test_suite(testdir, tmp_path):
    """Handle setup test suite."""
    pytest.importorskip("xdist")
    testdir.makeini(
        """\
        [pytest]
        disable_feature_autoload = true
        """,
    )
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
            """,
        ),
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
            """,
        ),
    )
    testdir.makepyfile(
        test_suite="""\
        from pytest_bdd import scenarios

        test_suite = scenarios("test_suite.feature")
        """,
    )
    return tmp_path / "report.html"


@when("I run the test suite with pytest-xdist and request an HTML report", target_fixture="run_xdist_with_html")
def execute_xdist(testdir, test_suite):
    """Execute xdist."""
    html_report_path = test_suite
    result = testdir.runpytest_subprocess(
        "-n",
        "2",
        "--capture=no",
        "--cucumber-html",
        str(html_report_path),
    )
    result.assert_outcomes(passed=3, failed=1)
    return html_report_path


@then("a single HTML report is generated")
def verify_html_report_generated(run_xdist_with_html):
    """Handle verify html report generated."""
    html_report_path = run_xdist_with_html
    assert html_report_path.exists(), "HTML report was not generated"
    assert html_report_path.stat().st_size > 0, "HTML report is empty"


@then("the HTML report contains results from all executed scenarios")
def verify_html_content(run_xdist_with_html):
    """Handle verify html content."""
    html_report_path = run_xdist_with_html
    content = html_report_path.read_text(encoding="utf-8")

    # We expect the HTML report to contain references to the scenarios
    assert "pass one" in content, "Missing 'pass one' scenario in HTML report"
    assert "pass two" in content, "Missing 'pass two' scenario in HTML report"
    assert "pass three" in content, "Missing 'pass three' scenario in HTML report"
    assert "fail four" in content, "Missing 'fail four' scenario in HTML report"
