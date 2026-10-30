"""Tag conversion supports model and protocol consumers together."""
import json

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("reporter", [False, True])
def test_protocol_tag_conversion_preserves_model_consumers(pytester, reporter):
    pytester.makeini("[pytest]\ncuke_features_dir = features\ncuke_parser = python\nmarkers =\n feature_tag\n rule_tag\n scenario_tag\n example_tag\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "tag-contract.feature").write_text(
        "@feature_tag\nFeature: Tags\n @rule_tag\n Rule: Group\n"
        "  @scenario_tag\n  Scenario Outline: Row\n   When action <value>\n"
        "   @example_tag\n   Examples:\n    | value |\n    | one |\n    | two |\n",
        encoding="utf-8",
    )
    pytester.makeconftest('''
import json
from pathlib import Path
import pytest
from cucumber_messages import GherkinDocument, Pickle
from pytest_cuke import when, parsers
from pytest_cuke.model import Feature, Scenario
import pytest_cuke.plugin as plugin

records = []
document_calls = []
original = plugin.feature_to_gherkin_document

def project(*args, **kwargs):
    document_calls.append(1)
    return original(*args, **kwargs)

class ModelConsumer:
    @pytest.hookimpl(tryfirst=True)
    def pytest_cuke_convert_tag_to_marks(self, feature, scenario, tag):
        assert isinstance(feature, Feature)
        assert isinstance(scenario, Scenario)
        records.append({"kind": "model", "name": scenario.name, "tag": tag,
                        "feature": id(feature), "scenario": id(scenario)})

class ProtocolConsumer:
    @pytest.hookimpl(tryfirst=True)
    def pytest_cuke_convert_tag_to_marks(self, gherkin_document, pickle, tag):
        assert isinstance(gherkin_document, GherkinDocument)
        assert isinstance(pickle, Pickle)
        assert gherkin_document.feature.name == "Tags"
        assert {t.name for t in pickle.tags} == {
            "@feature_tag", "@rule_tag", "@scenario_tag", "@example_tag"
        }
        assert pickle.name.startswith("Row[table_rows:")
        assert pickle.uri == gherkin_document.uri
        assert len(pickle.steps) == 1
        assert pickle.steps[0].text in {"action one", "action two"}
        records.append({"kind": "protocol", "id": pickle.id,
                        "document": id(gherkin_document), "tag": tag})

def pytest_configure(config):
    plugin.feature_to_gherkin_document = project
    config.pluginmanager.register(ModelConsumer())
    config.pluginmanager.register(ProtocolConsumer())

def pytest_sessionfinish():
    Path("observed.json").write_text(json.dumps({"records": records, "documents": len(document_calls)}))

@when(parsers.parse("action {value}"))
def action(value, feature, scenario):
    assert value in {"one", "two"}
    assert any(record["kind"] == "model" and record["feature"] == id(feature)
               and record["scenario"] == id(scenario) for record in records)
''')
    args = ["-m", "scenario_tag", "-q"]
    if reporter:
        args += ["--cuke-messages-ndjson", str(pytester.path / "messages.ndjson")]
    result = pytester.runpytest(*args)
    result.assert_outcomes(passed=2)
    observed = json.loads((pytester.path / "observed.json").read_text())
    protocol = [record for record in observed["records"] if record["kind"] == "protocol"]
    model = [record for record in observed["records"] if record["kind"] == "model"]
    assert len(protocol) == len(model) == 8
    assert len({record["id"] for record in protocol}) == 2
    assert len({record["document"] for record in protocol}) == 1
    assert observed["documents"] == 1


def test_model_tag_consumer_does_not_project_protocol(pytester):
    pytester.makeini("[pytest]\ncuke_features_dir = features\ncuke_parser = python\nmarkers = selected\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "selected.feature").write_text(
        "@selected\nFeature: Model\n Scenario: One\n  When action\n", encoding="utf-8"
    )
    pytester.makeconftest('''
from pytest_cuke import when
import pytest_cuke.plugin as plugin

def fail_projection(*args, **kwargs):
    raise AssertionError("model consumer must not trigger protocol projection")

def pytest_configure():
    plugin.feature_to_gherkin_document = fail_projection
    plugin.scenario_to_pickle = fail_projection

def pytest_cuke_convert_tag_to_marks(feature, scenario, tag):
    assert feature.name == "Model"
    assert scenario.name == "One"
    assert tag == "selected"

@when("action")
def action():
    pass
''')
    result = pytester.runpytest("-m", "selected", "-q")
    result.assert_outcomes(passed=1)
