"""pytest-bdd missing test code generation."""

import argparse
from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import lru_cache
from itertools import chain, filterfalse, zip_longest
from operator import methodcaller
from pathlib import Path
from typing import Any, cast

import py
from cucumber_messages import Pickle, PickleStep, PickleStepType  # type:ignore[attr-defined, import-untyped]
from jinja2 import Environment

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.compatibility.pytest import Config, ExitCode, FixtureRequest, Item, Session, wrap_session
from pytest_bdd.feature_locator import FeatureLocatorArgs, ScenarioLocatorBuilder
from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.other import format_as_simplified_python_identifier
from pytest_bdd.util.toolz_extra import chain_map

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
def get_code_generation_template():
    template_source = files("pytest_bdd.template").joinpath("test.py.jinja2").read_text(encoding="utf-8")
    return TEMPLATE_ENV.from_string(template_source)


# TODO Rework into plugin class
# TODO Use wrapping around other plugins
def check_existence(file_name):
    """Check file or directory name for existence."""
    if not Path(file_name).exists():
        msg = f"{file_name} is an invalid file or directory name"
        raise argparse.ArgumentTypeError(msg)
    return Path(file_name)


def generate_code(
    features: Sequence[Feature],
    feature_pickles: Sequence[tuple[Feature, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]],
) -> str:
    """Generate test code for the given filenames."""
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
    return cast(str, code)


def generate_and_print_missing_code_callback(config: Config, session: Session) -> None:
    """Preparing fixture duplicates for output."""
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
    """Validate if the --feature parameter is provided."""
    if config.option.features is None:
        tw.line("The --feature parameter is required.", red=True)
        session.exitstatus = 100
        return False
    return True


def process_session_items(
    session: Session,
) -> tuple[set[tuple[str, str]], list[tuple[tuple[Feature, Pickle], PickleStep]]]:
    """Process session items to gather matched and unmatched data."""
    seen_feature_pickles_ids: set[tuple[str, str]] = set()
    non_matched_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]] = []

    for item in session.items:
        process_single_item(cast(Item, item), seen_feature_pickles_ids, non_matched_feature_pickle_steps)

    return seen_feature_pickles_ids, non_matched_feature_pickle_steps


def process_single_item(
    item: Item | Any,
    seen_feature_pickles_ids: set[tuple[str, str]],
    non_matched_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]],
) -> None:
    """Handles processing for a single test item."""
    item.session._setupstate.setup(item)
    item_request: FixtureRequest = item._request
    pickle: Pickle = item_request.getfixturevalue("scenario")
    feature: Feature = item_request.getfixturevalue("feature")
    seen_feature_pickles_ids.add((feature.uri, pickle.name))
    process_pickle_steps(pickle, item_request, feature, non_matched_feature_pickle_steps)
    item.session._setupstate.teardown_exact(None)  # type: ignore[call-arg]


def process_pickle_steps(
    pickle: Pickle,
    item_request: FixtureRequest,
    feature: Feature,
    non_matched_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]],
) -> None:
    """Process pickle steps to gather unmatched steps."""
    previous_step: PickleStep | None = None
    for step in pickle.steps:
        try:
            item_request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=item_request,
                gherkin_document=feature.gherkin_document,
                pickle=pickle,
                step=step,
                previous_step=previous_step,
            )
        except StepDefinitionManager.Matcher.MatchNotFoundError:  # noqa:PERF203
            non_matched_feature_pickle_steps.append(((feature, pickle), step))
        finally:
            previous_step = step


def collect_features_and_seen_uris(
    config: Config,
    seen_feature_pickles_ids: set[tuple[str, str]],
) -> tuple[Sequence[Feature], set[str]]:
    """Collect all features and the set of seen feature URIs."""
    locator_builder = ScenarioLocatorBuilder(config=config)
    locators = locator_builder.build_for_feature_locator_args(
        cast(FeatureLocatorArgs, defaultdict(feature_paths=list(map(Path, config.option.features))))
    )
    feature_pickles_feature_source = chain_map(methodcaller("resolve", config), locators)

    features: Sequence[Feature] = [feature for feature, pickle, source in feature_pickles_feature_source]

    seen_features_uris: set[str] = {feature_uri for feature_uri, _ in seen_feature_pickles_ids}

    return features, seen_features_uris


def find_non_seen_features_and_pickles(
    features: Sequence[Feature],
    seen_feature_pickles_ids: set[tuple[str, str]],
    seen_features_uris: set[str],
) -> tuple[list[Feature], list[tuple[Feature, Pickle]]]:
    """Identify features and pickles that were not seen."""
    non_seen_features: list[Feature] = list(filterfalse(lambda feature: feature.uri in seen_features_uris, features))

    non_seen_feature_pickles: list[tuple[Feature, Pickle]] = list(
        filter(
            lambda feature_pickle: (feature_pickle[0].uri, feature_pickle[1].name) not in seen_feature_pickles_ids,
            chain.from_iterable(zip_longest((), feature.pickles, fillvalue=feature) for feature in features),
        ),
    )

    return non_seen_features, non_seen_feature_pickles


def find_unique_non_matched_steps(
    non_matched_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]],
) -> list[tuple[tuple[Feature, Pickle], PickleStep]]:
    """Find unique non-matched feature pickle steps."""
    unique_step_defs_ids: set[tuple[PickleStepType | None, str]] = {
        (step.type, step.text) for _, step in non_matched_feature_pickle_steps
    }
    unique_non_matched_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]] = list(
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
    """Wrap pytest session to show missing code."""
    return wrap_session(config=config, doit=generate_and_print_missing_code_callback)


def generate_and_print_code_callback(config: Config, session: Session) -> None:
    """Preparing fixture duplicates for output."""
    tw = py.io.TerminalWriter()

    if config.option.features is None:
        tw.line("The --feature parameter is required.", red=True)
        session.exitstatus = 100
        return

    locator_builder = ScenarioLocatorBuilder(config=config)
    locators = locator_builder.build_for_feature_locator_args(
        cast(FeatureLocatorArgs, defaultdict(feature_paths=list(map(Path, config.option.features))))
    )
    feature_pickles_feature_source = list(chain_map(methodcaller("resolve", config), locators))

    features: Sequence[Feature] = [feature for feature, pickle, source in feature_pickles_feature_source]

    feature_pickles: Sequence[tuple[Feature, Pickle]] = [
        (feature, pickle) for feature, pickle, source in feature_pickles_feature_source
    ]

    feature_pickles_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]] = list(
        chain.from_iterable(
            (
                cast(
                    Iterable[tuple[tuple[Feature, Pickle], PickleStep]],
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
        key=lambda feature_pickle_step: cast(str, feature_pickle_step[1].text),
    )

    code = generate_code(features, feature_pickles, unique_feature_pickle_steps)
    tw.write(code)


def generate_and_print_code(config: Config) -> int | ExitCode:
    """Wrap pytest session to show missing code."""
    verbosity = config.option.verbose
    try:
        config.option.verbose = -2
        exit_code = wrap_session(config=config, doit=generate_and_print_code_callback)
    finally:
        config.option.verbose = verbosity

    return exit_code


def print_missing_code(
    config: Config,
    features,
    feature_pickles: Sequence[tuple[Feature, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]],
    unique_steps,
) -> None:
    """Print missing code with TerminalWriter."""
    tw = py.io.TerminalWriter()
    scenario = step = None

    for feature, pickle in feature_pickles:
        tw.line()
        tw.line(
            f'Scenario "{pickle.name}" is not bound to any test in the feature "{feature.name}"'
            f" in the file {feature.filename}:{feature._get_pickle_line_number(pickle, config=config)}",
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
            f""" {feature.filename}:{getattr(step, 'line_number', None) or feature._get_step_line_number(step, config=config)}""",
            red=True,
        )

    if step:
        tw.sep("-", red=True)

    tw.line("Please place the code above to the test file(s):")
    tw.line()

    code = generate_code(features, feature_pickles, unique_steps)
    tw.write(code)


def make_python_docstring(string: str) -> str:
    """Make a python docstring literal out of a given string."""
    return '"""{}."""'.format(string.replace('"""', '\\"\\"\\"'))


def make_string_literal(string: str) -> str:
    """Make python string literal out of a given string."""
    return "'{}'".format(string.replace("'", "\\'"))
