"""
Owns the outcome observation and status derivation logic for the message stream validation system.

Responsibility:
    Owns the outcome observation and status derivation logic for the message stream validation system. Defines the
    OUTCOME_SCOPE_BY_PAYLOAD_KIND mapping that assigns each finished/attachment payload kind to an outcome scope
    (run/scenario/step/hook/attachment), implements observed_outcome_from_envelope() to extract a structured
    ObservedOutcome from a single EventEnvelope by resolving its payload kind, determining its outcome scope, and
    deriving its outcome status through _derive_outcome_status() which applies payload-kind-specific status derivation
    rules (test_step → result.status, test_case → implementation_status, test_run → success flag, test_run_hook →
    result.status, attachment → always passed). Also provides collect_observed_outcomes() (batch extraction) and
    default_outcome_mapping_rules() (generates default governance mapping rules for all scope × status combinations).

Reason for existence:
    Outcome observation is a distinct subdomain of message validation — it answers "what outcomes occurred?" while
    pipeline.py answers "are the messages well-formed?" This separation prevents pipeline.py from having to know about
    outcome scope classification, status derivation algorithms, or mapping rule generation. The
    OUTCOME_SCOPE_BY_PAYLOAD_KIND mapping is the key architectural decision: it encodes which message types carry
    outcome-relevant information and at what scope. Without this module, the outcome mapping diagnostics in
    validate_message_stream would need to embed this knowledge directly, making the already-long pipeline function even
    longer and mixing two different validation concerns.

Delegates:
    - get_payload_kind (from pytest_bdd.model.message_extension): Extracts the payload kind string from an EventEnvelope
    for scope lookup.
    - normalize_outcome_status (from pytest_bdd.model.message_outcome_mapping): Normalizes raw outcome status values to
    canonical OutcomeStatus enum values.
    - normalize_capability_status (from pytest_bdd.model.message_status_governance): Normalizes implementation_status
    values for capability-based outcome derivation.
    - ObservedOutcome (from pytest_bdd.model.message_outcome_mapping): The structured result type produced by
    observed_outcome_from_envelope.
    - OutcomeMappingRule (from pytest_bdd.model.message_outcome_mapping): The type produced by
    default_outcome_mapping_rules for governance mapping.
    - returns.maybe.Nothing: Provides the Maybe-type None value for return from functions that may not produce a result.

Cohesion:
    All entities in this module answer the question "what outcomes are observed in a message stream?" The
    OUTCOME_SCOPE_BY_PAYLOAD_KIND constant maps payload kinds to scopes, _derive_outcome_status determines the actual
    status for each kind, observed_outcome_from_envelope combines scope + status into an ObservedOutcome,
    collect_observed_outcomes batches the per-envelope extraction, and default_outcome_mapping_rules generates the
    governance mapping rules that consume these outcomes. Each function builds on the previous one in a clear pipeline.

Separation:
    - pytest_bdd.message_stream_validation.pipeline: Kept separate because pipeline.py owns stream-level validation
    (lifecycle ordering, schema validation, coverage tracking) while status.py owns outcome observation (per-envelope
    outcome extraction) — cross-envelope validation vs per-envelope observation, different granularities.
    - pytest_bdd.model.message_outcome_mapping: Kept separate because that module owns the outcome data types
    (ObservedOutcome, OutcomeMappingRule) and validation logic (validate_outcome_mappings), while status.py owns the
    extraction and derivation logic to produce those types — producer vs types/validator.

Main consumers:
    - pytest_bdd.message_stream_validation.pipeline.validate_message_stream: Calls collect_observed_outcomes() and
    default_outcome_mapping_rules() during the optional outcome mapping diagnostics stage.
    - pytest_bdd.message_stream_validation.facade: Re-exports collect_observed_outcomes, observed_outcome_from_envelope,
    and default_outcome_mapping_rules through the public API.
    - Test suites for outcome mapping: Use observed_outcome_from_envelope to test individual envelope outcome extraction.

State and side effects:
    None, keeps no persistent state. All functions are pure (same input → same output). The
    OUTCOME_SCOPE_BY_PAYLOAD_KIND constant is module-level immutable dict.

Invariants:
    - OUTCOME_SCOPE_BY_PAYLOAD_KIND must map every payload kind that can carry outcome information to a valid
    OutcomeScope — missing mappings would cause outcome observations to be silently dropped.
    - _derive_outcome_status must return None for payload kinds that don't carry outcome status, preventing false
    outcome observations.
    - default_outcome_mapping_rules must generate rules for all OutcomeScope × OutcomeStatus combinations defined in the
    scopes and statuses tuples.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
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
    Thin wrapper around normalize_outcome_status from pytest_bdd.model.message_outcome_mapping that normalizes a raw outc.

    Responsibility:
        Thin wrapper around normalize_outcome_status from pytest_bdd.model.message_outcome_mapping that normalizes a raw
        outcome status value (e.g., "PASSED", "passed", "FAILED") to a canonical OutcomeStatus string (e.g., "passed",
        "failed"). Returns None if the value cannot be normalized. This isolates the status module from changes to the
        normalization function's import path or signature.

    Reason for existence:
        Acts as a local re-export point within the status module, keeping the import of normalize_outcome_status
        centralized. If the normalization function moves or its signature changes, only this wrapper and
        observed_outcome_from_envelope need updating, not every function that derives outcome statuses. The indirection
        is minimal (direct pass-through) but provides import stability for the status module's internal functions.

    Delegates:
        - normalize_outcome_status (from pytest_bdd.model.message_outcome_mapping): Performs the actual status string
        normalization to canonical OutcomeStatus values.

    Cohesion:
        The function performs exactly one delegation call. It exists purely for import isolation, not for algorithmic value.

    Separation:
        - _derive_outcome_status: Kept separate because that function determines what status to derive from which
        payload attribute, while this function only performs normalization — derivation logic vs normalization utility.

    Main consumers:
        - _derive_outcome_status: Called to normalize the extracted status values from payload attributes
        (test_step_result.status, result.status).

    State and side effects:
        None, keeps no persistent state. Pure delegation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return normalize_outcome_status(value)


def _derive_outcome_status(payload_kind: str, payload: object) -> OutcomeStatus | None:
    """
    Derive the canonical outcome status from a message payload based on its payload kind, applying kind-specific status .

    Responsibility:
        Derives the canonical outcome status from a message payload based on its payload kind, applying kind-specific
        status extraction rules: test_step_finished → test_step_result.status (normalized), test_case_finished → derived
        from implementation_status (Not-Acceptable → "failed", Implemented/Partly-Applicable/Not-Applicable/Non-
        Implementable → "passed"), with will_be_retried check for "interrupted", test_run_finished → success boolean →
        "passed"/"failed", test_run_hook_finished → result.status (normalized, defaulting to "passed"),
        attachment/external_attachment → always "passed". Returns None for payload kinds that don't carry outcome
        information.

    Reason for existence:
        Each message type in the cucumber-messages protocol has a different attribute path to the status information:
        test_step_finished has test_step_result.status (an enum), test_case_finished has implementation_status (a
        governance string), test_run_finished has a boolean success flag, and test_run_hook_finished has result.status.
        This function encapsulates all this heterogeneous extraction logic in one place so that
        observed_outcome_from_envelope can be a simple two-step process: find the scope, derive the status. Without this
        function, the status extraction logic would be duplicated or scattered across the validation pipeline.

    Delegates:
        - getattr(payload, ...): Accesses status-related attributes on the payload object with None defaults for missing
        attributes.
        - _normalize_outcome_status: Normalizes raw status string values to canonical OutcomeStatus.
        - normalize_capability_status (from message_status_governance): Normalizes implementation_status strings for
        test_case_finished outcome derivation.

    Cohesion:
        The function contains a single dispatch chain (if/elif) where each branch handles one payload kind's status
        extraction. Every branch follows the same pattern: access attribute(s) → normalize/derive → return status. The
        attachment branch is the simplest (always "passed") and the test_case_finished branch is the most complex
        (multiple statuses checked, retry flag considered).

    Separation:
        - observed_outcome_from_envelope: Kept separate because that function determines the outcome scope (which
        payload kinds produce outcomes) and constructs ObservedOutcome objects, while this function only derives the
        status string — scope resolution vs status derivation.

    Main consumers:
        - observed_outcome_from_envelope: Called after determining the outcome scope to derive the status value for the
        ObservedOutcome construction.

    State and side effects:
        None, keeps no persistent state. Pure function of the payload kind and payload object.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
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
    Extract a structured ObservedOutcome from a single EventEnvelope by: (1) determining the payload kind via get_payloa.

    Responsibility:
        Extracts a structured ObservedOutcome from a single EventEnvelope by: (1) determining the payload kind via
        get_payload_kind(), (2) looking up the outcome scope from OUTCOME_SCOPE_BY_PAYLOAD_KIND, (3) deriving the
        outcome status via _derive_outcome_status(), and (4) populating is_retry and is_parallel_worker flags from the
        payload's will_be_retried and worker_id attributes. Returns None if the envelope's payload kind has no outcome
        scope mapping or if no status can be derived. This is the single-envelope outcome extraction entry point used by
        the batch collector.

    Reason for existence:
        Encapsulates the complete "one envelope → one outcome" transformation in a single function. The pipeline's
        outcome mapping diagnostics stage needs to extract outcomes from every envelope in a stream, and this function
        provides a uniform interface: pass an envelope, get back either a structured ObservedOutcome (with scope,
        status, retry flag, worker flag) or None (if the envelope doesn't carry outcome information). The is_retry and
        is_parallel_worker flags are extracted here because they are context metadata on the payload that affects how
        outcomes should be mapped.

    Delegates:
        - get_payload_kind: Extracts the payload kind string from the EventEnvelope.
        - OUTCOME_SCOPE_BY_PAYLOAD_KIND: Maps payload kind to outcome scope (run/scenario/step/hook/attachment).
        - _derive_outcome_status: Derives the canonical outcome status from the payload's attributes.
        - getattr(payload, ...): Extracts will_be_retried and worker_id flags from the payload.

    Cohesion:
        The function performs a single pipeline: payload_kind → scope → status → metadata flags → ObservedOutcome. Each
        step is a prerequisite for the next, and all steps are necessary to produce the final result.

    Separation:
        - collect_observed_outcomes: Kept separate because that function batches the per-envelope extraction across a
        list, while this function handles a single envelope — single vs batch.
        - _derive_outcome_status: Kept separate because that function only derives the status string, while this
        function combines scope + status + metadata into an ObservedOutcome — component extraction vs object
        construction.

    Main consumers:
        - collect_observed_outcomes: Iterates over envelopes and calls this function for each, collecting non-None results.
        - Test suites: May call this function directly to verify outcome extraction for specific envelope types.

    State and side effects:
        None, keeps no persistent state. Pure function of the input envelope.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
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
    Batches the per-envelope outcome extraction by iterating over a list of EventEnvelope objects, calling observed_outco.

    Responsibility:
        Batches the per-envelope outcome extraction by iterating over a list of EventEnvelope objects, calling
        observed_outcome_from_envelope() for each, and collecting all non-None results into a list. This is the entry
        point used by validate_message_stream's outcome mapping diagnostics stage to gather all observed outcomes from a
        complete message stream for mapping validation.

    Reason for existence:
        This function exists as a trivial batch wrapper to keep the "iterate over envelopes → call extractor → filter
        Nones" pattern in one place. While simple enough to inline, having this as a named function makes the intent
        explicit in validate_message_stream and provides a single point for adding filtering or transformation logic in
        the future (e.g., deduplication by outcome key, sorting by scope).

    Delegates:
        - observed_outcome_from_envelope: Performs the actual per-envelope outcome extraction, returning ObservedOutcome
        or None.

    Cohesion:
        The function performs exactly one operation: batch extraction with None filtering. The for loop, isinstance
        check, and list append all serve this single purpose.

    Separation:
        - observed_outcome_from_envelope: Kept separate because that function handles single-envelope extraction (the
        algorithm) while this function handles batch iteration (the collection pattern) — algorithm vs batch
        orchestration.
        - default_outcome_mapping_rules: Kept separate because that function generates mapping rules for governance,
        while this function collects the outcomes to be mapped — data collection vs rule generation.

    Main consumers:
        - validate_message_stream (in pipeline.py): Called when enforce_mapping_diagnostics=True to collect outcomes for
        mapping validation.
        - pytest_bdd.message_stream_validation.facade: Re-exported through the public API.

    State and side effects:
        None, keeps no persistent state. Creates a local list and returns it.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
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
    Generate the default set of outcome mapping rules for governance validation by creating the Cartesian product of 5 o.

    Responsibility:
        Generates the default set of outcome mapping rules for governance validation by creating the Cartesian product
        of 5 outcome scopes (run, scenario, step, hook, attachment) × 5 outcome statuses (passed, failed, skipped,
        undefined, interrupted), resulting in 25 default rules. Each rule has a unique mapping_id
        ("default-{scope}-{status}"), a generic capability_id, and a priority based on scope index. These rules serve as
        the fallback mapping when no custom rules are provided to validate_message_stream's outcome mapping diagnostics.

    Reason for existence:
        Outcome mapping diagnostics must have mapping rules to validate against, but users may not provide custom rules.
        This function generates a complete default rule set that covers all possible scope × status combinations,
        ensuring that the mapping validation always has rules to work with. Without this function,
        validate_message_stream would need to hardcode the 25 default rules, or every caller would need to pass
        mapping_rules explicitly. The priority assignment (0=run, 1=scenario, 2=step, 3=hook, 4=attachment) reflects the
        natural hierarchy of testing scopes.

    Delegates:
        - OutcomeMappingRule (from pytest_bdd.model.message_outcome_mapping): The data class constructor for individual
        mapping rules.

    Cohesion:
        Every aspect of this function serves rule generation: the scopes tuple defines the dimensions, the statuses
        tuple defines the values, and the nested comprehension generates the Cartesian product. The priority assignment
        uses enumerate for scope-level ordering.

    Separation:
        - collect_observed_outcomes: Kept separate because that function collects observed outcomes from messages, while
        this function generates mapping rules — data collection vs rule generation, complementary but distinct
        operations.
        - validate_outcome_mappings (from message_outcome_mapping): Kept separate because that function validates
        observed outcomes against rules, while this function generates the rules — rule consumer vs rule producer.

    Main consumers:
        - validate_message_stream (in pipeline.py): Used as the default value for mapping_rules when
        enforce_mapping_diagnostics=True and no custom rules are provided.
        - pytest_bdd.message_stream_validation.facade: Re-exported through the public API.

    State and side effects:
        None, keeps no persistent state. Generates and returns a new list each call.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
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
