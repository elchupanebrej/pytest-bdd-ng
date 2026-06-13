"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
"""

from __future__ import annotations

import logging
from contextlib import suppress
from functools import partial
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, cast

import pytest
from cucumber_messages import PickleStep  # upstream library missing type stubs

import pytest_bdd.types.exception as exceptions
from pytest_bdd.compatibility.pytest import FixtureRequest, call_fixture_func
from pytest_bdd.model.run import Run, RunStatus
from pytest_bdd.model.run_access import (
    require_step_object,
)
from pytest_bdd.model.scenario_run import ScenarioRun
from pytest_bdd.steps import Definition, Matcher
from pytest_bdd.util.inspect_extra import get_args
from pytest_bdd.util.pytest_extra import inject_fixture
from pytest_bdd.util.toolz_extra import DefaultMapping, ObjectCallable

from ..const import Steps
from ..status_policy import resolve_tolerant_status, resolve_wip_status

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Iterator, Mapping

    from pytest_bdd.plugin.pickle_runner.plugin._plugin import _FixtureCaller, _StepCaller

logger = logging.getLogger(__name__)


def _run_step_body(  # noqa: PLR0913  # type: ignore[no-untyped-def]  # module-level self-pattern for method-like usage
    self: Any,
    *,
    request: FixtureRequest,
    run: Run,
    gherkin_document: Any,
    pickle: Any,
    step: PickleStep,
    previous_step: Any,
    scenario_run: ScenarioRun,
) -> None:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    hook_kwargs: dict[str, object] = {
        "request": request,
        "run": run,
        "step_func_args": {},
    }

    step_definition = _match_step_or_report_lookup_error(
        self,
        request=request,
        run=run,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
    )
    hook_kwargs["step_func"] = step_definition.func
    hook_kwargs["step_definition"] = step_definition

    step_run = scenario_run.step_run
    if step_run is None:
        msg = "Step run is unavailable in _run_step_body; step context was not initialized."
        raise RuntimeError(msg)

    if step_definition.not_implemented:
        policy = resolve_wip_status(
            request.node,
            request.config.getoption(str(Steps.Cli.WIP_STATUS), default="failed"),
        )
        if policy.value == "passed":
            step_run.status = RunStatus.ok
            return
        if policy.value == "skipped":
            pytest.skip("not implemented step")

    self._invoke_bdd_hook(
        hook_name="pytest_bdd_before_step",
        request=request,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
        step_func=step_definition.func,
    )

    step_params = step_definition.get_parameters(request, step)
    step_run.parameters = step_params

    try:
        _run_step_call(
            self,
            hook_kwargs=hook_kwargs,
            request=request,
            gherkin_document=gherkin_document,
            pickle=pickle,
            step=step,
            previous_step=previous_step,
            step_definition=step_definition,
            step_params=step_params,
        )
    except Exception as exception:
        logger.warning("Step execution failed for %s", step.text, exc_info=True)
        step_run.status = RunStatus.failed

        self._invoke_bdd_hook(
            hook_name="pytest_bdd_step_error",
            request=request,
            gherkin_document=gherkin_document,
            pickle=pickle,
            step=step,
            previous_step=previous_step,
            status=RunStatus.failed,
            step_func=step_definition.func,
            step_func_args=hook_kwargs["step_func_args"],
            step_definition=step_definition,
            exception=exception,
        )
        if step_definition.tolerant:
            tolerant_policy = resolve_tolerant_status(
                request.node,
                request.config.getoption(str(Steps.Cli.TOLERANT_STATUS), default="failed"),
            )
            if tolerant_policy.value == "ignored":
                scenario_run.status = RunStatus.ok
                run.status = RunStatus.ok
                return
        raise


def _match_step_or_report_lookup_error(  # noqa: PLR0913  -- suppressed warning
    self: Any,
    *,
    request: FixtureRequest,
    run: Run,
    gherkin_document: Any,
    pickle: Any,
    step: PickleStep,
    previous_step: Any,
) -> Definition:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    try:
        return cast("Definition", self._match_to_step(run))
    except exceptions.StepDefinitionNotFoundError as exception:
        self._invoke_bdd_hook(
            hook_name="pytest_bdd_step_func_lookup_error",
            request=request,
            gherkin_document=gherkin_document,
            pickle=pickle,
            step=step,
            previous_step=previous_step,
            status=RunStatus.failed,
            exception=exception,
        )
        raise


def _run_step_call(  # noqa: PLR0913  -- suppressed warning
    self: Any,
    *,
    hook_kwargs: dict[str, object],
    request: FixtureRequest,
    gherkin_document: Any,
    pickle: Any,
    step: PickleStep,
    previous_step: Any,
    step_definition: Definition,
    step_params: Mapping[str, object],
) -> None:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    self._inject_step_parameters_as_fixtures(
        step_params=step_params,
        params_fixtures_mapping=step_definition.params_fixtures_mapping,
    )

    step_function_kwargs = dict(_get_step_function_kwargs(self, step, step_definition, step_params))
    hook_kwargs["step_func_args"] = step_function_kwargs

    self._invoke_bdd_hook(
        hook_name="pytest_bdd_before_step_call",
        request=request,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
        step_func=step_definition.func,
        step_func_args=step_function_kwargs,
        step_definition=step_definition,
    )

    step_caller = self._invoke_bdd_hook(
        hook_name="pytest_bdd_get_step_caller",
        request=request,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
        step_func=step_definition.func,
        step_func_args=step_function_kwargs,
        step_definition=step_definition,
    )
    step_result = cast("_StepCaller", step_caller)()

    _inject_target_fixtures(self, step_definition, step_result)
    self._invoke_bdd_hook(
        hook_name="pytest_bdd_after_step",
        request=request,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
        step_func=step_definition.func,
        step_func_args=step_function_kwargs,
        step_definition=step_definition,
    )


def _pytest_bdd_get_step_caller(
    self: Any,
    request: FixtureRequest,
    run: Run,
    step_func: object,
    step_func_args: Mapping[str, object],
    step_definition: Definition,
) -> Callable[[], object]:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    return partial(
        cast("_FixtureCaller", call_fixture_func),
        fixturefunc=step_definition.func,
        request=request,
        kwargs=step_func_args,
    )


def _inject_step_parameters_as_fixtures(
    self: Any,
    step_params: Mapping[str, object] | None = None,
    params_fixtures_mapping: bool | Collection[str] | Mapping[object, str | None] | None = None,  # noqa: FBT001  -- suppressed warning
) -> None:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    step_params = step_params or {}
    resolved_mapping: Mapping[object, object] = DefaultMapping.instantiate_from_collection_or_bool(
        params_fixtures_mapping if params_fixtures_mapping is not None else {},
        warm_up_keys=step_params.keys(),
    )

    for param, fixture_name in resolved_mapping.items():
        if param is ... or fixture_name is None or fixture_name is ...:
            continue
        inject_fixture(self._require_request(), str(fixture_name), step_params[str(param)])


def _get_step_function_kwargs(
    self: Any,
    step: PickleStep,
    step_definition: Definition,
    step_params: Mapping[str, object],
) -> Iterator[tuple[str, object]]:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    request = self._require_request()
    for param in get_args(cast("ObjectCallable", step_definition.func)):
        try:
            yield param, step_params[param]
        except KeyError:  # noqa: PERF203  -- suppressed warning
            try:
                yield param, {"step": step}[param]
            except KeyError:
                yield param, request.getfixturevalue(param)


def _inject_target_fixtures(self: Any, step_definition: Definition, step_result: object) -> None:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    if len(step_definition.target_fixtures) == 1:
        injectable_fixtures: Iterable[tuple[str, object]] = [(step_definition.target_fixtures[0], step_result)]
    elif step_result is not None and len(step_definition.target_fixtures) != 0:
        injectable_fixtures = zip(
            step_definition.target_fixtures,
            cast("Iterable[object]", step_result),
            strict=False,
        )
    else:
        injectable_fixtures = zip_longest(step_definition.target_fixtures, [])

    for target_fixture, return_value in injectable_fixtures:
        inject_fixture(self._require_request(), str(target_fixture), return_value)


def _match_to_step(self: Any, run: Run) -> Definition:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    step = require_step_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
    request = cast("FixtureRequest", self.request)
    try:
        return cast(
            "Definition",
            request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=request,
                run=run,
            ),
        )
    except Matcher.MatchNotFoundError as exception:
        scenario_run = run.require_active_scenario_run(hook_name="pytest_bdd_match_step_definition_to_step")
        step_to_report = scenario_run.step_run if scenario_run.step_run is not None else step
        step_lookup_exception = exceptions.StepDefinitionNotFoundError(
            self._require_gherkin_document(),
            self._require_pickle(),
            step_to_report,
        )
        with suppress(Exception):
            step_registry = request.getfixturevalue("step_registry")
            undefined_info = None
            while step_registry is not None:
                for step_definition in step_registry:
                    candidate = getattr(step_definition.parser, "last_undefined_parameter_type", None)
                    if isinstance(candidate, tuple) and len(candidate) == 2 and candidate[1]:  # noqa: PLR2004  -- suppressed warning
                        undefined_info = (str(candidate[0]), str(candidate[1]))
                        break
                if undefined_info is not None:
                    break
                step_registry = step_registry.parent
            if undefined_info is not None:
                step_lookup_exception.undefined_parameter_type = undefined_info
        raise step_lookup_exception from exception
