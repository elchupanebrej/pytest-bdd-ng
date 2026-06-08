"""
Provide message validation result types.

Responsibility:
    Provide message validation result types. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_validation_result` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - MessageValidationViolation: owns nested behavior below this boundary
    - MessageValidationResult: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `message_validation_result`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `message_validation_result`
    - src/pytest_bdd/model/message_validation.py: imports or references `message_validation_result`
    - src/pytest_bdd/model/message_validation_xdist.py: imports or references `message_validation_result`

State and side effects:
    mutates SchemaValidationResult, AllowedImplementationStatus, ValidationCode, code, message; depends on
    __future__.annotations, typing.TYPE_CHECKING, typing.Literal, attrs.frozen, returns.result.Result.

Invariants:
    - `pytest_bdd.model.message_validation_result` keeps its documented import path, ownership boundary, and observable
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
    #arch-eval:locational_stability=4
"""

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
    """
    Capture details about a specific validation error encountered while analyzing a message envelope or stream.

    Responsibility:
        Capture details about a specific validation error encountered while analyzing a message envelope or stream. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_validation_result.MessageValidationViolation` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `MessageValidationViolation`
        - src/pytest_bdd/model/__init__.py: imports or references `MessageValidationViolation`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `MessageValidationViolation`
        - src/pytest_bdd/model/message_validation.py: imports or references `MessageValidationViolation`
        - src/pytest_bdd/model/message_validation_xdist.py: imports or references `MessageValidationViolation`

    State and side effects:
        mutates code, message, json_path, schema_path, validator.

    Invariants:
        - `pytest_bdd.model.message_validation_result.MessageValidationViolation` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    code: ValidationCode
    message: str
    json_path: tuple[str, ...] = ()
    schema_path: tuple[str, ...] = ()
    validator: str | None = None


@frozen
class MessageValidationResult:
    """
    Aggregate outcomes and violations from a validation pass.

    Responsibility:
        Aggregate outcomes and violations from a validation pass. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_validation_result.MessageValidationResult`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - is_valid: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `MessageValidationResult`
        - src/pytest_bdd/model/__init__.py: imports or references `MessageValidationResult`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `MessageValidationResult`
        - src/pytest_bdd/model/message_validation.py: imports or references `MessageValidationResult`
        - src/pytest_bdd/model/message_validation_xdist.py: imports or references `MessageValidationResult`

    State and side effects:
        mutates status, orphan_reference_count, duplicate_lifecycle_id_count, blocked_for_release, violations.

    Invariants:
        - `pytest_bdd.model.message_validation_result.MessageValidationResult` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

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

        Responsibility:
            Determine if the validation result represents a complete success with no violations. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_validation_result.MessageValidationResult.is_valid` because it keeps the nearest
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
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `is_valid`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `is_valid`
            - src/pytest_bdd/model/message_validation.py: imports or references `is_valid`
            - src/pytest_bdd/model/message_validation_xdist.py: imports or references `is_valid`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `is_valid`

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
        return self.status == "pass"
