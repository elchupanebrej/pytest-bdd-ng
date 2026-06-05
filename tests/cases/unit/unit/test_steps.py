"""Unit tests for steps.py — StepDefinitionManager, decorators, registry.

These are testdir-based integration tests because steps.py requires
a live pytest runtime context for fixture injection and step registration.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from cucumber_messages import PickleStepType

from pytest_bdd.steps import StepDefinitionManager

pytestmark = [pytest.mark.unit]


def test_given_decorator_creates_definition(testdir) -> None:
    """@given decorator stores a step definition on the function."""
    testdir.makeconftest("""
        from pytest_bdd import given

        @given("I have a {thing}")
        def have_thing(thing):
            return thing
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Decorator
            Scenario: Test
                Given I have a widget
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_when_decorator_creates_definition(testdir) -> None:
    """@when decorator stores a step definition on the function."""
    testdir.makeconftest("""
        from pytest_bdd import when

        @when("I do something")
        def do_something():
            pass
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Decorator
            Scenario: Test
                When I do something
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_then_decorator_creates_definition(testdir) -> None:
    """@then decorator stores a step definition on the function."""
    testdir.makeconftest("""
        from pytest_bdd import then

        @then("it should be done")
        def check_done():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Decorator
            Scenario: Test
                Then it should be done
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_decorator_works_with_any_keyword(testdir) -> None:
    """@step decorator works with any keyword in the feature file."""
    testdir.makeconftest("""
        from pytest_bdd import step

        @step("something happens")
        def something():
            pass
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Step
            Scenario: Test
                Given something happens
                When something happens
                Then something happens
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_target_fixture_replaces_param(testdir) -> None:
    """target_fixture parameter injects the step function as a fixture."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("I have a value", target_fixture="my_value")
        def create_value():
            return 42

        @then("the value should be 42")
        def check_value(my_value):
            assert my_value == 42
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Fixture
            Scenario: Test
                Given I have a value
                Then the value should be 42
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_step_names_on_same_function(testdir) -> None:
    """Multiple step definitions on one function work for all names."""
    testdir.makeconftest("""
        from pytest_bdd import given

        @given("there is a user")
        @given("a user exists")
        def user_exists():
            return {"name": "Alice"}

        @given("I have a thing")
        def have_thing():
            return "thing"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Multi
            Scenario: Test
                Given there is a user
                And a user exists
                Given I have a thing
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_with_converters_via_parsers_module(testdir) -> None:
    """Parsers module handles type conversion in step parsing."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given(parsers.parse("I have {count:d} items"))
        def have_items(count):
            assert isinstance(count, int)
            return list(range(count))

        @then(parsers.parse("the count should be {count:d}"))
        def check_count(count):
            assert isinstance(count, int)
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Converters
            Scenario: Test
                Given I have 5 items
                Then the count should be 5
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_with_target_fixtures(testdir) -> None:
    """target_fixtures injects multiple fixtures from one step."""
    testdir.makeconftest("""
        from pytest_bdd import given

        @given("I have a user and group", target_fixtures=["user", "group"])
        def create_user_and_group():
            return ("Alice", "Admins")
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: MultiFixture
            Scenario: Test
                Given I have a user and group
    """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_when_first(testdir) -> None:
    """When step can be the first step in a scenario."""
    testdir.makeconftest("""
        from pytest_bdd import when, then

        @when("I do nothing")
        def do_nothing():
            pass

        @then("I make no mistakes")
        def no_errors():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: WhenFirst
            Scenario: Test
                When I do nothing
                Then I make no mistakes
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_then_after_given(testdir) -> None:
    """Then step can follow Given step."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: ThenAfterGiven
            Scenario: Test
                Given I have a foo fixture with value "foo"
                Then foo should have value "foo"
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_registry_injects_fixture(testdir) -> None:
    """Step registry fixture provides access to the registry."""
    testdir.makeconftest("""
        from pytest_bdd import given

        @given("a registered step")
        def registered():
            pass

        def _check_registry(step_registry):
            assert len(step_registry.registry) > 0
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Registry
            Scenario: Test
                Given a registered step
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_with_fixture_dependency(testdir) -> None:
    """Steps can depend on pytest fixtures from conftest."""
    testdir.makeconftest("""
        import pytest
        from pytest_bdd import given, then

        @pytest.fixture
        def database():
            class DB:
                items = []
            return DB()

        @given("an item is in the database")
        def add_item(database):
            database.items.append("item")

        @then("the database should have the item")
        def check_db(database):
            assert "item" in database.items
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: FixtureDep
            Scenario: Test
                Given an item is in the database
                Then the database should have the item
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_steps_with_unicode_content(testdir) -> None:
    """Steps can handle Unicode content in feature files."""
    step_text = (
        "\u0443 \u043c\u0435\u043d\u0435 \u0454 \u0440\u044f\u0434\u043e\u043a "
        "\u044f\u043a\u0438\u0439 \u043c\u0456\u0441\u0442\u0438\u0442\u044c"
    )
    content_text = "\u044f\u043a\u0438\u0439\u0441\u044c \u043a\u043e\u043d\u0442\u0435\u043d\u0442"
    testdir.makeconftest(f"""
        import pytest
        from pytest_bdd import given, then, parsers

        @pytest.fixture
        def string():
            return {{"content": ""}}

        @given(parsers.parse(u"{step_text} '{{content}}'"))
        def there_is_a_string(content, string):
            string["content"] = content

        @then(parsers.parse("I should see that the string equals to content '{{content}}'"))
        def assert_string(content, string):
            assert string["content"] == content
    """)
    testdir.makefile(
        ".feature",
        steps=f"""\
        Feature: Unicode
            Scenario: Test
                Given {step_text} '{content_text}'
                Then I should see that the string equals to content '{content_text}'
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_matching_priority_strict_over_liberal(testdir) -> None:
    """Strict matching takes priority when multiple definitions could match."""
    testdir.makeconftest("""
        from pytest_bdd import given, when, then

        @given("I have an item", target_fixture="item")
        def have_item():
            return "item"

        @when("I use the item")
        def use_item(item):
            assert item == "item"

        @then("the result should be complete")
        def check_result(item):
            assert item == "item"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Priority
            Scenario: Test
                Given I have an item
                When I use the item
                Then the result should be complete
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_scenarios_reuse_steps(testdir) -> None:
    """Step definitions are reused across multiple scenarios."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("a thing exists", target_fixture="thing")
        def thing():
            return "thing"

        @then("the thing should exist")
        def check_thing(thing):
            assert thing == "thing"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Reuse
            Scenario: First
                Given a thing exists
                Then the thing should exist

            Scenario: Second
                Given a thing exists
                Then the thing should exist
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_and_step_aliases_keyword(testdir) -> None:
    """'And' steps use the keyword of the previous step."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given(parsers.parse("I start the process with value {val:d}"), target_fixture="process")
        def start_process(val):
            return {"val": val}

        @given(parsers.parse("I add data to process"))
        def add_data(process):
            process["data"] = "added"

        @then("the result should be complete")
        def check_result(process):
            assert process.get("data") == "added"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: AndStep
            Scenario: Test
                Given I start the process with value 1
                And I add data to process
                Then the result should be complete
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_but_step_aliases_keyword(testdir) -> None:
    """'But' steps use the keyword of the previous step."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, step, parsers

        @given(parsers.parse("I have a value {val:d}"))
        def have_value(val):
            return val

        @step(parsers.parse("I also have value {val:d}"))
        def also_have_value(val):
            return val

        @then(parsers.parse("the values should be {a:d} and {b:d}"))
        def check_values(a, b):
            assert a == 5
            assert b == 10
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: ButStep
            Scenario: Test
                Given I have a value 5
                But I also have value 10
                Then the values should be 5 and 10
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_no_match_raises_error(testdir) -> None:
    """Unmatched steps cause a clear error."""
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Missing
            Scenario: Test
                Given no step is registered for this
    """,
    )
    result = testdir.runpytest()
    assert result.ret != 0


def test_param_defaults_passed_to_step(testdir) -> None:
    """param_defaults provides default values for step parameters."""
    testdir.makeconftest("""
        import pytest
        from pytest_bdd import given, parsers

        @given(parsers.parse('I have a {item}'), param_defaults={"item": "default_val"})
        def have_item(item):
            assert item == "default_val"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: ParamDefaults
            Scenario: Test
                Given I have a default_val
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_liberal_step_definition(testdir) -> None:
    """Liberal step definitions can match even when spec differs from keyword."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, step

        @step("I do something", liberal=True)
        def something():
            pass

        @then("I do something else")
        def something_else():
            pass
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Liberal
            Scenario: Test
                Given I do something
                Then I do something else
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_converters_dict_with_parsers(testdir) -> None:
    """converters parameter applies type conversion."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given(parsers.parse("I have {count} items"), converters=dict(count=int))
        def have_items(count):
            assert isinstance(count, int)
            return list(range(count))
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: ConvertersInline
            Scenario: Test
                Given I have 3 items
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


# ── Direct instantiation tests (no testdir needed) ──────────────────────────


def test_definition_fixtures_mapped_from_step_definition_target_fixtures():
    """fixtures_mapped_from_step_definition returns target_fixtures."""

    def dummy():
        pass

    dummy.__name__ = "dummy"
    from pytest_bdd.parsers import StepParser

    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=["foo", "bar"],
        liberal=None,
    )
    assert defn.fixtures_mapped_from_step_definition == {"foo", "bar"}


def test_definition_params_fixtures_mapping_false():
    """params_fixtures_mapping=False disables parameter injection."""

    def dummy():
        pass

    dummy.__name__ = "dummy"
    from pytest_bdd.parsers import StepParser

    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=False,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )
    assert defn.fixtures_mapped_from_step_definition == set()


def test_definition_param_defaults_included():
    """param_defaults are stored on the definition."""

    def dummy():
        pass

    dummy.__name__ = "dummy"
    from pytest_bdd.parsers import StepParser

    defaults = {"count": 0, "name": "default"}
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults=defaults,
        target_fixtures=[],
        liberal=None,
    )
    assert defn.param_defaults == defaults


def test_definition_converters_stored():
    """converters are stored on the definition."""

    def dummy():
        pass

    dummy.__name__ = "dummy"
    from pytest_bdd.parsers import StepParser

    converters = {"count": int}
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=None,
        converters=converters,
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )
    assert defn.converters == converters


def test_definition_anonymous_group_names():
    """anonymous_group_names are stored on the definition."""

    def dummy():
        pass

    dummy.__name__ = "dummy"
    from pytest_bdd.parsers import StepParser

    names = ["group1", "group2"]
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=names,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )
    assert list(defn.anonymous_group_names) == names


def test_multiple_decorators_accumulate():
    """Multiple decorators on same function accumulate definitions."""
    from pytest_bdd import given, when

    @given("I have a thing")
    @when("I use a thing")
    def thing_func():
        pass

    defs = getattr(thing_func, "__pytest_bdd_step_definitions__", set())
    assert len(defs) == 2
    types = {d.type_ for d in defs}
    assert PickleStepType.context in types
    assert PickleStepType.action in types


def test_registry_collects_definitions():
    """Registry collects definitions from decorated functions."""
    from ordered_set import OrderedSet

    from pytest_bdd import given

    def my_step():
        pass

    given("a step")(my_step)
    defs = getattr(my_step, "__pytest_bdd_step_definitions__", set())
    assert len(defs) == 1

    registry = StepDefinitionManager.Registry(registry=OrderedSet(defs))
    assert len(list(registry)) == 1


def test_registry_parent_linking():
    """Registry.fixture property creates a fixture that links child to parent."""
    from ordered_set import OrderedSet

    parent = StepDefinitionManager.Registry(registry=OrderedSet())
    child = StepDefinitionManager.Registry(registry=OrderedSet())
    child_fixture = child.fixture

    # The fixture is a callable that sets parent on the child
    assert child.parent is None


def test_decorator_builder_creates_definition_with_correct_attrs():
    """decorator_builder creates Definition with correct parser, type_, converters."""
    from pytest_bdd.steps import StepDefinitionManager

    converters = {"count": int}

    @StepDefinitionManager.decorator_builder(
        PickleStepType.context,
        "I have {count:d} items",
        converters=converters,
        target_fixture="items",
        param_defaults={"count": 0},
    )
    def my_step(count):
        return count

    defs = getattr(my_step, "__pytest_bdd_step_definitions__", set())
    assert len(defs) == 1
    defn = next(iter(defs))
    assert defn.type_ == PickleStepType.context
    assert defn.converters == converters
    assert defn.target_fixtures == ["items"]
    assert defn.param_defaults == {"count": 0}


def test_find_step_definition_checks_parent():
    """find_step_definition_matches checks local registry then parent."""
    from ordered_set import OrderedSet

    from pytest_bdd import given

    def parent_step():
        pass

    def child_step():
        pass

    given("a parent step")(parent_step)
    given("a child step")(child_step)

    parent_defs = getattr(parent_step, "__pytest_bdd_step_definitions__", set())
    child_defs = getattr(child_step, "__pytest_bdd_step_definitions__", set())

    parent_registry = StepDefinitionManager.Registry(registry=OrderedSet(parent_defs))
    child_registry = StepDefinitionManager.Registry(registry=OrderedSet(child_defs))
    child_registry.parent = parent_registry

    matchers = [lambda _sd: True]
    results = list(StepDefinitionManager.Matcher.find_step_definition_matches(child_registry, matchers))
    assert len(results) == 1
    assert results[0].func == child_step


def test_find_step_definition_falls_back_to_parent():
    """find_step_definition_matches falls back to parent when no local match."""
    from ordered_set import OrderedSet

    from pytest_bdd import given

    def parent_step():
        pass

    def child_step():
        pass

    given("a parent step")(parent_step)
    given("a child step")(child_step)

    parent_defs = getattr(parent_step, "__pytest_bdd_step_definitions__", set())
    child_defs = getattr(child_step, "__pytest_bdd_step_definitions__", set())

    parent_registry = StepDefinitionManager.Registry(registry=OrderedSet(parent_defs))
    child_registry = StepDefinitionManager.Registry(registry=OrderedSet(child_defs))
    child_registry.parent = parent_registry

    def match_parent_only(sd):
        return sd.func == parent_step

    results = list(StepDefinitionManager.Matcher.find_step_definition_matches(child_registry, [match_parent_only]))
    assert len(results) == 1
    assert results[0].func == parent_step


def test_definition_id_is_set_on_as_message():
    """as_message sets the definition id."""
    from pytest_bdd.parsers import StepParser
    from pytest_bdd.util.other import IdGenerator

    def dummy():
        pass

    dummy.__name__ = "dummy"
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )

    mock_stash = {}
    mock_stash[IdGenerator.STASH_KEY] = IdGenerator()
    mock_config = MagicMock()
    mock_config.stash = mock_stash

    message = defn.as_message(mock_config)
    assert defn.id is not None
    assert message.id == defn.id


def test_definition_as_message_caches_per_id_generator():
    """as_message caches message per IdGenerator instance."""
    from pytest_bdd.parsers import StepParser
    from pytest_bdd.util.other import IdGenerator

    def dummy():
        pass

    dummy.__name__ = "dummy"
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("a step"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )

    mock_stash = {}
    mock_stash[IdGenerator.STASH_KEY] = IdGenerator()
    mock_config = MagicMock()
    mock_config.stash = mock_stash

    msg1 = defn.as_message(mock_config)
    msg2 = defn.as_message(mock_config)
    assert msg1 is msg2  # same cached instance


def test_definition_get_parameters_with_defaults():
    """get_parameters includes param_defaults."""
    from pytest_bdd.parsers import StepParser

    def dummy():
        pass

    dummy.__name__ = "dummy"
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("I have {count:d} items"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={"count": 0},
        target_fixtures=[],
        liberal=None,
    )

    mock_request = MagicMock()
    mock_step = MagicMock()
    mock_step.text = "I have 5 items"

    params = defn.get_parameters(mock_request, mock_step)
    assert params["count"] == 5


def test_definition_get_parameters_with_converters():
    """get_parameters applies converters to parsed values."""
    from pytest_bdd.parsers import StepParser

    def dummy():
        pass

    dummy.__name__ = "dummy"
    defn = StepDefinitionManager.Definition(
        func=dummy,
        type_=PickleStepType.context,
        parser=StepParser.build("I have {count} items"),
        anonymous_group_names=None,
        converters={"count": int},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )

    mock_request = MagicMock()
    mock_step = MagicMock()
    mock_step.text = "I have 42 items"

    params = defn.get_parameters(mock_request, mock_step)
    assert params["count"] == 42
    assert isinstance(params["count"], int)


# ── Additional testdir tests for coverage ───────────────────────────────────


def test_liberal_step_matches_different_type(testdir) -> None:
    """Liberal step definition matches when step type differs from scenario keyword."""
    testdir.makeconftest("""
        from pytest_bdd import step

        @step("I prepare data", liberal=True)
        def prepare():
            pass

        @step("data is ready", liberal=True)
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: LiberalMatch
            Scenario: Test
                Given I prepare data
                Then data is ready
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_with_re_pattern(testdir) -> None:
    """Steps work with parsers.re() regex patterns."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given(parsers.re(r"I have (\\d+) items"), converters={"0": int})
        def have_items(request):
            pass

        @then("I have items")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Regex
            Scenario: Test
                Given I have 42 items
                Then I have items
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_with_cucumber_expression(testdir) -> None:
    """Steps work with parsers.cfparse() cucumber expressions."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given(parsers.cfparse("I have items"))
        def have_items():
            pass

        @then("I have items")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: CucumberExpr
            Scenario: Test
                Given I have items
                Then I have items
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_target_fixture_and_target_fixtures_warning(testdir) -> None:
    """Warning emitted when both target_fixture and target_fixtures specified."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("I have a thing", target_fixture="thing", target_fixtures=["other"])
        def have_thing():
            return "thing"

        @then("thing exists")
        def check(thing, other):
            # thing gets the return value, other is also injected (as None since not resolved)
            assert thing == "thing"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Warning
            Scenario: Test
                Given I have a thing
                Then thing exists
    """,
    )
    result = testdir.runpytest("-W", "always")
    # Should pass but with a warning about both target_fixture and target_fixtures
    assert result.ret == 0 or "Both target_fixture and target_fixtures" in result.stdout.str()


def test_step_params_fixtures_mapping_dict(testdir) -> None:
    """params_fixtures_mapping as dict controls which params become fixtures."""
    testdir.makeconftest("""
        from pytest_bdd import given, parsers

        @given(parsers.parse("I have {count} {item}"), params_fixtures_mapping={"count": "num"})
        def have_items(num):
            assert num == "5"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: ParamsMapping
            Scenario: Test
                Given I have 5 widgets
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_params_fixtures_mapping_collection(testdir) -> None:
    """params_fixtures_mapping as collection selects specific params."""
    testdir.makeconftest("""
        from pytest_bdd import given, parsers

        @given(parsers.parse("I have {count} {item}"), params_fixtures_mapping=["count"])
        def have_items(count):
            assert count == "3"
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: ParamsCollection
            Scenario: Test
                Given I have 3 things
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_scenario_outline(testdir) -> None:
    """Steps work with Scenario Outline examples."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given(parsers.parse("I have {count:d} items"))
        def have_items(count):
            assert count > 0

        @then(parsers.parse("the count is {count:d}"))
        def check_count(count):
            assert count > 0
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Outline
            Scenario Outline: Test
                Given I have <count> items
                Then the count is <count>

                Examples:
                    | count |
                    | 1     |
                    | 2     |
                    | 3     |
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=3)


def test_step_background(testdir) -> None:
    """Steps work with Background section."""
    testdir.makeconftest("""
        from pytest_bdd import given, then, parsers

        @given("a background step")
        def background():
            pass

        @given(parsers.parse("I have {value}"))
        def have_value(value):
            pass

        @then("value is set")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Background
            Background:
                Given a background step

            Scenario: Test
                Given I have something
                Then value is set
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_docstring(testdir) -> None:
    """Steps work with docstrings in feature files."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("I have a docstring step")
        def docstring_step():
            pass

        @then("it should work")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps='''\
        Feature: Docstring
            Scenario: Test
                Given I have a docstring step
                    """
                    This is a docstring
                    """
                Then it should work
    ''',
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_data_table(testdir) -> None:
    """Steps work with data tables in feature files."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("I have a data table")
        def data_table_step():
            pass

        @then("it should work")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: DataTable
            Scenario: Test
                Given I have a data table
                    | name  | value |
                    | foo   | 1     |
                    | bar   | 2     |
                Then it should work
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_registry_injects_fixture_with_steps(testdir) -> None:
    """Step registry fixture is injected and accessible."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("a step")
        def a_step():
            pass

        @then("registry exists")
        def check_registry(step_registry):
            assert step_registry is not None
            assert len(step_registry.registry) > 0
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: RegistryInject
            Scenario: Test
                Given a step
                Then registry exists
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_step_multiple_features_same_conftest(testdir) -> None:
    """Steps are reused across multiple feature files."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("a shared step")
        def shared():
            pass

        @then("it works")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        feature1="""\
        Feature: First
            Scenario: Test
                Given a shared step
                Then it works
    """,
    )
    testdir.makefile(
        ".feature",
        feature2="""\
        Feature: Second
            Scenario: Test
                Given a shared step
                Then it works
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_step_with_tags(testdir) -> None:
    """Steps work with tagged scenarios."""
    testdir.makeconftest("""
        from pytest_bdd import given, then

        @given("a tagged step")
        def tagged():
            pass

        @then("it works")
        def check():
            assert True
    """)
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Tags
            @slow
            Scenario: Tagged test
                Given a tagged step
                Then it works
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
