"""Provide test feature context lookup helpers."""

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
    Source,
    Step,
)

from pytest_bdd.model.run import Run


def _build_gherkin_document() -> GherkinDocument:
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
    return GherkinDocument(
        comments=[],
        feature=feature_message,
        uri="file:features/example.feature",
    )


def test_gherkin_document_does_not_expose_registry_attribute() -> None:
    """Verify gherkin document does not expose registry attribute."""
    gherkin_document = _build_gherkin_document()

    assert hasattr(gherkin_document, "registry") is False


def test_run_feature_binding_indexes_gherkin_document_objects_in_run_registry() -> None:
    """Verify run feature binding indexes gherkin document objects in run registry."""
    gherkin_document = _build_gherkin_document()
    config = SimpleNamespace(stash={})
    run = Run.initialize_for_config(stash=config.stash, config=config)

    binding = run.ensure_feature_binding(
        gherkin_document=gherkin_document,
        filename="features/example.feature",
        source=Source(
            uri=gherkin_document.uri,
            data="Feature: Feature",
            media_type="text/x.cucumber.gherkin+plain",
        ),
    )

    assert binding.resolve_node("ast-scenario-1").description == "Scenario description from gherkin document"
    assert binding.resolve_node("ast-step-1").text == "a step"
    assert run.identifiable_registry.resolve("ast-scenario-1") is binding.resolve_node("ast-scenario-1")


def test_run_feature_binding_is_reused_for_same_gherkin_document() -> None:
    """Verify run feature binding is reused for same gherkin document."""
    gherkin_document = _build_gherkin_document()
    config = SimpleNamespace(stash={})
    run = Run.initialize_for_config(stash=config.stash, config=config)

    first = run.ensure_feature_binding(
        gherkin_document=gherkin_document,
        filename="features/example.feature",
        source=Source(
            uri=gherkin_document.uri,
            data="Feature: Feature",
            media_type="text/x.cucumber.gherkin+plain",
        ),
    )
    second = run.ensure_feature_binding(
        gherkin_document=gherkin_document,
        filename="features/example.feature",
        source=Source(
            uri=gherkin_document.uri,
            data="Feature: Feature updated",
            media_type="text/x.cucumber.gherkin+plain",
        ),
    )

    assert first is second
    assert second.source is not None
    assert second.source.data == "Feature: Feature updated"
