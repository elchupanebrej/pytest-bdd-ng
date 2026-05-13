"""Collection helpers for code generation."""

from __future__ import annotations

from collections import defaultdict
from itertools import chain, filterfalse, zip_longest
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytest_bdd.feature_locator import FeatureLocatorArgs, ScenarioLocatorBuilder
from pytest_bdd.model.run import Run
from pytest_bdd.steps import StepDefinitionManager

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
        GherkinDocument,
        Pickle,
        PickleStep,
        PickleStepType,
        Source,
    )

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest, Item, Session
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
    from pytest_bdd.scenario_locator import ScenarioLocatorResolver


def process_session_items(
    session: Session,
) -> tuple[set[tuple[str, str]], list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]]]:
    """
    Process session items to gather matched and unmatched data.

    Returns:
        Tuple of (seen feature pickle IDs, non-matched feature pickle steps).

    """
    seen_feature_pickles_ids: set[tuple[str, str]] = set()
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]] = []

    for item in session.items:
        process_single_item(cast("Item", item), seen_feature_pickles_ids, non_matched_feature_pickle_steps)

    return seen_feature_pickles_ids, non_matched_feature_pickle_steps


def process_single_item(
    item: Item,
    seen_feature_pickles_ids: set[tuple[str, str]],
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> None:
    """Handle processing for a single test item."""
    item.session._setupstate.setup(item)  # noqa: SLF001
    item_request: FixtureRequest = item._request  # noqa: SLF001
    pickle: Pickle = item_request.getfixturevalue("pickle")
    gherkin_document: GherkinDocument = item_request.getfixturevalue("gherkin_document")
    feature_source: Source = item_request.getfixturevalue("feature_source")
    feature_binding = Run.from_stash(item_request.config.stash).ensure_feature_binding(
        gherkin_document=gherkin_document,
        source=feature_source,
        pickles=(pickle,),
    )
    seen_feature_pickles_ids.add((feature_binding.uri, pickle.name))
    process_pickle_steps(pickle, item_request, feature_binding, non_matched_feature_pickle_steps)
    item.session._setupstate.teardown_exact(None)  # type: ignore[call-arg]  # noqa: SLF001


def process_pickle_steps(
    pickle: Pickle,
    item_request: FixtureRequest,
    feature_binding: FeatureRuntimeBinding,
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> None:
    """Process pickle steps to gather unmatched steps."""
    run = Run.from_stash(item_request.config.stash)
    scenario_run = run.create_scenario_run(
        item_request,
        gherkin_document=feature_binding.gherkin_document,
        feature_source=feature_binding.source,
        pickle=pickle,
    )
    previous_step: PickleStep | None = None
    for step in pickle.steps:
        try:
            scenario_run.step_object = step
            scenario_run.previous_step_object = previous_step
            scenario_root = scenario_run.run
            if scenario_root is None:
                continue
            item_request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=item_request,
                run=scenario_root,
            )
        except StepDefinitionManager.Matcher.MatchNotFoundError:
            non_matched_feature_pickle_steps.append(((feature_binding, pickle), step))
        finally:
            previous_step = step


def collect_features_and_seen_uris(
    config: Config,
    seen_feature_pickles_ids: set[tuple[str, str]],
) -> tuple[Sequence[FeatureRuntimeBinding], set[str]]:
    """
    Collect all features and the set of seen feature URIs.

    Returns:
        Tuple of (features, seen feature URIs).

    """
    feature_pickles_feature_source = locate_feature_pickles(config)
    run = Run.from_stash(config.stash)
    features_by_uri = {
        str(gherkin_document.uri): run.ensure_feature_binding(gherkin_document=gherkin_document, source=source)
        for gherkin_document, _pickle, source in feature_pickles_feature_source
    }
    features: Sequence[FeatureRuntimeBinding] = list(features_by_uri.values())

    seen_features_uris: set[str] = {feature_uri for feature_uri, _ in seen_feature_pickles_ids}

    return features, seen_features_uris


def locate_feature_pickles(config: Config) -> list[tuple[GherkinDocument, Pickle, Source]]:
    """
    Resolve feature pickles for configured --feature paths.

    Returns:
        Feature document, pickle, and source tuples.

    """
    locator_builder = ScenarioLocatorBuilder(config=config)
    locators = cast(
        "Sequence[ScenarioLocatorResolver]",
        locator_builder.build_for_feature_locator_args(
            cast("FeatureLocatorArgs", defaultdict(feature_paths=list(map(Path, config.option.features)))),
        ),
    )
    return [feature_pickles_source for locator in locators for feature_pickles_source in locator.resolve(config)]


def find_non_seen_features_and_pickles(
    features: Sequence[FeatureRuntimeBinding],
    seen_feature_pickles_ids: set[tuple[str, str]],
    seen_features_uris: set[str],
) -> tuple[list[FeatureRuntimeBinding], list[tuple[FeatureRuntimeBinding, Pickle]]]:
    """
    Identify features and pickles that were not seen.

    Returns:
        Tuple of (non-seen features, non-seen feature pickles).

    """
    non_seen_features: list[FeatureRuntimeBinding] = list(
        filterfalse(lambda feature: feature.uri in seen_features_uris, features),
    )

    non_seen_feature_pickles: list[tuple[FeatureRuntimeBinding, Pickle]] = list(
        filter(
            lambda feature_pickle: (feature_pickle[0].uri, feature_pickle[1].name) not in seen_feature_pickles_ids,
            chain.from_iterable(zip_longest((), feature.pickles, fillvalue=feature) for feature in features),
        ),
    )

    return non_seen_features, non_seen_feature_pickles


def find_unique_non_matched_steps(
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]]:
    """
    Find unique non-matched feature pickle steps.

    Returns:
        List of unique non-matched feature pickle steps.

    """
    unique_step_defs_ids: set[tuple[PickleStepType | None, str]] = {
        (step.type, step.text) for _, step in non_matched_feature_pickle_steps
    }
    unique_non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]] = list(
        map(
            lambda step_def_id: next(
                filter(
                    lambda feature_pickle_step: (
                        feature_pickle_step[1].type == step_def_id[0] and feature_pickle_step[1].text == step_def_id[1]
                    ),
                    non_matched_feature_pickle_steps,
                ),
            ),
            unique_step_defs_ids,
        ),
    )
    return unique_non_matched_feature_pickle_steps


def collect_generation_inputs(
    config: Config,
) -> tuple[
    Sequence[FeatureRuntimeBinding],
    Sequence[tuple[FeatureRuntimeBinding, Pickle]],
    Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
]:
    """
    Collect features, pickles, and unique steps for full code generation.

    Returns:
        Features, feature pickles, and unique pickle steps.

    """
    feature_pickles_feature_source = locate_feature_pickles(config)
    run = Run.from_stash(config.stash)
    features_by_uri: dict[str, FeatureRuntimeBinding] = {}
    for gherkin_document, _pickle, source in feature_pickles_feature_source:
        features_by_uri.setdefault(
            str(gherkin_document.uri),
            run.ensure_feature_binding(gherkin_document=gherkin_document, source=source),
        )
    features: Sequence[FeatureRuntimeBinding] = list(features_by_uri.values())

    feature_pickles: Sequence[tuple[FeatureRuntimeBinding, Pickle]] = [
        (run.ensure_feature_binding(gherkin_document=gherkin_document, source=source), pickle)
        for gherkin_document, pickle, source in feature_pickles_feature_source
    ]

    feature_pickles_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]] = list(
        chain.from_iterable(
            (
                cast(
                    "Iterable[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]]",
                    zip_longest((), feature_pickle[1].steps, fillvalue=feature_pickle),
                )
                for feature_pickle in feature_pickles
            ),
        ),
    )

    unique_step_defs_ids = {(step.type, step.text) for (_feature, _pickle), step in feature_pickles_steps}
    unique_feature_pickle_steps = sorted(
        map(
            lambda step_def_id: next(  # type: ignore[no-any-return]
                filter(
                    lambda step: step[1].type == step_def_id[0] and step[1].text == step_def_id[1],
                    feature_pickles_steps,
                ),
            ),
            unique_step_defs_ids,
        ),
        key=lambda feature_pickle_step: cast("str", feature_pickle_step[1].text),
    )

    return features, feature_pickles, unique_feature_pickle_steps
