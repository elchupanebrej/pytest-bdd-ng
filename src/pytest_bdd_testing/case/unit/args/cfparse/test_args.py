"""

Step arguments tests.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import cfparse",  # Deprecated
        "from parse_type.cfparse import Parser as cfparse",
    ],
)
def test_every_step_takes_param_with_the_same_name(testdir, parser_import_string):
    """
    Test every step takes param with the same name.

    Test target:
        Verify argument extraction, validation, and type conversions to guarantee step definitions receive correct,
        isolated runtime values.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify argument extraction, validation, and type conversions to
        guarantee step definitions receive correct, isolated runtime values., then the expected outcome is produced.
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
        from pytest_bdd import given, when, then
        """
        f"{parser_import_string}"
        """

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(cfparse("I have {euro:d} Euro"))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(cfparse("I pay {} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @then(cfparse("I should have {euro:d} Euro"))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import cfparse",  # Deprecated
        "from parse_type.cfparse import Parser as cfparse",
    ],
)
def test_argument_in_when(testdir, parser_import_string):
    """
    Test step arguments in when steps.

    Test target:
        Verify argument extraction, validation, and type conversions to guarantee step definitions receive correct,
        isolated runtime values.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify argument extraction, validation, and type conversions to
        guarantee step definitions receive correct, isolated runtime values., then the expected outcome is produced.
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

        @given(cfparse("I have an argument {arg:Number}", extra_types=dict(Number=int)))
        def argument(arguments, arg):
            arguments["arg"] = arg

        @when(cfparse("I get argument {arg:d}"))
        def get_argument(arguments, arg):
            arguments["arg"] = arg

        @then(cfparse("My argument should be {arg:d}"))
        def assert_that_my_argument_is_arg(arguments, arg):
            assert arguments["arg"] == arg
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_cfparse_comma_separated(testdir):
    """
    Cfparse parser handles comma-separated values.

    Test target:
        Verify argument extraction, validation, and type conversions to guarantee step definitions receive correct,
        isolated runtime values.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify argument extraction, validation, and type conversions to
        guarantee step definitions receive correct, isolated runtime values., then the expected outcome is produced.
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
            Feature: CommaSeparated
                Scenario: Test
                    Given I have 5 items
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given
        from parse_type.cfparse import Parser as cfparse

        @given(cfparse("I have {count:d} items"))
        def have_items(count):
            assert count == 5
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_cfparse_optional_values(testdir):
    """
    Cfparse parser handles integer type expressions.

    Test target:
        Verify argument extraction, validation, and type conversions to guarantee step definitions receive correct,
        isolated runtime values.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify argument extraction, validation, and type conversions to
        guarantee step definitions receive correct, isolated runtime values., then the expected outcome is produced.
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
            Feature: Integer
                Scenario: Test
                    Given I have 100 items
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given
        from parse_type.cfparse import Parser as cfparse

        @given(cfparse("I have {count:d} items"))
        def have_items(count):
            assert count == 100
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
