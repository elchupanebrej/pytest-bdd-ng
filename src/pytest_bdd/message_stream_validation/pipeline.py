"""
Provide cucumber message stream validation pipeline.

Responsibility:
    Provide cucumber message stream validation pipeline. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.message_stream_validation.pipeline` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - collect_observed_capability_ids: owns nested behavior below this boundary
    - _is_non_empty_text: owns nested behavior below this boundary
    - _payload_id: owns nested behavior below this boundary
    - _track_fields: owns nested behavior below this boundary
    - _payload_object_for_kind: owns nested behavior below this boundary
    - validate_message_stream: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/facade.py: imports or references `pipeline`

State and side effects:
    mutates payload_id, orphan_reference_count, blocked_for_release, duplicate_lifecycle_id_count, hook_id; depends on
    __future__.annotations, typing.TYPE_CHECKING, typing.Final, typing.Literal, typing.cast.

Invariants:
    - `pytest_bdd.message_stream_validation.pipeline` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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
    Collect canonical capability identifiers observed in a message stream.

    Responsibility:
        Collect canonical capability identifiers observed in a message stream. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.pipeline.collect_observed_capability_ids` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - validate_message_stream: collaborator call used by this boundary
        - canonical_capability_id: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `collect_observed_capability_ids`
        - src/pytest_bdd/model/message_validation.py: imports or references `collect_observed_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `collect_observed_capability_ids`

    State and side effects:
        mutates validation_result, observed_ids.

    Invariants:
        - `pytest_bdd.message_stream_validation.pipeline.collect_observed_capability_ids` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.message_stream_validation.pipeline._is_non_empty_text` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.message_stream_validation.pipeline._is_non_empty_text`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - bool: collaborator call used by this boundary
        - value.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `_is_non_empty_text`
        - src/pytest_bdd/model/message_status_governance.py: imports or references `_is_non_empty_text`

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
    return isinstance(value, str) and bool(value.strip())


def _payload_id(payload: object) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.message_stream_validation.pipeline._payload_id` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.message_stream_validation.pipeline._payload_id` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `_payload_id`

    State and side effects:
        mutates payload_id.

    Invariants:
        - `pytest_bdd.message_stream_validation.pipeline._payload_id` keeps its documented import path, ownership
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
    payload_id = getattr(payload, "id", None)
    return payload_id if isinstance(payload_id, str) else None


def _track_fields(payload_kind: str, current_path: str, data: object, observed_coverage: ObservedCoverage) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.message_stream_validation.pipeline._track_fields` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.message_stream_validation.pipeline._track_fields` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - _track_fields: collaborator call used by this boundary
        - data.items: collaborator call used by this boundary
        - observed_coverage.record_field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `_track_fields`

    State and side effects:
        mutates new_path.

    Invariants:
        - `pytest_bdd.message_stream_validation.pipeline._track_fields` keeps its documented import path, ownership
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.message_stream_validation.pipeline._payload_object_for_kind` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.pipeline._payload_object_for_kind` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - payload_kind.split: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - part.capitalize: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `_payload_object_for_kind`

    State and side effects:
        mutates parts, camel_case_key.

    Invariants:
        - `pytest_bdd.message_stream_validation.pipeline._payload_object_for_kind` keeps its documented import path,
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
    if payload_kind in envelope_dict:
        return envelope_dict[payload_kind]
    if "_" in payload_kind:
        parts = payload_kind.split("_")
        camel_case_key = parts[0] + "".join(part.capitalize() for part in parts[1:])
        if camel_case_key in envelope_dict:
            return envelope_dict[camel_case_key]
    return {}


def validate_message_stream(  # noqa: PLR0912, PLR0913, PLR0914, PLR0915
    envelopes: list[EventEnvelope],
    *,
    latest_protocol_version: str | None = None,
    enforce_mapping_diagnostics: bool = False,
    mapping_rules: list[OutcomeMappingRule] | None = None,
    track_coverage: bool = True,
    serialization_profile: MessageSerializationProfile = MessageSerializationProfile.schema_compatible,
) -> MessageValidationResult:
    """
    Perform an exhaustive pass over a stream of message envelopes.

    Enforces schema compliance, lifecycle consistency, and capability governance rules.

    Returns:
        A comprehensive MessageValidationResult aggregating all findings, metrics, and coverage data.

    Responsibility:
        Perform an exhaustive pass over a stream of message envelopes. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.message_stream_validation.pipeline.validate_message_stream` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - MessageValidationViolation: collaborator call used by this boundary
        - violations.append: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - violations.extend: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/facade.py: imports or references `validate_message_stream`
        - src/pytest_bdd/model/__init__.py: imports or references `validate_message_stream`
        - src/pytest_bdd/model/message_validation.py: imports or references `validate_message_stream`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `validate_message_stream`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `validate_message_stream`

    State and side effects:
        mutates orphan_reference_count, payload_id, blocked_for_release, duplicate_lifecycle_id_count, hook_id.

    Invariants:
        - `pytest_bdd.message_stream_validation.pipeline.validate_message_stream` keeps its documented import path,
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
