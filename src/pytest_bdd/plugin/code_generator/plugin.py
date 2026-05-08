"""pytest-bdd missing test code generation."""

import argparse
from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import lru_cache
from itertools import chain, filterfalse, zip_longest
from pathlib import Path
from typing import TYPE_CHECKING, cast

import py
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    GherkinDocument,
    Pickle,
    PickleStep,
    PickleStepType,
    Source,
)
from jinja2 import Environment
from jinja2.environment import Template

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.compatibility.pytest import Config, ExitCode, FixtureRequest, Item, Session, wrap_session
from pytest_bdd.feature_locator import FeatureLocatorArgs, ScenarioLocatorBuilder
from pytest_bdd.model.scenario_run import FeatureRuntimeBinding, Run
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.other import format_as_simplified_python_identifier

if TYPE_CHECKING:
    from pytest_bdd.scenario_locator import ScenarioLocatorResolver

STEP_TYPE_TO_STEP_PREFIX = {
    PickleStepType.unknown: "*",
    PickleStepType.outcome: "Then",
    PickleStepType.context: "Given",
    PickleStepType.action: "When",
}

STEP_TYPE_TO_STEP_METHOD_NAME = {
    PickleStepType.unknown: "step",
    PickleStepType.outcome: "then",
    PickleStepType.context: "given",
    PickleStepType.action: "when",
}

TEMPLATE_ENV = Environment(autoescape=False, keep_trailing_newline=True)  # noqa: S701


@lru_cache(maxsize=1)
def get_code_generation_template() -> Template:
    """
    Return code generation template.

    Returns:
        Jinja2 template for code generation.

    """
    template_source = files("pytest_bdd.template").joinpath("test.py.jinja2").read_text(encoding="utf-8")
    return TEMPLATE_ENV.from_string(template_source)


# TODO: Rework into plugin class
# TODO: Use wrapping around other plugins
def check_existence(file_name: str) -> Path:
    """
    Check file or directory name for existence.

    Args:
        file_name: File or directory name.

    Returns:
        Path object if exists.

    Raises:
        argparse.ArgumentTypeError: If the file or directory does not exist.

    """
    if not Path(file_name).exists():
        msg = f"{file_name} is an invalid file or directory name"
        raise argparse.ArgumentTypeError(msg)
    return Path(file_name)


def generate_code(
    features: Sequence[FeatureRuntimeBinding],
    feature_pickles: Sequence[tuple[FeatureRuntimeBinding, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> str:
    """
    Generate test code for the given filenames.

    Returns:
        Generated Python code string.

    """
    template = get_code_generation_template()
    code = template.render(
        features=features,
        feature_pickles=feature_pickles,
        feature_pickle_steps=feature_pickle_steps,
        make_python_name=format_as_simplified_python_identifier,
        make_python_docstring=make_python_docstring,
        make_string_literal=make_string_literal,
        step_type_to_method_name=STEP_TYPE_TO_STEP_METHOD_NAME,
    )
    return cast("str", code)


def generate_and_print_missing_code_callback(config: Config, session: Session) -> None:
    """Prepare fixture duplicates for output."""
    tw = py.io.TerminalWriter()
    config.hook.pytest_collection(session=session)

    if not validate_feature_option(config, session, tw):
        return

    seen_feature_pickles_ids, non_matched_feature_pickle_steps = process_session_items(session)

    features, seen_features_uris = collect_features_and_seen_uris(config, seen_feature_pickles_ids)

    non_seen_features, non_seen_feature_pickles = find_non_seen_features_and_pickles(
        features,
        seen_feature_pickles_ids,
        seen_features_uris,
    )

    unique_non_matched_feature_pickle_steps = find_unique_non_matched_steps(non_matched_feature_pickle_steps)

    print_missing_code(
        config,
        non_seen_features,
        non_seen_feature_pickles,  # type: ignore[arg-type]
        non_matched_feature_pickle_steps,
        unique_non_matched_feature_pickle_steps,
    )

    if non_seen_feature_pickles or non_matched_feature_pickle_steps:
        session.exitstatus = 100


def validate_feature_option(config: Config, session: Session, tw: py.io.TerminalWriter) -> bool:
    """
    Validate if the --feature parameter is provided.

    Returns:
        True if valid, False otherwise.

    """
    if config.option.features is None:
        tw.line("The --feature parameter is required.", red=True)
        session.exitstatus = 100
        return False
    return True


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
    item.session._setupstate.setup(item)
    item_request: FixtureRequest = item._request
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
    item.session._setupstate.teardown_exact(None)  # type: ignore[call-arg]


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
    locator_builder = ScenarioLocatorBuilder(config=config)
    locators = cast(
        "Sequence[ScenarioLocatorResolver]",
        locator_builder.build_for_feature_locator_args(
            cast("FeatureLocatorArgs", defaultdict(feature_paths=list(map(Path, config.option.features)))),
        ),
    )
    feature_pickles_feature_source: list[tuple[GherkinDocument, Pickle, Source]] = [
        feature_pickles_source for locator in locators for feature_pickles_source in locator.resolve(config)
    ]
    run = Run.from_stash(config.stash)
    features_by_uri = {
        str(gherkin_document.uri): run.ensure_feature_binding(gherkin_document=gherkin_document, source=source)
        for gherkin_document, _pickle, source in feature_pickles_feature_source
    }
    features: Sequence[FeatureRuntimeBinding] = list(features_by_uri.values())

    seen_features_uris: set[str] = {feature_uri for feature_uri, _ in seen_feature_pickles_ids}

    return features, seen_features_uris


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


def generate_and_print_missing_code(config: Config) -> int | ExitCode:
    """
    Wrap pytest session to show missing code.

    Returns:
        Exit code.

    """
    return wrap_session(config=config, doit=generate_and_print_missing_code_callback)


def generate_and_print_code_callback(config: Config, session: Session) -> None:
    """Prepare fixture duplicates for output."""
    tw = py.io.TerminalWriter()

    if config.option.features is None:
        tw.line("The --feature parameter is required.", red=True)
        session.exitstatus = 100
        return

    locator_builder = ScenarioLocatorBuilder(config=config)
    locators = cast(
        "Sequence[ScenarioLocatorResolver]",
        locator_builder.build_for_feature_locator_args(
            cast("FeatureLocatorArgs", defaultdict(feature_paths=list(map(Path, config.option.features)))),
        ),
    )
    feature_pickles_feature_source: list[tuple[GherkinDocument, Pickle, Source]] = [
        feature_pickles_source for locator in locators for feature_pickles_source in locator.resolve(config)
    ]

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

    unique_step_defs_ids = {(step.type, step.text) for (feature, pickle), step in feature_pickles_steps}
    unique_feature_pickle_steps = sorted(
        map(
            lambda step_def_id: next(  # type: ignore[no-any-return]
                filter(
                    lambda s: s[1].type == step_def_id[0] and s[1].text == step_def_id[1],
                    feature_pickles_steps,
                ),
            ),
            unique_step_defs_ids,
        ),
        key=lambda feature_pickle_step: cast("str", feature_pickle_step[1].text),
    )

    code = generate_code(features, feature_pickles, unique_feature_pickle_steps)
    tw.write(code)


def generate_and_print_code(config: Config) -> int | ExitCode:
    """
    Wrap pytest session to show missing code.

    Returns:
        Exit code.

    """
    verbosity = config.option.verbose
    try:
        config.option.verbose = -2
        exit_code = wrap_session(config=config, doit=generate_and_print_code_callback)
    finally:
        config.option.verbose = verbosity

    return exit_code


def print_missing_code(
    _config: Config,
    features: Sequence[FeatureRuntimeBinding],
    feature_pickles: Sequence[tuple[FeatureRuntimeBinding, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
    unique_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> None:
    """Print missing code with TerminalWriter."""
    tw = py.io.TerminalWriter()
    scenario = step = None

    for feature, pickle in feature_pickles:
        tw.line()
        tw.line(
            f'Scenario "{pickle.name}" is not bound to any test in the feature "{feature.name}"'
            f" in the file {feature.filename}:{feature.pickle_line_number(pickle)}",
            red=True,
        )

    if scenario:
        tw.sep("-", red=True)

    for (feature, pickle), step in feature_pickle_steps:
        tw.line()
        step_type = STEP_TYPE_TO_STEP_PREFIX[step.type if step.type is not None else PickleStepType.unknown]
        tw.line(
            f"""Step {step_type} "{step.text}" is not defined in the scenario "{pickle.name}" in the feature"""
            f""" "{feature.name}" in the file"""
            f""" {feature.filename}:{getattr(step, "line_number", None) or feature.step_line_number(step)}""",
            red=True,
        )

    if step:
        tw.sep("-", red=True)

    tw.line("Please place the code above to the test file(s):")
    tw.line()

    code = generate_code(features, feature_pickles, unique_steps)
    tw.write(code)


def make_python_docstring(string: str) -> str:
    """
    Make a python docstring literal out of a given string.

    Args:
        string: Input string.

    Returns:
        Python docstring literal.

    """
    return '"""{}."""'.format(string.replace('"""', '\\"\\"\\"'))


def make_string_literal(string: str) -> str:
    """
    Make python string literal out of a given string.

    Args:
        string: Input string.

    Returns:
        Python string literal.

    """
    return "'{}'".format(string.replace("'", "\\'"))
