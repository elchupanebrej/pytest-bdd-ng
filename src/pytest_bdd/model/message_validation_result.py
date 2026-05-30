"""Provide message validation result types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from attrs import frozen
from returns.result import Result

from pytest_bdd.types.failure_reasons import MessageValidationFailure

if TYPE_CHECKING:
    from pytest_bdd.model.coverage.tracker import ObservedCoverage

SchemaValidationResult = Result[object, MessageValidationFailure]


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
