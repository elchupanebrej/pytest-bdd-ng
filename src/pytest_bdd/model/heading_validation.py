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
        """
        Provide a human-readable label for the heading type, used in diagnostic output.

        Returns:
            The string label corresponding to the specific heading type.

        """
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
        """
        Normalize a raw heading title string by applying policy rules, such as whitespace trimming.

        Returns:
            The normalized heading title as a string, or an empty string if the input is None.

        """
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
        """
        Convert the validation violation into a JSON-serializable dictionary format.

        Returns:
            A dictionary containing the structured violation data.

        """
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
        """
        Determine the overall pass/fail status of the validation run based on emitted violations.

        Returns:
            The string 'fail' if violations exist, otherwise 'pass'.

        """
        return "fail" if self.violations else "pass"

    def to_payload(self) -> dict[str, object]:
        """
        Convert the comprehensive validation run results into a JSON-serializable dictionary format.

        Returns:
            A dictionary capturing the full validation run state.

        """
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
        """
        Convert the baseline audit summary into a JSON-serializable dictionary format.

        Returns:
            A dictionary summarizing the baseline compliance check.

        """
        return {
            "record_id": self.record_id,
            "policy_id": self.policy_id,
            "run_id": self.run_id,
            "violations_count": self.violations_count,
            "compliant": self.compliant,
        }


def default_heading_validation_policy() -> HeadingValidationPolicy:
    """
    Instantiate the default heading validation policy ruleset.

    Returns:
        A HeadingValidationPolicy populated with standard defaults.

    """
    return HeadingValidationPolicy()
