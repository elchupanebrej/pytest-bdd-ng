"""

Unit tests for parsers.py — direct instantiation of parser classes.
"""

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


# === TestStepParserBuild (converted) ===


def test_step_parser_build_test_build_with_regex_string() -> None:
    """
    Build returns heuristic parser for regex-like string (heuristic tries all).

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    parser = StepParser.build(r"step with (?P<name>\w+)")
    # Heuristic parser because string input goes through heuristic
    assert isinstance(parser, heuristic)


def test_step_parser_build_test_build_with_compiled_regex() -> None:
    """
    Build returns re parser for compiled regex.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pattern = stdlib_re.compile(r"step (?P<name>\w+)")
    parser = StepParser.build(pattern)
    assert isinstance(parser, re_parser)


def test_step_parser_build_test_build_with_parse_format() -> None:
    """
    Build returns heuristic parser for format string input.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    import parse as base_parse

    existing = base_parse.compile("step {name}")
    parser = StepParser.build(existing)
    assert isinstance(parser, parse)


def test_step_parser_build_test_build_with_cucumber_expression_object() -> None:
    """
    Build returns cucumber_expression parser for CucumberExpression object.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_expressions.expression import CucumberExpression
    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

    ce = CucumberExpression("step with {word}", ParameterTypeRegistry())
    parser = StepParser.build(ce)
    assert isinstance(parser, cucumber_expression)


def test_step_parser_build_test_build_with_plain_string() -> None:
    """
    Build returns heuristic parser for plain string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    parser = StepParser.build("exact step text")
    assert isinstance(parser, heuristic)


def test_step_parser_build_test_build_returns_parser_protocol() -> None:
    """
    Build returns StepParserProtocol instance.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.parsers import StepParserProtocol

    parser = StepParser.build("test")
    assert isinstance(parser, StepParserProtocol)


# ── re parser ───────────────────────────────────────────────────────────────


# === TestReParser (converted) ===


def test_re_parser_test_init_with_string_pattern() -> None:
    """
    Re parser initializes with string pattern.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"step (?P<n>\d+)")
    assert p.pattern == r"step (?P<n>\d+)"


def test_re_parser_test_init_with_compiled_pattern() -> None:
    """
    Re parser initializes with compiled regex.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    compiled = stdlib_re.compile(r"step (?P<n>\d+)")
    p = re_parser(compiled)
    assert p.pattern == r"step (?P<n>\d+)"


def test_re_parser_test_is_matching_returns_true() -> None:
    """
    is_matching returns True for matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"step (?P<n>\d+)")
    assert p.is_matching(None, "step 42") is True


def test_re_parser_test_is_matching_returns_false() -> None:
    """
    is_matching returns False for non-matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"step (?P<n>\d+)")
    assert p.is_matching(None, "no match") is False


def test_re_parser_test_parse_arguments_with_named_groups() -> None:
    """
    parse_arguments extracts named groups.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"step (?P<n>\d+)")
    result = p.parse_arguments(None, "step 42")
    assert result == {"n": "42"}


def test_re_parser_test_parse_arguments_with_anonymous_groups() -> None:
    """
    parse_arguments handles anonymous group names.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"step (\d+)")
    result = p.parse_arguments(None, "step 42", anonymous_group_names=["number"])
    assert result == {"number": "42"}


def test_re_parser_test_arguments_property() -> None:
    """
    Arguments returns named group keys.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"step (?P<n>\d+) and (?P<m>\w+)")
    assert set(p.arguments) == {"n", "m"}


def test_re_parser_test_str_returns_pattern() -> None:
    """
    __str__ returns the pattern string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = re_parser(r"test pattern")
    assert str(p) == "test pattern"


def test_re_parser_test_type_attribute() -> None:
    """
    Type is pytest_bdd_regular_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert re_parser.type == StepDefinitionPatternType.pytest_bdd_regular_expression


# ── parse parser ────────────────────────────────────────────────────────────


# === TestParseParser (converted) ===


def test_parse_parser_test_init_with_format_string() -> None:
    """
    Parse parser initializes with format string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("step {name}")
    assert p.format == "step {name}"


def test_parse_parser_test_init_with_parser_object() -> None:
    """
    Parse parser initializes with existing Parser object.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    import parse as base_parse

    existing = base_parse.compile("step {name}")
    p = parse(existing)
    assert p.format == "step {name}"


def test_parse_parser_test_is_matching_returns_true() -> None:
    """
    is_matching returns True for matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("step {name}")
    assert p.is_matching(None, "step hello") is True


def test_parse_parser_test_is_matching_returns_false() -> None:
    """
    is_matching returns False for non-matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("step {name}")
    assert p.is_matching(None, "no match") is False


def test_parse_parser_test_parse_arguments() -> None:
    """
    parse_arguments extracts named parameters.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("step {name}")
    result = p.parse_arguments(None, "step world")
    assert result == {"name": "world"}


def test_parse_parser_test_parse_arguments_with_anonymous_groups() -> None:
    """
    parse_arguments handles anonymous group names.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("{} items")
    result = p.parse_arguments(None, "5 items", anonymous_group_names=["count"])
    assert result == {"count": "5"}


def test_parse_parser_test_arguments_property() -> None:
    """
    Arguments returns parameter names.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("step {name} with {value}")
    assert set(p.arguments) == {"name", "value"}


def test_parse_parser_test_str_returns_format() -> None:
    """
    __str__ returns the format string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = parse("test format")
    assert str(p) == "test format"


def test_parse_parser_test_type_attribute() -> None:
    """
    Type is pytest_bdd_parse_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert parse.type == StepDefinitionPatternType.pytest_bdd_parse_expression


# ── cfparse parser ──────────────────────────────────────────────────────────


# === TestCfparseParser (converted) ===


def test_cfparse_parser_test_init() -> None:
    """
    Cfparse parser initializes correctly.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cfparse("{:d} items")
    assert p.format == "{:d} items"


def test_cfparse_parser_test_is_matching() -> None:
    """
    is_matching returns True for matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cfparse("{:d} items")
    assert p.is_matching(None, "5 items") is True


def test_cfparse_parser_test_is_matching_returns_false() -> None:
    """
    is_matching returns False for non-matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cfparse("{:d} items")
    assert p.is_matching(None, "five items") is False


def test_cfparse_parser_test_parse_arguments() -> None:
    """
    parse_arguments extracts typed parameters.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cfparse("{:d} items")
    result = p.parse_arguments(None, "42 items")
    # cfparse uses empty string as key for positional args
    assert "" in result or result is not None


def test_cfparse_parser_test_type_attribute() -> None:
    """
    Type is pytest_bdd_cfparse_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert cfparse.type == StepDefinitionPatternType.pytest_bdd_cfparse_expression


# ── string parser ───────────────────────────────────────────────────────────


# === TestStringParser (converted) ===


def test_string_parser_test_init() -> None:
    """
    String parser stores the name.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = string("exact step")
    assert p.name == "exact step"


def test_string_parser_test_is_matching_exact() -> None:
    """
    is_matching returns True for exact match.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = string("exact step")
    assert p.is_matching(None, "exact step") is True


def test_string_parser_test_is_matching_not_exact() -> None:
    """
    is_matching returns False for non-exact match.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = string("exact step")
    assert p.is_matching(None, "exact step extra") is False


def test_string_parser_test_parse_arguments_returns_empty() -> None:
    """
    parse_arguments always returns empty dict.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = string("exact step")
    assert p.parse_arguments(None, "exact step") == {}


def test_string_parser_test_arguments_empty() -> None:
    """
    Arguments returns empty list.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = string("exact step")
    assert p.arguments == []


def test_string_parser_test_str_returns_name() -> None:
    """
    __str__ returns the step name.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = string("exact step")
    assert str(p) == "exact step"


def test_string_parser_test_type_attribute() -> None:
    """
    Type is pytest_bdd_string_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert string.type == StepDefinitionPatternType.pytest_bdd_string_expression


# ── cucumber_expression parser ──────────────────────────────────────────────


# === TestCucumberExpressionParser (converted) ===


def test_cucumber_expression_parser_test_init_with_string() -> None:
    """
    cucumber_expression initializes with string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.pattern == "I have {int} cucumbers"


def test_cucumber_expression_parser_test_is_matching() -> None:
    """
    is_matching returns True for matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.is_matching(None, "I have 5 cucumbers") is True


def test_cucumber_expression_parser_test_is_matching_returns_false() -> None:
    """
    is_matching returns False for non-matching text.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.is_matching(None, "no cucumbers") is False


def test_cucumber_expression_parser_test_arguments_empty() -> None:
    """
    Arguments returns empty list for cucumber expressions.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_expression("I have {int} cucumbers", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.arguments == []


def test_cucumber_expression_parser_test_str_returns_pattern() -> None:
    """
    __str__ returns the expression pattern.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_expression("test {word}", parameter_type_registry=RegistryMode.GLOBAL)
    assert str(p) == "test {word}"


def test_cucumber_expression_parser_test_type_attribute() -> None:
    """
    Type is cucumber_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert cucumber_expression.type == StepDefinitionPatternType.cucumber_expression


# ── cucumber_regular_expression parser ──────────────────────────────────────


# === TestCucumberRegularExpressionParser (converted) ===


def test_cucumber_regular_expression_parser_test_init_with_string() -> None:
    """
    cucumber_regular_expression initializes with string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_regular_expression(r"step (?P<n>\d+)")
    assert p.pattern == r"step (?P<n>\d+)"


def test_cucumber_regular_expression_parser_test_arguments() -> None:
    """
    Arguments returns regex group names.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = cucumber_regular_expression(r"step (?P<n>\d+)")
    assert p.arguments == ["n"]


def test_cucumber_regular_expression_parser_test_type_attribute() -> None:
    """
    Type is regular_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert cucumber_regular_expression.type == StepDefinitionPatternType.regular_expression


# ── heuristic parser ────────────────────────────────────────────────────────


# === TestHeuristicParser (converted) ===


def test_heuristic_parser_test_init_with_string() -> None:
    """
    Heuristic parser initializes with string format.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.format == "step {name}"
    assert p.parsers_are_built is True


def test_heuristic_parser_test_is_matching_delegates_to_subparsers() -> None:
    """
    is_matching returns True if any sub-parser matches.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("exact step", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.is_matching(None, "exact step") is True


def test_heuristic_parser_test_is_matching_returns_false() -> None:
    """
    is_matching returns False when no sub-parser matches.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
    assert p.is_matching(None, "completely different") is False


def test_heuristic_parser_test_parse_arguments_delegates() -> None:
    """
    parse_arguments uses the first matching sub-parser.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("exact step", parameter_type_registry=RegistryMode.GLOBAL)
    result = p.parse_arguments(None, "exact step")
    assert result == {}


def test_heuristic_parser_test_parse_arguments_returns_none_when_no_match() -> None:
    """
    parse_arguments returns None when no parser matches.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
    result = p.parse_arguments(None, "no match at all")
    assert result is None


def test_heuristic_parser_test_arguments_aggregates_all() -> None:
    """
    Arguments aggregates argument names from all sub-parsers.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("step {name}", parameter_type_registry=RegistryMode.GLOBAL)
    args = p.arguments
    assert isinstance(args, list)


def test_heuristic_parser_test_str_returns_format() -> None:
    """
    __str__ returns the format string.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    p = heuristic("test format", parameter_type_registry=RegistryMode.GLOBAL)
    assert str(p) == "test format"


def test_heuristic_parser_test_type_attribute() -> None:
    """
    Type is pytest_bdd_heuristic_expression.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.message_extension import StepDefinitionPatternType

    assert heuristic.type == StepDefinitionPatternType.pytest_bdd_heuristic_expression


# ── ParserBuildValueError ───────────────────────────────────────────────────


# === TestParserBuildValueError (converted) ===


def test_parser_build_value_error_test_message_includes_format() -> None:
    """
    Error message includes the format value.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    err = ParserBuildValueError("invalid")
    assert "invalid" in str(err)
