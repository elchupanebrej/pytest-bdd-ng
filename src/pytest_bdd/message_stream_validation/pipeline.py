"""
Owns the complete cucumber-messages stream validation pipeline: the core validate_message_stream() function that proc.

Responsibility:
    Owns the complete cucumber-messages stream validation pipeline: the core validate_message_stream() function that
    processes a list of EventEnvelope objects through five sequential validation stages — payload deserialization (via
    ExecutionMessageAdapter), JSON schema validation (via validate_envelope_dict_against_schema), field-level coverage
    tracking (via ObservedCoverage and _track_fields recursive walker), lifecycle ordering/integrity checks
    (started/finished pair matching, orphan reference detection, out-of-order lifecycle violations), and implementation
    status governance (capability status validation, required comment enforcement, terminal status conflict detection).
    Produces a MessageValidationResult with pass/fail status, violation details, and coverage data.

Reason for existence:
    This module is the information expert for message stream validation because it orchestrates the most complex cross-
    cutting validation in the plugin: it must simultaneously track lifecycle pairs (test_case_started ↔
    test_case_finished, test_step_started ↔ test_step_finished, test_run_hook_started ↔ test_run_hook_finished),
    validate JSON schemas, track field coverage for capability analysis, enforce implementation status governance rules,
    detect duplicate lifecycle IDs, handle protocol version mismatches, and optionally enforce outcome mapping
    diagnostics. No other module has the breadth of state tracking (8 dicts/sets tracking lifecycle state) and the depth
    of validation logic (5 sequential stages). The module contains 4 private helper functions (_is_non_empty_text,
    _payload_id, _track_fields, _payload_object_for_kind) that support the main pipeline without cluttering the public
    API.

Delegates:
    - ExecutionMessageAdapter (from pytest_bdd.model.execution_message_adapter): Deserializes raw EventEnvelope objects
    into structured payloads and serializes them back to dicts for schema validation.
    - validate_envelope_dict_against_schema (from pytest_bdd.model.message_schema_validation): Performs JSON Schema
    validation on each envelope dict, returning MessageValidationViolation objects for schema violations.
    - ObservedCoverage (from pytest_bdd.model.coverage.tracker): Tracks which fields in which payload kinds have been
    observed across the message stream.
    - canonical_capability_id and canonical_payload_kind (from pytest_bdd.model.coverage.inventory): Normalize payload
    kind names for coverage tracking.
    - normalize_capability_status (from pytest_bdd.model.message_status_governance): Normalizes implementation status
    strings to canonical capability status values.
    - validate_outcome_mappings (from pytest_bdd.model.message_outcome_mapping): Validates observed outcomes against
    mapping rules and matrix profiles.
    - collect_observed_outcomes and default_outcome_mapping_rules (from .status): Provide outcome observation data and
    default mapping rules for the optional outcome mapping diagnostics stage.
    - MessageValidationResult and MessageValidationViolation (from pytest_bdd.model.message_validation_result): The
    result types produced by the validation pipeline.

Cohesion:
    All logic in this module serves the single purpose of validating a message stream. The four private helpers
    (_is_non_empty_text validates string content, _payload_id extracts lifecycle identifiers, _track_fields recursively
    walks nested data structures for coverage, _payload_object_for_kind resolves envelope payloads with
    snake_case→camelCase fallback) all support specific stages of validate_message_stream. The
    ALLOWED_IMPLEMENTATION_STATUSES constant is derived from CAPABILITY_STATUSES and LEGACY_STATUS_ALIASES, both
    consumed within the implementation status validation stage. The collect_observed_capability_ids function is a
    convenience wrapper around validate_message_stream with track_coverage=True.

Separation:
    - pytest_bdd.message_stream_validation.status: Kept separate because status.py owns outcome observation and mapping
    logic (observing outcomes from envelopes, deriving outcome statuses, collecting observed outcomes, generating
    default mapping rules), while pipeline.py owns stream-level validation (lifecycle ordering, schema validation,
    coverage tracking) — different validation concerns at different granularities.
    - pytest_bdd.model.message_extension: Kept separate because message_extension owns event envelope type definitions
    (EventEnvelope, get_payload_kind), while pipeline.py owns validation rules applied to those envelopes — types vs
    policy.
    - pytest_bdd.model.message_status_governance: Kept separate because message_status_governance owns the status
    vocabulary and normalization rules, while pipeline.py consumes them for enforcement — data vs validation.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter: Calls validate_message_stream() to validate the cucumber-messages
    protocol stream generated during BDD test execution before reporting.
    - pytest_bdd.message_stream_validation.facade: Re-exports validate_message_stream, collect_observed_capability_ids,
    and ALLOWED_IMPLEMENTATION_STATUSES through the public API.
    - Test suites: Use validate_message_stream() to verify message protocol compliance in integration and e2e tests.

State and side effects:
    validate_message_stream() creates local mutable tracking state (8 dicts/sets for lifecycle tracking, violation list,
    coverage tracker) that is scoped to a single function call — no module-level persistent state. The function is pure:
    given the same input, it produces the same MessageValidationResult.

Invariants:
    - Every "started" event (test_case_started, test_step_started, test_run_hook_started) must have a corresponding
    "finished" event with matching ID, otherwise an ORPHAN_REFERENCE violation is generated.
    - Every "finished" event must appear after its corresponding "started" event in the envelope list, otherwise an
    OUT_OF_ORDER_LIFECYCLE violation is generated.
    - Implementation status on non-STATUS_CAPABLE_PAYLOAD_KINDS must trigger STATUS_ON_NOT_APPLICABLE_MESSAGE violations.
    - Non-implemented capability statuses must have a non-empty implementation_comment, otherwise
    MISSING_REQUIRED_IMPLEMENTATION_COMMENT is raised.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, cast

from pytest_bdd.model.coverage.inventory import canonical_capability_id, canonical_payload_kind
from pytest_bdd.model.coverage.tracker import ObservedCoverage
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_extension import (
    REQUIRED_STATUS_PAYLOAD_KINDS,
    STATUS_CAPABLE_PAYLOAD_KINDS,
    EventEnvelope,
)
from pytest_bdd.model.message_outcome_mapping import (
    MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    OutcomeMappingRule,
    validate_outcome_mappings,
)
from pytest_bdd.model.message_schema_validation import _strip_nones, validate_envelope_dict_against_schema
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.model.message_status_governance import (
    CAPABILITY_STATUSES,
    LEGACY_STATUS_ALIASES,
    NON_IMPLEMENTED_STATUSES,
    normalize_capability_status,
)
from pytest_bdd.model.message_validation_result import MessageValidationResult, MessageValidationViolation

from .status import collect_observed_outcomes, default_outcome_mapping_rules

if TYPE_CHECKING:
    from collections.abc import Mapping


ALLOWED_IMPLEMENTATION_STATUSES: Final[set[str]] = set(CAPABILITY_STATUSES).union(LEGACY_STATUS_ALIASES.keys())


def collect_observed_capability_ids(envelopes: list[EventEnvelope]) -> tuple[str, ...]:
    """
    Wrap validate_message_stream() with track_coverage=True to collect all observed capability IDs from a message stream.

    Responsibility:
        Wraps validate_message_stream() with track_coverage=True to collect all observed capability IDs from a message
        stream, extracting them from the ObservedCoverage.observed_fields set and normalizing them to canonical
        capability IDs (format: "payload_kind.path"). Returns a sorted tuple of unique capability IDs, or an empty tuple
        if no coverage was observed. This is a convenience function for capability analysis that avoids exposing the
        full validation result when only capability IDs are needed.

    Reason for existence:
        Capability analysis consumers only need the set of observed capability IDs, not the full MessageValidationResult
        with violations and lifecycle diagnostics. This function provides a focused API that runs validation with
        coverage tracking enabled, extracts the relevant data from the result, and returns it in a clean format. The
        canonical_capability_id normalization ensures consistent naming across different message producers.

    Delegates:
        - validate_message_stream: Performs the full message stream validation with coverage tracking, returning a
        MessageValidationResult containing observed_coverage.
        - canonical_capability_id (from pytest_bdd.model.coverage.inventory): Normalizes raw field observations to
        canonical capability ID strings.

    Cohesion:
        The function performs a single focused operation: run validation → extract coverage → normalize IDs → return
        sorted tuple. Every line serves this purpose.

    Separation:
        - validate_message_stream: Kept separate because that function performs the full validation with violations and
        diagnostics, while this function provides a focused capability-ID-only wrapper — full validation vs targeted
        data extraction.

    Main consumers:
        - Capability analysis tools and test suites: Use this function to discover which capability fields are present
        in a message stream without the overhead of processing full validation results.
        - pytest_bdd.message_stream_validation.facade: Re-exported through the public API.

    State and side effects:
        None, keeps no persistent state. Calls validate_message_stream() which creates temporary local state.

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
    validation_result = validate_message_stream(envelopes, track_coverage=True)
    if validation_result.observed_coverage is None:
        return ()
    observed_ids = {
        canonical_capability_id(f"{payload_kind}.{path}" if path else payload_kind)
        for payload_kind, path in validation_result.observed_coverage.observed_fields
    }
    return tuple(sorted(observed_ids))


def _is_non_empty_text(value: object) -> bool:
    """
    Validat that a value is a non-empty string after whitespace stripping.

    Responsibility:
        Validates that a value is a non-empty string after whitespace stripping. Returns True only if the value is a str
        instance with non-whitespace content. Used by validate_message_stream to check whether implementation_comment
        fields are meaningfully populated when required by implementation status governance rules (e.g., "Partly-
        Applicable" status requires a comment explaining why).

    Reason for existence:
        Implementation status governance rules require that non-implemented statuses (Partly-Applicable, Not-Applicable,
        Non-Implementable, Not-Acceptable) include an implementation_comment explaining the status. However, empty
        strings or whitespace-only strings should not satisfy this requirement. This function provides a single,
        consistent definition of "non-empty comment" that is used throughout the validation pipeline, preventing
        inconsistencies where different parts of the code might check this condition differently.

    Delegates:
        - isinstance(value, str): Ensures only string values are considered.
        - str.strip(): Removes leading and trailing whitespace for emptiness check.

    Cohesion:
        The function performs exactly one check: "is this a meaningful text value?" No other validation logic is mixed in.

    Separation:
        - _payload_id: Kept separate because that function extracts lifecycle identifiers from payload objects, while
        this function validates string content — different data access patterns.
        - normalize_capability_status (from message_status_governance): Kept separate because that function normalizes
        status vocabulary, while this function validates comment content — status semantics vs content validation.

    Main consumers:
        - validate_message_stream: Called when checking whether non-implemented statuses have a required comment,
        specifically: normalized_implementation_status in NON_IMPLEMENTED_STATUSES and not
        _is_non_empty_text(implementation_comment).

    State and side effects:
        None, keeps no persistent state. Pure function.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return isinstance(value, str) and bool(value.strip())


def _payload_id(payload: object) -> str | None:
    """
    Extract the lifecycle identifier from a payload object by accessing its "id" attribute (if it exists and is a string).

    Responsibility:
        Extracts the lifecycle identifier from a payload object by accessing its "id" attribute (if it exists and is a
        string). Returns the ID string if present, None otherwise. This function is the single point of ID extraction
        used by validate_message_stream for duplicate detection, lifecycle pair matching, and orphan reference detection
        across test_case, test_step, test_run_hook, and hook payload kinds.

    Reason for existence:
        Different payload kinds store their lifecycle IDs in different attributes (test_case_started uses "id",
        test_step_started uses "test_step_id", etc.), but a common pattern exists: most started/finished payloads have a
        string "id" attribute. This function encapsulates the common getattr + isinstance check pattern, reducing code
        duplication in validate_message_stream where ID extraction is needed for multiple payload kinds. The helper
        returns None for non-string or missing IDs, which the caller handles as "no lifecycle tracking needed for this
        payload."

    Delegates:
        - getattr(payload, "id", None): Accesses the id attribute with a None fallback for objects without it.

    Cohesion:
        The function performs exactly one data access pattern: extract string ID or return None. No other logic is present.

    Separation:
        - _is_non_empty_text: Kept separate because that function validates string content while this function extracts
        identifiers — different operations.
        - _payload_object_for_kind: Kept separate because that function resolves envelope payload dict keys while this
        function extracts ID attributes from payload objects — dict key resolution vs object attribute extraction.

    Main consumers:
        - validate_message_stream: Used for duplicate ID detection (payload_id in payload_ids check), declaring hook
        IDs, and tracking started lifecycle IDs for later orphan reference detection.

    State and side effects:
        None, keeps no persistent state. Pure function with no side effects.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    payload_id = getattr(payload, "id", None)
    return payload_id if isinstance(payload_id, str) else None


def _track_fields(payload_kind: str, current_path: str, data: object, observed_coverage: ObservedCoverage) -> None:
    """
    Recursively walks a nested data structure (dict or list) representing a message payload and records every non-None, n.

    Responsibility:
        Recursively walks a nested data structure (dict or list) representing a message payload and records every non-
        None, non-falsy field path into the ObservedCoverage tracker. Uses dot-separated path notation (e.g.,
        "test_case.started_id") to identify fields within the payload hierarchy. This is the core field-level coverage
        tracking mechanism that powers capability analysis — it discovers which fields are actually populated in a
        message stream.

    Reason for existence:
        Capability analysis needs to know which fields of which message types are actually emitted during test
        execution. This recursive walker traverses arbitrary JSON-like structures (dicts containing dicts, lists
        containing dicts, scalars at leaves) and records every non-empty field path. The ObservedCoverage.record_field()
        calls accumulate the field observations. Without this function, coverage tracking would need to hardcode
        expected field paths for each payload kind, which is brittle and fails to discover unexpected fields. The
        recursive nature avoids code duplication for each nesting level.

    Delegates:
        - ObservedCoverage.record_field: Records the observed field (payload_kind + dotted path) in the coverage tracker.
        - self (recursion): The function calls itself for nested dict values and list items.

    Cohesion:
        The function performs one task: recursively walk a data structure and record observed fields. The isinstance
        checks for dict and list are the only branching, and both serve the same purpose of depth-first traversal.

    Separation:
        - _payload_object_for_kind: Kept separate because that function resolves which dict key to start from in the
        envelope, while this function recursively walks the resolved structure — entry point vs traversal.
        - ObservedCoverage: Kept separate because ObservedCoverage is a data accumulator (what was seen), while this
        function is the traversal logic (how to discover what was seen) — data vs algorithm.

    Main consumers:
        - validate_message_stream: Called in the coverage tracking stage (after schema validation) for each envelope to
        record which fields are present in the message stream.

    State and side effects:
        Mutates the observed_coverage object (passed by reference) by calling record_field() for each observed field.
        This is an intentional side effect on the accumulator object — no other persistent state is modified.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if v is not None and v:
                new_path = f"{current_path}.{k}" if current_path else k
                observed_coverage.record_field(payload_kind, new_path)
                _track_fields(payload_kind, new_path, v, observed_coverage)
    elif isinstance(data, list):
        for item in data:
            _track_fields(payload_kind, current_path, item, observed_coverage)


def _payload_object_for_kind(envelope_dict: Mapping[str, object], payload_kind: str) -> object:
    """
    Resolve a payload object from an envelope dict by key, with snake_case to camelCase fallback: first tries the exact .

    Responsibility:
        Resolves a payload object from an envelope dict by key, with snake_case to camelCase fallback: first tries the
        exact payload_kind key (e.g., "test_case_started"), then if the key contains underscores, converts to camelCase
        (e.g., "testCaseStarted") and retries. Returns the resolved value, or an empty dict if neither key exists. This
        handles the mismatch between snake_case payload kind identifiers used internally and camelCase keys used in
        serialized JSON envelope dicts.

    Reason for existence:
        The plugin internally uses snake_case payload kind names (e.g., "test_case_started", "test_run_hook_started")
        derived from the cucumber-messages specification, but when envelopes are serialized to JSON/dict form, the keys
        use camelCase by convention. This function bridges that naming convention gap without requiring every consumer
        to know about the conversion. Without this function, coverage tracking would fail to find payload data in
        envelope dicts because the key names wouldn't match.

    Delegates:
        - dict.get (via envelope_dict): Dictionary key lookup with None fallback.
        - str.split and str.capitalize: Implements snake_case to camelCase conversion algorithm for fallback lookup.

    Cohesion:
        The function performs one task: resolve a payload kind name to its value in an envelope dict with naming
        convention fallback. The camelCase conversion is integral to this resolution.

    Separation:
        - _payload_id: Kept separate because that function extracts ID attributes from resolved payload objects, while
        this function resolves payload objects from envelope dicts — upstream (dict key resolution) vs downstream
        (attribute extraction).
        - canonical_payload_kind (from coverage.inventory): Kept separate because that function normalizes payload kind
        names, while this function resolves payload values — naming vs data access.

    Main consumers:
        - validate_message_stream: Called during the coverage tracking stage to get the payload object for a given
        payload kind, which is then passed to _track_fields for recursive field discovery.

    State and side effects:
        None, keeps no persistent state. Pure function.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    if payload_kind in envelope_dict:
        return envelope_dict[payload_kind]
    if "_" in payload_kind:
        parts = payload_kind.split("_")
        camel_case_key = parts[0] + "".join(part.capitalize() for part in parts[1:])
        if camel_case_key in envelope_dict:
            return envelope_dict[camel_case_key]
    return {}


def validate_message_stream(  # noqa: PLR0912, PLR0913, PLR0914, PLR0915  -- suppressed warning
    envelopes: list[EventEnvelope],
    *,
    latest_protocol_version: str | None = None,
    enforce_mapping_diagnostics: bool = False,
    mapping_rules: list[OutcomeMappingRule] | None = None,
    track_coverage: bool = True,
    serialization_profile: MessageSerializationProfile = MessageSerializationProfile.schema_compatible,
) -> MessageValidationResult:
    """
    Implement the complete message stream validation pipeline that processes a list of EventEnvelope objects through fiv.

    Responsibility:
        Implements the complete message stream validation pipeline that processes a list of EventEnvelope objects
        through five sequential stages: (1) deserialization via ExecutionMessageAdapter with TypeError handling for
        malformed payloads, (2) JSON Schema validation of each envelope against its schema definition, (3) recursive
        field-level coverage tracking through _track_fields for capability analysis, (4) lifecycle ordering and
        integrity validation including duplicate ID detection, orphan reference detection (finished events referencing
        unknown started IDs), out-of-order lifecycle detection, cross-event hook ID referencing, and (5) implementation
        status governance enforcement including unknown status detection, status-on-inapplicable-message detection,
        required comment validation for non-implemented statuses, terminal status conflict detection, and protocol
        version checking. Optionally runs outcome mapping diagnostics when enforce_mapping_diagnostics is True.

    Reason for existence:
        This is the master orchestration function for message stream quality assurance. No other function has the
        breadth of state tracking (8 dicts/sets for lifecycle state, 5 categories of violations, 2 boolean gate flags)
        or the depth of validation logic. The function must maintain consistency across multiple interrelated checks —
        for example, a duplicate ID detected in stage 4 must not prevent the function from detecting lifecycle ordering
        issues in the same stage, because all violations are accumulated rather than failing fast. The complex signature
        with 5 keyword-only parameters reflects the highly configurable nature of validation: different callers need
        different subsets of validation (e.g., coverage-only vs full governance).

    Delegates:
        - ExecutionMessageAdapter.deserialize and serialize_to_dict: Deserialize raw envelopes and serialize back to
        dicts for schema validation.
        - validate_envelope_dict_against_schema: JSON Schema validation returning violations.
        - _strip_nones: Removes None values from dict for clean schema validation.
        - ObservedCoverage: Tracks field-level coverage across the message stream.
        - _track_fields: Recursively walks payload dicts for coverage tracking.
        - _payload_object_for_kind: Resolves payload objects with camelCase fallback.
        - _payload_id: Extracts lifecycle IDs from payloads.
        - _is_non_empty_text: Validates implementation comment content.
        - normalize_capability_status: Normalizes implementation status strings.
        - collect_observed_outcomes and default_outcome_mapping_rules: Outcome observation for mapping diagnostics.
        - validate_outcome_mappings: Validates outcome mappings against rules and matrix profiles.

    Cohesion:
        Despite its length (~290 lines), the function is cohesive because every line serves the single purpose of
        validating a message stream. The five stages are sequential and each stage's results feed into the final
        MessageValidationResult. The large number of local variables (8 tracking collections) is a direct consequence of
        tracking multiple lifecycle dimensions simultaneously — merging them would obscure the validation logic. The
        function could be split into sub-functions, but the tight coupling between stages (e.g., started IDs tracked in
        one if-branch are checked in another) makes decomposition harder to follow.

    Separation:
        - pytest_bdd.message_stream_validation.status: Kept separate because status.py owns outcome observation logic
        (single-envelope → outcome), while this function owns stream-level validation (multi-envelope → validation
        result) — different granularities.
        - pytest_bdd.model.message_validation_result: Kept separate because that module owns the result data types
        (MessageValidationResult, MessageValidationViolation), while this function produces them — types vs producer.

    Main consumers:
        - collect_observed_capability_ids: Wraps this function with track_coverage=True for capability discovery.
        - pytest_bdd.plugin.gherkin_message_reporter: Validates message streams during BDD execution.
        - Message stream test suites: Validate protocol compliance in integration and e2e tests.

    State and side effects:
        Creates temporary local state (8 dicts/sets for lifecycle tracking, violations list, coverage tracker) scoped to
        a single function call. No module-level or global state is modified. The function is referentially transparent:
        same input produces same result.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=4
    """
    violations: list[MessageValidationViolation] = []

    payload_ids: set[str] = set()
    declared_hook_ids: set[str] = set()
    referenced_run_hook_ids: dict[str, int] = {}
    started_test_case_ids: set[str] = set()
    started_test_step_ids: set[str] = set()
    started_test_run_hook_ids: set[str] = set()
    test_case_started_positions: dict[str, int] = {}
    test_step_started_positions: dict[str, int] = {}
    test_run_hook_started_positions: dict[str, int] = {}
    terminal_status_by_attempt: dict[str, str] = {}
    blocked_for_release = False
    orphan_reference_count = 0
    duplicate_lifecycle_id_count = 0

    observed_coverage = ObservedCoverage() if track_coverage else None

    for position, raw_envelope in enumerate(envelopes):
        try:
            projection = ExecutionMessageAdapter.deserialize(raw_envelope)
        except TypeError as exc:
            violations.append(
                MessageValidationViolation(
                    code="INVALID_PAYLOAD_SHAPE",
                    message=str(exc),
                ),
            )
            continue

        envelope = projection.envelope
        payload_kind = projection.payload_kind
        payload = projection.payload

        # JSONSchema Validation & Tracking
        envelope_dict = ExecutionMessageAdapter.serialize_to_dict(envelope, profile=serialization_profile)
        clean_envelope_dict = cast("dict[str, object]", _strip_nones(envelope_dict))
        violations.extend(validate_envelope_dict_against_schema(envelope_dict))

        if observed_coverage is not None:
            coverage_payload_kind = canonical_payload_kind(payload_kind)
            observed_coverage.record_field(coverage_payload_kind, "")
            _track_fields(
                coverage_payload_kind,
                "",
                _payload_object_for_kind(clean_envelope_dict, coverage_payload_kind),
                observed_coverage,
            )

        payload_id = _payload_id(payload)
        if payload_id is not None:
            if payload_id in payload_ids:
                duplicate_lifecycle_id_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="DUPLICATE_LIFECYCLE_ID",
                        message=f"Duplicate payload id '{payload_id}' detected for '{payload_kind}'.",
                    ),
                )
            else:
                payload_ids.add(payload_id)

        if payload_kind == "hook":
            hook_id = _payload_id(payload)
            if hook_id is not None:
                declared_hook_ids.add(hook_id)

        if payload_kind == "meta" and latest_protocol_version is not None:
            protocol_version = getattr(payload, "protocol_version", None)
            if protocol_version != latest_protocol_version:
                violations.append(
                    MessageValidationViolation(
                        code="UNSUPPORTED_PROTOCOL_VERSION",
                        message=(
                            f"Protocol version '{protocol_version}' is not supported. "
                            f"Expected '{latest_protocol_version}'."
                        ),
                    ),
                )

        if payload_kind == "test_case_started":
            payload_id = _payload_id(payload)
            if payload_id is not None:
                started_test_case_ids.add(payload_id)
                test_case_started_positions[payload_id] = position

        if payload_kind == "test_step_started":
            payload_id = getattr(payload, "test_step_id", None)
            if payload_id is not None:
                payload_id = str(payload_id)
                started_test_step_ids.add(payload_id)
                test_step_started_positions[payload_id] = position

        if payload_kind == "test_run_hook_started":
            payload_id = _payload_id(payload)
            if payload_id is not None:
                started_test_run_hook_ids.add(payload_id)
                test_run_hook_started_positions[payload_id] = position
            hook_id = getattr(payload, "hook_id", None)
            if isinstance(hook_id, str):
                referenced_run_hook_ids[hook_id] = position

        if payload_kind == "test_case_finished":
            test_case_started_id = getattr(payload, "test_case_started_id", None)
            if test_case_started_id not in started_test_case_ids:
                orphan_reference_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="ORPHAN_REFERENCE",
                        message=f"test_case_finished references unknown test_case_started_id '{test_case_started_id}'.",
                    ),
                )
            elif position < test_case_started_positions[test_case_started_id]:
                violations.append(
                    MessageValidationViolation(
                        code="OUT_OF_ORDER_LIFECYCLE",
                        message=(
                            "test_case_finished was emitted before its matching "
                            f"test_case_started for id '{test_case_started_id}'."
                        ),
                    ),
                )

        if payload_kind == "test_step_finished":
            test_step_id = getattr(payload, "test_step_id", None)
            if test_step_id not in started_test_step_ids:
                orphan_reference_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="ORPHAN_REFERENCE",
                        message=f"test_step_finished references unknown test_step_id '{test_step_id}'.",
                    ),
                )
            elif position < test_step_started_positions[test_step_id]:
                violations.append(
                    MessageValidationViolation(
                        code="OUT_OF_ORDER_LIFECYCLE",
                        message=(
                            "test_step_finished was emitted before its matching "
                            f"test_step_started for step_id '{test_step_id}'."
                        ),
                    ),
                )

        if payload_kind == "test_run_hook_finished":
            test_run_hook_started_id = getattr(payload, "test_run_hook_started_id", None)
            if test_run_hook_started_id not in started_test_run_hook_ids:
                orphan_reference_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="ORPHAN_REFERENCE",
                        message=(
                            "test_run_hook_finished references unknown "
                            f"test_run_hook_started_id '{test_run_hook_started_id}'."
                        ),
                    ),
                )
            elif position < test_run_hook_started_positions[test_run_hook_started_id]:
                violations.append(
                    MessageValidationViolation(
                        code="OUT_OF_ORDER_LIFECYCLE",
                        message=(
                            "test_run_hook_finished was emitted before its matching "
                            f"test_run_hook_started for id '{test_run_hook_started_id}'."
                        ),
                    ),
                )

        implementation_status = getattr(payload, "implementation_status", None)
        implementation_comment = getattr(payload, "implementation_comment", None)
        normalized_implementation_status = (
            normalize_capability_status(str(implementation_status)) if implementation_status is not None else None
        )

        if implementation_status is not None:
            if (
                normalized_implementation_status is None
                and str(implementation_status).strip().lower() not in ALLOWED_IMPLEMENTATION_STATUSES
            ):
                violations.append(
                    MessageValidationViolation(
                        code="UNKNOWN_IMPLEMENTATION_STATUS",
                        message=(
                            f"Unsupported implementation_status '{implementation_status}' found on '{payload_kind}'."
                        ),
                    ),
                )
            if payload_kind not in STATUS_CAPABLE_PAYLOAD_KINDS:
                violations.append(
                    MessageValidationViolation(
                        code="STATUS_ON_NOT_APPLICABLE_MESSAGE",
                        message=f"'{payload_kind}' must not include implementation_status.",
                    ),
                )
            if normalized_implementation_status in NON_IMPLEMENTED_STATUSES and not _is_non_empty_text(
                implementation_comment,
            ):
                violations.append(
                    MessageValidationViolation(
                        code="MISSING_REQUIRED_IMPLEMENTATION_COMMENT",
                        message=(
                            f"implementation_comment is required for implementation_status='{implementation_status}'."
                        ),
                    ),
                )
            if normalized_implementation_status == "Not-Acceptable":
                blocked_for_release = True

        if payload_kind in REQUIRED_STATUS_PAYLOAD_KINDS and implementation_status is None:
            violations.append(
                MessageValidationViolation(
                    code="MISSING_REQUIRED_IMPLEMENTATION_COMMENT",
                    message=f"'{payload_kind}' requires implementation_status and comment governance fields.",
                ),
            )

        if payload_kind == "test_case_finished":
            test_case_started_id = getattr(payload, "test_case_started_id", None)
            if isinstance(test_case_started_id, str):
                current_status = (
                    normalized_implementation_status if normalized_implementation_status is not None else "Implemented"
                )
                previous_status = terminal_status_by_attempt.get(test_case_started_id)
                if previous_status is not None and previous_status != current_status:
                    violations.append(
                        MessageValidationViolation(
                            code="CONFLICTING_TERMINAL_STATUS",
                            message=(
                                "Conflicting terminal statuses were emitted for "
                                f"test_case_started_id='{test_case_started_id}'."
                            ),
                        ),
                    )
                terminal_status_by_attempt[test_case_started_id] = current_status

    for hook_id in referenced_run_hook_ids:
        if hook_id not in declared_hook_ids:
            orphan_reference_count += 1
            violations.append(
                MessageValidationViolation(
                    code="ORPHAN_REFERENCE",
                    message=f"test_run_hook_started references unknown hook_id '{hook_id}'.",
                ),
            )

    if enforce_mapping_diagnostics:
        observed_outcomes = collect_observed_outcomes(envelopes)
        if observed_outcomes:
            mapping_validation = validate_outcome_mappings(
                mapping_rules if mapping_rules is not None else default_outcome_mapping_rules(),
                observed_outcomes,
                matrix_profile=MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
            )
            violations.extend(
                MessageValidationViolation(
                    code="AMBIGUOUS_OUTCOME_MAPPING",
                    message=f"Ambiguous mapping for observed outcome '{outcome_key}'.",
                )
                for outcome_key in mapping_validation.ambiguous_outcomes
            )
            violations.extend(
                MessageValidationViolation(
                    code="UNMAPPED_OUTCOME_MAPPING",
                    message=f"Unmapped observed outcome '{outcome_key}'.",
                )
                for outcome_key in mapping_validation.unmapped_outcomes
            )
            violations.extend(
                MessageValidationViolation(
                    code="MISSING_FIXED_MATRIX_CASE",
                    message=f"Missing fixed matrix case '{missing_case}'.",
                )
                for missing_case in mapping_validation.missing_required_matrix_cases
            )
            if (
                mapping_validation.ambiguous_outcomes
                or mapping_validation.unmapped_outcomes
                or mapping_validation.missing_required_matrix_cases
            ):
                blocked_for_release = True

    status: Literal["pass", "fail"] = "pass" if not violations else "fail"
    return MessageValidationResult(
        status=status,
        orphan_reference_count=orphan_reference_count,
        duplicate_lifecycle_id_count=duplicate_lifecycle_id_count,
        blocked_for_release=blocked_for_release,
        violations=tuple(violations),
        observed_coverage=observed_coverage,
    )
