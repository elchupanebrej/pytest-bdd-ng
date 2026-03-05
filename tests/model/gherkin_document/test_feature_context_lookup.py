from __future__ import annotations

from types import SimpleNamespace

from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Feature as FeatureMessage,
)
from cucumber_messages import (
    FeatureChild,
    GherkinDocument,
    Location,
    Scenario,
    Step,
)

from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.model.gherkin_document import core as core_module
from pytest_bdd.plugin.scenario_runner.run_store import RunStore


def _build_feature() -> Feature:
    scenario_step = Step(
        id="ast-step-1",
        keyword="Given ",
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


def test_feature_does_not_expose_registry_attribute() -> None:
    feature = _build_feature()

    assert hasattr(feature, "registry") is False


def test_resolver_uses_stash_envelope_registry_as_primary_source() -> None:
    feature = _build_feature()
    config = SimpleNamespace(stash={})
    envelope_registry = RunStore.ensure_envelope_registry_in_config(config)
    ast_node = SimpleNamespace(id="ast-id", description="from-stash-registry")
    envelope_registry.identifiable.objects_by_id["ast-id"] = ast_node

    resolved = core_module._resolve_registry_for_feature(feature, config=config)

    assert resolved["ast-id"] is ast_node
    assert resolved["ast-id"].description == "from-stash-registry"


def test_resolver_falls_back_to_gherkin_document_when_stash_registry_missing() -> None:
    feature = _build_feature()
    config = SimpleNamespace(stash={})

    resolved = core_module._resolve_registry_for_feature(feature, config=config)

    assert resolved["ast-scenario-1"].description == "Scenario description from gherkin document"
    assert resolved["ast-step-1"].text == "a step"
