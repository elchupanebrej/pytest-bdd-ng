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
    Scenario,
    Source,
    Step,
    StepKeywordType,
)

from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.model.message_extension import get_payload_kind
from pytest_bdd.plugin.scenario_runner.context_store import ExecutionContextStore
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.util.other import IdGenerator


@attrs
class _DummyLocator(ScenarioLocatorFilterMixin):
    entries = attrib(default=())

    def resolve_features(self, config):
        _ = config
        yield from self.entries


class _HookSpy:
    def __init__(self, *, register_in_stash: bool = False) -> None:
        self.messages = []
        self.register_in_stash = register_in_stash

    def pytest_bdd_message(self, *, config, message) -> None:
        self.messages.append(message)
        if self.register_in_stash:
            ExecutionContextStore.register_envelope_in_config(config, message)


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


def test_resolve_features_phase_does_not_materialize_pickles() -> None:
    feature = _build_feature()
    source = Source(uri=feature.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(feature, source)])
    config = SimpleNamespace(stash={}, pytest_bdd_id_generator=IdGenerator())

    resolved_features = list(locator.resolve_features(config))

    assert len(resolved_features) == 1
    assert feature.pickles == []


def test_resolve_pipeline_materializes_pickles_and_registers_envelopes_in_order() -> None:
    feature = _build_feature()
    source = Source(uri=feature.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(feature, source)])
    config = SimpleNamespace(stash={}, pytest_bdd_id_generator=IdGenerator(), hook=_HookSpy(register_in_stash=True))

    resolved = list(locator.resolve(config))

    assert len(resolved) == 1
    assert len(feature.pickles) == 1

    envelope_registry = ExecutionContextStore.get_envelope_registry_from_config(config)
    assert envelope_registry is not None
    observed_payload_order = [get_payload_kind(envelope) for envelope in envelope_registry.envelopes]

    assert observed_payload_order[:3] == ["source", "gherkin_document", "pickle"]


def test_resolve_pipeline_emits_messages_via_pytest_bdd_message_hook() -> None:
    feature = _build_feature()
    source = Source(uri=feature.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(feature, source)])
    hook_spy = _HookSpy()
    config = SimpleNamespace(stash={}, pytest_bdd_id_generator=IdGenerator(), hook=hook_spy)

    _ = list(locator.resolve(config))

    emitted_payload_order = [get_payload_kind(message) for message in hook_spy.messages]
    assert emitted_payload_order[:3] == ["source", "gherkin_document", "pickle"]
