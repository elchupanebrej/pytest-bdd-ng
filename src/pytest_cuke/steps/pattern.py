"""Project built-in parser syntax into a standard Messages pattern family."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pytest_cuke.model import message_types as messages
from pytest_cuke.model.message_extension import StepDefinitionPatternType

if TYPE_CHECKING:
    from pytest_cuke.parsers.base import StepParser


def definition_pattern(parser: StepParser) -> messages.StepDefinitionPattern:
    declared_type = parser.type
    family = (
        declared_type
        if isinstance(declared_type, StepDefinitionPatternType)
        else StepDefinitionPatternType(str(declared_type))
    )
    regex_family = messages.MessageStepDefinitionPatternType("REGULAR_EXPRESSION")
    if family == StepDefinitionPatternType.pytest_cuke_string_expression:
        return messages.StepDefinitionPattern(source=r"\A" + re.escape(str(parser)) + r"\Z", type=regex_family)

    compiled = None
    if family in {
        StepDefinitionPatternType.pytest_cuke_parse_expression,
        StepDefinitionPatternType.pytest_cuke_cfparse_expression,
    }:
        compiled = getattr(getattr(parser, "parser", None), "_match_re", None)
    elif family in {
        StepDefinitionPatternType.regular_expression,
        StepDefinitionPatternType.pytest_cuke_regular_expression,
    }:
        compiled = getattr(parser, "regex", None)
    if isinstance(compiled, re.Pattern) and isinstance(compiled.pattern, str):
        flags = "".join(
            name
            for flag, name in (
                (re.ASCII, "a"),
                (re.IGNORECASE, "i"),
                (re.MULTILINE, "m"),
                (re.DOTALL, "s"),
                (re.VERBOSE, "x"),
            )
            if compiled.flags & flag
        )
        source = (f"(?{flags})" if flags else "") + compiled.pattern
        return messages.StepDefinitionPattern(source=source, type=regex_family)

    return messages.StepDefinitionPattern(
        source=str(parser), type=messages.to_wire_step_definition_pattern_type(family)
    )
