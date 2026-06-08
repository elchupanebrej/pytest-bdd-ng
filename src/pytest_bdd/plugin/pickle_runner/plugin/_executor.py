"""
Step execution methods for the PickleRunner — extracted to keep _plugin.py under 400 LOC.

Responsibility:
    Step execution methods for the PickleRunner — extracted to keep _plugin.py under 400 LOC. It directly owns the
    observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._executor` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _run_step_body: owns nested behavior below this boundary
    - _match_step_or_report_lookup_error: owns nested behavior below this boundary
    - _run_step_call: owns nested behavior below this boundary
    - _pytest_bdd_get_step_caller: owns nested behavior below this boundary
    - _inject_step_parameters_as_fixtures: owns nested behavior below this boundary
    - _get_step_function_kwargs: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates injectable_fixtures, step_run.status, step_params, request, step_registry; depends on
    __future__.annotations, logging, contextlib.suppress, functools.partial, itertools.zip_longest.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.plugin._executor` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises re-raise, RuntimeError, step_lookup_exception; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
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
    Execute a single step body with error handling and hook invocation.

    Responsibility:
        Execute a single step body with error handling and hook invocation. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._executor._run_step_body`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - request.config.getoption: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - self._invoke_bdd_hook: collaborator call used by this boundary
        - _match_step_or_report_lookup_error: collaborator call used by this boundary
        - RuntimeError: collaborator call used by this boundary
        - resolve_wip_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_run_step_body`

    State and side effects:
        mutates step_run.status, hook_kwargs, step_definition, step_run, msg.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._executor._run_step_body` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError, re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
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


def _match_step_or_report_lookup_error(  # noqa: PLR0913
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
    Match a step definition or report a lookup error to BDD hooks.

    Responsibility:
        Match a step definition or report a lookup error to BDD hooks. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.plugin._executor._match_step_or_report_lookup_error` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - self._match_to_step: collaborator call used by this boundary
        - self._invoke_bdd_hook: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references
          `_match_step_or_report_lookup_error`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
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


def _run_step_call(  # noqa: PLR0913
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
    Execute the step call after injecting parameters and invoking hooks.

    Responsibility:
        Execute the step call after injecting parameters and invoking hooks. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._executor._run_step_call`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - self._invoke_bdd_hook: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - self._inject_step_parameters_as_fixtures: collaborator call used by this boundary
        - dict: collaborator call used by this boundary
        - _get_step_function_kwargs: collaborator call used by this boundary
        - _inject_target_fixtures: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_run_step_call`

    State and side effects:
        mutates step_function_kwargs, step_caller, step_result.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._executor._run_step_call` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
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
    Get step caller function.

    Returns:
        Callable that executes the step as a fixture.

    Responsibility:
        Get step caller function. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.plugin._executor._pytest_bdd_get_step_caller` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - partial: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_pytest_bdd_get_step_caller`

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
        #arch-eval:locational_stability=3

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
    params_fixtures_mapping: bool | Collection[str] | Mapping[object, str | None] | None = None,  # noqa: FBT001
) -> None:
    """
    Inject step parameters as pytest fixtures based on the parameter-to-fixture mapping.

    Responsibility:
        Inject step parameters as pytest fixtures based on the parameter-to-fixture mapping. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.plugin._executor._inject_step_parameters_as_fixtures` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - DefaultMapping.instantiate_from_collection_or_bool: collaborator call used by this boundary
        - step_params.keys: collaborator call used by this boundary
        - resolved_mapping.items: collaborator call used by this boundary
        - inject_fixture: collaborator call used by this boundary
        - self._require_request: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references
          `_inject_step_parameters_as_fixtures`

    State and side effects:
        mutates step_params, resolved_mapping.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._executor._inject_step_parameters_as_fixtures` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
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
    Resolve step function keyword arguments from parameters and fixtures.

    Responsibility:
        Resolve step function keyword arguments from parameters and fixtures. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.plugin._executor._get_step_function_kwargs` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - self._require_request: collaborator call used by this boundary
        - get_args: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - request.getfixturevalue: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_get_step_function_kwargs`

    State and side effects:
        mutates request.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._executor._get_step_function_kwargs` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    request = self._require_request()
    for param in get_args(cast("ObjectCallable", step_definition.func)):
        try:
            yield param, step_params[param]
        except KeyError:  # noqa: PERF203
            try:
                yield param, {"step": step}[param]
            except KeyError:
                yield param, request.getfixturevalue(param)


def _inject_target_fixtures(self: Any, step_definition: Definition, step_result: object) -> None:
    """
    Inject step result into target fixtures based on step definition configuration.

    Responsibility:
        Inject step result into target fixtures based on step definition configuration. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.plugin._executor._inject_target_fixtures` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - len: collaborator call used by this boundary
        - zip: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - zip_longest: collaborator call used by this boundary
        - inject_fixture: collaborator call used by this boundary
        - self._require_request: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_inject_target_fixtures`

    State and side effects:
        mutates injectable_fixtures.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._executor._inject_target_fixtures` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
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
    Match the current step to a registered step definition.

    Responsibility:
        Match the current step to a registered step definition. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._executor._match_to_step`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - require_step_object: collaborator call used by this boundary
        - request.config.hook.pytest_bdd_match_step_definition_to_step: collaborator call used by this boundary
        - run.require_active_scenario_run: collaborator call used by this boundary
        - exceptions.StepDefinitionNotFoundError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_match_to_step`

    State and side effects:
        mutates step_registry, undefined_info, step, request, scenario_run.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._executor._match_to_step` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises step_lookup_exception; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
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
                    if isinstance(candidate, tuple) and len(candidate) == 2 and candidate[1]:  # noqa: PLR2004
                        undefined_info = (str(candidate[0]), str(candidate[1]))
                        break
                if undefined_info is not None:
                    break
                step_registry = step_registry.parent
            if undefined_info is not None:
                step_lookup_exception.undefined_parameter_type = undefined_info
        raise step_lookup_exception from exception
