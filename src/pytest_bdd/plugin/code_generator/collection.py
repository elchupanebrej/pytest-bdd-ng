"""
Collection helpers for code generation.

Responsibility:
    Collection helpers for code generation. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.collection` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - process_session_items: owns nested behavior below this boundary
    - _bind_and_track_pickle: owns nested behavior below this boundary
    - process_single_item: owns nested behavior below this boundary
    - process_pickle_steps: owns nested behavior below this boundary
    - _match_step_to_definition: owns nested behavior below this boundary
    - collect_features_and_seen_uris: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates run, previous_step, feature_pickles_feature_source, features_by_uri, features; depends on
    __future__.annotations, collections.defaultdict, itertools.chain, itertools.filterfalse, itertools.zip_longest.

Invariants:
    - `pytest_bdd.plugin.code_generator.collection` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from collections import defaultdict
from itertools import chain, filterfalse, zip_longest
from typing import TYPE_CHECKING, cast

from pytest_bdd.feature_locator import FeatureLocatorArgs, ScenarioLocatorBuilder
from pytest_bdd.model.run import Run
from pytest_bdd.steps import StepDefinitionManager

from .request import get_feature_paths

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from cucumber_messages import (  # upstream library missing type stubs
        GherkinDocument,
        Pickle,
        PickleStep,
        PickleStepType,
        Source,
    )

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest, Item, Session
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
    from pytest_bdd.model.scenario_run import ScenarioRun
    from pytest_bdd.scenario_locator import ScenarioLocatorResolver


def process_session_items(
    session: Session,
) -> tuple[set[tuple[str, str]], list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]]]:
    """
    Process session items to gather matched and unmatched data.

    Returns:
        Tuple of (seen feature pickle IDs, non-matched feature pickle steps).

    Responsibility:
        Process session items to gather matched and unmatched data. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.collection.process_session_items`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - process_single_item: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `process_session_items`

    State and side effects:
        mutates seen_feature_pickles_ids, non_matched_feature_pickle_steps.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.process_session_items` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    seen_feature_pickles_ids: set[tuple[str, str]] = set()
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]] = []

    for item in session.items:
        process_single_item(cast("Item", item), seen_feature_pickles_ids, non_matched_feature_pickle_steps)

    return seen_feature_pickles_ids, non_matched_feature_pickle_steps


def _bind_and_track_pickle(
    item: Item,
    seen_feature_pickles_ids: set[tuple[str, str]],
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.collection._bind_and_track_pickle` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.collection._bind_and_track_pickle`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - item_request.getfixturevalue: collaborator call used by this boundary
        - Run.from_stash.ensure_feature_binding: collaborator call used by this boundary
        - Run.from_stash: collaborator call used by this boundary
        - seen_feature_pickles_ids.add: collaborator call used by this boundary
        - process_pickle_steps: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates item_request, pickle, gherkin_document, feature_source, feature_binding.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection._bind_and_track_pickle` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
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


def process_single_item(
    item: Item,
    seen_feature_pickles_ids: set[tuple[str, str]],
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> None:
    """
    Handle processing for a single test item.

    Responsibility:
        Handle processing for a single test item. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.collection.process_single_item`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - item.session._setupstate.setup: collaborator call used by this boundary
        - _bind_and_track_pickle: collaborator call used by this boundary
        - item.session._setupstate.teardown_exact: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    item.session._setupstate.setup(item)  # noqa: SLF001
    try:
        _bind_and_track_pickle(item, seen_feature_pickles_ids, non_matched_feature_pickle_steps)
    finally:
        item.session._setupstate.teardown_exact(None)  # noqa: SLF001


def process_pickle_steps(
    pickle: Pickle,
    item_request: FixtureRequest,
    feature_binding: FeatureRuntimeBinding,
    non_matched_feature_pickle_steps: list[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> None:
    """
    Process pickle steps to gather unmatched steps.

    Responsibility:
        Process pickle steps to gather unmatched steps. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.collection.process_pickle_steps`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Run.from_stash: collaborator call used by this boundary
        - run.create_scenario_run: collaborator call used by this boundary
        - _match_step_to_definition: collaborator call used by this boundary
        - non_matched_feature_pickle_steps.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates previous_step, run, scenario_run.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.process_pickle_steps` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
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
            _match_step_to_definition(
                scenario_run=scenario_run,
                step=step,
                previous_step=previous_step,
                item_request=item_request,
            )
        except StepDefinitionManager.Matcher.MatchNotFoundError:  # noqa: PERF203
            non_matched_feature_pickle_steps.append(((feature_binding, pickle), step))
        finally:
            previous_step = step


def _match_step_to_definition(
    *,
    scenario_run: ScenarioRun,
    step: PickleStep,
    previous_step: PickleStep | None,
    item_request: FixtureRequest,
) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.collection._match_step_to_definition` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.collection._match_step_to_definition` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - item_request.config.hook.pytest_bdd_match_step_definition_to_step: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates scenario_run.step_object, scenario_run.previous_step_object, scenario_root.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection._match_step_to_definition` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    scenario_run.step_object = step
    scenario_run.previous_step_object = previous_step  # type: ignore[assignment]  # PickleStep | None vs PickleStep | NoPreviousStep
    scenario_root = scenario_run.run
    if scenario_root is None:
        return
    item_request.config.hook.pytest_bdd_match_step_definition_to_step(
        request=item_request,
        run=scenario_root,
    )


def collect_features_and_seen_uris(
    config: Config,
    seen_feature_pickles_ids: set[tuple[str, str]],
) -> tuple[Sequence[FeatureRuntimeBinding], set[str]]:
    """
    Collect all features and the set of seen feature URIs.

    Returns:
        Tuple of (features, seen feature URIs).

    Responsibility:
        Collect all features and the set of seen feature URIs. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.collection.collect_features_and_seen_uris` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - locate_feature_pickles: collaborator call used by this boundary
        - Run.from_stash: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - run.ensure_feature_binding: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - features_by_uri.values: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `collect_features_and_seen_uris`

    State and side effects:
        mutates feature_pickles_feature_source, run, features_by_uri, features, seen_features_uris.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.collect_features_and_seen_uris` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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

    Responsibility:
        Resolve feature pickles for configured --feature paths. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.collection.locate_feature_pickles`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - ScenarioLocatorBuilder: collaborator call used by this boundary
        - locator_builder.build_for_feature_locator_args: collaborator call used by this boundary
        - defaultdict: collaborator call used by this boundary
        - get_feature_paths: collaborator call used by this boundary
        - locator.resolve: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates locator_builder, locators.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.locate_feature_pickles` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    locator_builder = ScenarioLocatorBuilder(config=config)
    locators = cast(
        "Sequence[ScenarioLocatorResolver]",
        locator_builder.build_for_feature_locator_args(
            cast("FeatureLocatorArgs", defaultdict(feature_paths=get_feature_paths(config))),
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

    Responsibility:
        Identify features and pickles that were not seen. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.collection.find_non_seen_features_and_pickles` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - list: collaborator call used by this boundary
        - filterfalse: collaborator call used by this boundary
        - filter: collaborator call used by this boundary
        - chain.from_iterable: collaborator call used by this boundary
        - zip_longest: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `find_non_seen_features_and_pickles`

    State and side effects:
        mutates non_seen_features, non_seen_feature_pickles.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.find_non_seen_features_and_pickles` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    non_seen_features: list[FeatureRuntimeBinding] = list(
        filterfalse(lambda feature: feature.uri in seen_features_uris, features),
    )

    non_seen_feature_pickles: list[tuple[FeatureRuntimeBinding, Pickle]] = list(
        filter(
            lambda feature_pickle: (feature_pickle[0].uri, feature_pickle[1].name) not in seen_feature_pickles_ids,  # type: ignore[arg-type]  # zip_longest produces mixed tuples
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

    Responsibility:
        Find unique non-matched feature pickle steps. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.collection.find_unique_non_matched_steps` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - list: collaborator call used by this boundary
        - map: collaborator call used by this boundary
        - next: collaborator call used by this boundary
        - filter: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `find_unique_non_matched_steps`

    State and side effects:
        mutates unique_step_defs_ids, unique_non_matched_feature_pickle_steps.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.find_unique_non_matched_steps` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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

    Responsibility:
        Collect features, pickles, and unique steps for full code generation. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.collection.collect_generation_inputs` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - run.ensure_feature_binding: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - locate_feature_pickles: collaborator call used by this boundary
        - Run.from_stash: collaborator call used by this boundary
        - features_by_uri.setdefault: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `collect_generation_inputs`

    State and side effects:
        mutates feature_pickles_feature_source, run, features_by_uri, features, feature_pickles.

    Invariants:
        - `pytest_bdd.plugin.code_generator.collection.collect_generation_inputs` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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
            lambda step_def_id: next(  # function may return untyped value
                filter(
                    lambda step: step[1].type == step_def_id[0] and step[1].text == step_def_id[1],
                    feature_pickles_steps,
                ),
            ),
            unique_step_defs_ids,
        ),
        key=lambda feature_pickle_step: feature_pickle_step[1].text,
    )

    return features, feature_pickles, unique_feature_pickle_steps
