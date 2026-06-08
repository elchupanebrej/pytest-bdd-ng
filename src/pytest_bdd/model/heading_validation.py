"""
Models for feature heading validation.

Responsibility:
    Models for feature heading validation. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.heading_validation` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - HeadingType: owns nested behavior below this boundary
    - ParsedHeadingRecord: owns nested behavior below this boundary
    - HeadingValidationPolicy: owns nested behavior below this boundary
    - HeadingValidationViolation: owns nested behavior below this boundary
    - HeadingValidationRun: owns nested behavior below this boundary
    - BaselineAuditSummary: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/validate_feature_headings.py: imports or references `heading_validation`

State and side effects:
    mutates heading_type, line, policy_id, normalized, run_id; depends on __future__.annotations, datetime.datetime,
    datetime.timezone, enum.Enum, attrs.frozen.

Invariants:
    - `pytest_bdd.model.heading_validation` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from datetime import datetime, timezone
from enum import Enum

from attrs import frozen

EMPTY_HEADING_TITLE_CODE = "EMPTY_HEADING_TITLE"


class HeadingType(str, Enum):
    """
    Heading kinds covered by validation policy.

    Responsibility:
        Heading kinds covered by validation policy. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.heading_validation.HeadingType` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - display_name: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `HeadingType`

    State and side effects:
        mutates FEATURE, SCENARIO, SCENARIO_OUTLINE.

    Invariants:
        - `pytest_bdd.model.heading_validation.HeadingType` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    FEATURE = "feature"
    SCENARIO = "scenario"
    SCENARIO_OUTLINE = "scenario_outline"

    @property
    def display_name(self) -> str:
        """
        Provide a human-readable label for the heading type, used in diagnostic output.

        Returns:
            The string label corresponding to the specific heading type.

        Responsibility:
            Provide a human-readable label for the heading type, used in diagnostic output. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.heading_validation.HeadingType.display_name`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/_feature_tree.py: imports or references `display_name`
            - src/pytest_bdd/script/validate_feature_headings.py: imports or references `display_name`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3

        """
        if self is HeadingType.FEATURE:
            return "Feature"
        if self is HeadingType.SCENARIO:
            return "Scenario"
        return "Scenario Outline"


@frozen
class ParsedHeadingRecord:
    """
    Single parsed heading located in a feature document.

    Responsibility:
        Single parsed heading located in a feature document. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.heading_validation.ParsedHeadingRecord` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `ParsedHeadingRecord`

    State and side effects:
        mutates document_path, heading_type, name_raw, line, column.

    Invariants:
        - `pytest_bdd.model.heading_validation.ParsedHeadingRecord` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    document_path: str
    heading_type: HeadingType
    name_raw: str | None
    line: int
    column: int | None = None


@frozen
class HeadingValidationPolicy:
    """
    Rule set for heading title validation.

    Responsibility:
        Rule set for heading title validation. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.heading_validation.HeadingValidationPolicy` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_name: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `HeadingValidationPolicy`

    State and side effects:
        mutates normalized, policy_id, enforced_heading_types, trim_whitespace, empty_name_is_violation.

    Invariants:
        - `pytest_bdd.model.heading_validation.HeadingValidationPolicy` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

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

        Responsibility:
            Normalize a raw heading title string by applying policy rules, such as whitespace trimming. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.heading_validation.HeadingValidationPolicy.normalize_name` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - normalized.strip: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/validate_feature_headings.py: imports or references `normalize_name`

        State and side effects:
            mutates normalized.

        Invariants:
            - `pytest_bdd.model.heading_validation.HeadingValidationPolicy.normalize_name` keeps its documented import
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
            #arch-eval:locational_stability=3

        """
        normalized = "" if name is None else name
        if self.trim_whitespace:
            normalized = normalized.strip()
        return normalized


@frozen
class HeadingValidationViolation:
    """
    Validation violation emitted for one heading.

    Responsibility:
        Validation violation emitted for one heading. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.heading_validation.HeadingValidationViolation`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - to_payload: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `HeadingValidationViolation`

    State and side effects:
        mutates path, line, heading_type, code, message.

    Invariants:
        - `pytest_bdd.model.heading_validation.HeadingValidationViolation` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

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

        Responsibility:
            Convert the validation violation into a JSON-serializable dictionary format. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.heading_validation.HeadingValidationViolation.to_payload` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/validate_feature_headings.py: imports or references `to_payload`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3

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
    """
    Result of repository heading validation scan.

    Responsibility:
        Result of repository heading validation scan. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.heading_validation.HeadingValidationRun` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - status: owns nested behavior below this boundary
        - to_payload: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `HeadingValidationRun`

    State and side effects:
        mutates run_id, started_at, finished_at, documents_scanned, violations.

    Invariants:
        - `pytest_bdd.model.heading_validation.HeadingValidationRun` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

        Responsibility:
            Determine the overall pass/fail status of the validation run based on emitted violations. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.heading_validation.HeadingValidationRun.status`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `status`
            - src/pytest_bdd/message_stream_validation/status.py: imports or references `status`
            - src/pytest_bdd/model/message_governance_checklist.py: imports or references `status`
            - src/pytest_bdd/model/message_outcome_mapping.py: imports or references `status`
            - src/pytest_bdd/model/message_status_governance.py: imports or references `status`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

        """
        return "fail" if self.violations else "pass"

    def to_payload(self) -> dict[str, object]:
        """
        Convert the comprehensive validation run results into a JSON-serializable dictionary format.

        Returns:
            A dictionary capturing the full validation run state.

        Responsibility:
            Convert the comprehensive validation run results into a JSON-serializable dictionary format. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.heading_validation.HeadingValidationRun.to_payload` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - violation.to_payload: collaborator call used by this boundary
            - self.started_at.astimezone.isoformat: collaborator call used by this boundary
            - self.started_at.astimezone: collaborator call used by this boundary
            - self.finished_at.astimezone.isoformat: collaborator call used by this boundary
            - self.finished_at.astimezone: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/validate_feature_headings.py: imports or references `to_payload`

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
    """
    Baseline compliance summary for repository features tree.

    Responsibility:
        Baseline compliance summary for repository features tree. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.heading_validation.BaselineAuditSummary` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - to_payload: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `BaselineAuditSummary`

    State and side effects:
        mutates record_id, policy_id, run_id, violations_count, compliant.

    Invariants:
        - `pytest_bdd.model.heading_validation.BaselineAuditSummary` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

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

        Responsibility:
            Convert the baseline audit summary into a JSON-serializable dictionary format. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.heading_validation.BaselineAuditSummary.to_payload` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/validate_feature_headings.py: imports or references `to_payload`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3

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

    Responsibility:
        Instantiate the default heading validation policy ruleset. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.heading_validation.default_heading_validation_policy` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - HeadingValidationPolicy: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `default_heading_validation_policy`

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
    return HeadingValidationPolicy()
