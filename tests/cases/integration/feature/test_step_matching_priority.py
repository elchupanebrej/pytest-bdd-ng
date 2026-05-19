"""Test step matching priority — strict > unspecified > liberal ordering."""

import textwrap


def test_strict_given_has_precedence_over_step_decorator(testdir):
    """Strict Given beats unspecified step() for same text."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, step, then

            step_type = []

            @given("I have a thing")
            def given_i_have_a_thing():
                step_type.append("given")

            @step("I have a thing")
            def step_i_have_a_thing():
                step_type.append("step")

            @then("we recorded given")
            def check_given():
                assert step_type[-1] == "given"
        """),
    )
    testdir.makefile(
        ".feature",
        test_strict_given="""\
            Feature: Strict precedence
                Scenario: Strict Given wins
                    Given I have a thing
                    Then we recorded given
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_strict_when_has_precedence_over_step_decorator(testdir):
    """Strict When beats unspecified step() for same text."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import when, step, then

            step_type = []

            @when("I do an action")
            def when_i_do_action():
                step_type.append("when")

            @step("I do an action")
            def step_i_do_action():
                step_type.append("step")

            @then("we recorded when")
            def check_when():
                assert step_type[-1] == "when"
        """),
    )
    testdir.makefile(
        ".feature",
        test_strict_when="""\
            Feature: Strict When precedence
                Scenario: Strict When wins
                    When I do an action
                    Then we recorded when
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_strict_then_has_precedence_over_step_decorator(testdir):
    """Strict Then beats unspecified step() for same text."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, step, then

            step_type = []

            @given("I have setup")
            def i_have_setup():
                pass

            @then("I verify strict")
            def strict_then():
                step_type.append("then")

            @step("I verify strict")
            def step_then():
                step_type.append("step")
        """),
    )
    testdir.makefile(
        ".feature",
        test_strict_then="""\
            Feature: Strict Then precedence
                Scenario: Strict Then wins
                    Given I have setup
                    Then I verify strict
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_multiple_definitions_same_type_first_registered_wins(testdir):
    """When two definitions of same type match, first-registered wins."""
    testdir.makeini(
        "[pytest]\nfilterwarnings = ignore::pytest_bdd.PytestBDDStepDefinitionWarning\n",
    )
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, step, then

            results = []

            @given("a defined step")
            def first_definition():
                results.append("definition_a")
                return "definition_a"

            @given("a defined step")
            def second_definition():
                results.append("definition_b")
                return "definition_b"

            @then("the first definition is used")
            def check_first():
                assert results[-1] == "definition_a"
        """),
    )
    testdir.makefile(
        ".feature",
        test_first_wins="""\
            Feature: First registration wins
                Scenario: First definition used
                    Given a defined step
                    Then the first definition is used
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_wildcard_parser_beats_regex_catchall(testdir):
    """Specific parser match beats generic regex catch-all."""
    testdir.makeini(
        "[pytest]\nfilterwarnings = ignore::pytest_bdd.PytestBDDStepDefinitionWarning\n",
    )
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, parsers, then

            match_types = []

            @given(parsers.parse("I have {count:d} {fruit}"))
            def specific_parser(count, fruit):
                match_types.append("specific")

            @given(parsers.re("I have (?P<count>\\\\d+) (?P<fruit>\\\\w+)"))
            def generic_regex(count, fruit):
                match_types.append("regex")

            @then("the match type is specific")
            def check_specific():
                assert match_types[-1] == "specific"
        """),
    )
    testdir.makefile(
        ".feature",
        test_parser_specific="""\
            Feature: Parser specificity
                Scenario: Specific parser wins
                    Given I have 5 apples
                    Then the match type is specific
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_step_matching_respects_liberal_option(testdir):
    """Liberal step only matches when liberal_steps is enabled."""
    testdir.makeini(
        "[pytest]\nliberal_steps = True\n",
    )
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, scenario, when

            @when("a liberal step", liberal=True)
            def liberal_step():
                pass
        """),
    )
    testdir.makefile(
        ".feature",
        test_liberal_enabled="""\
            Feature: Liberal enabled via ini
                Scenario: Liberal step matches Given
                    Given a liberal step
        """,
    )
    # No need for a separate py file - the scenario auto-discovers
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_step_with_regex_metacharacters(testdir):
    """Step patterns with regex metacharacters are handled safely."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, parsers, then

            regex_matched = []

            @given(parsers.re("I have \\\\d+ items"))
            def i_have_items():
                regex_matched.append(True)

            @then("it is correct")
            def check():
                assert regex_matched[-1] is True
        """),
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
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_unspecified_step_matches_given_when_then_equally(testdir):
    """Unspecified step() decorator matches Given, When, and Then keywords equally."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import step, then

            matched_keywords = []

            @step("a universal step")
            def universal_step():
                matched_keywords.append("matched")

            @then("we matched universal")
            def check():
                assert matched_keywords.count("matched") == 1
        """),
    )
    testdir.makefile(
        ".feature",
        test_universal="""\
            Feature: Unspecified step matching
                Scenario: step() matches Given
                    Given a universal step
                    Then we matched universal
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_unspecified_step_matches_when_keyword(testdir):
    """Unspecified step() decorator matches When keyword."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, step, then

            matched = []

            @given("initial state")
            def initial():
                pass

            @step("an action step")
            def action_step():
                matched.append("when")

            @then("action was recorded")
            def check():
                assert matched == ["when"]
        """),
    )
    testdir.makefile(
        ".feature",
        test_universal_when="""\
            Feature: Unspecified step matching When
                Scenario: step() matches When
                    Given initial state
                    When an action step
                    Then action was recorded
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_unspecified_step_matches_then_keyword(testdir):
    """Unspecified step() decorator matches Then keyword."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, step

            matched = []

            @given("setup done")
            def setup():
                pass

            @step("verify outcome")
            def verify():
                matched.append("then")
        """),
    )
    testdir.makefile(
        ".feature",
        test_universal_then="""\
            Feature: Unspecified step matching Then
                Scenario: step() matches Then
                    Given setup done
                    Then verify outcome
        """,
    )
    testdir.makepyfile(
        textwrap.dedent("""\
            from pytest_bdd import scenario

            @scenario("test.feature", "step() matches Then")
            def test_universal_then():
                pass
        """),
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1, skipped=1)


def test_import_order_independence_nested_conftest(testdir):
    """Step matching is order-independent of import: nested conftest steps
    resolve identically regardless of which conftest is loaded first."""
    testdir.makeini(
        "[pytest]\nfilterwarnings = ignore::pytest_bdd.PytestBDDStepDefinitionWarning\n",
    )
    # Parent conftest with a step definition
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, then

            @given("a shared step", target_fixture="step_source")
            def parent_shared_step():
                return "parent"

            @then("step came from parent")
            def check_parent(step_source):
                assert step_source == "parent"
        """),
    )
    # Child directory with its own conftest that overrides the parent step
    subdir = testdir.mkdir("child")
    subdir.join("conftest.py").write(
        textwrap.dedent("""\
            from pytest_bdd import given, then

            @given("a shared step", target_fixture="step_source")
            def child_shared_step():
                return "child"

            @then("step came from child")
            def check_child(step_source):
                assert step_source == "child"
        """),
    )
    subdir.join("test_import_order.feature").write(
        textwrap.dedent("""\
            Feature: Import order independence
                Scenario: Child conftest overrides parent
                    Given a shared step
                    Then step came from child
        """),
    )
    subdir.join("test_import_order.py").write(
        textwrap.dedent("""\
            from pytest_bdd import scenario

            @scenario("test_import_order.feature", "Child conftest overrides parent")
            def test_child_wins():
                pass
        """),
    )
    result = testdir.runpytest("child/", "-v")
    result.assert_outcomes(passed=1, skipped=1)


def test_parent_child_registry_precedence(testdir):
    """Parent registry vs child registry: child definitions take precedence
    over parent definitions for the same step text."""
    testdir.makeconftest(
        textwrap.dedent("""\
            from pytest_bdd import given, then

            @given("an overridden step", target_fixture="registry_source")
            def parent_registry_step():
                return "parent_registry"

            @then("registry source is child")
            def check_child_registry(registry_source):
                assert registry_source == "child_registry"
        """),
    )
    subdir = testdir.mkdir("sub_registry")
    subdir.join("conftest.py").write(
        textwrap.dedent("""\
            from pytest_bdd import given

            @given("an overridden step", target_fixture="registry_source")
            def child_registry_step():
                return "child_registry"
        """),
    )
    subdir.join("test_registry.feature").write(
        textwrap.dedent("""\
            Feature: Registry precedence
                Scenario: Child registry wins
                    Given an overridden step
                    Then registry source is child
        """),
    )
    subdir.join("test_registry.py").write(
        textwrap.dedent("""\
            from pytest_bdd import scenario

            @scenario("test_registry.feature", "Child registry wins")
            def test_child_registry():
                pass
        """),
    )
    result = testdir.runpytest("sub_registry/", "-v")
    result.assert_outcomes(passed=1, skipped=1)
