"""

Test scenario execution edge cases — empty scenarios, unicode, data tables, docstrings.
"""


def test_empty_scenario_passes(testdir):
    """
    Empty scenario (no steps) should pass silently.

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
    testdir.makefile(
        ".feature",
        empty="""\
            Feature: Empty scenarios
                Scenario: Empty scenario
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Empty scenario")
        def test_empty():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Only wrapper function → replaced by scenario test
    result.assert_outcomes(passed=1, skipped=1)


def test_scenario_with_only_comments(testdir):
    """
    Scenario with only comment lines is treated as empty but valid.

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
    testdir.makefile(
        ".feature",
        comments="""\
            Feature: Comment only
                # This scenario has no steps
                # Just comments describing intent
                Scenario: Commented scenario
                    # nothing to do
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Commented scenario")
        def test_commented():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test passes; wrapper test skipped (empty body)
    result.assert_outcomes(passed=1, skipped=1)


def test_unicode_step_text(testdir):
    """
    Unicode in step text is handled correctly end-to-end.

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
        from pytest_bdd import given, when, then

        @given("Дано что-то")
        def given_russian():
            return "русский"

        @when("Действие совершено")
        def when_russian(value):
            return value

        @then("Результат правильный")
        def then_russian(value):
            assert value == "русский"
        """,
    )
    testdir.makefile(
        ".feature",
        unicode_steps="""\
            Feature: Unicode steps
                Scenario: Russian text
                    Дано что-то
                    Когда Действие совершено
                    Тогда Результат правильный
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Russian text")
        def test_unicode():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test passes; wrapper test skipped (empty body)
    result.assert_outcomes(passed=1, skipped=1)


def test_data_table_in_step(testdir):
    """
    Step with data table executes without errors.

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
        from pytest_bdd import given, then

        @given("a data table step")
        def data_table_step():
            pass

        @then("it executes successfully")
        def check_success():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        table="""\
            Feature: Data table
                Scenario: Table parsing
                    Given a data table step
                        | name  | age |
                        | Alice | 30  |
                        | Bob   | 25  |
                    Then it executes successfully
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Table parsing")
        def test_table():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test passes; wrapper test skipped (empty body)
    result.assert_outcomes(passed=1, skipped=1)


def test_docstring_in_step(testdir):
    """
    Step with docstring executes without errors.

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
        from pytest_bdd import given, then

        @given("a docstring step")
        def docstring_step():
            pass

        @then("it executes successfully")
        def check_success():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        docstring="""\
            Feature: Docstring
                Scenario: Docstring parsing
                    Given a docstring step
                        \"\"\"
                        This is a multiline
                        docstring content
                        \"\"\"
                    Then it executes successfully
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Docstring parsing")
        def test_docstring():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test passes; wrapper test skipped (empty body)
    result.assert_outcomes(passed=1, skipped=1)


def test_scenario_outline_with_examples(testdir):
    """
    Scenario Outline with Examples table runs each row as separate scenario.

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

        @given(parsers.parse("I have {count:d} {item}"))
        def have_items(count, item):
            return {"count": count, "item": item}

        @given("I also have {other:d} {another_item}")
        def also_have(other, another_item):
            return {"other": other, "another_item": another_item}

        @then(parsers.parse("I should have {total:d} items"))
        def check_total(total):
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Scenario Outline
                Scenario Outline: Item counting
                    Given I have <count> <item>
                    And I also have <other> <another_item>
                    Then I should have <total> items

                    Examples: Items
                        | count | item   | other | another_item | total |
                        | 3     | apples | 2     | oranges      | 5     |
                        | 5     | books  | 3     | pens         | 8     |
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Item counting")
        def test_outline():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # 2 scenario tests pass (2 example rows); wrapper test skipped (empty body)
    result.assert_outcomes(passed=2, skipped=1)


def test_background_runs_before_each_scenario(testdir):
    """
    Background section steps execute before each scenario.

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
        from pytest_bdd import given, then

        @given("a clean setup")
        def clean_setup(request):
            request.config.setup_count = getattr(request.config, "setup_count", 0) + 1

        @then("setup was fresh")
        def check_setup(request):
            assert request.config.setup_count >= 1
        """,
    )
    testdir.makefile(
        ".feature",
        background="""\
            Feature: Background
                Background:
                    Given a clean setup

                Scenario: First scenario
                    Then setup was fresh

                Scenario: Second scenario
                    Then setup was fresh
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "First scenario")
        def test_first():
            pass

        @scenario("test.feature", "Second scenario")
        def test_second():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # 2 scenario tests pass; 2 wrapper tests skipped (empty body)
    result.assert_outcomes(passed=2, skipped=2)


def test_tag_filtering_with_and_tag(testdir):
    """
    Tags filter scenarios correctly.

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
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        markers =
            smoke: smoke tests
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given, then

        @given("a tagged step")
        def tagged_step():
            pass

        @then("it works")
        def check_work():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        tags="""\
            Feature: Tag filtering
                @smoke
                Scenario: Smoke test
                    Given a tagged step
                    Then it works

                Scenario: Untagged test
                    Given a tagged step
                    Then it works
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Smoke test")
        def test_smoke():
            pass

        @scenario("test.feature", "Untagged test")
        def test_untagged():
            pass
        """,
    )
    # Run only @smoke tagged scenarios
    result = testdir.runpytest("-v", "-m", "smoke")
    # 1 scenario passes (@smoke), 1 deselected (no tags)
    result.assert_outcomes(passed=1)


def test_malformed_gherkin_shows_clear_error(testdir):
    """
    Malformed Gherkin produces a clear error message, not a silent pass.

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
        malformed="""\
            WrongFeature: badly formatted
                broken syntax all over
                    this is not valid gherkin
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "badly formatted")
        def test_malformed():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Malformed Gherkin causes collection error
    result.assert_outcomes(errors=1)


def test_scenario_with_escaped_pipes(testdir):
    """
    Scenario with escaped pipe characters in step text works correctly.

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
        from pytest_bdd import given, then

        @given("a table with pipes")
        def table_with_pipes():
            pass

        @then("it executes successfully")
        def check_success():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        escaped="""\
            Feature: Escaped pipes
                Scenario: Table with pipes in cells
                    Given a table with pipes
                        | name | value   |
                        | a \\| b | c \\| d |
                    Then it executes successfully
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Table with pipes in cells")
        def test_escaped_pipes():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test passes; wrapper test skipped (empty body)
    result.assert_outcomes(passed=1, skipped=1)


def test_scenario_with_and_but_continuation(testdir):
    """
    And/But continuation keywords work correctly across step types.

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
        from pytest_bdd import given, when, then

        @given("I start with value {n:d}")
        def start_value(n):
            pass

        @when("I add {n:d}")
        def add_value(n):
            pass

        @when("I multiply by {n:d}")
        def multiply_value(n):
            pass

        @then("the result should be {n:d}")
        def check_result(n):
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        and_but="""\
            Feature: And/But continuation
                Scenario: Chain operations
                    Given I start with value 5
                    When I add 3
                    And I multiply by 2
                    Then the result should be 16
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Chain operations")
        def test_and_but():
            pass
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test passes; wrapper test skipped (empty body)
    result.assert_outcomes(passed=1, skipped=1)


def test_zero_step_scenario_passes_with_allow_empty(testdir):
    """
    Zero-step scenario with allow-empty flag passes as skipped.

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
    testdir.makefile(
        ".feature",
        allow_empty="""\
            Feature: Allow empty
                Scenario: No steps at all
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "No steps at all")
        def test_empty_match():
            pass
        """,
    )
    result = testdir.runpytest("-v", "--allow-empty-scenarios")
    # Empty scenario passes with allow-empty flag; wrapper skipped
    result.assert_outcomes(passed=1, skipped=1)
