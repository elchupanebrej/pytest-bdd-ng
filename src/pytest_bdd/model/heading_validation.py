"""Models for feature heading validation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from attrs import frozen

EMPTY_HEADING_TITLE_CODE = "EMPTY_HEADING_TITLE"


class HeadingType(str, Enum):
    """Heading kinds covered by validation policy."""

    FEATURE = "feature"
    SCENARIO = "scenario"
    SCENARIO_OUTLINE = "scenario_outline"

    @property
    def display_name(self) -> str:
        """Human-friendly heading label used in diagnostics."""
        if self is HeadingType.FEATURE:
            return "Feature"
        if self is HeadingType.SCENARIO:
            return "Scenario"
        return "Scenario Outline"


@frozen
class ParsedHeadingRecord:
    """Single parsed heading located in a feature document."""

    document_path: str
    heading_type: HeadingType
    name_raw: str | None
    line: int
    column: int | None = None


@frozen
class HeadingValidationPolicy:
    """Rule set for heading title validation."""

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
        """Normalize heading title according to policy."""
        normalized = "" if name is None else name
        if self.trim_whitespace:
            normalized = normalized.strip()
        return normalized


@frozen
class HeadingValidationViolation:
    """Validation violation emitted for one heading."""

    path: str
    line: int
    heading_type: HeadingType
    code: str
    message: str
    raw_name: str | None

    def to_payload(self) -> dict[str, object]:
        """Serialize violation to contract-compatible payload."""
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
    """Result of repository heading validation scan."""

    run_id: str
    started_at: datetime
    finished_at: datetime
    documents_scanned: int
    violations: tuple[HeadingValidationViolation, ...]

    @property
    def status(self) -> str:
        """Run status in contract form."""
        return "fail" if self.violations else "pass"

    def to_payload(self) -> dict[str, object]:
        """Serialize run result to contract-compatible payload."""
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
    """Baseline compliance summary for repository features tree."""

    record_id: str
    policy_id: str
    run_id: str
    violations_count: int
    compliant: bool

    def to_payload(self) -> dict[str, object]:
        """Serialize audit summary to contract-compatible payload."""
        return {
            "record_id": self.record_id,
            "policy_id": self.policy_id,
            "run_id": self.run_id,
            "violations_count": self.violations_count,
            "compliant": self.compliant,
        }


def default_heading_validation_policy() -> HeadingValidationPolicy:
    """Build default policy instance."""
    return HeadingValidationPolicy()
