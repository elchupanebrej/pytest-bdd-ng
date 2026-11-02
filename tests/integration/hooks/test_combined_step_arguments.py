import json
from importlib.metadata import version

import pytest


@pytest.mark.parametrize("parser_mode", ["python", pytest.param("go", marks=pytest.mark.external)])
@pytest.mark.parametrize("report_messages", [False, True])
def test_combined_arguments_keep_both_bodies_and_their_order(pytester, parser_mode, report_messages):
    if parser_mode == "python" and int(version("gherkin-official").split(".")[0]) < 42:
        pytest.skip("Combined arguments require Gherkin 42; older comparison profiles retain the common grammar.")
    pytester.makeini(f"[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = {parser_mode}\n")
    pytester.makefile(
        ".feature",
        combined='''Feature: Combined arguments
  Scenario: Doc first
    Given combined
      """text/plain
      body
      """
      | key |
      | row |
  Scenario: Table first
    Given combined
      | key |
      | row |
      """text/plain
      body
      """
''',
    )
    pytester.makeconftest("""from pytest_cuke import given
@given("combined")
def combined(step, request):
    argument = step.argument
    assert argument.doc_string.content == "body"
    assert argument.doc_string.media_type == "text/plain"
    assert [[cell.value for cell in row.cells] for row in argument.data_table.rows] == [["key"], ["row"]]
    expected = (1, 2) if "Doc first" in request.node.name else (2, 1)
    assert (argument.doc_string.argument_index, argument.data_table.argument_index) == expected
""")
    arguments = ["-q"]
    if report_messages:
        arguments.append("--cuke-messages-ndjson=messages.ndjson")
    result = pytester.runpytest_subprocess(*arguments)
    result.assert_outcomes(passed=2)
    if report_messages:
        messages = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
        pickles = [message["pickle"] for message in messages if "pickle" in message]
        assert len(pickles) == 2
        for pickle in pickles:
            argument = pickle["steps"][0]["argument"]
            assert argument["docString"]["content"] == "body"
            assert argument["dataTable"]["rows"][1]["cells"][0]["value"] == "row"
            expected = (1, 2) if pickle["name"] == "Doc first" else (2, 1)
            assert (argument["docString"]["argumentIndex"], argument["dataTable"]["argumentIndex"]) == expected
