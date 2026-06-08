"""
Step decorator builders — given, when, then, step.

Responsibility:
    Step decorator builders — given, when, then, step. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.steps.decorators` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - not_implemented: owns nested behavior below this boundary
    - tolerant: owns nested behavior below this boundary
    - given: owns nested behavior below this boundary
    - when: owns nested behavior below this boundary
    - then: owns nested behavior below this boundary
    - step: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `decorators`
    - src/pytest_bdd/steps/__init__.py: imports or references `decorators`

State and side effects:
    mutates cast.__pytest_bdd_not_implemented__, definition.not_implemented, cast.__pytest_bdd_tolerant__,
    definition.tolerant; depends on __future__.annotations, collections.abc.Iterable, collections.abc.Mapping,
    collections.abc.Sequence, typing.Any.

Invariants:
    - `pytest_bdd.steps.decorators` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence  # noqa: TC003
from typing import Any, cast

from cucumber_messages import PickleStepType

from pytest_bdd.steps.definition import (
    ConverterT,
    Definition,
    ParamsFixturesMapping,
    StepDecorator,
    StepFunc,
)
from pytest_bdd.steps.manager import StepDefinitionManager


def not_implemented(step_func: StepFunc) -> StepFunc:
    """
    Mark a step definition as intentionally not implemented.

    Args:
        step_func: Step definition function.

    Returns:
        Marked step definition function.

    Responsibility:
        Mark a step definition as intentionally not implemented. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.decorators.not_implemented` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `not_implemented`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `not_implemented`
        - src/pytest_bdd/steps/__init__.py: imports or references `not_implemented`
        - src/pytest_bdd/steps/definition.py: imports or references `not_implemented`

    State and side effects:
        mutates cast.__pytest_bdd_not_implemented__, definition.not_implemented.

    Invariants:
        - `pytest_bdd.steps.decorators.not_implemented` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    cast("Any", step_func).__pytest_bdd_not_implemented__ = True
    for definition in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        if isinstance(definition, Definition):
            definition.not_implemented = True
    return step_func


def tolerant(step_func: StepFunc) -> StepFunc:
    """
    Mark a step definition as tolerant to failure.

    Args:
        step_func: Step definition function.

    Returns:
        Marked step definition function.

    Responsibility:
        Mark a step definition as tolerant to failure. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.decorators.tolerant` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `tolerant`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `tolerant`
        - src/pytest_bdd/steps/__init__.py: imports or references `tolerant`
        - src/pytest_bdd/steps/definition.py: imports or references `tolerant`

    State and side effects:
        mutates cast.__pytest_bdd_tolerant__, definition.tolerant.

    Invariants:
        - `pytest_bdd.steps.decorators.tolerant` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    cast("Any", step_func).__pytest_bdd_tolerant__ = True
    for definition in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        if isinstance(definition, Definition):
            definition.tolerant = True
    return step_func


def given(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Define a Given step that sets up preconditions for a scenario.

    Given steps establish the initial context or state required before
    the action under test is performed. They typically create test
    data, configure system state, or set up fixtures that subsequent
    When and Then steps depend on.

    The ``parserlike`` parameter accepts a plain string (matched
    literally), or a parser object from ``pytest_bdd.parsers`` such
    as ``parsers.parse()``, ``parsers.re()``, or ``parsers.cfparse()``
    for parameterized step patterns.

    Multiple step decorators can be stacked on the same function to
    register it under different step patterns.

    Args:
        parserlike: Step pattern string or parser object. A plain
            string matches the step text literally. Parser objects
            from ``pytest_bdd.parsers`` enable parameter extraction
            (e.g., ``parsers.parse("I have {count:d} items")``).
        anonymous_group_names: Names for unnamed regex capture groups
            in ``parsers.re()`` patterns. A sequence of strings
            matching the order of unnamed groups in the regex.
        converters: Dictionary mapping parameter names to converter
            functions. Each converter receives the raw parsed value
            and returns the transformed value
            (e.g., ``{"count": int}``).
        target_fixture: Name of a single pytest fixture to populate
            with the return value of the step definition function.
            Mutually exclusive with ``target_fixtures`` — a warning
            is emitted if both are specified.
        target_fixtures: Sequence of fixture names to populate with
            the step definition return value. Use when a step should
            provide values to multiple fixtures. Mutually exclusive
            with ``target_fixture``.
        params_fixtures_mapping: Controls how step parameters are
            injected as fixtures. ``True`` (default) injects all
            parameters. ``False`` disables injection. A collection
            of strings injects only named parameters. A dict maps
            parameter names to fixture names.
        param_defaults: Default values for step parameters when they
            are not matched by the parser. A dict mapping parameter
            names to default values.
        liberal: Whether this step definition can match any Gherkin
            keyword (Given/When/Then). ``None`` uses the project-wide
            config default (``liberal_steps`` ini option or CLI flag).
        stacklevel: Caller frame depth for fixture injection. Used
            internally to locate the correct module scope when
            registering step definitions. Defaults to ``1``.

    Returns:
        A ``StepDecorator`` — a decorator to apply to step definition
        functions. The decorated function is registered in the step
        registry and becomes available for scenario execution.

    Example:
        Basic Given step::

            from pytest_bdd import given

            @given("I have a user")
            def given_user():
                return create_user()

        With parameterized pattern and target_fixture::

            from pytest_bdd import given, parsers

            @given(
                parsers.parse("I have {count:d} users"),
                target_fixture="users",
            )
            def given_users(count):
                return [create_user() for _ in range(count)]

        With converters::

            @given(
                parsers.parse("the date is {date}"),
                converters={"date": datetime.fromisoformat},
                target_fixture="current_date",
            )
            def given_date(date):
                return date

    See Also:
        :func:`when`: Define action steps.
        :func:`then`: Define assertion steps.
        :func:`step`: Define liberal steps matching any keyword.

    Responsibility:
        Define a Given step that sets up preconditions for a scenario. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.decorators.given` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - StepDefinitionManager.decorator_builder: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `given`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `given`
        - src/pytest_bdd/steps/__init__.py: imports or references `given`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.context,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def when(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Define a When step that describes an action or event in a scenario.

    When steps represent the action or event that triggers the behavior
    being tested. They typically interact with the system under test —
    submitting a form, clicking a button, calling an API endpoint,
    or invoking a method.

    The parameter set and behavior are identical to :func:`given`,
    but the step type is ``PickleStepType.action`` in the Cucumber
    Messages protocol, which affects reporting and step matching.

    Args:
        parserlike: Step pattern string or parser object. A plain
            string matches the step text literally. Parser objects
            from ``pytest_bdd.parsers`` enable parameter extraction.
        anonymous_group_names: Names for unnamed regex capture groups
            in ``parsers.re()`` patterns.
        converters: Dictionary mapping parameter names to converter
            functions (e.g., ``{"count": int}``).
        target_fixture: Name of a single pytest fixture to populate
            with the return value. Mutually exclusive with
            ``target_fixtures``.
        target_fixtures: Sequence of fixture names to populate.
            Mutually exclusive with ``target_fixture``.
        params_fixtures_mapping: Controls parameter-to-fixture
            injection. ``True`` (default), ``False``, collection,
            or dict.
        param_defaults: Default values for unmatched parameters.
        liberal: Whether this step can match any Gherkin keyword.
            ``None`` uses the project-wide config default.
        stacklevel: Caller frame depth for fixture injection.

    Returns:
        A ``StepDecorator`` — a decorator to apply to step definition
        functions.

    Example:
        Basic When step::

            from pytest_bdd import when

            @when("I submit the login form")
            def submit_login(login_page):
                login_page.click_login()

        With parameterized pattern::

            from pytest_bdd import when, parsers

            @when(parsers.parse("I search for {query}"))
            def search(query, search_page):
                search_page.enter_query(query)
                search_page.submit()

    See Also:
        :func:`given`: Define precondition steps.
        :func:`then`: Define assertion steps.
        :func:`step`: Define liberal steps matching any keyword.

    Responsibility:
        Define a When step that describes an action or event in a scenario. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.decorators.when` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - StepDefinitionManager.decorator_builder: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `when`
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `when`
        - src/pytest_bdd/plugin/debug_mcp/failure.py: imports or references `when`
        - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `when`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `when`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.action,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def then(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Define a Then step that asserts expected outcomes in a scenario.

    Then steps verify the results of the action performed in When steps.
    They contain assertions about system state, UI elements, API
    responses, database records, or any observable behavior.

    The parameter set and behavior are identical to :func:`given`,
    but the step type is ``PickleStepType.outcome`` in the Cucumber
    Messages protocol, which affects reporting and step matching.

    Args:
        parserlike: Step pattern string or parser object. A plain
            string matches the step text literally. Parser objects
            from ``pytest_bdd.parsers`` enable parameter extraction.
        anonymous_group_names: Names for unnamed regex capture groups
            in ``parsers.re()`` patterns.
        converters: Dictionary mapping parameter names to converter
            functions (e.g., ``{"count": int}``).
        target_fixture: Name of a single pytest fixture to populate
            with the return value. Mutually exclusive with
            ``target_fixtures``.
        target_fixtures: Sequence of fixture names to populate.
            Mutually exclusive with ``target_fixture``.
        params_fixtures_mapping: Controls parameter-to-fixture
            injection. ``True`` (default), ``False``, collection,
            or dict.
        param_defaults: Default values for unmatched parameters.
        liberal: Whether this step can match any Gherkin keyword.
            ``None`` uses the project-wide config default.
        stacklevel: Caller frame depth for fixture injection.

    Returns:
        A ``StepDecorator`` — a decorator to apply to step definition
        functions.

    Example:
        Basic Then step with assertion::

            from pytest_bdd import then

            @then("I should see the dashboard")
            def should_see_dashboard(page):
                assert "Dashboard" in page.title

        With parameterized pattern::

            from pytest_bdd import then, parsers

            @then(parsers.parse("I should see {count:d} results"))
            def should_see_results(count, results_page):
                assert len(results_page.get_results()) == count

    See Also:
        :func:`given`: Define precondition steps.
        :func:`when`: Define action steps.
        :func:`step`: Define liberal steps matching any keyword.

    Responsibility:
        Define a Then step that asserts expected outcomes in a scenario. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.decorators.then` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - StepDefinitionManager.decorator_builder: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `then`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `then`
        - src/pytest_bdd/steps/__init__.py: imports or references `then`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.outcome,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def step(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Define a liberal step that can match any Gherkin keyword (Given/When/Then).

    Liberal steps are registered with ``PickleStepType.unknown`` and
    can match scenario steps regardless of their keyword. This is
    useful for step definitions that are semantically neutral or
    applicable across multiple step types (e.g., shared utility steps
    like "I wait for the page to load").

    A step decorated with ``@step`` matches when no specific
    Given/When/Then step definition matches the step text, or when
    the ``liberal`` configuration is enabled (via the ``liberal_steps``
    ini option or CLI flag) allowing liberal steps to match even when
    a keyword-specific definition exists but has a different step type.

    Use ``@step`` instead of ``@given``/``@when``/``@then`` when:
    - The step definition is reusable across Given, When, and Then contexts.
    - The step performs a side-effect that is not specific to any phase.
    - You want to reduce step definition duplication.

    Prefer ``@given``/``@when``/``@then`` when:
    - The step has a clear semantic role (precondition, action, assertion).
    - You want precise control over step matching order.
    - Your team follows strict Gherkin conventions.

    Args:
        parserlike: Step pattern string or parser object. A plain
            string matches the step text literally. Parser objects
            from ``pytest_bdd.parsers`` enable parameter extraction.
        anonymous_group_names: Names for unnamed regex capture groups
            in ``parsers.re()`` patterns.
        converters: Dictionary mapping parameter names to converter
            functions (e.g., ``{"count": int}``).
        target_fixture: Name of a single pytest fixture to populate
            with the return value. Mutually exclusive with
            ``target_fixtures``.
        target_fixtures: Sequence of fixture names to populate.
            Mutually exclusive with ``target_fixture``.
        params_fixtures_mapping: Controls parameter-to-fixture
            injection. ``True`` (default), ``False``, collection,
            or dict.
        param_defaults: Default values for unmatched parameters.
        liberal: Whether this step can match steps with different
            keywords. ``None`` uses the project-wide config default.
            When ``True``, this step can match any keyword even if
            a keyword-specific definition exists.
        stacklevel: Caller frame depth for fixture injection.

    Returns:
        A ``StepDecorator`` — a decorator to apply to step definition
        functions.

    Example:
        Liberal step matching any keyword::

            from pytest_bdd import step

            @step("the page is loaded")
            def wait_for_page(page):
                page.wait_for_ready()

        This matches "Given the page is loaded", "When the page is loaded",
        and "Then the page is loaded" equally.

        With parameterized pattern::

            from pytest_bdd import step, parsers

            @step(parsers.parse("I wait {seconds:d} seconds"))
            def wait(seconds):
                time.sleep(seconds)

    See Also:
        :func:`given`: Define precondition steps (PickleStepType.context).
        :func:`when`: Define action steps (PickleStepType.action).
        :func:`then`: Define assertion steps (PickleStepType.outcome).

    Responsibility:
        Define a liberal step that can match any Gherkin keyword (Given/When/Then). It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.decorators.step` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - StepDefinitionManager.decorator_builder: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `step`
        - src/pytest_bdd/model/feature_binding.py: imports or references `step`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `step`
        - src/pytest_bdd/model/run_access.py: imports or references `step`
        - src/pytest_bdd/model/scenario_report.py: imports or references `step`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.unknown,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )
