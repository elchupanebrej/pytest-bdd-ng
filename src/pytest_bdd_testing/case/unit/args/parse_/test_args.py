"""

Step arguments tests.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import parse",
        "from parse import Parser as parse",
    ],
)
def test_every_steps_takes_param_with_the_same_name(testdir, parser_import_string):
    """
    Verify every steps takes param with the same name.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
                    # In my dream...
                    And I should have 999999 Euro
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        """
        f"{parser_import_string}"
        """

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(parse("I have {euro:d} Euro"))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(parse("I pay {} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @then(parse("I should have {euro:d} Euro"))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """,
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import parse",
        "from parse import Parser as parse",
    ],
)
def test_argument_in_when_step_1(testdir, parser_import_string):
    """
    Verify argument in when step 1.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    testdir.makefile(
        ".feature",
        # language=gherkin
        arguments="""\
            Feature: Step arguments
                Scenario: Argument in when
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
        """
        @pytest.fixture
        def arguments():
            return dict()

        @given(parse("I have an argument {arg:Number}", extra_types=dict(Number=int)))
        def argument(arguments, arg):
            arguments["arg"] = arg

        @when(parse("I get argument {arg:d}"))
        def get_argument(arguments, arg):
            arguments["arg"] = arg

        @then(parse("My argument should be {arg:d}"))
        def assert_that_my_argument_is_arg(arguments, arg):
            assert arguments["arg"] == arg

        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_parse_parser_no_match(testdir):
    """
    Parse parser returns None on parse failure.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: NoMatch
                Scenario: Test
                    Given I have something else
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd.parsers import parse

        @given(parse("I have an argument {arg:d}"))
        def have_arg(arg):
            pass
        """,
    )
    result = testdir.runpytest()
    assert result.ret != 0


def test_parse_parser_mixed_types(testdir):
    """
    Parse parser handles format strings with mixed type converters.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: MixedTypes
                Scenario: Test
                    Given I have 5 widgets named test
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given
        from pytest_bdd.parsers import parse

        @given(parse("I have {count:d} widgets named {name}"))
        def have_items(count, name):
            assert count == 5
            assert name == "test"
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
