"""Policy and structured results for semantic Gherkin heading validation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from attrs import frozen

EMPTY_HEADING_TITLE_CODE = "EMPTY_HEADING_TITLE"


class HeadingType(str, Enum):
    """Heading kinds whose titles can be checked by the validation policy."""

    FEATURE = "feature"
    SCENARIO = "scenario"
    SCENARIO_OUTLINE = "scenario_outline"

    @property
    def display_name(self) -> str:
        if self is HeadingType.FEATURE:
            return "Feature"
        if self is HeadingType.SCENARIO:
            return "Scenario"
        return "Scenario Outline"


@frozen
class ParsedHeadingRecord:
    """A title and source location read from the configured Gherkin parser model."""

    document_path: str
    heading_type: HeadingType
    name_raw: str | None
    line: int
    column: int | None = None


@frozen
class HeadingValidationPolicy:
    """The stable semantic rules used by the CLI, baseline audit and strict collection."""

    policy_id: str = "feature-heading-policy-v1"
    enforced_heading_types: tuple[HeadingType, ...] = (
        HeadingType.FEATURE,
        HeadingType.SCENARIO,
        HeadingType.SCENARIO_OUTLINE,
    )
    trim_whitespace: bool = True
    empty_name_is_violation: bool = True
    snippet_text_excluded: bool = True

    def normalize_name(self, name: str | None) -> str:
        normalized = "" if name is None else name
        return normalized.strip() if self.trim_whitespace else normalized

    def to_payload(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "enforced_heading_types": [heading_type.value for heading_type in self.enforced_heading_types],
            "trim_whitespace": self.trim_whitespace,
            "empty_name_is_violation": self.empty_name_is_violation,
            "snippet_text_excluded": self.snippet_text_excluded,
        }


@frozen
class HeadingValidationViolation:
    """A parsed Feature or Scenario heading that violates the active policy."""

    path: str
    line: int
    heading_type: HeadingType
    code: str
    message: str
    raw_name: str | None

    def to_payload(self) -> dict[str, object]:
        return {
            "path": self.path,
            "line": self.line,
            "heading_type": self.heading_type.value,
            "code": self.code,
            "message": self.message,
            "raw_name": self.raw_name,
        }


@frozen
class HeadingValidationRun:
    """One deterministic scan result; timestamps and run identity identify its execution."""

    run_id: str
    started_at: datetime
    finished_at: datetime
    documents_scanned: int
    violations: tuple[HeadingValidationViolation, ...]

    @property
    def status(self) -> str:
        return "fail" if self.violations else "pass"

    def to_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "documents_scanned": self.documents_scanned,
            "violations": [violation.to_payload() for violation in self.violations],
            "status": self.status,
            "started_at": self.started_at.astimezone(timezone.utc).isoformat(),
            "finished_at": self.finished_at.astimezone(timezone.utc).isoformat(),
        }


@frozen
class BaselineAuditSummary:
    """A compact compliance record for the current heading policy and scan."""

    record_id: str
    policy_id: str
    run_id: str
    violations_count: int
    compliant: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "policy_id": self.policy_id,
            "run_id": self.run_id,
            "violations_count": self.violations_count,
            "compliant": self.compliant,
        }


def default_heading_validation_policy() -> HeadingValidationPolicy:
    """Return the versioned default policy used by scans and strict collection."""
    return HeadingValidationPolicy()


def heading_validation_policy_payload(
    policy: HeadingValidationPolicy | None = None,
) -> dict[str, object]:
    """Serialize the policy using its historical, stable JSON field names."""
    active_policy = default_heading_validation_policy() if policy is None else policy
    return active_policy.to_payload()


def validate_heading_records(
    records: tuple[ParsedHeadingRecord, ...] | list[ParsedHeadingRecord],
    policy: HeadingValidationPolicy | None = None,
) -> list[HeadingValidationViolation]:
    """Apply the pure policy to records produced from a parsed Gherkin document."""
    active_policy = default_heading_validation_policy() if policy is None else policy
    violations: list[HeadingValidationViolation] = []
    for record in records:
        if record.heading_type not in active_policy.enforced_heading_types:
            continue
        if active_policy.empty_name_is_violation and not active_policy.normalize_name(record.name_raw):
            violations.append(
                HeadingValidationViolation(
                    path=record.document_path,
                    line=record.line,
                    heading_type=record.heading_type,
                    code=EMPTY_HEADING_TITLE_CODE,
                    message=f"{record.heading_type.display_name} heading title is empty after trimming whitespace",
                    raw_name=record.name_raw,
                ),
            )
    return violations


__all__ = [
    "EMPTY_HEADING_TITLE_CODE",
    "BaselineAuditSummary",
    "HeadingType",
    "HeadingValidationPolicy",
    "HeadingValidationRun",
    "HeadingValidationViolation",
    "ParsedHeadingRecord",
    "default_heading_validation_policy",
    "heading_validation_policy_payload",
    "validate_heading_records",
]
