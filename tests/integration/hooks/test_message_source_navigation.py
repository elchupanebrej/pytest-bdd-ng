import json
from pathlib import Path

from gherkin.parser import Parser

from pytest_cuke.model.message_types import Envelope, GherkinDocument, message_from_dict, message_to_dict
from pytest_cuke.model.message_validation import validate_envelope_data


def _without_ids(value):
    if isinstance(value, dict):
        return {key: _without_ids(child) for key, child in value.items() if key != "id"}
    if isinstance(value, list):
        return [_without_ids(child) for child in value]
    return value


def test_live_messages_preserve_source_navigation_and_outline_locations(pytester):
    source = Path(__file__).parents[2].joinpath("data", "source-navigation.feature").read_text()
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_parser = python\n")
    pytester.makefile(".feature", navigation=source)
    pytester.makeconftest('from pytest_cuke import step, parsers\n@step(parsers.re(".*"))\ndef any_step():\n    pass\n')
    result = pytester.runpytest("--cuke-messages-ndjson=messages.ndjson", "-q")
    assert result.ret == 0
    result.assert_outcomes(passed=2)
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    documents = [item["gherkinDocument"] for item in envelopes if "gherkinDocument" in item]
    assert len(documents) == 1
    observed = documents[0]
    raw = Parser().parse(source)
    expected = message_from_dict(raw, GherkinDocument)
    expected.uri = observed["uri"]
    canonical = message_to_dict(Envelope(gherkin_document=expected))["gherkinDocument"]
    assert _without_ids(observed) == _without_ids(canonical)
    assert validate_envelope_data({"gherkinDocument": observed}) == ()
    pickles = [item["pickle"] for item in envelopes if "pickle" in item]
    rows = raw["feature"]["children"][1]["rule"]["children"][1]["scenario"]["examples"][0]["tableBody"]
    assert [item["location"] for item in pickles] == [row["location"] for row in rows]
    for item in pickles:
        assert {tag["name"] for tag in item["tags"]} == {"@feature-tag", "@rule-tag", "@scenario-tag", "@examples-tag"}
