"""
Best-effort pytest-bdd-ng metadata extraction for debug MCP.

Responsibility:
    Best-effort pytest-bdd-ng metadata extraction for debug MCP. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - BddContextExtractor: owns nested behavior below this boundary
    - enrich_failure_with_bdd_context: owns nested behavior below this boundary
    - _string_or_none: owns nested behavior below this boundary
    - _tags: owns nested behavior below this boundary
    - _step_keyword: owns nested behavior below this boundary
    - _example_row: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates feature, run, scenario_run, binding, pickle; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.cast, attrs, pytest_bdd.model.run.Run.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.bdd_adapter` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from typing import TYPE_CHECKING, cast

import attrs

from pytest_bdd.model.run import Run

from .schemas import BddMetadata

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config

    from .failure import QueuedFailure


class BddContextExtractor:
    """
    Extract BDD metadata from active pytest-bdd-ng runtime state.

    Responsibility:
        Extract BDD metadata from active pytest-bdd-ng runtime state. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter.BddContextExtractor` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - extract: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates feature, run, scenario_run, binding, pickle.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.bdd_adapter.BddContextExtractor` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    @staticmethod
    def extract(config: Config) -> BddMetadata | None:
        """
        Extract BDD metadata from config stash.

        Returns:
            BDD metadata when active scenario state exists, else None.

        Responsibility:
            Extract BDD metadata from config stash. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.bdd_adapter.BddContextExtractor.extract` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - _string_or_none: collaborator call used by this boundary
            - Run.find_in_stash.value_or: collaborator call used by this boundary
            - Run.find_in_stash: collaborator call used by this boundary
            - BddMetadata: collaborator call used by this boundary
            - _step_keyword: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates feature, run, scenario_run, binding, pickle.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.bdd_adapter.BddContextExtractor.extract` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2

        """
        run = Run.find_in_stash(config.stash).value_or(None)
        scenario_run = getattr(run, "active_scenario_run", None)
        if scenario_run is None:
            return None

        binding = getattr(scenario_run, "feature_binding", None)
        pickle = getattr(scenario_run, "pickle", None)
        step = getattr(scenario_run, "step_object", None)
        feature = getattr(getattr(scenario_run, "gherkin_document", None), "feature", None)
        if feature is None and binding is not None:
            feature = getattr(getattr(binding, "gherkin_document", None), "feature", None)

        feature_path = getattr(binding, "filename", None) or getattr(scenario_run, "feature_uri", None)
        return BddMetadata(
            feature_path=_string_or_none(feature_path),
            feature_name=_string_or_none(getattr(feature, "name", None)),
            scenario_name=_string_or_none(getattr(pickle, "name", None)),
            step_keyword=_step_keyword(binding, step),
            step_text=_string_or_none(getattr(step, "text", None)),
            tags=_tags(pickle),
            example_row=_example_row(binding, pickle),
        )


def enrich_failure_with_bdd_context(config: Config, failure: QueuedFailure) -> QueuedFailure:
    """
    Return queued failure with best-effort BDD metadata.

    Returns:
        Failure with BDD metadata dictionary, or original failure if none exists.

    Responsibility:
        Return queued failure with best-effort BDD metadata. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.debug_mcp.bdd_adapter.enrich_failure_with_bdd_context` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - attrs.evolve: collaborator call used by this boundary
        - BddContextExtractor.extract: collaborator call used by this boundary
        - metadata.model_dump: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `enrich_failure_with_bdd_context`

    State and side effects:
        mutates metadata.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.bdd_adapter.enrich_failure_with_bdd_context` keeps its documented import path,
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
    metadata = BddContextExtractor.extract(config)
    if metadata is None:
        return failure
    return attrs.evolve(failure, summary=attrs.evolve(failure.summary, bdd=metadata.model_dump(mode="json")))


def _string_or_none(value: object) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.bdd_adapter._string_or_none` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter._string_or_none` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return str(value) if value not in {None, ""} else None


def _tags(pickle: object | None) -> list[str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.bdd_adapter._tags` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter._tags` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - str.lstrip: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - result.append: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates tags, result, name, text.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.bdd_adapter._tags` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    tags = getattr(pickle, "tags", None) or ()
    result = []
    for tag in tags:
        name = getattr(tag, "name", tag)
        text = str(name).lstrip("@")
        if text:
            result.append(text)
    return sorted(result)


def _step_keyword(binding: object | None, step: object | None) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.bdd_adapter._step_keyword` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter._step_keyword` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - callable: collaborator call used by this boundary
        - resolver: collaborator call used by this boundary
        - _string_or_none: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `_step_keyword`

    State and side effects:
        mutates resolver, ast_step.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.bdd_adapter._step_keyword` keeps its documented import path, ownership boundary,
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
        #arch-eval:locational_stability=3
    """
    if binding is None or step is None:
        return None
    resolver = getattr(binding, "pickle_step_ast_step", None)
    if not callable(resolver):
        return None
    ast_step = resolver(step)
    return _string_or_none(getattr(ast_step, "keyword", None))


def _example_row(binding: object | None, pickle: object | None) -> dict[str, str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.bdd_adapter._example_row` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter._example_row` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _call_optional: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates breadcrumb.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.bdd_adapter._example_row` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if binding is None or pickle is None:
        return {}
    breadcrumb = _call_optional(binding, "pickle_table_rows_breadcrumb", pickle)
    if breadcrumb:
        return {"breadcrumb": str(breadcrumb)}
    return {}


def _call_optional(target: object, method_name: str, *args: object) -> object | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.bdd_adapter._call_optional` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.bdd_adapter._call_optional` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - callable: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - method: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates method.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.bdd_adapter._call_optional` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    method = getattr(target, method_name, None)
    if not callable(method):
        return None
    return cast("object | None", method(*args))
