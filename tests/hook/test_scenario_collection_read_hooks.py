from __future__ import annotations

from types import SimpleNamespace

from attr import attrib, attrs
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
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

from pytest_bdd.model.gherkin_document import Feature
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


def _build_feature() -> Feature:
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

    return Feature(
        gherkin_document=GherkinDocument(comments=[], feature=feature_message, uri="file:features/example.feature"),
        uri="file:features/example.feature",
        filename="features/example.feature",
    )


def test_collection_iter_calls_read_hooks_in_expected_order() -> None:
    feature = _build_feature()
    source = Source(uri=feature.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(feature, source)])
    hook = _HookSpy()
    config = SimpleNamespace(stash={}, pytest_bdd_id_generator=IdGenerator(), hook=hook)

    resolved = list(_iter_resolved_feature_scenarios(config, [locator]))

    assert len(resolved) == 1
    assert len(feature.pickles) == 1
    assert hook.events[:3] == [("source", feature.uri), ("feature", feature.uri), ("pickle", feature.pickles[0].id)]
