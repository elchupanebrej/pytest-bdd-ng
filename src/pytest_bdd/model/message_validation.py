"""Provide message validation helpers."""

from __future__ import annotations

import json
from functools import cache
from typing import TYPE_CHECKING, Final, Literal, cast

from attrs import frozen
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.jsonschema import SchemaValidator, ValidationError, build_validator

from .coverage.inventory import canonical_capability_id, canonical_payload_kind
from .coverage.tracker import ObservedCoverage
from .execution_message_adapter import ExecutionMessageAdapter
from .message_capability_inventory import load_envelope_schema
from .message_converter import validate_envelope_shape
from .message_extension import (
    REQUIRED_STATUS_PAYLOAD_KINDS,
    STATUS_CAPABLE_PAYLOAD_KINDS,
    EventEnvelope,
    get_payload_kind,
)
from .message_outcome_mapping import (
    MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    ObservedOutcome,
    OutcomeMappingRule,
    OutcomeScope,
    OutcomeStatus,
    normalize_outcome_status,
    validate_outcome_mappings,
)
from .message_serialization import MessageSerializationProfile
from .message_status_governance import CAPABILITY_STATUSES, LEGACY_STATUS_ALIASES, normalize_capability_status

if TYPE_CHECKING:
    from collections.abc import Mapping


def _build_schema_validator() -> tuple[SchemaValidator | None, str | None]:
    from referencing import Registry, Resource  # noqa: PLC0415 -- optional referencing dependency

    try:
        schema_dir, envelope_schema = load_envelope_schema()
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, f"Unable to load Envelope.json schema: {exc}"

    registry = Registry()
    for schema_path in sorted(schema_dir.glob("*.json")):
        contents = json.loads(schema_path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents)
        file_uri = schema_path.resolve().as_uri()
        registry = registry.with_resource(file_uri, resource)
        registry = registry.with_resource(schema_path.name, resource)
        registry = registry.with_resource(f"./{schema_path.name}", resource)

    return build_validator(envelope_schema, registry=registry), None


@cache
def _schema_validator_state() -> tuple[SchemaValidator | None, str | None]:
    return _build_schema_validator()


AllowedImplementationStatus = str
ValidationCode = Literal[
    "ORPHAN_REFERENCE",
    "DUPLICATE_LIFECYCLE_ID",
    "INVALID_PAYLOAD_SHAPE",
    "OUT_OF_ORDER_LIFECYCLE",
    "UNSUPPORTED_PROTOCOL_VERSION",
    "UNKNOWN_IMPLEMENTATION_STATUS",
    "MISSING_REQUIRED_IMPLEMENTATION_COMMENT",
    "CONFLICTING_TERMINAL_STATUS",
    "STATUS_ON_NOT_APPLICABLE_MESSAGE",
    "AMBIGUOUS_OUTCOME_MAPPING",
    "UNMAPPED_OUTCOME_MAPPING",
    "MISSING_FIXED_MATRIX_CASE",
    "SCHEMA_VIOLATION",
]

ALLOWED_IMPLEMENTATION_STATUSES: Final[set[str]] = set(CAPABILITY_STATUSES).union(LEGACY_STATUS_ALIASES.keys())
OUTCOME_SCOPE_BY_PAYLOAD_KIND: Final[dict[str, OutcomeScope]] = {
    "test_run_finished": "run",
    "test_case_finished": "scenario",
    "test_step_finished": "step",
    "test_run_hook_finished": "hook",
    "attachment": "attachment",
    "external_attachment": "attachment",
}


@frozen
class MessageValidationViolation:
    """Capture details about a specific validation error encountered while analyzing a message envelope or stream."""

    code: ValidationCode
    message: str
    json_path: tuple[str, ...] = ()
    schema_path: tuple[str, ...] = ()
    validator: str | None = None


@frozen
class MessageValidationResult:
    """Aggregate outcomes and violations from a validation pass."""

    status: Literal["pass", "fail"]
    orphan_reference_count: int
    duplicate_lifecycle_id_count: int
    blocked_for_release: bool
    violations: tuple[MessageValidationViolation, ...]
    observed_coverage: ObservedCoverage | None = None

    @property
    def is_valid(self) -> bool:
        """
        Determine if the validation result represents a complete success with no violations.

        Returns:
            True if the status is 'pass', otherwise False.

        """
        return self.status == "pass"


@frozen
class XdistReportingCompatibilityResult:
    """Indicate whether the current distributed execution environment meets the requirements for xdist reporting."""

    status: Literal["pass", "fail"]
    reason: str | None = None

    @property
    def is_valid(self) -> bool:
        """
        Determine if the environment is fully compatible for xdist reporting.

        Returns:
            True if the status is 'pass', otherwise False.

        """
        return self.status == "pass"


def validate_xdist_reporting_compatibility(  # noqa: PLR0913
    *,
    xdist_active: bool,
    is_worker: bool,
    is_controller: bool,
    remote_module_available: bool,
    controller_event_patch_installed: bool,
    worker_sender_available: bool,
) -> XdistReportingCompatibilityResult:
    """
    Verify that the xdist plugin configuration and node topology support remote message aggregation.

    Returns:
        An XdistReportingCompatibilityResult detailing success or the specific blocking constraint.

    """
    if not xdist_active:
        return XdistReportingCompatibilityResult(status="pass")
    if is_controller and not remote_module_available:
        return XdistReportingCompatibilityResult(
            status="fail",
            reason=(
                "Distributed reporting requires pytest_xdist_getremotemodule, but the hook integration is unavailable."
            ),
        )
    if is_controller and not controller_event_patch_installed:
        return XdistReportingCompatibilityResult(
            status="fail",
            reason="Distributed reporting requires controller support for reporter-specific xdist channel events.",
        )
    if is_worker and not worker_sender_available:
        return XdistReportingCompatibilityResult(
            status="fail",
            reason=(
                "Distributed reporting requires the xdist remote-module adapter to expose a worker channel sender. "
                "Falling back to a side-channel transport is not allowed."
            ),
        )
    return XdistReportingCompatibilityResult(status="pass")


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _payload_id(payload: object) -> str | None:
    payload_id = getattr(payload, "id", None)
    return payload_id if isinstance(payload_id, str) else None


def _normalize_outcome_status(value: object) -> OutcomeStatus | None:
    return normalize_outcome_status(value)


def _derive_outcome_status(payload_kind: str, payload: object) -> OutcomeStatus | None:  # noqa: C901, PLR0911
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
    return None


def observed_outcome_from_envelope(envelope: EventEnvelope) -> ObservedOutcome | None:
    """
    Extract and normalize the execution outcome status associated with a specific message envelope.

    Returns:
        An ObservedOutcome representing the status and context, or None if the payload does not carry an outcome.

    """
    payload_kind = get_payload_kind(envelope)
    if payload_kind is None:
        return None
    outcome_scope = OUTCOME_SCOPE_BY_PAYLOAD_KIND.get(payload_kind)
    if outcome_scope is None:
        return None
    payload = getattr(envelope, payload_kind)
    outcome_status = _derive_outcome_status(payload_kind, payload)
    if outcome_status is None:
        return None
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

    """
    outcomes: list[ObservedOutcome] = []
    for envelope in envelopes:
        outcome = observed_outcome_from_envelope(envelope)
        if outcome is not None:
            outcomes.append(outcome)
    return outcomes


def collect_observed_capability_ids(envelopes: list[EventEnvelope]) -> tuple[str, ...]:
    """
    Perform a coverage pass over a stream of envelopes to extract a distinct set of exercised capability identifiers.

    Returns:
        A sorted tuple of canonical capability strings observed in the stream.

    """
    validation_result = validate_message_stream(envelopes, track_coverage=True)
    if validation_result.observed_coverage is None:
        return ()
    observed_ids = {
        canonical_capability_id(f"{payload_kind}.{path}" if path else payload_kind)
        for payload_kind, path in validation_result.observed_coverage.observed_fields
    }
    return tuple(sorted(observed_ids))


def default_outcome_mapping_rules() -> list[OutcomeMappingRule]:
    """
    Generate the standard baseline mapping rules for resolving execution outcomes across standard BDD scopes.

    Returns:
        A list of OutcomeMappingRule instances encoding the default governance rules.

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


def _track_fields(payload_kind: str, current_path: str, data: object, observed_coverage: ObservedCoverage) -> None:
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
    if payload_kind in envelope_dict:
        return envelope_dict[payload_kind]
    if "_" in payload_kind:
        parts = payload_kind.split("_")
        camel_case_key = parts[0] + "".join(part.capitalize() for part in parts[1:])
        if camel_case_key in envelope_dict:
            return envelope_dict[camel_case_key]
    return {}


def _schema_violation(error: ValidationError) -> MessageValidationViolation:
    json_path = tuple(str(part) for part in error.absolute_path)
    schema_path = tuple(str(part) for part in error.absolute_schema_path)
    return MessageValidationViolation(
        code="SCHEMA_VIOLATION",
        message=f"Schema violation: {error.message}",
        json_path=json_path,
        schema_path=schema_path,
        validator=str(error.validator) if error.validator is not None else None,
    )


def _strip_nones(value: object) -> object:
    if isinstance(value, dict):
        return {k: _strip_nones(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_nones(v) for v in value if v is not None]
    return value


def validate_execnet_serializable_payload(
    payload: object,
    *,
    path: tuple[str, ...] = (),
) -> tuple[MessageValidationViolation, ...]:
    """
    Recursively verify that a payload dictionary only contains types that can be reliably transported via execnet.

    Returns:
        A tuple of MessageValidationViolation instances for any keys or values that break serialization constraints.

    """
    if payload is None or isinstance(payload, (str, int, float, bool)):
        return ()
    if isinstance(payload, tuple):
        payload = list(payload)
    if isinstance(payload, list):
        violations: list[MessageValidationViolation] = []
        for index, item in enumerate(payload):
            violations.extend(validate_execnet_serializable_payload(item, path=(*path, str(index))))
        return tuple(violations)
    if isinstance(payload, dict):
        violations = []
        for key, value in payload.items():
            if not isinstance(key, str):
                violations.append(
                    MessageValidationViolation(
                        code="INVALID_PAYLOAD_SHAPE",
                        message=f"Execnet payload keys must be strings at {'.'.join(path) or '<root>'}.",
                        json_path=path,
                    ),
                )
                continue
            violations.extend(validate_execnet_serializable_payload(value, path=(*path, key)))
        return tuple(violations)
    return (
        MessageValidationViolation(
            code="INVALID_PAYLOAD_SHAPE",
            message=(
                f"Execnet payload contains unsupported type '{type(payload).__name__}' at {'.'.join(path) or '<root>'}."
            ),
            json_path=path,
        ),
    )


def format_xdist_transport_compatibility_error(reason: str) -> str:
    """
    Construct a standardized error message indicating a failure in the xdist reporting transport constraints.

    Returns:
        A formatted error string detailing the incompatibility.

    """
    return (
        "Distributed reporting requires the pytest-bdd xdist remote-module adapter and "
        f"compatible worker/controller channel handling. {reason}"
    )


def validate_envelope_dict_against_schema(
    envelope_dict: Mapping[str, object],
) -> tuple[MessageValidationViolation, ...]:
    """
    Validate a raw dictionary representation of a message envelope against the loaded JSON schema.

    Returns:
        A tuple of MessageValidationViolation instances mapping to specific JSON schema violations, if any.

    """
    clean_envelope_dict = cast("dict[str, object]", _strip_nones(envelope_dict))
    validator, validator_init_error = _schema_validator_state()
    if validator_init_error is not None:
        return (
            MessageValidationViolation(
                code="SCHEMA_VIOLATION",
                message=validator_init_error,
            ),
        )
    if validator is None:
        return ()
    return tuple(_schema_violation(error) for error in validator.iter_errors(clean_envelope_dict))


def validate_envelope_against_schema(
    envelope: EventEnvelope,
    *,
    serialization_profile: MessageSerializationProfile = MessageSerializationProfile.schema_compatible,
) -> tuple[MessageValidationViolation, ...]:
    """
    Serialize an EventEnvelope into its dictionary representation and validate it against the JSON schema.

    Returns:
        A tuple of MessageValidationViolation instances discovered during schema validation.

    """
    return validate_envelope_dict_against_schema(
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=serialization_profile),
    )


def validate_message_stream(  # noqa: C901, PLR0912, PLR0913, PLR0914, PLR0915
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
            if normalized_implementation_status in {
                "Partly-Applicable",
                "Non-Implementable",
                "Not-Acceptable",
                "Not-Applicable",
                "Pending",
            } and not _is_non_empty_text(implementation_comment):
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


def parse_message_dict(payload: dict) -> EventEnvelope:
    """
    Instantiate an EventEnvelope from a raw dictionary while ensuring strict payload shape enforcement.

    Returns:
        The instantiated EventEnvelope object.

    """
    message = Message(**payload)
    validate_envelope_shape(message)
    return message
