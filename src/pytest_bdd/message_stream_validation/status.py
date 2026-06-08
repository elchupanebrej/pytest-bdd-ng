"""
Provide outcome status extraction and capability coverage helpers.

Responsibility:
    Provide outcome status extraction and capability coverage helpers. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.message_stream_validation.status` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _normalize_outcome_status: owns nested behavior below this boundary
    - _derive_outcome_status: owns nested behavior below this boundary
    - observed_outcome_from_envelope: owns nested behavior below this boundary
    - collect_observed_outcomes: owns nested behavior below this boundary
    - default_outcome_mapping_rules: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/facade.py: imports or references `status`
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `status`
    - src/pytest_bdd/model/heading_validation.py: imports or references `status`
    - src/pytest_bdd/model/message_governance_checklist.py: imports or references `status`
    - src/pytest_bdd/model/message_outcome_mapping.py: imports or references `status`

State and side effects:
    mutates result_status, result, outcome_status, OUTCOME_SCOPE_BY_PAYLOAD_KIND, test_step_result; depends on
    __future__.annotations, typing.Final, returns.maybe.Nothing, pytest_bdd.model.message_extension.EventEnvelope,
    pytest_bdd.model.message_extension.get_payload_kind.

Invariants:
    - `pytest_bdd.message_stream_validation.status` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from typing import Final

from returns.maybe import Nothing

from pytest_bdd.model.message_extension import EventEnvelope, get_payload_kind
from pytest_bdd.model.message_outcome_mapping import (
    ObservedOutcome,
    OutcomeMappingRule,
    OutcomeScope,
    OutcomeStatus,
    normalize_outcome_status,
)
from pytest_bdd.model.message_status_governance import normalize_capability_status

OUTCOME_SCOPE_BY_PAYLOAD_KIND: Final[dict[str, OutcomeScope]] = {
    "test_run_finished": "run",
    "test_case_finished": "scenario",
    "test_step_finished": "step",
    "test_run_hook_finished": "hook",
    "attachment": "attachment",
    "external_attachment": "attachment",
}


def _normalize_outcome_status(value: object) -> OutcomeStatus | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.message_stream_validation.status._normalize_outcome_status` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.status._normalize_outcome_status` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_outcome_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `_normalize_outcome_status`

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
    return normalize_outcome_status(value)


def _derive_outcome_status(payload_kind: str, payload: object) -> OutcomeStatus | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.message_stream_validation.status._derive_outcome_status` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.message_stream_validation.status._derive_outcome_status`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - _normalize_outcome_status: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - normalize_capability_status: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `_derive_outcome_status`

    State and side effects:
        mutates result_status, test_step_result, implementation_status, capability_status, will_be_retried.

    Invariants:
        - `pytest_bdd.message_stream_validation.status._derive_outcome_status` keeps its documented import path,
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
    if payload_kind == "test_step_finished":
        test_step_result = getattr(payload, "test_step_result", None)
        result_status = getattr(test_step_result, "status", None) if test_step_result is not None else None
        return _normalize_outcome_status(result_status)
    if payload_kind == "test_case_finished":
        implementation_status = getattr(payload, "implementation_status", None)
        if implementation_status is not None:
            capability_status = normalize_capability_status(str(implementation_status))
            if capability_status == "Not-Acceptable":
                return "failed"
            if capability_status in {"Implemented", "Partly-Applicable", "Not-Applicable", "Non-Implementable"}:
                return "passed"
        will_be_retried = getattr(payload, "will_be_retried", None)
        if isinstance(will_be_retried, bool) and will_be_retried:
            return "interrupted"
        return "passed"
    if payload_kind == "test_run_finished":
        success = getattr(payload, "success", None)
        if isinstance(success, bool):
            return "passed" if success else "failed"
    if payload_kind == "test_run_hook_finished":
        result = getattr(payload, "result", None)
        result_status = getattr(result, "status", None) if result is not None else None
        outcome_status = _normalize_outcome_status(result_status)
        return "passed" if outcome_status is None else outcome_status
    if payload_kind in {"attachment", "external_attachment"}:
        return "passed"
    return Nothing.value_or(None)


def observed_outcome_from_envelope(envelope: EventEnvelope) -> ObservedOutcome | None:
    """
    Extract and normalize the execution outcome status associated with a specific message envelope.

    Returns:
        An ObservedOutcome representing the status and context, or None if the payload does not carry an outcome.

    Responsibility:
        Extract and normalize the execution outcome status associated with a specific message envelope. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.status.observed_outcome_from_envelope` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - get_payload_kind: collaborator call used by this boundary
        - OUTCOME_SCOPE_BY_PAYLOAD_KIND.get: collaborator call used by this boundary
        - _derive_outcome_status: collaborator call used by this boundary
        - ObservedOutcome: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `observed_outcome_from_envelope`
        - src/pytest_bdd/model/__init__.py: imports or references `observed_outcome_from_envelope`
        - src/pytest_bdd/model/message_validation.py: imports or references `observed_outcome_from_envelope`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `observed_outcome_from_envelope`

    State and side effects:
        mutates payload_kind, outcome_scope, payload, outcome_status.

    Invariants:
        - `pytest_bdd.message_stream_validation.status.observed_outcome_from_envelope` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """
    payload_kind = get_payload_kind(envelope)
    if payload_kind is None:
        return Nothing.value_or(None)
    outcome_scope = OUTCOME_SCOPE_BY_PAYLOAD_KIND.get(payload_kind)
    if outcome_scope is None:
        return Nothing.value_or(None)
    payload = getattr(envelope, payload_kind)
    outcome_status = _derive_outcome_status(payload_kind, payload)
    if outcome_status is None:
        return Nothing.value_or(None)
    return ObservedOutcome(
        outcome_scope=outcome_scope,
        outcome_status=outcome_status,
        is_retry=bool(getattr(payload, "will_be_retried", False)),
        is_parallel_worker=getattr(payload, "worker_id", None) not in {None, "", "master"},
    )


def collect_observed_outcomes(envelopes: list[EventEnvelope]) -> list[ObservedOutcome]:
    """
    Iterate over a sequence of message envelopes, extracting all normalized observed execution outcomes.

    Returns:
        A list of ObservedOutcome instances harvested from the stream.

    Responsibility:
        Iterate over a sequence of message envelopes, extracting all normalized observed execution outcomes. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.status.collect_observed_outcomes` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - observed_outcome_from_envelope: collaborator call used by this boundary
        - outcomes.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `collect_observed_outcomes`
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `collect_observed_outcomes`
        - src/pytest_bdd/model/__init__.py: imports or references `collect_observed_outcomes`
        - src/pytest_bdd/model/message_validation.py: imports or references `collect_observed_outcomes`

    State and side effects:
        mutates outcomes, outcome.

    Invariants:
        - `pytest_bdd.message_stream_validation.status.collect_observed_outcomes` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """
    outcomes: list[ObservedOutcome] = []
    for envelope in envelopes:
        outcome = observed_outcome_from_envelope(envelope)
        if outcome is not None:
            outcomes.append(outcome)
    return outcomes


def default_outcome_mapping_rules() -> list[OutcomeMappingRule]:
    """
    Generate the standard baseline mapping rules for resolving execution outcomes across standard BDD scopes.

    Returns:
        A list of OutcomeMappingRule instances encoding the default governance rules.

    Responsibility:
        Generate the standard baseline mapping rules for resolving execution outcomes across standard BDD scopes. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.status.default_outcome_mapping_rules` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - enumerate: collaborator call used by this boundary
        - result.extend: collaborator call used by this boundary
        - OutcomeMappingRule: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `default_outcome_mapping_rules`
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `default_outcome_mapping_rules`
        - src/pytest_bdd/model/__init__.py: imports or references `default_outcome_mapping_rules`
        - src/pytest_bdd/model/message_validation.py: imports or references `default_outcome_mapping_rules`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `default_outcome_mapping_rules`

    State and side effects:
        mutates scopes, statuses, result.

    Invariants:
        - `pytest_bdd.message_stream_validation.status.default_outcome_mapping_rules` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """
    scopes: tuple[OutcomeScope, ...] = ("run", "scenario", "step", "hook", "attachment")
    statuses: tuple[OutcomeStatus, ...] = ("passed", "failed", "skipped", "undefined", "interrupted")
    result: list[OutcomeMappingRule] = []
    for scope_index, scope in enumerate(scopes):
        result.extend(
            OutcomeMappingRule(
                mapping_id=f"default-{scope}-{status}",
                outcome_scope=scope,
                outcome_status=status,
                capability_ids=(f"default.{scope}.{status}",),
                priority=scope_index,
                mapping_rationale="default-governance-mapping",
            )
            for status in statuses
        )
    return result
