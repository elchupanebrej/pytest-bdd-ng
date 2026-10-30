import json

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("messages", [False, True])
def test_read_hooks_observe_sources_and_expanded_pickles_without_reporter_dependency(pytester, messages):
    pytester.makeini("[pytest]\ncuke_features_dir = features\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "read.feature").write_text(
        "Feature: Read events\n"
        "  Scenario: Plain\n    Given value plain\n"
        "  Scenario Outline: Expanded <value>\n    Given value <value>\n"
        "    Examples:\n      | value |\n      | one |\n      | two |\n",
        encoding="utf-8",
    )
    pytester.makeconftest(
        r"""
import json
from pathlib import Path
from cucumber_messages import GherkinDocument, Pickle, Source
from pytest_cuke import given, parsers

events = []

@given(parsers.parse("value {value}"))
def value(value):
    assert value in {"plain", "one", "two"}

def pytest_cuke_source_read(config, gherkin_document, source):
    assert isinstance(source, Source)
    assert isinstance(gherkin_document, GherkinDocument)
    assert source.uri == gherkin_document.uri
    assert "Scenario Outline: Expanded <value>" in source.data
    events.append(["source", source.media_type])

def pytest_cuke_feature_read(config, gherkin_document):
    assert isinstance(gherkin_document, GherkinDocument)
    events.append(["feature", gherkin_document.feature.name])

def pytest_cuke_pickle_read(config, gherkin_document, pickle):
    assert isinstance(pickle, Pickle)
    assert pickle.uri == gherkin_document.uri
    events.append(["pickle", pickle.name, [step.text for step in pickle.steps]])

def pytest_collection_finish(session):
    Path("read-events.json").write_text(json.dumps(events), encoding="utf-8")
"""
    )
    arguments = ["features/read.feature", "-q"]
    if messages:
        arguments.append("--cuke-messages-ndjson=messages.ndjson")
    result = pytester.runpytest_subprocess(*arguments)
    result.assert_outcomes(passed=3)
    assert json.loads((pytester.path / "read-events.json").read_text(encoding="utf-8")) == [
        ["source", "text/x.cucumber.gherkin+plain"],
        ["feature", "Read events"],
        ["pickle", "Plain", ["value plain"]],
        ["pickle", "Expanded <value>[table_rows:[line: 8]]", ["value one"]],
        ["pickle", "Expanded <value>[table_rows:[line: 9]]", ["value two"]],
    ]


@pytest.mark.parametrize("observe", [False, True])
def test_read_hook_document_projection_is_bounded(pytester, observe):
    pytester.makeini("[pytest]\ncuke_features_dir = features\ncuke_parser = python\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "projections.feature").write_text(
        "Feature: Projection work\n" + "".join(f"  Scenario: item {index}\n    Given a value\n" for index in range(20)),
        encoding="utf-8",
    )
    observer = (
        r"""
document = None
pickle_calls = 0

def pytest_cuke_source_read(gherkin_document):
    global document
    document = gherkin_document

def pytest_cuke_feature_read(gherkin_document):
    assert gherkin_document is document

def pytest_cuke_pickle_read(gherkin_document, pickle):
    global pickle_calls
    assert gherkin_document is document
    pickle_calls += 1
"""
        if observe
        else ""
    )
    pytester.makeconftest(
        r"""
import json
from pathlib import Path
import pytest
from pytest_cuke import given
from pytest_cuke import scenario_locator

stats = {"document_projections": 0}
original = scenario_locator.feature_to_gherkin_document

def counted(feature, *args, **kwargs):
    stats["document_projections"] += 1
    return original(feature, *args, **kwargs)

@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    scenario_locator.feature_to_gherkin_document = counted

@given("a value")
def value():
    pass

def pytest_sessionfinish(session):
    stats["pickle_calls"] = globals().get("pickle_calls", 0)
    Path("observed.json").write_text(json.dumps(stats))
"""
        + observer
    )
    result = pytester.runpytest_subprocess("features/projections.feature", "--collect-only", "-q")
    assert result.ret == 0
    assert "20 tests collected" in result.stdout.str()
    assert json.loads((pytester.path / "observed.json").read_text()) == {
        "document_projections": 1 if observe else 0,
        "pickle_calls": 20 if observe else 0,
    }
