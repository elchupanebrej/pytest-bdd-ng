"""Provide test scenario collection read hooks helpers."""

from __future__ import annotations

from types import SimpleNamespace

from attr import attrib, attrs
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped] — upstream library missing type stubs
    Feature as FeatureMessage,
)
from cucumber_messages import (
    FeatureChild,
    GherkinDocument,
    Location,
    Pickle,
    Scenario,
    Source,
    Step,
    StepKeywordType,
)

from pytest_bdd.compatibility.parser import ParsedFeature
from pytest_bdd.model.run import Run
from pytest_bdd.plugin.scenario_test_collector.plugin import _iter_resolved_feature_scenarios
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.util.other import IdGenerator


@attrs
class _DummyLocator(ScenarioLocatorFilterMixin):
    entries = attrib(default=())

    def resolve_features(self, config):
        _ = config
        yield from self.entries


class _HookSpy:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def pytest_bdd_source_read(self, *, config, gherkin_document: GherkinDocument, source: Source) -> None:
        _ = config
        self.events.append(("source", source.uri))
        assert gherkin_document.uri == source.uri

    def pytest_bdd_feature_read(self, *, config, gherkin_document: GherkinDocument) -> None:
        _ = config
        self.events.append(("feature", gherkin_document.uri))

    def pytest_bdd_pickle_read(self, *, config, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        _ = config
        self.events.append(("pickle", pickle.id))
        assert gherkin_document.uri


def _build_gherkin_document() -> ParsedFeature:
    scenario_step = Step(
        id="ast-step-1",
        keyword="Given ",
        keyword_type=StepKeywordType.context,
        location=Location(line=3, column=1),
        text="a step",
    )
    scenario_node = Scenario(
        description="Scenario description from gherkin document",
        examples=[],
        id="ast-scenario-1",
        keyword="Scenario",
        location=Location(line=2, column=1),
        name="Scenario",
        steps=[scenario_step],
        tags=[],
    )
    feature_message = FeatureMessage(
        children=[FeatureChild(scenario=scenario_node)],
        description="Feature description",
        keyword="Feature",
        language="en",
        location=Location(line=1, column=1),
        name="Feature",
        tags=[],
    )

    gherkin_document = GherkinDocument(
        comments=[],
        feature=feature_message,
        uri="file:features/example.feature",
    )
    return ParsedFeature(
        gherkin_document=gherkin_document,
        filename="features/example.feature",
        raw_data="Feature: Feature",
    )


def test_collection_iter_calls_read_hooks_in_expected_order() -> None:
    """Verify collection iter calls read hooks in expected order."""
    parsed = _build_gherkin_document()
    gherkin_document = parsed.gherkin_document
    source = Source(uri=gherkin_document.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(parsed, source)])
    hook = _HookSpy()
    config = SimpleNamespace(stash={}, hook=hook)
    Run.initialize_for_config(stash=config.stash, config=config)
    IdGenerator().initialize_in_stash(config.stash)

    resolved = list(_iter_resolved_feature_scenarios(config, [locator]))
    run = Run.from_stash(config.stash)
    binding = run.feature_binding_for_document(gherkin_document)

    assert len(resolved) == 1
    assert binding is not None
    assert len(binding.pickles) == 1
    assert hook.events[:3] == [
        ("source", gherkin_document.uri),
        ("feature", gherkin_document.uri),
        ("pickle", binding.pickles[0].id),
    ]
