"""

Test step matching ambiguity detection and resolution.
"""


def test_two_strict_same_type_warning_and_first_wins(testdir):
    """
    Two strict definitions of same type for same text: warning emitted,
                first-registered definition wins.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given

        @given("an ambiguous step")
        def first_definition():
            return "first"

        @given("an ambiguous step")
        def second_definition():
            return "second"
        """,
    )
    testdir.makefile(
        ".feature",
        test_ambiguous="""\
            Feature: Ambiguous definitions
                Scenario: Ambiguous step
                    Given an ambiguous step
        """,
    )
    result = testdir.runpytest("-v", "-W", "ignore::pytest_bdd.PytestBDDStepDefinitionWarning")
    result.assert_outcomes(passed=1)


def test_conftest_parent_child_precedence(testdir):
    """
    Child conftest definition takes precedence over parent conftest.

    Test target:
        Enforce step definition precedence rules to resolve execution ambiguity deterministically.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Enforce step definition precedence rules to resolve execution
        ambiguity deterministically., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given

        @given("a shared step", target_fixture="result")
        def parent_step():
            return "parent"
        """,
    )
    subdir = testdir.mkdir("sub")
    subdir.join("conftest.py").write(
        """
from pytest_bdd import given, then

@given("a shared step", target_fixture="result")
def child_step():
    return "child"

@then("a shared step")
def check_child(result):
    assert result == "child"
""",
    )
    subdir.join("test_child_precedence.feature").write(
        """\
Feature: Child precedence
    Scenario: Child definition wins
        Given a shared step
        Then a shared step
""",
    )
    subdir.join("test_child_precedence.py").write(
        """
from pytest_bdd import scenario

@scenario("test_child_precedence.feature", "Child definition wins")
def test_child_precedence():
    pass
""",
    )
    result = testdir.runpytest("sub/", "-v")
    result.assert_outcomes(passed=1, skipped=1)


def test_undefined_step_raises_error(testdir):
    """
    Step with no matching definition raises StepDefinitionNotFoundError
                and the scenario fails.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
        undefined="""\
            Feature: Undefined steps
                Scenario: Missing step definition
                    Given I am not defined anywhere
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Missing step definition")
        def test_undefined():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # The feature test fails, and the @scenario test is skipped
    result.assert_outcomes(failed=1, skipped=1)


def test_liberal_step_without_liberal_flag_no_match(testdir):
    """
    Liberal step definition does NOT match when liberal_steps is disabled
                and step type differs from keyword.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, scenario, when

        @when("a liberal action step")
        def when_action():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        test_liberal_disabled="""\
            Feature: Liberal disabled
                Scenario: Liberal step not matched by Given
                    Given a liberal action step
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Liberal step not matched by Given")
        def test_liberal_disabled():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Feature test fails, @scenario test is skipped
    result.assert_outcomes(failed=1, skipped=1)


def test_liberal_step_with_ini_option_enabled(testdir):
    """
    Liberal step definition matches when liberal_steps ini option is set.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    testdir.makeini(
        """
        [pytest]
        liberal_steps = True
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given, scenario, when

        @when("a liberal step", liberal=True)
        def liberal_step():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        test_liberal_enabled="""\
            Feature: Liberal enabled via ini
                Scenario: Liberal step matches Given
                    Given a liberal step
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Liberal step matches Given")
        def test_liberal_enabled():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Both feature test and @scenario test run; feature passes, @scenario is skipped
    result.assert_outcomes(passed=1, skipped=1)


def test_step_not_found_error_message_is_helpful(testdir):
    """
    Undefined step error message includes the step text.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
        test_helpful_error="""\
            Feature: Helpful error message
                Scenario: Missing step
                    Given this step does not exist in any conftest
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Missing step")
        def test_missing():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(failed=1, skipped=1)
    result.stdout.fnmatch_lines("*this step does not exist in any conftest*")


def test_step_with_regex_metacharacters(testdir):
    """
    Step patterns with regex metacharacters are handled safely.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, parsers, then

        @given(parsers.re("I have \\\\d+ items"))
        def i_have_items():
            return "items"

        @then("it is correct")
        def check():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        test_regex="""\
            Feature: Regex metacharacters
                Scenario: Regex step works
                    Given I have 5 items
                    Then it is correct
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Regex step works")
        def test_regex():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1, skipped=1)


def test_parameterized_step_closest_match_wins(testdir):
    """
    Parameterized step with same text but different parameter sets:
                closest (first-registered) match wins.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    testdir.makeini(
        "[pytest]\nfilterwarnings = ignore::pytest_bdd.PytestBDDStepDefinitionWarning\n",
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given, parsers, then

        matched_patterns = []

        @given(parsers.parse("I have {count} items"))
        def count_items(count):
            matched_patterns.append(f"count={count}")

        @given(parsers.parse("I have {count:d} items"))
        def typed_count_items(count):
            matched_patterns.append(f"typed_count={count}")

        @then("the first pattern matched")
        def check_first():
            assert matched_patterns[-1].startswith("count=")
        """,
    )
    testdir.makefile(
        ".feature",
        test_param_match="""\
            Feature: Parameterized match priority
                Scenario: First registered pattern wins
                    Given I have 5 items
                    Then the first pattern matched
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)
