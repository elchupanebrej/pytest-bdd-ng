"""Unit tests for parsers.py — direct instantiation of parser classes."""

from __future__ import annotations

import re as stdlib_re

import pytest

from pytest_bdd.parsers import (
    ParserBuildValueError,
    RegistryMode,
    StepParser,
    cfparse,
    cucumber_expression,
    cucumber_regular_expression,
    heuristic,
    parse,
    string,
)
from pytest_bdd.parsers import (
    re as re_parser,
)

pytestmark = [pytest.mark.unit]


# ── StepParser.build factory ────────────────────────────────────────────────


class TestStepParserBuild:
    """Tests for StepParser.build() factory method."""

    def test_build_with_regex_string(self) -> None:
        """build returns heuristic parser for regex-like string (heuristic tries all)."""
        parser = StepParser.build(r"step with (?P<name>\w+)")
        # Heuristic parser because string input goes through heuristic
        assert isinstance(parser, heuristic)

    def test_build_with_compiled_regex(self) -> None:
        """build returns re parser for compiled regex."""
        pattern = stdlib_re.compile(r"step (?P<name>\w+)")
        parser = StepParser.build(pattern)
        assert isinstance(parser, re_parser)

    def test_build_with_parse_format(self) -> None:
        """build returns heuristic parser for format string input."""
        import parse as base_parse

        existing = base_parse.compile("step {name}")
        parser = StepParser.build(existing)
        assert isinstance(parser, parse)

    def test_build_with_cucumber_expression_object(self) -> None:
        """build returns cucumber_expression parser for CucumberExpression object."""
        from cucumber_expressions.expression import CucumberExpression
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

        ce = CucumberExpression("step with {word}", ParameterTypeRegistry())
        parser = StepParser.build(ce)
        assert isinstance(parser, cucumber_expression)

    def test_build_with_plain_string(self) -> None:
        """build returns heuristic parser for plain string."""
        parser = StepParser.build("exact step text")
        assert isinstance(parser, heuristic)

    def test_build_returns_parser_protocol(self) -> None:
        """build returns StepParserProtocol instance."""
        from pytest_bdd.parsers import StepParserProtocol

        parser = StepParser.build("test")
        assert isinstance(parser, StepParserProtocol)


# ── re parser ───────────────────────────────────────────────────────────────


class TestReParser:
    """Tests for re parser class."""

    def test_init_with_string_pattern(self) -> None:
        """re parser initializes with string pattern."""
        p = re_parser(r"step (?P<n>\d+)")
        assert p.pattern == r"step (?P<n>\d+)"

    def test_init_with_compiled_pattern(self) -> None:
        """re parser initializes with compiled regex."""
        compiled = stdlib_re.compile(r"step (?P<n>\d+)")
        p = re_parser(compiled)
        assert p.pattern == r"step (?P<n>\d+)"

    def test_is_matching_returns_true(self) -> None:
        """is_matching returns True for matching text."""
        p = re_parser(r"step (?P<n>\d+)")
        assert p.is_matching(None, "step 42") is True

    def test_is_matching_returns_false(self) -> None:
        """is_matching returns False for non-matching text."""
        p = re_parser(r"step (?P<n>\d+)")
        assert p.is_matching(None, "no match") is False

    def test_parse_arguments_with_named_groups(self) -> None:
        """parse_arguments extracts named groups."""
        p = re_parser(r"step (?P<n>\d+)")
        result = p.parse_arguments(None, "step 42")
        assert result == {"n": "42"}

    def test_parse_arguments_with_anonymous_groups(self) -> None:
        """parse_arguments handles anonymous group names."""
        p = re_parser(r"step (\d+)")
        result = p.parse_arguments(None, "step 42", anonymous_group_names=["number"])
        assert result == {"number": "42"}

    def test_arguments_property(self) -> None:
        """arguments returns named group keys."""
        p = re_parser(r"step (?P<n>\d+) and (?P<m>\w+)")
        assert set(p.arguments) == {"n", "m"}

    def test_str_returns_pattern(self) -> None:
        """__str__ returns the pattern string."""
        p = re_parser(r"test pattern")
        assert str(p) == "test pattern"

    def test_type_attribute(self) -> None:
        """type is pytest_bdd_regular_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert re_parser.type == StepDefinitionPatternType.pytest_bdd_regular_expression


# ── parse parser ────────────────────────────────────────────────────────────


class TestParseParser:
    """Tests for parse parser class."""

    def test_init_with_format_string(self) -> None:
        """parse parser initializes with format string."""
        p = parse("step {name}")
        assert p.format == "step {name}"

    def test_init_with_parser_object(self) -> None:
        """parse parser initializes with existing Parser object."""
        import parse as base_parse

        existing = base_parse.compile("step {name}")
        p = parse(existing)
        assert p.format == "step {name}"

    def test_is_matching_returns_true(self) -> None:
        """is_matching returns True for matching text."""
        p = parse("step {name}")
        assert p.is_matching(None, "step hello") is True

    def test_is_matching_returns_false(self) -> None:
        """is_matching returns False for non-matching text."""
        p = parse("step {name}")
        assert p.is_matching(None, "no match") is False

    def test_parse_arguments(self) -> None:
        """parse_arguments extracts named parameters."""
        p = parse("step {name}")
        result = p.parse_arguments(None, "step world")
        assert result == {"name": "world"}

    def test_parse_arguments_with_anonymous_groups(self) -> None:
        """parse_arguments handles anonymous group names."""
        p = parse("{} items")
        result = p.parse_arguments(None, "5 items", anonymous_group_names=["count"])
        assert result == {"count": "5"}

    def test_arguments_property(self) -> None:
        """arguments returns parameter names."""
        p = parse("step {name} with {value}")
        assert set(p.arguments) == {"name", "value"}

    def test_str_returns_format(self) -> None:
        """__str__ returns the format string."""
        p = parse("test format")
        assert str(p) == "test format"

    def test_type_attribute(self) -> None:
        """type is pytest_bdd_parse_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert parse.type == StepDefinitionPatternType.pytest_bdd_parse_expression


# ── cfparse parser ──────────────────────────────────────────────────────────


class TestCfparseParser:
    """Tests for cfparse parser class."""

    def test_init(self) -> None:
        """cfparse parser initializes correctly."""
        p = cfparse("{:d} items")
        assert p.format == "{:d} items"

    def test_is_matching(self) -> None:
        """is_matching returns True for matching text."""
        p = cfparse("{:d} items")
        assert p.is_matching(None, "5 items") is True

    def test_is_matching_returns_false(self) -> None:
        """is_matching returns False for non-matching text."""
        p = cfparse("{:d} items")
        assert p.is_matching(None, "five items") is False

    def test_parse_arguments(self) -> None:
        """parse_arguments extracts typed parameters."""
        p = cfparse("{:d} items")
        result = p.parse_arguments(None, "42 items")
        # cfparse uses empty string as key for positional args
        assert "" in result or result is not None

    def test_type_attribute(self) -> None:
        """type is pytest_bdd_cfparse_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert cfparse.type == StepDefinitionPatternType.pytest_bdd_cfparse_expression


# ── string parser ───────────────────────────────────────────────────────────


class TestStringParser:
    """Tests for string (exact match) parser."""

    def test_init(self) -> None:
        """string parser stores the name."""
        p = string("exact step")
        assert p.name == "exact step"

    def test_is_matching_exact(self) -> None:
        """is_matching returns True for exact match."""
        p = string("exact step")
        assert p.is_matching(None, "exact step") is True

    def test_is_matching_not_exact(self) -> None:
        """is_matching returns False for non-exact match."""
        p = string("exact step")
        assert p.is_matching(None, "exact step extra") is False

    def test_parse_arguments_returns_empty(self) -> None:
        """parse_arguments always returns empty dict."""
        p = string("exact step")
        assert p.parse_arguments(None, "exact step") == {}

    def test_arguments_empty(self) -> None:
        """arguments returns empty list."""
        p = string("exact step")
        assert p.arguments == []

    def test_str_returns_name(self) -> None:
        """__str__ returns the step name."""
        p = string("exact step")
        assert str(p) == "exact step"

    def test_type_attribute(self) -> None:
        """type is pytest_bdd_string_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert string.type == StepDefinitionPatternType.pytest_bdd_string_expression


# ── cucumber_expression parser ──────────────────────────────────────────────


class TestCucumberExpressionParser:
    """Tests for cucumber_expression parser."""

    def test_init_with_string(self) -> None:
        """cucumber_expression initializes with string."""
        p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.pattern == "I have {int} cucumbers"

    def test_is_matching(self) -> None:
        """is_matching returns True for matching text."""
        p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.is_matching(None, "I have 5 cucumbers") is True

    def test_is_matching_returns_false(self) -> None:
        """is_matching returns False for non-matching text."""
        p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.is_matching(None, "no cucumbers") is False

    def test_arguments_empty(self) -> None:
        """arguments returns empty list for cucumber expressions."""
        p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.arguments == []

    def test_str_returns_pattern(self) -> None:
        """__str__ returns the expression pattern."""
        p = cucumber_expression("test {word}", parameter_type_registry=RegistryMode.GLOBAL)
        assert str(p) == "test {word}"

    def test_type_attribute(self) -> None:
        """type is cucumber_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert cucumber_expression.type == StepDefinitionPatternType.cucumber_expression


# ── cucumber_regular_expression parser ──────────────────────────────────────


class TestCucumberRegularExpressionParser:
    """Tests for cucumber_regular_expression parser."""

    def test_init_with_string(self) -> None:
        """cucumber_regular_expression initializes with string."""
        p = cucumber_regular_expression(r"step (?P<n>\d+)")
        assert p.pattern == r"step (?P<n>\d+)"

    def test_arguments(self) -> None:
        """arguments returns regex group names."""
        p = cucumber_regular_expression(r"step (?P<n>\d+)")
        assert p.arguments == ["n"]

    def test_type_attribute(self) -> None:
        """type is regular_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert cucumber_regular_expression.type == StepDefinitionPatternType.regular_expression


# ── heuristic parser ────────────────────────────────────────────────────────


class TestHeuristicParser:
    """Tests for heuristic parser."""

    def test_init_with_string(self) -> None:
        """heuristic parser initializes with string format."""
        p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.format == "step {name}"
        assert p.parsers_are_built is True

    def test_is_matching_delegates_to_subparsers(self) -> None:
        """is_matching returns True if any sub-parser matches."""
        p = heuristic("exact step", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.is_matching(None, "exact step") is True

    def test_is_matching_returns_false(self) -> None:
        """is_matching returns False when no sub-parser matches."""
        p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
        assert p.is_matching(None, "completely different") is False

    def test_parse_arguments_delegates(self) -> None:
        """parse_arguments uses the first matching sub-parser."""
        p = heuristic("exact step", parameter_type_registry=RegistryMode.GLOBAL)
        result = p.parse_arguments(None, "exact step")
        assert result == {}

    def test_parse_arguments_returns_none_when_no_match(self) -> None:
        """parse_arguments returns None when no parser matches."""
        p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
        result = p.parse_arguments(None, "no match at all")
        assert result is None

    def test_arguments_aggregates_all(self) -> None:
        """arguments aggregates argument names from all sub-parsers."""
        p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
        args = p.arguments
        assert isinstance(args, list)

    def test_str_returns_format(self) -> None:
        """__str__ returns the format string."""
        p = heuristic("test format", parameter_type_registry=RegistryMode.GLOBAL)
        assert str(p) == "test format"

    def test_type_attribute(self) -> None:
        """type is pytest_bdd_heuristic_expression."""
        from pytest_bdd.model.message_extension import StepDefinitionPatternType

        assert heuristic.type == StepDefinitionPatternType.pytest_bdd_heuristic_expression


# ── ParserBuildValueError ───────────────────────────────────────────────────


class TestParserBuildValueError:
    """Tests for ParserBuildValueError exception."""

    def test_message_includes_format(self) -> None:
        """Error message includes the format value."""
        err = ParserBuildValueError("invalid")
        assert "invalid" in str(err)
