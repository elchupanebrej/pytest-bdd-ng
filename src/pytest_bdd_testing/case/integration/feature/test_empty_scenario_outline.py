"""
Test empty scenario outlines and empty Examples tables handling during collection and execution.
"""


def test_scenario_outline_empty_examples_header_only_decorator(testdir):
    """
    Scenario Outline with empty Examples table (headers only) should not crash collection.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a feature file with a Scenario Outline having an Examples table with only headers and no data rows,
        when tests are collected and run using the @scenario decorator,
        then collection succeeds without error and the empty scenario outline is skipped.
    BDD reference:
        None
    Fixtures:
        - testdir
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
        test="""\
            Feature: Empty Scenario Outline
                Scenario Outline: Outline with header only
                    Given I have <count> items
                    Then I should have <count> items

                    Examples:
                        | count |
        """,
    )
    test_file = testdir.makepyfile(
        """
        from pytest_bdd import scenario, given, then

        @given("I have <count> items")
        def given_items(count):
            pass

        @then("I should have <count> items")
        def then_items(count):
            pass

        @scenario("test.feature", "Outline with header only")
        def test_outline():
            pass
        """,
    )
    result = testdir.runpytest(str(test_file), "-v")
    result.assert_outcomes(skipped=1)


def test_scenario_outline_empty_examples_via_scenarios(testdir):
    """
    Scenario Outline with empty Examples table loaded via scenarios() should not crash collection.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a feature file with a Scenario Outline having empty Examples,
        when tests are collected via scenarios(),
        then collection succeeds without error.
    BDD reference:
        None
    Fixtures:
        - testdir
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
        test="""\
            Feature: Empty Scenario Outline via scenarios
                Scenario Outline: Outline with empty examples
                    Given I have <count> items

                    Examples:
                        | count |
        """,
    )
    test_file = testdir.makepyfile(
        """
        from pytest_bdd import scenarios, given

        @given("I have <count> items")
        def given_items(count):
            pass

        test_outline = scenarios("test.feature")
        """,
    )
    result = testdir.runpytest(str(test_file), "-v")
    result.assert_outcomes(skipped=1)


def test_scenario_outline_empty_examples_autoload(testdir):
    """
    Scenario Outline with empty Examples table under feature autoload should not crash collection.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a feature file with a Scenario Outline having empty Examples,
        when pytest runs directly on the feature file,
        then collection succeeds without crashing.
    BDD reference:
        None
    Fixtures:
        - testdir
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

        @given("I have <count> items")
        def given_items(count):
            pass
        """,
    )
    feature_file = testdir.makefile(
        ".feature",
        autoload="""\
            Feature: Empty Scenario Outline Autoload
                Scenario Outline: Outline autoload
                    Given I have <count> items

                    Examples:
                        | count |
        """,
    )
    result = testdir.runpytest(str(feature_file), "-v")
    result.assert_outcomes(skipped=1)


def test_scenario_outline_multiple_examples_one_empty(testdir):
    """
    Scenario Outline with one valid and one empty Examples table runs valid rows and skips empty.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a Scenario Outline with two Examples blocks (one with data rows, one empty),
        when tests are executed,
        then the non-empty rows pass and the empty block does not crash collection.
    BDD reference:
        None
    Fixtures:
        - testdir
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
        test="""\
            Feature: Multiple Examples
                Scenario Outline: Mixed examples
                    Given I have <count> items

                    Examples: Non-empty
                        | count |
                        | 1     |
                        | 2     |

                    Examples: Empty
                        | count |
        """,
    )
    test_file = testdir.makepyfile(
        """
        from pytest_bdd import scenario, given, parsers

        @given(parsers.parse("I have {count} items"))
        def given_items(count):
            pass

        @scenario("test.feature", "Mixed examples")
        def test_mixed():
            pass
        """,
    )
    result = testdir.runpytest(str(test_file), "-v")
    result.assert_outcomes(passed=2, skipped=0)


def test_scenario_outline_empty_alongside_regular_scenario(testdir):
    """
    Feature with both a regular Scenario and an empty Scenario Outline executes regular scenario.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a feature file containing a regular Scenario and an empty Scenario Outline,
        when tests are executed,
        then the regular scenario passes and the empty scenario outline does not cause collection failure.
    BDD reference:
        None
    Fixtures:
        - testdir
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

        @given("a working step")
        def working_step():
            pass

        @given("I have <count> items")
        def given_items(count):
            pass
        """,
    )
    feature_file = testdir.makefile(
        ".feature",
        test="""\
            Feature: Mixed feature
                Scenario: Regular scenario
                    Given a working step

                Scenario Outline: Empty outline
                    Given I have <count> items

                    Examples:
                        | count |
        """,
    )
    result = testdir.runpytest(str(feature_file), "-v")
    result.assert_outcomes(passed=1, skipped=0)


def test_scenario_outline_empty_examples_keyword_no_table(testdir):
    """
    Scenario Outline with empty Examples keyword (no table at all) should not crash collection.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a Scenario Outline with an Examples: keyword but no table rows or headers,
        when tests are executed,
        then collection succeeds without crashing.
    BDD reference:
        None
    Fixtures:
        - testdir
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
        test="""\
            Feature: Empty Examples Keyword
                Scenario Outline: Outline with empty examples block
                    Given I have <count> items

                    Examples:
        """,
    )
    test_file = testdir.makepyfile(
        """
        from pytest_bdd import scenarios, given

        @given("I have <count> items")
        def given_items(count):
            pass

        test_outline = scenarios("test.feature")
        """,
    )
    result = testdir.runpytest(str(test_file), "-v")
    result.assert_outcomes(skipped=1)


def test_scenario_outline_markdown_empty_examples(testdir):
    """
    Markdown feature with empty Scenario Outline Examples table should not crash collection.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given a .feature.md file with an empty Scenario Outline Examples table,
        when tests are executed,
        then collection succeeds without error.
    BDD reference:
        None
    Fixtures:
        - testdir
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
        ".feature.md",
        test="""\
            # Feature: Markdown Empty Scenario Outline

            ## Scenario Outline: Outline in markdown

            * Given I have <count> items

            ### Examples:
            | count |
        """,
    )
    test_file = testdir.makepyfile(
        """
        from pytest_bdd import scenarios, given

        @given("I have <count> items")
        def given_items(count):
            pass

        test_outline = scenarios("test.feature.md")
        """,
    )
    result = testdir.runpytest(str(test_file), "-v")
    result.assert_outcomes(skipped=1)
