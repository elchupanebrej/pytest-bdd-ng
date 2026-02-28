from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from jsonschema import RefResolver, validators

from .coverage.tracker import ObservedCoverage
from .message_extension import (
    REQUIRED_STATUS_PAYLOAD_KINDS,
    STATUS_CAPABLE_PAYLOAD_KINDS,
    EventEnvelope,
    get_payload_kind,
    has_single_payload,
)
from .message_outcome_mapping import (
    MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    ObservedOutcome,
    OutcomeMappingRule,
    OutcomeScope,
    OutcomeStatus,
    validate_outcome_mappings,
)
from .message_status_governance import CAPABILITY_STATUSES, LEGACY_STATUS_ALIASES, normalize_capability_status

SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "messages" / "jsonschema" / "src"
if not (SCHEMA_DIR / "Envelope.json").exists():
    SCHEMA_DIR = Path.cwd() / "messages" / "jsonschema" / "src"

_validator = None
try:
    with Path(SCHEMA_DIR / "Envelope.json").open(encoding="utf-8") as f:
        ENVELOPE_SCHEMA = json.load(f)

    # Use Draft202012Validator if possible, fallback to Draft7
    base_uri = f"file://{SCHEMA_DIR.absolute()}/"
    _schema_resolver = RefResolver(base_uri=base_uri, referrer=ENVELOPE_SCHEMA)
    _validator = validators.Draft202012Validator(ENVELOPE_SCHEMA, resolver=_schema_resolver)
except FileNotFoundError:
    pass


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
}


@dataclass(frozen=True, slots=True)
class MessageValidationViolation:
    code: ValidationCode
    message: str


@dataclass(frozen=True, slots=True)
class MessageValidationResult:
    status: Literal["pass", "fail"]
    orphan_reference_count: int
    duplicate_lifecycle_id_count: int
    blocked_for_release: bool
    violations: tuple[MessageValidationViolation, ...]
    observed_coverage: ObservedCoverage | None = None

    @property
    def is_valid(self) -> bool:
        return self.status == "pass"


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _payload_id(payload: object) -> str | None:
    payload_id = getattr(payload, "id", None)
    return payload_id if isinstance(payload_id, str) else None


def _normalize_outcome_status(value: object) -> OutcomeStatus | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    normalized = raw.split(".")[-1].lower()
    if normalized in {"passed", "failed", "skipped", "undefined", "interrupted"}:
        return cast(OutcomeStatus, normalized)
    if normalized == "pass":
        return "passed"
    if normalized in {"fail", "error"}:
        return "failed"
    return None


def _derive_outcome_status(payload_kind: str, payload: object) -> OutcomeStatus | None:
    if payload_kind == "test_step_finished":
        test_step_result = getattr(payload, "test_step_result", None)
        result_status = getattr(test_step_result, "status", None) if test_step_result is not None else None
        return _normalize_outcome_status(result_status)
    if payload_kind == "test_case_finished":
        implementation_status = getattr(payload, "implementation_status", None)
        if implementation_status is not None:
            normalized = normalize_capability_status(str(implementation_status))
            if normalized == "Not-Acceptable":
                return "failed"
            if normalized in {"Implemented", "Not-Applicable", "Non-Implementable"}:
                return "passed"
        will_be_retried = getattr(payload, "will_be_retried", None)
        if isinstance(will_be_retried, bool) and will_be_retried:
            return "interrupted"
        return "passed"
    if payload_kind == "test_run_finished":
        success = getattr(payload, "success", None)
        if isinstance(success, bool):
            return "passed" if success else "failed"
    return None


def observed_outcome_from_envelope(envelope: EventEnvelope) -> ObservedOutcome | None:
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
    outcomes: list[ObservedOutcome] = []
    for envelope in envelopes:
        outcome = observed_outcome_from_envelope(envelope)
        if outcome is not None:
            outcomes.append(outcome)
    return outcomes


def default_outcome_mapping_rules() -> list[OutcomeMappingRule]:
    scopes: tuple[OutcomeScope, ...] = ("run", "scenario", "step")
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


def _track_fields(payload_kind: str, current_path: str, data: object, observed_coverage: ObservedCoverage):
    if isinstance(data, dict):
        for k, v in data.items():
            if v is not None and v != "":
                new_path = f"{current_path}.{k}" if current_path else k
                observed_coverage.observed_fields.add((payload_kind, new_path))
                _track_fields(payload_kind, new_path, v, observed_coverage)
    elif isinstance(data, list):
        for item in data:
            _track_fields(payload_kind, current_path, item, observed_coverage)


def validate_message_stream(  # noqa: C901
    envelopes: list[EventEnvelope],
    *,
    latest_protocol_version: str | None = None,
    enforce_mapping_diagnostics: bool = False,
    mapping_rules: list[OutcomeMappingRule] | None = None,
    track_coverage: bool = True,
) -> MessageValidationResult:
    violations: list[MessageValidationViolation] = []

    payload_ids: set[str] = set()
    started_test_case_ids: set[str] = set()
    started_test_step_ids: set[str] = set()
    test_case_started_positions: dict[str, int] = {}
    test_step_started_positions: dict[str, int] = {}
    terminal_status_by_attempt: dict[str, str] = {}
    blocked_for_release = False
    orphan_reference_count = 0
    duplicate_lifecycle_id_count = 0

    observed_coverage = ObservedCoverage() if track_coverage else None

    for position, envelope in enumerate(envelopes):
        # JSONSchema Validation & Tracking
        from .message_converter import envelope_to_dict

        envelope_dict = envelope_to_dict(envelope)

        # Strip None values for jsonschema to validate properly
        def _strip_nones(d):
            if isinstance(d, dict):
                return {k: _strip_nones(v) for k, v in d.items() if v is not None}
            elif isinstance(d, list):
                return [_strip_nones(v) for v in d if v is not None]
            return d

        clean_envelope_dict = _strip_nones(envelope_dict)

        if _validator is not None:
            try:
                violations.extend(
                    MessageValidationViolation(
                        code="SCHEMA_VIOLATION",
                        message=f"Schema violation: {error.message} at path {list(error.absolute_path)}",
                    )
                    for error in _validator.iter_errors(clean_envelope_dict)
                )
            except Exception:
                # Catch ref resolution errors if schema is complex
                pass

        if not has_single_payload(envelope):
            violations.append(
                MessageValidationViolation(
                    code="INVALID_PAYLOAD_SHAPE",
                    message="Envelope must include exactly one payload.",
                )
            )
            continue

        payload_kind = get_payload_kind(envelope)
        if payload_kind is None:
            continue

        if observed_coverage is not None:
            observed_coverage.observed_fields.add((payload_kind, ""))
            _track_fields(payload_kind, "", clean_envelope_dict.get(payload_kind, {}), observed_coverage)

        payload = getattr(envelope, payload_kind)
        payload_id = _payload_id(payload)
        if payload_id is not None:
            if payload_id in payload_ids:
                duplicate_lifecycle_id_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="DUPLICATE_LIFECYCLE_ID",
                        message=f"Duplicate payload id '{payload_id}' detected for '{payload_kind}'.",
                    )
                )
            else:
                payload_ids.add(payload_id)

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
                    )
                )

        if payload_kind == "test_case_started":
            payload_id = _payload_id(payload)
            if payload_id is not None:
                started_test_case_ids.add(payload_id)
                test_case_started_positions[payload_id] = position

        if payload_kind == "test_step_started":
            payload_id = _payload_id(payload)
            if payload_id is not None:
                started_test_step_ids.add(payload_id)
                test_step_started_positions[payload_id] = position

        if payload_kind == "test_case_finished":
            test_case_started_id = getattr(payload, "test_case_started_id", None)
            if test_case_started_id not in started_test_case_ids:
                orphan_reference_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="ORPHAN_REFERENCE",
                        message=f"test_case_finished references unknown test_case_started_id '{test_case_started_id}'.",
                    )
                )
            elif position < test_case_started_positions[test_case_started_id]:
                violations.append(
                    MessageValidationViolation(
                        code="OUT_OF_ORDER_LIFECYCLE",
                        message=(
                            "test_case_finished was emitted before its matching "
                            f"test_case_started for id '{test_case_started_id}'."
                        ),
                    )
                )

        if payload_kind == "test_step_finished":
            test_step_id = getattr(payload, "test_step_id", None)
            if test_step_id not in started_test_step_ids:
                orphan_reference_count += 1
                violations.append(
                    MessageValidationViolation(
                        code="ORPHAN_REFERENCE",
                        message=f"test_step_finished references unknown test_step_id '{test_step_id}'.",
                    )
                )
            elif position < test_step_started_positions[test_step_id]:
                violations.append(
                    MessageValidationViolation(
                        code="OUT_OF_ORDER_LIFECYCLE",
                        message=(
                            "test_step_finished was emitted before its matching "
                            f"test_step_started for step_id '{test_step_id}'."
                        ),
                    )
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
                    )
                )
            if payload_kind not in STATUS_CAPABLE_PAYLOAD_KINDS:
                violations.append(
                    MessageValidationViolation(
                        code="STATUS_ON_NOT_APPLICABLE_MESSAGE",
                        message=f"'{payload_kind}' must not include implementation_status.",
                    )
                )
            if normalized_implementation_status in {
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
                    )
                )
            if normalized_implementation_status == "Not-Acceptable":
                blocked_for_release = True

        if payload_kind in REQUIRED_STATUS_PAYLOAD_KINDS and implementation_status is None:
            violations.append(
                MessageValidationViolation(
                    code="MISSING_REQUIRED_IMPLEMENTATION_COMMENT",
                    message=f"'{payload_kind}' requires implementation_status and comment governance fields.",
                )
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
                        )
                    )
                terminal_status_by_attempt[test_case_started_id] = current_status

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


def validate_envelope_shape(envelope: EventEnvelope) -> None:
    if not has_single_payload(envelope):
        message = "Envelope must include exactly one payload field"
        raise TypeError(message)


def parse_message_dict(payload: dict) -> EventEnvelope:
    message = Message(**payload)
    validate_envelope_shape(message)
    return message
