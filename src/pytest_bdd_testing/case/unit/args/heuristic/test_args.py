"""

Step arguments tests.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


def test_heuristic_parser(
    testdir,
):
    """
    Verify heuristic parser.

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
                    Given I have a wallet
                    Given I have 6 Euro
                    When I lose 3 Euro
                    And I pay 2 Euro
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

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 0, 999999]

        @given("I have a wallet", param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        @given("I have {int} Euro", anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_have(euro, values):
            assert euro == values.pop(0)


        @when("I pay {} Euro", anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values):
            assert euro == values.pop(0)

        @when("I lose {euro:d} Euro", converters=dict(euro=int))
        def i_pay(euro, values):
            assert euro == values.pop(0)


        @then(r"I should have (\\d+) Euro", anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """,
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_heuristic_parser_fallback_to_re(testdir):
    """
    Heuristic parser falls back to re when other parsers fail.

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
            Feature: Fallback
                Scenario: Test
                    Given I have 42 digits here
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("I have {count:d} digits here")
        def have_pattern(count):
            assert count == 42
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_heuristic_parser_plain_string(testdir):
    """
    Heuristic parser matches plain strings.

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
            Feature: PlainString
                Scenario: Test
                    Given I have a plain string step
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("I have a plain string step")
        def plain_step():
            pass
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_heuristic_parser_with_param_defaults(testdir):
    """
    Heuristic parser uses param_defaults when no params matched.

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
            Feature: ParamDefaults
                Scenario: Test
                    Given I have a default param
            """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("I have a default param", param_defaults={"value": "default"})
        def have_default(value):
            assert value == "default"
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
