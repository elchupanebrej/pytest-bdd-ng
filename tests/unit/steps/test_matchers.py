from __future__ import annotations

from pytest_bdd.parsers.base import ParserBuildValueError, RegistryMode, StepMatch, StepParser, StepParserProtocol
from pytest_bdd.parsers.string_parser import string


def test_step_match_and_enums() -> None:
    match = StepMatch(parameters={"x": "1"}, span=(0, 5))
    assert match.parameters == {"x": "1"} and match.span == (0, 5) and match.parser is None
    assert RegistryMode.NEW.value == "NEW" and RegistryMode.NOT_DEFINED.value is None
    assert "bad" in str(ParserBuildValueError("bad"))


def test_step_parser_protocol() -> None:
    class Dummy(StepParser):
        def parse_arguments(self, request, name, anonymous_group_names=None):
            return {}

        @property
        def arguments(self):
            return []

        def is_matching(self, request, name):
            return True

        def __str__(self):
            return "dummy"

    d = Dummy()
    assert isinstance(d, StepParserProtocol) and StepParser.build(d) is d


def test_string_parser() -> None:
    parser = string("I have 5 apples")
    assert parser.is_matching(None, "I have 5 apples")
    assert not parser.is_matching(None, "I have 6 apples")
    assert parser.parse_arguments(None, "I have 5 apples") == {}
    assert parser.arguments == []
    assert str(parser) == "I have 5 apples"
