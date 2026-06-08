"""
Provide run access helpers.

Responsibility:
    Provide run access helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run_access` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - resolve_feature_binding: owns nested behavior below this boundary
    - require_feature_binding: owns nested behavior below this boundary
    - require_feature_object: owns nested behavior below this boundary
    - require_pickle_object: owns nested behavior below this boundary
    - require_step_object: owns nested behavior below this boundary
    - resolve_feature_object: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `run_access`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `run_access`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `run_access`
    - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `run_access`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `run_access`

State and side effects:
    mutates scenario_run, run_ref, node, binding, message; depends on __future__.annotations, contextlib.suppress,
    typing.TYPE_CHECKING, returns.maybe.Nothing, pytest_bdd.model.run.ActiveObjectSet.

Invariants:
    - `pytest_bdd.model.run_access` keeps its documented import path, ownership boundary, and observable behavior stable
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
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from returns.maybe import Nothing

from pytest_bdd.model.run import (
    ActiveObjectSet,
    ContextErrorState,
    LifecycleKind,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    Run,
    RunStage,
)
from pytest_bdd.model.run.transitions import build_lifecycle_ref

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source

    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
    from pytest_bdd.model.scenario_run import ScenarioRun
    from pytest_bdd.types.protocol import Identifiable


def resolve_feature_binding(run: Run) -> FeatureRuntimeBinding | None:
    """
    Resolve feature binding from run.

    Args:
        run: Current run.

    Returns:
        Feature binding or None.

    Responsibility:
        Resolve feature binding from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_feature_binding` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_feature_binding`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_feature_binding`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_feature_binding`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_feature_binding`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_feature_binding`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_feature_binding` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    scenario_run = run.active_scenario_run
    return scenario_run.feature_binding if scenario_run is not None else None


def require_feature_binding(run: Run, *, hook_name: str) -> FeatureRuntimeBinding:
    """
    Require feature binding from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Feature binding.

    Responsibility:
        Require feature binding from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.require_feature_binding` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - run.require_active_scenario_run: collaborator call used by this boundary
        - scenario_run.require_feature_binding: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `require_feature_binding`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_feature_binding`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_feature_binding`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `require_feature_binding`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `require_feature_binding`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.require_feature_binding` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_feature_binding(hook_name=hook_name)


def require_feature_object(run: Run, *, hook_name: str) -> GherkinDocument:
    """
    Require feature object from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Gherkin document.

    Responsibility:
        Require feature object from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.require_feature_object` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - run.require_active_scenario_run: collaborator call used by this boundary
        - scenario_run.require_gherkin_document: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `require_feature_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_feature_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_feature_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `require_feature_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `require_feature_object`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.require_feature_object` keeps its documented import path, ownership boundary, and
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_gherkin_document(hook_name=hook_name)


def require_pickle_object(run: Run, *, hook_name: str) -> Pickle:
    """
    Require pickle object from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Pickle object.

    Responsibility:
        Require pickle object from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.require_pickle_object` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - run.require_active_scenario_run: collaborator call used by this boundary
        - scenario_run.require_pickle: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `require_pickle_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_pickle_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_pickle_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `require_pickle_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `require_pickle_object`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.require_pickle_object` keeps its documented import path, ownership boundary, and
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_pickle(hook_name=hook_name)


def require_step_object(run: Run, *, hook_name: str) -> PickleStep:
    """
    Require step object from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Step object.

    Responsibility:
        Require step object from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.require_step_object` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - run.require_active_scenario_run: collaborator call used by this boundary
        - scenario_run.require_step_object: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `require_step_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_step_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_step_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `require_step_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `require_step_object`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.require_step_object` keeps its documented import path, ownership boundary, and
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_step_object(hook_name=hook_name)


def resolve_feature_object(run: Run) -> GherkinDocument | None:
    """
    Resolve feature object from run.

    Args:
        run: Current run.

    Returns:
        Gherkin document or None.

    Responsibility:
        Resolve feature object from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_feature_object` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_feature_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_feature_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_feature_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_feature_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_feature_object`

    State and side effects:
        mutates binding, scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_feature_object` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    binding = run.active_feature_binding
    if binding is not None:
        return binding.gherkin_document
    scenario_run = run.active_scenario_run
    return scenario_run.gherkin_document if scenario_run is not None else None


def resolve_feature_source(run: Run) -> Source | None:
    """
    Resolve feature source from run.

    Args:
        run: Current run.

    Returns:
        Source or None.

    Responsibility:
        Resolve feature source from run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_feature_source` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_feature_source`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_feature_source`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_feature_source`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_feature_source`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_feature_source`

    State and side effects:
        mutates binding, scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_feature_source` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    binding = run.active_feature_binding
    if binding is not None:
        return binding.source
    scenario_run = run.active_scenario_run
    return scenario_run.feature_source if scenario_run is not None else None


def resolve_pickle_object(run: Run) -> Pickle | None:
    """
    Resolve pickle object.

    Returns:
        Pickle object or None.

    Responsibility:
        Resolve pickle object. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_pickle_object` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_pickle_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_pickle_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_pickle_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_pickle_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_pickle_object`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_pickle_object` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    scenario_run = run.active_scenario_run
    return scenario_run.pickle if scenario_run is not None else None


def resolve_step_object(run: Run) -> PickleStep | None:
    """
    Resolve step object.

    Returns:
        Pickle step or None.

    Responsibility:
        Resolve step object. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_step_object` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_step_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_step_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_step_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_step_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_step_object`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_step_object` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    scenario_run = run.active_scenario_run
    return scenario_run.step_object if scenario_run is not None else None


def resolve_previous_step_object(run: Run) -> PickleStep | object | None:
    """
    Resolve previous step object.

    Returns:
        Previous step object or None.

    Responsibility:
        Resolve previous step object. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_previous_step_object` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_previous_step_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_previous_step_object`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_previous_step_object`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_previous_step_object`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_previous_step_object`

    State and side effects:
        mutates scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_previous_step_object` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    scenario_run = run.active_scenario_run
    return scenario_run.previous_step_object if scenario_run is not None else None


def resolve_active_object_or_error(
    *,
    hook_name: str,
    scenario_run: ScenarioRun,
    requested_kind: LifecycleKind,
) -> tuple[LifecycleObjectRef | None, ContextErrorState | None]:
    """
    Resolve active object or error.

    Returns:
        Tuple of (active object, error state).

    Responsibility:
        Resolve active object or error. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_active_object_or_error` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - scenario_run.get_active_object: collaborator call used by this boundary
        - scenario_run.record_context_error: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_active_object_or_error`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
          `resolve_active_object_or_error`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_active_object_or_error`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_active_object_or_error`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
          `resolve_active_object_or_error`

    State and side effects:
        mutates message, active_object, inactive_candidate, error.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_active_object_or_error` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    active_object = scenario_run.get_active_object(requested_kind)
    if active_object is not None:
        return active_object, None

    inactive_candidate = {
        "run": scenario_run.active_set.run,
        "feature": scenario_run.active_set.feature,
        "scenario": scenario_run.active_set.scenario,
        "step": scenario_run.active_set.step,
    }[requested_kind]
    message = (
        f"Lifecycle object '{requested_kind}' is unavailable during {hook_name} at stage '{scenario_run.stage.value}'"
    )
    if inactive_candidate.empty_state_reason is not None:
        message = f"{message} (empty state: {inactive_candidate.empty_state_reason})"
    error = scenario_run.record_context_error(
        code="object_inactive",
        message=message,
        hook_name=hook_name,
        requested_kind=requested_kind,
    )
    return Nothing.value_or(None), error


def _fallback_reporting_snapshot(
    request: FixtureRequest,
    *,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run_access._fallback_reporting_snapshot` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access._fallback_reporting_snapshot` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - Run.find_in_stash.value_or: collaborator call used by this boundary
        - Run.find_in_stash: collaborator call used by this boundary
        - build_lifecycle_ref: collaborator call used by this boundary
        - LifecycleObjectRef: collaborator call used by this boundary
        - id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `_fallback_reporting_snapshot`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_fallback_reporting_snapshot`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_fallback_reporting_snapshot`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `_fallback_reporting_snapshot`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_fallback_reporting_snapshot`

    State and side effects:
        mutates run_ref, run_id, run_root.

    Invariants:
        - `pytest_bdd.model.run_access._fallback_reporting_snapshot` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """
    run_root = Run.find_in_stash(request.config.stash).value_or(None)
    if run_root is None:
        run_ref = build_lifecycle_ref("run", getattr(request, "session", None), is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)
        run_id = f"run-{id(getattr(request, 'session', request))}"
    else:
        run_ref = run_root.run_ref
        run_id = run_root.id

    return ReportingContextSnapshot(
        run_id=run_id,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle),
        stage=RunStage.idle,
        resolved_from_hierarchy=False,
        fallback_reason=fallback_reason or "hierarchy_not_available",
    )


def build_reporting_context_snapshot(
    *,
    request: FixtureRequest,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot:
    """
    Build reporting context snapshot.

    Returns:
        Reporting context snapshot.

    Responsibility:
        Build reporting context snapshot. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.build_reporting_context_snapshot` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ReportingContextSnapshot: collaborator call used by this boundary
        - Run.find_in_stash.value_or: collaborator call used by this boundary
        - Run.find_in_stash: collaborator call used by this boundary
        - ActiveObjectSet: collaborator call used by this boundary
        - _fallback_reporting_snapshot: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `build_reporting_context_snapshot`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
          `build_reporting_context_snapshot`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references
          `build_reporting_context_snapshot`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `build_reporting_context_snapshot`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
          `build_reporting_context_snapshot`

    State and side effects:
        mutates run, active_scenario_run.

    Invariants:
        - `pytest_bdd.model.run_access.build_reporting_context_snapshot` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    run = Run.find_in_stash(request.config.stash).value_or(None)

    if run is not None and run.active_scenario_run is not None:
        active_scenario_run = run.active_scenario_run
        return ReportingContextSnapshot(
            run_id=run.id,
            active_set=active_scenario_run.active_set,
            stage=active_scenario_run.stage,
            resolved_from_hierarchy=True,
            fallback_reason=None,
        )
    if run is not None:
        return ReportingContextSnapshot(
            run_id=run.id,
            active_set=ActiveObjectSet(run=run.run_ref, captured_at_stage=RunStage.idle),
            stage=RunStage.idle,
            resolved_from_hierarchy=True,
            fallback_reason=fallback_reason or "run_has_no_active_scenario",
        )

    return _fallback_reporting_snapshot(request, fallback_reason=fallback_reason)


def resolve_registry_node(
    *,
    feature_binding: FeatureRuntimeBinding | None,
    ast_node_id: str,
    scenario_run: ScenarioRun | None = None,
) -> Identifiable | None:
    """
    Resolve registry node.

    Returns:
        Identifiable node or None.

    Responsibility:
        Resolve registry node. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_registry_node` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - suppress: collaborator call used by this boundary
        - feature_binding.resolve_node: collaborator call used by this boundary
        - scenario_run.reference_resolver.add_missing_reference: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_registry_node`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_registry_node`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_registry_node`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_registry_node`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_registry_node`

    State and side effects:
        mutates node.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_registry_node` keeps its documented import path, ownership boundary, and
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
    node = None
    if feature_binding is not None:
        with suppress(KeyError):
            node = feature_binding.resolve_node(ast_node_id)

    if node is None and scenario_run is not None:
        scenario_run.reference_resolver.add_missing_reference(f"Missing AST node id: {ast_node_id}")
    return node


def resolve_scenario_description(
    *,
    pickle: Pickle,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> str | None:
    """
    Resolve scenario description.

    Returns:
        Scenario description or None.

    Responsibility:
        Resolve scenario description. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_scenario_description` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - scenario_run.reference_resolver.add_missing_reference: collaborator call used by this boundary
        - resolve_registry_node: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_scenario_description`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_scenario_description`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_scenario_description`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_scenario_description`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_scenario_description`

    State and side effects:
        mutates ast_node_ids, ast_node_id, effective_binding, node, description.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_scenario_description` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    ast_node_ids = getattr(pickle, "ast_node_ids", None) or ()
    if not ast_node_ids:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference("Pickle has no ast_node_ids")
        return Nothing.value_or(None)
    ast_node_id = str(ast_node_ids[0])
    effective_binding = feature_binding or (scenario_run.feature_binding if scenario_run is not None else None)
    node = resolve_registry_node(
        feature_binding=effective_binding,
        ast_node_id=ast_node_id,
        scenario_run=scenario_run,
    )
    if node is None:
        return Nothing.value_or(None)
    description = getattr(node, "description", None)
    return str(description) if description is not None else None


def resolve_step_runtime_enrichment(
    *,
    step: PickleStep,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> dict[str, object]:
    """
    Resolve step runtime enrichment.

    Returns:
        Step runtime enrichment dictionary.

    Responsibility:
        Resolve step runtime enrichment. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run_access.resolve_step_runtime_enrichment` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - effective_binding.pickle_step_ast_step: collaborator call used by this boundary
        - scenario_run.reference_resolver.add_missing_reference: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - effective_binding.step_keyword: collaborator call used by this boundary
        - effective_binding.step_prefix: collaborator call used by this boundary
        - effective_binding.step_line_number: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `resolve_step_runtime_enrichment`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
          `resolve_step_runtime_enrichment`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `resolve_step_runtime_enrichment`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `resolve_step_runtime_enrichment`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
          `resolve_step_runtime_enrichment`

    State and side effects:
        mutates effective_binding, model_step.

    Invariants:
        - `pytest_bdd.model.run_access.resolve_step_runtime_enrichment` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    effective_binding = feature_binding or (scenario_run.feature_binding if scenario_run is not None else None)
    model_step = effective_binding.pickle_step_ast_step(step) if effective_binding is not None else None
    if model_step is None:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference(
                f"Missing pickle step mapping: {getattr(step, 'id', 'unknown')}",
            )
        return {
            "keyword": None,
            "prefix": None,
            "line_number": None,
            "doc_string": None,
            "data_table": None,
            "state": "unresolved",
            "reason": "missing_pickle_step_mapping",
        }
    return {
        "keyword": effective_binding.step_keyword(step) if effective_binding is not None else None,
        "prefix": effective_binding.step_prefix(step) if effective_binding is not None else None,
        "line_number": effective_binding.step_line_number(step) if effective_binding is not None else None,
        "doc_string": effective_binding.step_doc_string(step) if effective_binding is not None else None,
        "data_table": effective_binding.step_data_table(step) if effective_binding is not None else None,
        "state": "resolved",
        "reason": None,
    }
