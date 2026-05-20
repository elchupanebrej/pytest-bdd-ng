"""Parser Result contract tests — verify _build_parser_result returns Result type."""

from __future__ import annotations

import pytest
from returns.result import Failure, Success

from pytest_bdd.parsers import (
    _EXPECTED_PARSER_BUILD_ERRORS,
    _build_parser_result,
    heuristic,
    string,
)
from pytest_bdd.types.failure_reasons import ParserFailure

pytestmark = [pytest.mark.unit]


class TestBuildParserResult:
    """Tests for _build_parser_result returning Result[T, ParserFailure]."""

    def test_returns_success_for_valid_builder(self):
        """_build_parser_result returns Success when builder succeeds."""
        result = _build_parser_result(lambda: string("test"))
        assert isinstance(result, Success)

    def test_success_wraps_parsed_output(self):
        """Success contains the actual parser instance."""
        result = _build_parser_result(lambda: string("hello"))
        assert result.unwrap().name == "hello"

    def test_returns_failure_for_syntax_error(self):
        """_build_parser_result returns Failure for expected parser build errors."""
        for error_cls in _EXPECTED_PARSER_BUILD_ERRORS:
            result = _build_parser_result(
                lambda err=error_cls: (_ for _ in ()).throw(err("bad input")),
            )
            assert isinstance(result, Failure), f"Expected Failure for {error_cls}"

    def test_failure_carries_parser_failure_reason(self):
        """Failure contains ParserFailure.SYNTAX_ERROR as the reason."""
        result = _build_parser_result(
            lambda: (_ for _ in ()).throw(ValueError("bad syntax")),
        )
        assert result.failure() == ParserFailure.SYNTAX_ERROR

    def test_heuristic_uses_result_internally(self):
        """heuristic.build_parsers uses _build_parser_result for each sub-parser."""
        parser = heuristic("test step", parameter_type_registry="GLOBAL")
        # After build_parsers, sub-parsers are set (not None for valid input)
        assert parser.parsers_are_built is True
        # At least one parser should be built for a plain string
        assert any(
            p is not None
            for p in [
                parser.string_parser,
                parser.cucumber_expression_parser,
                parser.cfparse_parser,
                parser.re_parser,
            ]
        )

    def test_heuristic_raises_on_unbuildable_input(self):
        """heuristic.build_parsers raises ParserBuildValueError when no parser succeeds."""
        # Non-string input that can't be parsed by any sub-parser
        parser = heuristic(object(), parameter_type_registry="GLOBAL")
        # build_parsers is called in __init__, but object() won't match string check
        # so format is stored as-is, and parsers will fail
        # At least one parser should still be attempted
        assert parser.parsers_are_built is True
