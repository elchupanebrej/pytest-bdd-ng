import json
import re

from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry


def test_builtin_parser_patterns_are_executable_in_their_declared_family(pytester):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_parser = python\n")
    pytester.makefile(
        ".feature",
        patterns="Feature: Patterns\n  Scenario: parser families\n    Given literal [x] {raw}.\n    And count 7\n    And many 1, 2\n    And CASE LOWER\n    And cuke 11\n",
    )
    pytester.makeconftest(
        r"""import re
from pytest_cuke import given, parsers
def number(value):
    return int(value)
number.pattern = r"\d+"
@given(parsers.string("literal [x] {raw}."))
def literal():
    pass
@given(parsers.parse("count {value:d}"))
def count(value):
    assert value == 7
@given(parsers.cfparse("many {values:Number+}", extra_types={"Number": number}))
def many(values):
    assert values == [1, 2]
@given(parsers.re(r"case (?P<value>[a-z]+)", flags=re.IGNORECASE))
def uppercase(value):
    assert value == "LOWER"
@given(parsers.cucumber_expression("cuke {int}"))
def cuke():
    pass
"""
    )
    result = pytester.runpytest("--cuke-messages-ndjson=messages.ndjson", "-q")
    assert result.ret == 0
    rows = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    definitions = {
        row["stepDefinition"]["sourceReference"]["javaMethod"]["methodName"]: row["stepDefinition"]["pattern"]
        for row in rows
        if "stepDefinition" in row and row["stepDefinition"]["sourceReference"].get("uri", "").endswith("/conftest.py")
    }
    assert set(definitions) == {"literal", "count", "many", "uppercase", "cuke"}
    for name, accepted, rejected in [
        ("literal", "literal [x] {raw}.", "literal x {raw}."),
        ("count", "count 7", "count seven"),
        ("many", "many 1, 2", "many nope"),
        ("uppercase", "CASE LOWER", "case 123"),
    ]:
        pattern = definitions[name]
        assert pattern["type"] == "REGULAR_EXPRESSION"
        compiled = re.compile(pattern["source"])
        assert compiled.fullmatch(accepted)
        assert not compiled.fullmatch(rejected)
    pattern = definitions["cuke"]
    assert pattern == {"source": "cuke {int}", "type": "CUCUMBER_EXPRESSION"}
    expression = CucumberExpression(pattern["source"], ParameterTypeRegistry())
    assert expression.match("cuke 11") is not None
    assert expression.match("cuke eleven") is None
