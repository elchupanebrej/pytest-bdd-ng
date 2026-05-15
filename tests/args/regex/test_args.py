"""Step arguments tests."""

import pytest


@pytest.mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import re as parse_re",
        "from re import compile as parse_re",
    ],
)
def test_every_steps_takes_param_with_the_same_name(testdir, parser_import_string):
    """Verify every steps takes param with the same name."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        arguments="""\
            Feature: Step arguments
                Scenario: Every step takes a parameter with the same name
                    Given I have 1 Euro
                    When I pay 2 Euro
                    And I pay 1 Euro
                    Then I should have 0 Euro
                    And I should have 999999 Euro
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from pytest_bdd import given, when, then
        """
        f"{parser_import_string}"
        r"""
        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(parse_re(r"I have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(parse_re(r"I pay (\d+) Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values):
            assert euro == values.pop(0)

        @then(parse_re(r"I should have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import re as parse_re",
        "from re import compile as parse_re",
    ],
)
def test_argument_in_when(testdir, parser_import_string):
    """Verify argument in when."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        arguments="""\
            Feature: Step arguments
                Scenario: Argument in when, step 1
                    Given I have an argument 1
                    When I get argument 5
                    Then My argument should be 5
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from pytest_bdd import given, when, then
        """
        f"{parser_import_string}"
        r"""
        @pytest.fixture
        def arguments():
            return dict()

        @given(parse_re(r"I have an argument (?P<arg>\d+)"))
        def argument(arguments, arg):
            arguments["arg"] = arg

        @when(parse_re(r"I get argument (?P<arg>\d+)"))
        def get_argument(arguments, arg):
            arguments["arg"] = arg

        @then(parse_re(r"My argument should be (?P<arg>\d+)"))
        def assert_that_my_argument_is_arg(arguments, arg):
            assert arguments["arg"] == arg
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_re_parser_no_match(testdir):
    """Re parser raises when step text does not match."""
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: NoMatch
                Scenario: Test
                    Given I have no match here
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd.parsers import re

        @given(re(r"I have (?P<item>\\w+) Euro"))
        def have_item(item):
            pass
        """,
    )
    result = testdir.runpytest()
    assert result.ret != 0


def test_re_parser_escaped_characters(testdir):
    """Re parser handles escaped regex characters."""
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: Escaped
                Scenario: Test
                    Given I have a (special) item
            """,
    )
    testdir.makeconftest(
        r"""
        from pytest_bdd import given
        from pytest_bdd.parsers import re

        @given(re(r"I have a \(special\) item"))
        def have_special():
            pass
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_re_parser_no_groups(testdir):
    """Re parser returns empty dict for no capture groups."""
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: NoGroups
                Scenario: Test
                    Given I have a simple step
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given
        from pytest_bdd.parsers import re

        @given(re(r"I have a simple step"), target_fixture="result")
        def simple_step():
            return "done"
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_re_parser_anonymous_groups(testdir):
    """Re parser matches with anonymous groups."""
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: AnonymousGroups
                Scenario: Test
                    Given I have 42 items
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given
        from pytest_bdd.parsers import re

        @given(re(r"I have (\\d+) items"), anonymous_group_names=['count'], converters={'count': int})
        def have_items(count):
            assert count == 42
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
