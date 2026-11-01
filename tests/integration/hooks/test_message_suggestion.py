import ast
import json

import pytest


@pytest.mark.parametrize("parameter", ["unknownParameter", "int"])
def test_latest_messages_suggestion_for_unknown_parameter(pytester, parameter):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_parser = python\n")
    pytester.makefile(
        ".feature",
        missing="Feature: Suggestions\n  Scenario: value\n    Given value is 10\n",
    )
    pytester.makeconftest(
        "from pytest_cuke import given, parsers\n"
        f'@given(parsers.cucumber_expression("value is {{{parameter}}}"))\n'
        "def value_is_known():\n    pass\n"
    )
    result = pytester.runpytest("--cuke-messages-ndjson=messages.ndjson", "-q")
    unknown = parameter == "unknownParameter"
    assert result.ret == (1 if unknown else 0)
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    suggestions = [envelope["suggestion"] for envelope in envelopes if "suggestion" in envelope]
    diagnostics = [envelope["undefinedParameterType"] for envelope in envelopes if "undefinedParameterType" in envelope]
    if not unknown:
        assert not suggestions
        assert not diagnostics
        assert next(envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope)["success"]
        return
    assert diagnostics == [{"expression": "value is {unknownParameter}", "name": "unknownParameter"}]
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    step_ids = {step["id"] for envelope in envelopes if "pickle" in envelope for step in envelope["pickle"]["steps"]}
    assert suggestion["id"]
    assert suggestion["pickleStepId"] in step_ids
    assert len(suggestion["snippets"]) == 1
    snippet = suggestion["snippets"][0]
    assert snippet["language"] == "python"
    tree = ast.parse(snippet["code"])
    compile(tree, "<Messages suggestion>", "exec")
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    decorator = function.decorator_list[0]
    assert isinstance(decorator, ast.Call)
    assert isinstance(decorator.func, ast.Name)
    assert decorator.func.id == "given"
    assert isinstance(decorator.args[0], ast.Constant)
    assert decorator.args[0].value == "value is 10"
