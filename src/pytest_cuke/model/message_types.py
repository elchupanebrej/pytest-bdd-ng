"""Official Cucumber Messages classes and the pytest-cuke wire adapter.

The upstream Python binding uses dataclasses rather than Pydantic models. This
module keeps the producer's import surface in one place and centralizes the
camelCase JSON conversion required by the Messages wire format.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, TypeAlias, TypeVar, cast, overload

from cucumber_messages import (
    Attachment,
    AttachmentContentEncoding,
    Background,
    Ci,
    Comment,
    DataTable,
    DocString,
    Duration,
    Envelope,
    Examples,
    Feature,
    FeatureChild,
    GherkinDocument,
    Git,
    Group,
    Hook,
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    Meta,
    ParameterType,
    ParseError,
    Pickle,
    PickleDocString,
    PickleStep,
    PickleStepArgument,
    PickleStepType,
    PickleTable,
    PickleTableCell,
    PickleTableRow,
    PickleTag,
    Product,
    Rule,
    RuleChild,
    Scenario,
    Source,
    SourceMediaType,
    SourceReference,
    Step,
    StepDefinition,
    StepDefinitionPattern,
    StepKeywordType,
    TableCell,
    TableRow,
    Tag,
    TestCase,
    TestCaseFinished,
    TestCaseStarted,
    TestRunFinished,
    TestRunHookFinished,
    TestRunHookStarted,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepResultStatus,
    TestStepStarted,
    Timestamp,
    UndefinedParameterType,
    message_converter,
)
from cucumber_messages import (
    Exception as ExceptionMessage,
)
from cucumber_messages import (
    StepDefinitionPatternType as MessageStepDefinitionPatternType,
)

ContentEncoding: TypeAlias = AttachmentContentEncoding
Status: TypeAlias = TestStepResultStatus
KeywordType: TypeAlias = StepKeywordType

_T = TypeVar("_T")

_PYTEST_PATTERN_TYPES: dict[str, str] = {
    # Messages standardizes patterns to two executable syntaxes. pytest-cuke
    # keeps its parser-specific identity internally; the wire format records
    # the standard expression family understood by downstream consumers.
    "PYTEST_BDD_HEURISTIC_EXPRESSION": "CUCUMBER_EXPRESSION",
    "PYTEST_BDD_STRING_EXPRESSION": "CUCUMBER_EXPRESSION",
    "PYTEST_BDD_PARSE_EXPRESSION": "CUCUMBER_EXPRESSION",
    "PYTEST_BDD_CFPARSE_EXPRESSION": "CUCUMBER_EXPRESSION",
    "PYTEST_BDD_OTHER_EXPRESSION": "CUCUMBER_EXPRESSION",
    "PYTEST_BDD_REGULAR_EXPRESSION": "REGULAR_EXPRESSION",
}


def message_field_names(message_type: type[Any]) -> tuple[str, ...]:
    """Return generated dataclass fields in declaration order."""
    if not is_dataclass(message_type):
        raise TypeError(f"{message_type!r} is not a Cucumber Messages dataclass")
    return tuple(field.name for field in fields(message_type))


def message_to_dict(message: Any) -> dict[str, Any]:
    """Serialize a Messages dataclass to its canonical camelCase wire object."""
    wire_data: Any
    if is_dataclass(message):
        wire_data = message_converter.to_dict(message)
    else:
        dump = getattr(message, "model_dump", None)
        if not callable(dump):
            raise TypeError(f"{type(message).__name__} is not a Cucumber Messages dataclass")
        wire_data = dump(mode="json", exclude_none=True, by_alias=True)
    if not isinstance(wire_data, dict):
        raise TypeError("a Cucumber Messages envelope must serialize to a JSON object")
    wire = cast("dict[str, Any]", wire_data)

    step_definition_data = wire.get("stepDefinition")
    step_definition = (
        cast("dict[str, Any]", step_definition_data)
        if isinstance(step_definition_data, dict)
        else None
    )
    pattern = cast(
        "dict[str, Any] | None",
        step_definition.get("pattern") if step_definition is not None else None,
    )
    pattern_type = pattern.get("type") if pattern is not None else None
    if isinstance(pattern_type, Enum):
        pattern_type = pattern_type.value
    if (
        isinstance(pattern, dict)
        and isinstance(pattern_type, str)
        and pattern_type in _PYTEST_PATTERN_TYPES
    ):
        pattern["type"] = _PYTEST_PATTERN_TYPES[pattern_type]
    return wire


def to_wire_step_definition_pattern_type(
    value: Enum | str,
) -> MessageStepDefinitionPatternType:
    """Translate pytest-cuke parser types to the standard Messages enum."""
    pattern_type = value.value if isinstance(value, Enum) else value
    if not isinstance(pattern_type, str):
        raise TypeError("step definition pattern type must be a string")
    pattern_type = _PYTEST_PATTERN_TYPES.get(pattern_type, pattern_type)
    return MessageStepDefinitionPatternType(pattern_type)


@overload
def message_from_dict(payload: dict[str, Any]) -> Envelope: ...


@overload
def message_from_dict(payload: dict[str, Any], message_type: type[_T]) -> _T: ...


def message_from_dict(
    payload: dict[str, Any], message_type: type[Any] = Envelope
) -> Any:
    """Build a generated Messages dataclass from its camelCase JSON object."""
    return message_converter.from_dict(payload, message_type)


def message_json(message: Any) -> str:
    """Serialize a Messages dataclass using the canonical wire vocabulary."""
    return json.dumps(message_to_dict(message), ensure_ascii=False)


__all__ = [
    "Attachment",
    "Background",
    "Ci",
    "Comment",
    "ContentEncoding",
    "DataTable",
    "DocString",
    "Duration",
    "Envelope",
    "Examples",
    "ExceptionMessage",
    "Feature",
    "FeatureChild",
    "GherkinDocument",
    "Git",
    "Group",
    "Hook",
    "HookType",
    "JavaMethod",
    "JavaStackTraceElement",
    "KeywordType",
    "Location",
    "MessageStepDefinitionPatternType",
    "Meta",
    "ParameterType",
    "ParseError",
    "Pickle",
    "PickleDocString",
    "PickleStep",
    "PickleStepArgument",
    "PickleStepType",
    "PickleTable",
    "PickleTableCell",
    "PickleTableRow",
    "PickleTag",
    "Product",
    "Rule",
    "RuleChild",
    "Scenario",
    "Source",
    "SourceMediaType",
    "SourceReference",
    "Status",
    "Step",
    "StepDefinition",
    "StepDefinitionPattern",
    "StepKeywordType",
    "TableCell",
    "TableRow",
    "Tag",
    "TestCase",
    "TestCaseFinished",
    "TestCaseStarted",
    "TestRunFinished",
    "TestRunHookFinished",
    "TestRunHookStarted",
    "TestRunStarted",
    "TestStep",
    "TestStepFinished",
    "TestStepResult",
    "TestStepResultStatus",
    "TestStepStarted",
    "Timestamp",
    "UndefinedParameterType",
    "message_converter",
    "message_field_names",
    "message_from_dict",
    "message_json",
    "message_to_dict",
    "to_wire_step_definition_pattern_type",
]
