"""Direct unit tests for step parsers."""

from __future__ import annotations

from re import compile as re_compile

import pytest
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.regular_expression import RegularExpression
from parse import Parser as ParseParser
from returns.result import Failure, Success

from pytest_bdd.parsers import (
    ParserBuildValueError,
    StepParser,
    _build_parser_result,
    cfparse,
    cucumber_expression,
    cucumber_regular_expression,
    heuristic,
    parse,
    re,
    string,
)

pytestmark = [pytest.mark.unit]


class TestStepParserBuild:
    """Tests for StepParser.build() factory method."""

    def test_build_with_re_pattern(self):
        """Build parser from compiled regex pattern."""
        pattern = re_compile(r"I have (\d+) Euro")
        parser = StepParser.build(pattern)
        assert isinstance(parser, re)
        assert parser.is_matching(None, "I have 5 Euro")

    def test_build_with_parse_parser(self):
        """Build parser from parse.Parser instance."""
        parse_parser = ParseParser("I have {euro:d} Euro")
        parser = StepParser.build(parse_parser)
        assert isinstance(parser, parse)
        assert parser.is_matching(None, "I have 5 Euro")

    def test_build_with_cucumber_expression(self):
        """Build parser from CucumberExpression instance."""
        expr = CucumberExpression("I have {int} Euro", ParameterTypeRegistry())
        parser = StepParser.build(expr)
        assert isinstance(parser, cucumber_expression)

    def test_build_with_cucumber_regular_expression(self):
        """Build parser from CucumberRegularExpression instance."""
        expr = RegularExpression(r"I have (\d+) Euro", ParameterTypeRegistry())
        parser = StepParser.build(expr)
        assert isinstance(parser, cucumber_regular_expression)

    def test_build_with_plain_string(self):
        """Build parser from plain string uses heuristic."""
        parser = StepParser.build("I have a wallet")
        assert isinstance(parser, heuristic)
        assert parser.is_matching(None, "I have a wallet")

    def test_build_with_regex_str(self):
        """Build parser from string pattern delegates to heuristic, then re."""
        parser = StepParser.build(r"I have (\d+) Euro")
        assert isinstance(parser, heuristic)

    def test_build_with_step_parser_protocol(self):
        """Build returns existing StepParserProtocol instance unchanged."""
        existing = re(r"I have (\d+) Euro")
        parser = StepParser.build(existing)
        assert parser is existing


class TestReParser:
    """Tests for re step parser."""

    def test_init_with_string(self):
        """Initialize from string pattern."""
        parser = re(r"I have (\d+) Euro")
        assert parser.pattern == r"I have (\d+) Euro"

    def test_init_with_compiled_pattern(self):
        """Initialize from compiled regex."""
        compiled = re_compile(r"I have (\d+) Euro")
        parser = re(compiled)
        assert parser.pattern == r"I have (\d+) Euro"

    def test_is_matching_positive(self):
        """Regex matches step text."""
        parser = re(r"I have (\d+) Euro")
        assert parser.is_matching(None, "I have 5 Euro") is True

    def test_is_matching_negative(self):
        """Regex does not match unrelated text."""
        parser = re(r"I have (\d+) Euro")
        assert parser.is_matching(None, "I pay 5 Euro") is False

    def test_parse_arguments_named_group(self):
        """Parse named groups from step text."""
        parser = re(r"I have (?P<euro>\d+) Euro")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result == {"euro": "5"}

    def test_parse_arguments_anonymous_groups(self):
        """Parse anonymous groups with anonymous_group_names."""
        parser = re(r"I have (\d+) Euro")
        result = parser.parse_arguments(None, "I have 5 Euro", anonymous_group_names=["euro"])
        assert result == {"euro": "5"}

    def test_parse_arguments_anonymous_with_named(self):
        """Parse mix of anonymous and named groups."""
        parser = re(r"I have (\d+) (.+)")
        result = parser.parse_arguments(None, "I have 5 Euro", anonymous_group_names=["count"])
        assert result["count"] == "5"

    def test_parse_arguments_optional_named_group(self):
        """Parse arguments with optional named group that doesn't capture."""
        parser = re(r"I have (?P<euro>\d+) Euro")
        assert parser.is_matching(None, "I have 5 Euro")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result == {"euro": "5"}

    def test_arguments_property_named(self):
        """Arguments returns named group names."""
        parser = re(r"I have (?P<euro>\d+) Euro")
        assert parser.arguments == ["euro"]

    def test_arguments_property_empty(self):
        """Arguments returns empty list for no named groups."""
        parser = re(r"I have (\d+) Euro")
        assert parser.arguments == []

    def test_str_returns_pattern(self):
        """String representation returns pattern."""
        parser = re(r"I have (\d+) Euro")
        assert str(parser) == r"I have (\d+) Euro"


class TestParseParser:
    """Tests for parse step parser."""

    def test_init_with_string(self):
        """Initialize from string format."""
        parser = parse("I have {euro:d} Euro")
        assert parser.format == "I have {euro:d} Euro"

    def test_init_with_parse_parser(self):
        """Initialize from existing parse.Parser."""
        existing = ParseParser("I have {euro:d} Euro")
        parser = parse(existing)
        assert parser.format == "I have {euro:d} Euro"

    def test_cfparse_classmethod(self):
        """Create cfparse-based parser via classmethod returns parse instance."""
        parser = parse.cfparse("I have {euro:d} Euro")
        assert isinstance(parser, parse)
        assert parser.format == "I have {euro:d} Euro"

    def test_is_matching_positive(self):
        """Parse format matches step text."""
        parser = parse("I have {euro:d} Euro")
        assert parser.is_matching(None, "I have 5 Euro") is True

    def test_is_matching_negative(self):
        """Parse format does not match unrelated text."""
        parser = parse("I have {euro:d} Euro")
        assert parser.is_matching(None, "I pay 5 Euro") is False

    def test_parse_arguments(self):
        """Parse arguments from step text."""
        parser = parse("I have {euro:d} Euro")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result["euro"] == 5

    def test_is_matching_handles_conversion_failure(self):
        """Parse format reports no match when conversion fails."""
        parser = parse("I have {euro:d} Euro")

        assert parser.is_matching(None, "I have five Euro") is False

    def test_parse_arguments_named(self):
        """Parse named arguments."""
        parser = parse("I have {euro} Euro")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result["euro"] == "5"

    def test_arguments_property(self):
        """Arguments returns argument names from format."""
        parser = parse("I have {euro:d} Euro")
        assert parser.arguments == ["euro"]

    def test_str_returns_format(self):
        """String representation returns format string."""
        parser = parse("I have {euro:d} Euro")
        assert str(parser) == "I have {euro:d} Euro"


class TestCfparseParser:
    """Tests for cfparse step parser."""

    def test_init_delegates(self):
        """Initialize cfparse delegates to parse."""
        parser = cfparse("I have {euro:d} Euro")
        assert isinstance(parser, cfparse)
        assert parser.format == "I have {euro:d} Euro"

    def test_is_matching(self):
        """cfparse matches step text."""
        parser = cfparse("I have {euro:d} Euro")
        assert parser.is_matching(None, "I have 5 Euro") is True

    def test_parse_arguments(self):
        """cfparse parses arguments."""
        parser = cfparse("I have {euro:d} Euro")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result["euro"] == 5


class TestCucumberExpression:
    """Tests for cucumber_expression parser."""

    def test_init_with_string(self):
        """Initialize with string pattern and FIXTURE registry mode."""
        parser = cucumber_expression("I have {int} Euro")
        assert parser.pattern == "I have {int} Euro"

    def test_init_with_cucumber_expression_object(self):
        """Initialize from existing CucumberExpression object."""
        expr = CucumberExpression("I have {int} Euro", ParameterTypeRegistry())
        parser = cucumber_expression(expr)
        assert parser.pattern == "I have {int} Euro"

    def test_arguments_always_empty(self):
        """Cucumber expression arguments is always empty."""
        parser = cucumber_expression("I have {int} Euro")
        assert parser.arguments == []

    def test_str_returns_pattern(self):
        """String representation returns pattern."""
        parser = cucumber_expression("I have {int} Euro")
        assert str(parser) == "I have {int} Euro"


class TestCucumberRegularExpression:
    """Tests for cucumber_regular_expression parser."""

    def test_init_with_string(self):
        """Initialize with string pattern."""
        parser = cucumber_regular_expression(r"I have (\d+) Euro")
        assert parser.pattern == r"I have (\d+) Euro"

    def test_init_with_regexp_object(self):
        """Initialize from existing CucumberRegularExpression."""
        expr = RegularExpression(r"I have (\d+) Euro", ParameterTypeRegistry())
        parser = cucumber_regular_expression(expr)
        assert parser.pattern == r"I have (\d+) Euro"

    def test_arguments_returns_group_names(self):
        """Arguments returns named group names from regex."""
        parser = cucumber_regular_expression(r"(?P<euro>\d+)")
        assert parser.arguments == ["euro"]


class TestStringParser:
    """Tests for string (exact match) parser."""

    def test_init(self):
        """Initialize with exact string."""
        parser = string("I have a wallet")
        assert parser.name == "I have a wallet"

    def test_is_matching_exact(self):
        """Matches exact step text."""
        parser = string("I have a wallet")
        assert parser.is_matching(None, "I have a wallet") is True

    def test_is_matching_no_match(self):
        """Does not match different text."""
        parser = string("I have a wallet")
        assert parser.is_matching(None, "I have 5 Euro") is False

    def test_parse_arguments_always_empty(self):
        """String parser returns empty dict."""
        parser = string("I have a wallet")
        result = parser.parse_arguments(None, "I have a wallet")
        assert result == {}

    def test_arguments_empty(self):
        """Arguments is always empty for string parser."""
        parser = string("I have a wallet")
        assert parser.arguments == []

    def test_str_returns_name(self):
        """String representation returns exact name."""
        parser = string("I have a wallet")
        assert str(parser) == "I have a wallet"


class TestHeuristicParser:
    """Tests for heuristic step parser."""

    def _make_parser(self, format_: str, *, registry_mode: str | None = None):
        """Helper to create heuristic parser with explicit registry mode."""
        from pytest_bdd.parsers import RegistryMode

        mode = registry_mode if registry_mode is not None else RegistryMode.GLOBAL
        return heuristic(format_, parameter_type_registry=mode)

    def test_init_with_string(self):
        """Initialize from plain string."""
        parser = heuristic("I have a wallet")
        assert parser.format == "I have a wallet"
        assert parser.parsers_are_built is True

    def test_build_parsers(self):
        """Builds all sub-parsers."""
        parser = self._make_parser("I have {euro:d} Euro")
        parser.build_parsers()
        assert parser.parsers_are_built is True

    def test_build_parsers_idempotent(self):
        """Calling build_parsers twice is safe."""
        parser = self._make_parser("I have a wallet")
        parser.build_parsers()
        parser.build_parsers()
        assert parser.parsers_are_built is True

    def test_is_matching_exact_string(self):
        """Matches exact string."""
        parser = self._make_parser("I have a wallet")
        assert parser.is_matching(None, "I have a wallet") is True

    def test_is_matching_no_match(self):
        """Does not match unrelated text."""
        parser = self._make_parser("I have a wallet")
        assert parser.is_matching(None, "I have 5 Euro") is False

    def test_is_matching_regex(self):
        """Matches via regex sub-parser."""
        parser = self._make_parser(r"I have (\d+) Euro")
        assert parser.is_matching(None, "I have 5 Euro") is True

    def test_is_matching_parse_format(self):
        """Matches via parse sub-parser."""
        parser = self._make_parser("I have {euro:d} Euro")
        assert parser.is_matching(None, "I have 5 Euro") is True

    def test_parse_arguments_exact_string(self):
        """Parse arguments for exact string returns empty."""
        parser = self._make_parser("I have a wallet")
        result = parser.parse_arguments(None, "I have a wallet")
        assert result == {}

    def test_parse_arguments_parse_format(self):
        """Parse arguments via parse sub-parser."""
        parser = self._make_parser("I have {euro:d} Euro")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result["euro"] == 5

    def test_parse_arguments_none_when_no_match(self):
        """Returns None when no parser matches."""
        parser = self._make_parser("I have a wallet")
        result = parser.parse_arguments(None, "I have 5 Euro")
        assert result is None

    def test_arguments_empty_string(self):
        """Arguments is empty for plain string."""
        parser = self._make_parser("I have a wallet")
        assert parser.arguments == []

    def test_arguments_includes_all_sub_parsers(self):
        """Arguments includes names from matching sub-parsers."""
        parser = self._make_parser("I have {euro:d} Euro")
        args = parser.arguments
        assert "euro" in args

    def test_str_returns_format(self):
        """String representation returns format."""
        parser = self._make_parser("I have a wallet")
        assert str(parser) == "I have a wallet"


class TestParserBuildResult:
    """Tests for _build_parser_result helper."""

    def test_build_success(self):
        """Returns Success for valid parser."""
        result = _build_parser_result(lambda: string("test"))
        assert isinstance(result, Success)

    def test_build_failure(self):
        """Returns Failure for builder that raises an expected error."""
        from pytest_bdd.parsers import _EXPECTED_PARSER_BUILD_ERRORS

        def bad_builder():
            msg = "test error"
            raise _EXPECTED_PARSER_BUILD_ERRORS[0](msg)

        result = _build_parser_result(bad_builder)
        assert isinstance(result, Failure)


class TestParserBuildValueError:
    """Tests for ParserBuildValueError."""

    def test_inherits_from_value_error(self):
        """Is a subclass of ValueError."""
        assert issubclass(ParserBuildValueError, ValueError)

    def test_error_message(self):
        """Error message includes format info."""
        err = ParserBuildValueError(42)
        assert "42" in str(err)
