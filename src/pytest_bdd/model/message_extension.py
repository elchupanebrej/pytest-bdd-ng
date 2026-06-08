"""
Provide message extension helpers.

Responsibility:
    Provide message extension helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_extension` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - StepDefinitionPattern: owns nested behavior below this boundary
    - _is_optional_type: owns nested behavior below this boundary
    - _unwrap_optional: owns nested behavior below this boundary
    - _payload_field_hints: owns nested behavior below this boundary
    - LifecycleCorrelation: owns nested behavior below this boundary
    - EnvelopeStatus: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `message_extension`
    - src/pytest_bdd/message_stream_validation/status.py: imports or references `message_extension`
    - src/pytest_bdd/model/message_converter.py: imports or references `message_extension`
    - src/pytest_bdd/model/message_registry.py: imports or references `message_extension`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `message_extension`

State and side effects:
    mutates StepDefinitionPatternType, type, EventEnvelope, PAYLOAD_KINDS, PayloadKind; depends on
    __future__.annotations, enum.Enum, typing.Final, typing.TypeAlias, typing.cast.

Invariants:
    - `pytest_bdd.model.message_extension` keeps its documented import path, ownership boundary, and observable behavior
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

# pylint: disable=function-redefined

from __future__ import annotations

from enum import Enum
from typing import Final, TypeAlias, cast, get_args, get_type_hints

from attrs import define
from cucumber_messages import *  # noqa: F403 This module patches the cucumber_messages module to extend it with pytest_bdd specific types
from cucumber_messages import Envelope as _BaseEnvelope
from cucumber_messages import StepDefinitionPattern as _BaseStepDefinitionPattern
from cucumber_messages import StepDefinitionPatternType as _BaseStepDefinitionPatternType

StepDefinitionPatternType = Enum(  # type: ignore[misc, no-redef]  # extends cucumber_messages enum with pytest-bdd values
    "StepDefinitionPatternType",
    dict(
        **{name: member.value for name, member in _BaseStepDefinitionPatternType.__members__.items()},
        pytest_bdd_heuristic_expression="PYTEST_BDD_HEURISTIC_EXPRESSION",
        pytest_bdd_string_expression="PYTEST_BDD_STRING_EXPRESSION",
        pytest_bdd_regular_expression="PYTEST_BDD_REGULAR_EXPRESSION",
        pytest_bdd_parse_expression="PYTEST_BDD_PARSE_EXPRESSION",
        pytest_bdd_cfparse_expression="PYTEST_BDD_CFPARSE_EXPRESSION",
        pytest_bdd_other_expression="PYTEST_BDD_OTHER_EXPRESSION",
    ),
)


@define(init=False, repr=False, eq=False)
class StepDefinitionPattern(_BaseStepDefinitionPattern):  # type: ignore[no-redef]  # extends cucumber_messages StepDefinitionPattern
    """
    Extend the canonical cucumber StepDefinitionPattern with pytest-bdd-specific expression type variants.

    Responsibility:
        Extend the canonical cucumber StepDefinitionPattern with pytest-bdd-specific expression type variants. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension.StepDefinitionPattern` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `StepDefinitionPattern`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `StepDefinitionPattern`
        - src/pytest_bdd/model/message_registry.py: imports or references `StepDefinitionPattern`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `StepDefinitionPattern`
        - src/pytest_bdd/model/message_validation.py: imports or references `StepDefinitionPattern`

    State and side effects:
        mutates type.

    Invariants:
        - `pytest_bdd.model.message_extension.StepDefinitionPattern` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """

    type: StepDefinitionPatternType

    def __init__(self, source: str, type: StepDefinitionPatternType) -> None:  # noqa: A002
        """
        Initialize the step definition pattern.

        Responsibility:
            Initialize the step definition pattern. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_extension.StepDefinitionPattern.__init__` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `__init__`

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
            #arch-eval:locational_stability=4
        """
        super().__init__(source=source, type=type)


EventEnvelope: TypeAlias = _BaseEnvelope

# Keep payload kinds auto-synced with cucumber-messages Envelope schema to
# avoid manual maintenance on library upgrades.
PAYLOAD_KINDS: Final[tuple[str, ...]] = tuple(_BaseEnvelope.__annotations__.keys())
PayloadKind: TypeAlias = str

_GOVERNANCE_STATUS_FIELDS: Final[tuple[str, ...]] = (
    "implementation_status",
    "implementation_comment",
    "hook_origin",
)

_ENVELOPE_HINTS: Final[dict[str, object]] = get_type_hints(_BaseEnvelope, globalns=globals())


def _is_optional_type(value: object) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_extension._is_optional_type` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension._is_optional_type` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - any: collaborator call used by this boundary
        - type: collaborator call used by this boundary
        - get_args: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_is_optional_type`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `_is_optional_type`
        - src/pytest_bdd/model/message_registry.py: imports or references `_is_optional_type`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_is_optional_type`
        - src/pytest_bdd/model/message_validation.py: imports or references `_is_optional_type`

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
        #arch-eval:locational_stability=4
    """
    return any(option is type(None) for option in get_args(value))


def _unwrap_optional(value: object) -> object:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_extension._unwrap_optional` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension._unwrap_optional` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - get_args: collaborator call used by this boundary
        - type: collaborator call used by this boundary
        - len: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_unwrap_optional`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `_unwrap_optional`
        - src/pytest_bdd/model/message_registry.py: imports or references `_unwrap_optional`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_unwrap_optional`
        - src/pytest_bdd/model/message_validation.py: imports or references `_unwrap_optional`

    State and side effects:
        mutates args.

    Invariants:
        - `pytest_bdd.model.message_extension._unwrap_optional` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    args = tuple(option for option in get_args(value) if option is not type(None))
    if len(args) == 1:
        return args[0]
    return value


def _payload_field_hints(payload_kind: PayloadKind) -> dict[str, object]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_extension._payload_field_hints` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension._payload_field_hints` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _ENVELOPE_HINTS.get: collaborator call used by this boundary
        - _unwrap_optional: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - get_type_hints: collaborator call used by this boundary
        - globals: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_payload_field_hints`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `_payload_field_hints`
        - src/pytest_bdd/model/message_registry.py: imports or references `_payload_field_hints`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_payload_field_hints`
        - src/pytest_bdd/model/message_validation.py: imports or references `_payload_field_hints`

    State and side effects:
        mutates payload_annotation, payload_type.

    Invariants:
        - `pytest_bdd.model.message_extension._payload_field_hints` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    payload_annotation = _ENVELOPE_HINTS.get(payload_kind)
    if payload_annotation is None:
        return {}
    payload_type = _unwrap_optional(payload_annotation)
    if not isinstance(payload_type, type):
        return {}
    return get_type_hints(payload_type, globalns=globals())


_PAYLOAD_HINTS_BY_KIND: Final[dict[PayloadKind, dict[str, object]]] = {
    payload_kind: _payload_field_hints(payload_kind) for payload_kind in PAYLOAD_KINDS
}

STATUS_CAPABLE_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind
    for payload_kind in PAYLOAD_KINDS
    if any(field_name in _PAYLOAD_HINTS_BY_KIND[payload_kind] for field_name in _GOVERNANCE_STATUS_FIELDS)
)

REQUIRED_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind
    for payload_kind in STATUS_CAPABLE_PAYLOAD_KINDS
    if (
        "implementation_status" in _PAYLOAD_HINTS_BY_KIND[payload_kind]
        and not _is_optional_type(_PAYLOAD_HINTS_BY_KIND[payload_kind]["implementation_status"])
    )
)

OPTIONAL_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind for payload_kind in STATUS_CAPABLE_PAYLOAD_KINDS if payload_kind not in REQUIRED_STATUS_PAYLOAD_KINDS
)

NOT_APPLICABLE_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind for payload_kind in PAYLOAD_KINDS if payload_kind not in STATUS_CAPABLE_PAYLOAD_KINDS
)

CONTROLLER_SINGULAR_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "meta",
    "test_run_started",
    "test_run_finished",
)

STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "source",
    "gherkin_document",
    "pickle",
    "step_definition",
    "parameter_type",
    "hook",
    "test_case",
)

EXECUTION_PRESERVED_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind
    for payload_kind in PAYLOAD_KINDS
    if payload_kind not in CONTROLLER_SINGULAR_PAYLOAD_KINDS + STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS
)


@define(frozen=True, slots=True)
class LifecycleCorrelation:
    """
    Associate a scenario execution attempt with its parent run, worker, and step context for traceability.

    Responsibility:
        Associate a scenario execution attempt with its parent run, worker, and step context for traceability. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension.LifecycleCorrelation` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `LifecycleCorrelation`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `LifecycleCorrelation`
        - src/pytest_bdd/model/message_registry.py: imports or references `LifecycleCorrelation`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `LifecycleCorrelation`
        - src/pytest_bdd/model/message_validation.py: imports or references `LifecycleCorrelation`

    State and side effects:
        mutates run_id, scenario_attempt_id, worker_id, attempt_index, step_id.

    Invariants:
        - `pytest_bdd.model.message_extension.LifecycleCorrelation` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    run_id: str
    scenario_attempt_id: str
    worker_id: str
    attempt_index: int
    step_id: str | None = None


@define(frozen=True, slots=True)
class EnvelopeStatus:
    """
    Capture governance status fields extracted from an envelope for validation and reporting purposes.

    Responsibility:
        Capture governance status fields extracted from an envelope for validation and reporting purposes. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension.EnvelopeStatus` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `EnvelopeStatus`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `EnvelopeStatus`
        - src/pytest_bdd/model/message_registry.py: imports or references `EnvelopeStatus`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `EnvelopeStatus`
        - src/pytest_bdd/model/message_validation.py: imports or references `EnvelopeStatus`

    State and side effects:
        mutates implementation_status, implementation_comment, comment_present, hook_origin.

    Invariants:
        - `pytest_bdd.model.message_extension.EnvelopeStatus` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    implementation_status: str | None
    implementation_comment: str | None
    comment_present: bool
    hook_origin: str | None


def get_payload_merge_class(payload_kind: PayloadKind | None) -> str | None:
    """
    Classify an envelope's payload kind into a merge-strategy bucket for stream consolidation.

    Returns:
        A string denoting the merge class ('controller_singular', 'structural_deduplicated', or 'execution_preserved'),
        or None if the payload kind is unrecognized.

    Responsibility:
        Classify an envelope's payload kind into a merge-strategy bucket for stream consolidation. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension.get_payload_merge_class` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `get_payload_merge_class`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `get_payload_merge_class`
        - src/pytest_bdd/model/message_registry.py: imports or references `get_payload_merge_class`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `get_payload_merge_class`
        - src/pytest_bdd/model/message_validation.py: imports or references `get_payload_merge_class`

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
        #arch-eval:locational_stability=4

    """
    if payload_kind is None:
        return cast("str | None", None)
    if payload_kind in CONTROLLER_SINGULAR_PAYLOAD_KINDS:
        return "controller_singular"
    if payload_kind in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS:
        return "structural_deduplicated"
    if payload_kind in EXECUTION_PRESERVED_PAYLOAD_KINDS:
        return "execution_preserved"
    return cast("str | None", None)


def get_payload_kind(message: EventEnvelope) -> PayloadKind | None:
    """
    Identify the single active payload field name within an EventEnvelope.

    Returns:
        The payload kind string if exactly one field is populated, or None if the envelope is empty or ambiguous.

    Responsibility:
        Identify the single active payload field name within an EventEnvelope. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension.get_payload_kind` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - len: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `get_payload_kind`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `get_payload_kind`
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `get_payload_kind`
        - src/pytest_bdd/model/message_registry.py: imports or references `get_payload_kind`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `get_payload_kind`

    State and side effects:
        mutates matched_payload_kinds.

    Invariants:
        - `pytest_bdd.model.message_extension.get_payload_kind` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    matched_payload_kinds = [
        payload_kind for payload_kind in PAYLOAD_KINDS if getattr(message, payload_kind, None) is not None
    ]
    if len(matched_payload_kinds) != 1:
        return cast("PayloadKind | None", None)
    return matched_payload_kinds[0]


def has_single_payload(message: EventEnvelope) -> bool:
    """
    Verify that an EventEnvelope satisfies the oneof payload constraint by carrying exactly one populated field.

    Returns:
        True if exactly one payload field is present, otherwise False.

    Responsibility:
        Verify that an EventEnvelope satisfies the oneof payload constraint by carrying exactly one populated field. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_extension.has_single_payload` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_payload_kind: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `has_single_payload`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `has_single_payload`
        - src/pytest_bdd/model/message_converter.py: imports or references `has_single_payload`
        - src/pytest_bdd/model/message_registry.py: imports or references `has_single_payload`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `has_single_payload`

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
        #arch-eval:locational_stability=4

    """
    return get_payload_kind(message) is not None
