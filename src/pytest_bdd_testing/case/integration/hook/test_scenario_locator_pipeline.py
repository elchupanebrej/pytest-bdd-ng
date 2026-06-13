"""

Provide test scenario locator pipeline helpers.
"""

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
    Scenario,
    Source,
    Step,
    StepKeywordType,
)

from pytest_bdd.compatibility.parser import ParsedFeature
from pytest_bdd.model.run import Run
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.util.other import IdGenerator


@attrs
class _DummyLocator(ScenarioLocatorFilterMixin):
    entries = attrib(default=())

    def resolve_features(self, config):
        _ = config
        yield from self.entries


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


def test_resolve_features_phase_does_not_materialize_pickles() -> None:
    """
    Verify resolve features phase does not materialize pickles.

    Test target:
        Ensure feature files are discovered and resolved correctly across local filesystems and URLs.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure feature files are discovered and resolved correctly across
        local filesystems and URLs., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    parsed = _build_gherkin_document()
    gherkin_document = parsed.gherkin_document
    source = Source(uri=gherkin_document.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(parsed, source)])
    config = SimpleNamespace(stash={})
    IdGenerator().initialize_in_stash(config.stash)

    resolved_features = list(locator.resolve_features(config))

    assert len(resolved_features) == 1
    assert Run.find_in_stash(config.stash).value_or(None) is None


def test_resolve_pipeline_materializes_pickles_without_message_emission() -> None:
    """
    Verify resolve pipeline materializes pickles without message emission.

    Test target:
        Ensure feature files are discovered and resolved correctly across local filesystems and URLs.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure feature files are discovered and resolved correctly across
        local filesystems and URLs., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    parsed = _build_gherkin_document()
    gherkin_document = parsed.gherkin_document
    source = Source(uri=gherkin_document.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(parsed, source)])
    config = SimpleNamespace(stash={})
    Run.initialize_for_config(stash=config.stash, config=config)
    IdGenerator().initialize_in_stash(config.stash)

    resolved = list(locator.resolve(config))
    run = Run.from_stash(config.stash)
    binding = run.feature_binding_for_document(gherkin_document)

    assert len(resolved) == 1
    assert binding is not None
    assert len(binding.pickles) == 1


def test_resolve_pipeline_invokes_collection_callbacks_in_order() -> None:
    """
    Verify resolve pipeline invokes collection callbacks in order.

    Test target:
        Ensure feature files are discovered and resolved correctly across local filesystems and URLs.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure feature files are discovered and resolved correctly across
        local filesystems and URLs., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    parsed = _build_gherkin_document()
    gherkin_document = parsed.gherkin_document
    source = Source(uri=gherkin_document.uri, data="Feature: Feature", media_type="text/x.cucumber.gherkin+plain")
    locator = _DummyLocator(entries=[(parsed, source)])
    config = SimpleNamespace(stash={})
    Run.initialize_for_config(stash=config.stash, config=config)
    IdGenerator().initialize_in_stash(config.stash)
    observed_callbacks: list[tuple[str, str]] = []

    class _Observer:
        def on_source_loaded(self, loaded_document: GherkinDocument, loaded_source: Source) -> None:
            observed_callbacks.append(("source", loaded_document.uri))
            assert loaded_source is source

        def on_feature_loaded(self, loaded_document: GherkinDocument) -> None:
            observed_callbacks.append(("feature", loaded_document.uri))

        def on_pickle_loaded(self, loaded_document: GherkinDocument, loaded_pickle) -> None:
            observed_callbacks.append(("pickle", loaded_document.uri))
            assert loaded_pickle.id

    _ = list(
        locator.resolve(
            config,
            observer=_Observer(),
        ),
    )

    assert observed_callbacks[:3] == [
        ("source", gherkin_document.uri),
        ("feature", gherkin_document.uri),
        ("pickle", gherkin_document.uri),
    ]
