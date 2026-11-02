import json

import pytest


@pytest.mark.parametrize("producer", ["hook", "parameter", "builtin-parameter", "parse-error"])
def test_callable_provenance_reaches_messages_consumers(pytester, producer):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    if producer == "parse-error":
        feature = "Feature: Invalid\n  Scenario: Broken\n    Given text\n    | one |\n    | two | three |\n"
        conftest = ""
    elif producer in {"parameter", "builtin-parameter"}:
        feature = "Feature: Parameter source\n  Scenario: Converts\n    Given word hello\n"
        conftest = '''import pytest
from cucumber_expressions.parameter_type import ParameterType
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from pytest_cuke import given, parsers
def transform_word(value):
    return value.upper()
@pytest.fixture
def parameter_type_registry():
    registry = ParameterTypeRegistry()
    registry.define_parameter_type(ParameterType("wordcap", "[a-z]+", str, transform_word))
    return registry
@given(parsers.cucumber_expression("word {wordcap}"), anonymous_group_names=["word"])
def word(word):
    assert word == "HELLO"
'''
    else:
        feature = "@source\nFeature: Hook source\n  Scenario: Hooks\n    Given a step\n"
        conftest = '''from pathlib import Path
from pytest_cuke import given
from pytest_cuke.hook import before_tag
@before_tag("@source", name="source-hook")
def source_hook(request):
    Path("hook-executed").write_text("yes")
@given("a step")
def a_step():
    assert Path("hook-executed").read_text() == "yes"
'''
    if producer == "builtin-parameter":
        conftest = conftest.replace('str, transform_word)', 'str, str.upper)')
    pytester.makefile(".feature", provenance=feature)
    pytester.makeconftest(conftest)
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    assert result.ret == (2 if producer == "parse-error" else 0)
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    if producer == "parse-error":
        source = next(message["parseError"]["source"] for message in envelopes if "parseError" in message)
        assert source["uri"].endswith("provenance.feature")
    elif producer in {"parameter", "builtin-parameter"}:
        parameter = next(message["parameterType"] for message in envelopes if message.get("parameterType", {}).get("name") == "wordcap")
        if producer == "builtin-parameter":
            assert parameter.get("sourceReference") is None
            return
        source = parameter.get("sourceReference", {})
        assert source.get("uri", "").endswith("conftest.py")
    else:
        hook = next(message["hook"] for message in envelopes if message.get("hook", {}).get("name") == "source-hook")
        assert hook["tagExpression"] == "@source"
        source = hook["sourceReference"]
    assert source["location"]["line"] > 0
    assert source["location"]["column"] > 0
    method = source.get("javaMethod", {})
    assert method.get("className")
    assert method.get("methodName")
    assert isinstance(method.get("methodParameterTypes"), list)
    trace = source.get("javaStackTraceElement", {})
    assert trace.get("className")
    assert trace.get("methodName")
    assert trace.get("fileName")
    if producer != "hook":
        assert trace["fileName"].endswith(".py")
