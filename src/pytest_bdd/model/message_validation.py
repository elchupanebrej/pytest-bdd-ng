from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]

from .message_extension import (
    REQUIRED_STATUS_PAYLOAD_KINDS,
    STATUS_CAPABLE_PAYLOAD_KINDS,
    EventEnvelope,
    get_payload_kind,
    has_single_payload,
)

AllowedImplementationStatus = Literal["done", "non-implementable", "not-acceptable"]
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
]

ALLOWED_IMPLEMENTATION_STATUSES: Final[set[str]] = {
    "done",
    "non-implementable",
    "not-acceptable",
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

    @property
    def is_valid(self) -> bool:
        return self.status == "pass"


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _payload_id(payload: object) -> str | None:
    payload_id = getattr(payload, "id", None)
    return payload_id if isinstance(payload_id, str) else None


def validate_message_stream(  # noqa: C901
    envelopes: list[EventEnvelope],
    *,
    latest_protocol_version: str | None = None,
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

    for position, envelope in enumerate(envelopes):
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

        if implementation_status is not None:
            if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
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
            if implementation_status in {"non-implementable", "not-acceptable"} and not _is_non_empty_text(
                implementation_comment
            ):
                violations.append(
                    MessageValidationViolation(
                        code="MISSING_REQUIRED_IMPLEMENTATION_COMMENT",
                        message=(
                            f"implementation_comment is required for implementation_status='{implementation_status}'."
                        ),
                    )
                )
            if implementation_status == "not-acceptable":
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
                current_status = str(implementation_status) if implementation_status is not None else "done"
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

    status: Literal["pass", "fail"] = "pass" if not violations else "fail"
    return MessageValidationResult(
        status=status,
        orphan_reference_count=orphan_reference_count,
        duplicate_lifecycle_id_count=duplicate_lifecycle_id_count,
        blocked_for_release=blocked_for_release,
        violations=tuple(violations),
    )


def validate_envelope_shape(envelope: EventEnvelope) -> None:
    if not has_single_payload(envelope):
        message = "Envelope must include exactly one payload field"
        raise TypeError(message)


def parse_message_dict(payload: dict) -> EventEnvelope:
    message = Message(**payload)
    validate_envelope_shape(message)
    return message
