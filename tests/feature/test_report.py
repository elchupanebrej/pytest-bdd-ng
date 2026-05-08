"""Test scenario reporting."""

import re
from pathlib import Path

import execnet.gateway_base
import pytest

from pytest_bdd.plugin.gherkin_terminal_reporter.plugin import canonical_terminal_step_status
from pytest_bdd.plugin.scenario_reporter.report import normalize_runtime_step_status
from pytest_bdd.util.toolz_test import InstanceOfType

pytestmark = [pytest.mark.technical_nonconvertible]


def test_status_terminology_normalization_is_shared_between_reporters() -> None:
    """Verify status terminology normalization is shared between reporters."""
    assert normalize_runtime_step_status("passed", failed_fallback=False) == "passed"
    assert normalize_runtime_step_status("FAILED", failed_fallback=False) == "failed"
    assert canonical_terminal_step_status({"status": "passed", "failed": False}) == "passed"
    assert canonical_terminal_step_status({"status": "FAILED", "failed": False}) == "failed"
    assert canonical_terminal_step_status({"failed": True}) == "failed"


def matchreport(
    result,
    inamepart_match: str | re.Pattern = "",
    names="pytest_runtest_logreport pytest_collectreport",
    when=None,
):
    """Return a testreport whose dotted import path matches.

    Raises:
        ValueError: If no report or more than one report matches.
    """
    values = []
    for rep in result.getreports(names=names):
        if not when and rep.when != "call" and rep.passed:
            # setup/teardown passing reports - let's ignore those
            continue
        if when and rep.when != when:
            continue
        iname_parts = rep.nodeid.split("::")
        if (
            not inamepart_match
            or inamepart_match in iname_parts
            or (isinstance(inamepart_match, re.Pattern) and any(map(inamepart_match.match, iname_parts)))
        ):
            values.append(rep)
    # TODO: use extracted exceptions
    if not values:
        msg = f"Could not find test report matching {inamepart_match}: no test reports at all!"
        raise ValueError(msg)
    if len(values) > 1:
        msg = f"Found 2 or more testreports matching {inamepart_match!r}: {values}"
        raise ValueError(msg)
    return values[0]


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile(
        ".ini",
        pytest="""\
            [pytest]
            markers =
                feature-tag
                scenario-passing-tag
                scenario-failing-tag
            """,
    )
    feature = testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
            @feature-tag
            Feature: One passing scenario, one failing scenario

                @scenario-passing-tag
                Scenario: Passing
                    Given a passing step
                    And some other passing step

                @scenario-failing-tag
                Scenario: Failing
                    Given a passing step
                    And a failing step

                Scenario Outline: Outlined
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |
                    |  5    |  4  |  1   |
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, when, then, parsers

        @given('a passing step')
        def a_passing_step():
            return 'pass'

        @given('some other passing step')
        def some_other_passing_step():
            return 'pass'

        @given('a failing step')
        def a_failing_step():
            raise Exception('Error')

        @given(parsers.parse('there are {start:d} cucumbers'), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            assert isinstance(start, int)
            return {"start": start}

        @when(parsers.parse('I eat {eat:g} cucumbers'))
        def eat_cucumbers(start_cucumbers, eat):
            assert isinstance(eat, float)
            start_cucumbers['eat'] = eat

        @then(parsers.parse('I should have {left} cucumbers'))
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            assert isinstance(left, str)
            assert start - eat == int(left)
            assert start_cucumbers['start'] == start
            assert start_cucumbers['eat'] == eat
        """,
    )
    result = testdir.inline_run("-vvl")
    assert result.ret

    report = matchreport(
        result,
        re.compile(r"test.*\[file:test\.feature-One passing scenario, one failing scenario-Passing\]"),
        when="call",
    ).scenario
    expected = {
        "feature": {
            "description": "",
            "filename": Path(feature.strpath).as_posix(),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": "test.feature",
            "tags": ["feature-tag"],
        },
        "line_number": 5,
        "name": "Passing",
        "steps": [
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "Given",
                "line_number": 6,
                "name": "a passing step",
                "type": "given",
            },
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "And",
                "line_number": 7,
                "name": "some other passing step",
                "type": "and",
            },
        ],
        "tags": ["scenario-passing-tag"],
    }

    assert report == expected

    report = matchreport(
        result,
        re.compile(r"test.*\[file:test.feature-One passing scenario, one failing scenario-Failing]"),
        when="call",
    ).scenario
    expected = {
        "feature": {
            "description": "",
            "filename": Path(feature.strpath).as_posix(),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": "test.feature",
            "tags": ["feature-tag"],
        },
        "line_number": 10,
        "name": "Failing",
        "steps": [
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "Given",
                "line_number": 11,
                "name": "a passing step",
                "type": "given",
            },
            {
                "duration": InstanceOfType(float),
                "failed": True,
                "status": "failed",
                "keyword": "And",
                "line_number": 12,
                "name": "a failing step",
                "type": "and",
            },
        ],
        "tags": ["scenario-failing-tag"],
    }
    assert report == expected

    report = matchreport(
        result,
        re.compile(
            r"test.*\[file:test\.feature-One passing scenario, one failing scenario-Outlined\[table_rows:\[line: 21]]]",
        ),
        when="call",
    ).scenario
    expected = {
        "feature": {
            "description": "",
            "filename": Path(feature.strpath).as_posix(),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": "test.feature",
            "tags": ["feature-tag"],
        },
        "line_number": 14,
        "name": "Outlined",
        "steps": [
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "Given",
                "line_number": 15,
                "name": "there are 12 cucumbers",
                "type": "given",
            },
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "When",
                "line_number": 16,
                "name": "I eat 5 cucumbers",
                "type": "when",
            },
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "Then",
                "line_number": 17,
                "name": "I should have 7 cucumbers",
                "type": "then",
            },
        ],
        "tags": [],
    }
    assert report == expected

    report = matchreport(
        result,
        re.compile(
            r"test.*\[file:test\.feature-One passing scenario, one failing scenario-Outlined\[table_rows:\[line: 22]]]",
        ),
        when="call",
    ).scenario
    expected = {
        "feature": {
            "description": "",
            "filename": Path(feature.strpath).as_posix(),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": "test.feature",
            "tags": ["feature-tag"],
        },
        "line_number": 14,
        "name": "Outlined",
        "steps": [
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "Given",
                "line_number": 15,
                "name": "there are 5 cucumbers",
                "type": "given",
            },
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "When",
                "line_number": 16,
                "name": "I eat 4 cucumbers",
                "type": "when",
            },
            {
                "duration": InstanceOfType(float),
                "failed": False,
                "status": "passed",
                "keyword": "Then",
                "line_number": 17,
                "name": "I should have 1 cucumbers",
                "type": "then",
            },
        ],
        "tags": [],
    }
    assert report == expected


def test_complex_types(testdir):
    """Test serialization of the complex types."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
            Feature: Report serialization containing parameters of complex types

            Scenario Outline: Complex
                Given there is a coordinate <point>

                Examples:
                |  point  |
                |  10,20  |
            """,
    )
    testdir.makepyfile(
        # language=python
        """\
        import pytest
        from pytest_bdd import given,  scenario, parsers

        class Point:

            def __init__(self, x, y):
                self.x = x
                self.y = y

            @classmethod
            def parse(cls, value):
                return cls(*(int(x) for x in value.split(',')))

        class Alien(object):
            pass

        @given(
            parsers.parse('there is a coordinate {point}'),
            target_fixture="point",
            converters={"point": Point.parse},
        )
        def given_there_is_a_point(point):
            assert isinstance(point, Point)
            return point

        @pytest.mark.parametrize('alien', [Alien()])
        @scenario('test.feature', 'Complex')
        def test_complex(alien):
            pass
        """,
    )
    result = testdir.inline_run("-vvl")
    report = matchreport(
        result,
        re.compile(
            r"test_complex.*\["
            r"file:test\.feature-Report serialization containing parameters of complex types-"
            r"Complex\[table_rows:\[line: 8]]-alien0"
            r"]",
        ),
        when="call",
    )
    assert report.passed
    assert execnet.gateway_base.dumps(report.item)
    assert execnet.gateway_base.dumps(report.scenario)


def test_missing_step_and_failed_step_have_completion_reports(testdir):
    """Verify missing step and failed step have completion reports."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
        Feature: mixed completion paths

            Scenario: failing step scenario
                Given a failing step

            Scenario: missing step scenario
                Given a missing step
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("a failing step")
        def failing_step():
            raise RuntimeError("expected failure")
        """,
    )

    result = testdir.inline_run("-vvl")
    assert result.ret

    failing_report = matchreport(
        result,
        re.compile(r".*failing step scenario]"),
        when="call",
    ).scenario
    missing_report = matchreport(
        result,
        re.compile(r".*missing step scenario]"),
        when="call",
    ).scenario

    assert any(step["failed"] for step in failing_report["steps"])
    assert missing_report["name"] == "missing step scenario"
    assert missing_report["feature"]["name"] == "mixed completion paths"
    assert isinstance(missing_report["steps"], list)
