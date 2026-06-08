"""
Typed failure reasons for Result-based pytest-bdd operations.

Responsibility:
    Typed failure reasons for Result-based pytest-bdd operations. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.types.failure_reasons` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - StashFailure: owns nested behavior below this boundary
    - ScenarioRunFailure: owns nested behavior below this boundary
    - MessageValidationFailure: owns nested behavior below this boundary
    - FeatureLocatorFailure: owns nested behavior below this boundary
    - CollectorFailure: owns nested behavior below this boundary
    - ParserFailure: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `failure_reasons`
    - src/pytest_bdd/feature_locator.py: imports or references `failure_reasons`
    - src/pytest_bdd/model/message_validation_result.py: imports or references `failure_reasons`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `failure_reasons`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `failure_reasons`

State and side effects:
    mutates PARSE_FAILED, NOT_FOUND, TYPE_MISMATCH, ALREADY_INITIALIZED, FEATURE_NOT_BOUND; depends on
    __future__.annotations, pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.types.failure_reasons` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from pytest_bdd.compatibility.enum import StrEnum


class StashFailure(StrEnum):
    """
    Failure reasons for stash access operations.

    Responsibility:
        Failure reasons for stash access operations. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.StashFailure` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `StashFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `StashFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `StashFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `StashFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `StashFailure`

    State and side effects:
        mutates NOT_FOUND, TYPE_MISMATCH, ALREADY_INITIALIZED.

    Invariants:
        - `pytest_bdd.types.failure_reasons.StashFailure` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    NOT_FOUND = "not_found"
    TYPE_MISMATCH = "type_mismatch"
    ALREADY_INITIALIZED = "already_initialized"


class ScenarioRunFailure(StrEnum):
    """
    Failure reasons for scenario run operations.

    Responsibility:
        Failure reasons for scenario run operations. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.ScenarioRunFailure` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `ScenarioRunFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `ScenarioRunFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `ScenarioRunFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ScenarioRunFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `ScenarioRunFailure`

    State and side effects:
        mutates FEATURE_NOT_BOUND, STEP_NOT_FOUND, INVALID_STAGE, BINDING_FAILED.

    Invariants:
        - `pytest_bdd.types.failure_reasons.ScenarioRunFailure` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    FEATURE_NOT_BOUND = "feature_not_bound"
    STEP_NOT_FOUND = "step_not_found"
    INVALID_STAGE = "invalid_stage"
    BINDING_FAILED = "binding_failed"


class MessageValidationFailure(StrEnum):
    """
    Failure reasons for message validation operations.

    Responsibility:
        Failure reasons for message validation operations. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.MessageValidationFailure` because it
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
        - src/pytest_bdd/collector_batch.py: imports or references `MessageValidationFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `MessageValidationFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `MessageValidationFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `MessageValidationFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `MessageValidationFailure`

    State and side effects:
        mutates SCHEMA_LOAD_ERROR, VALIDATION_FAILED, INVALID_ENVELOPE.

    Invariants:
        - `pytest_bdd.types.failure_reasons.MessageValidationFailure` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """

    SCHEMA_LOAD_ERROR = "schema_load_error"
    VALIDATION_FAILED = "validation_failed"
    INVALID_ENVELOPE = "invalid_envelope"


class FeatureLocatorFailure(StrEnum):
    """
    Failure reasons for feature locator operations.

    Responsibility:
        Failure reasons for feature locator operations. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.FeatureLocatorFailure` because it
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
        - src/pytest_bdd/collector_batch.py: imports or references `FeatureLocatorFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `FeatureLocatorFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `FeatureLocatorFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `FeatureLocatorFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `FeatureLocatorFailure`

    State and side effects:
        mutates FILE_NOT_FOUND, PARSE_FAILED, RESOLUTION_FAILED.

    Invariants:
        - `pytest_bdd.types.failure_reasons.FeatureLocatorFailure` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    FILE_NOT_FOUND = "file_not_found"
    PARSE_FAILED = "parse_failed"
    RESOLUTION_FAILED = "resolution_failed"


class CollectorFailure(StrEnum):
    """
    Failure reasons for collection operations.

    Responsibility:
        Failure reasons for collection operations. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.CollectorFailure` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `CollectorFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `CollectorFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `CollectorFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `CollectorFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `CollectorFailure`

    State and side effects:
        mutates PARSE_FAILED, READ_FAILED, BATCH_FAILED.

    Invariants:
        - `pytest_bdd.types.failure_reasons.CollectorFailure` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    PARSE_FAILED = "parse_failed"
    READ_FAILED = "read_failed"
    BATCH_FAILED = "batch_failed"


class ParserFailure(StrEnum):
    """
    Failure reasons for parser operations.

    Responsibility:
        Failure reasons for parser operations. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.ParserFailure` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `ParserFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `ParserFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `ParserFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ParserFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `ParserFailure`

    State and side effects:
        mutates SYNTAX_ERROR, UNSUPPORTED_MIMETYPE.

    Invariants:
        - `pytest_bdd.types.failure_reasons.ParserFailure` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    SYNTAX_ERROR = "syntax_error"
    UNSUPPORTED_MIMETYPE = "unsupported_mimetype"


class GenericFailure(StrEnum):
    """
    Failure reasons for uncategorized operations.

    Responsibility:
        Failure reasons for uncategorized operations. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.failure_reasons.GenericFailure` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `GenericFailure`
        - src/pytest_bdd/feature_locator.py: imports or references `GenericFailure`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `GenericFailure`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `GenericFailure`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `GenericFailure`

    State and side effects:
        mutates UNEXPECTED_ERROR.

    Invariants:
        - `pytest_bdd.types.failure_reasons.GenericFailure` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    UNEXPECTED_ERROR = "unexpected_error"
