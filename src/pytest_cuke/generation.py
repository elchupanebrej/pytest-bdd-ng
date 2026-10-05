"""pytest-bdd missing test code generation."""

from __future__ import annotations

import argparse
import os.path
import warnings
from dataclasses import dataclass
from itertools import chain, filterfalse, zip_longest
from operator import lt, methodcaller
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

import py
from mako.template import Template

from pytest_cuke.compatibility.importlib.resources import as_file, files
from pytest_cuke.compatibility.pytest import wrap_session
from pytest_cuke.model import StepType
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.packaging import compare_distribution_version
from pytest_cuke.scenario_locator import FileScenarioLocator
from pytest_cuke.steps import Matcher
from pytest_cuke.utils import make_python_name
from pytest_cuke.warning_types import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from pytest_cuke.compatibility.pytest import Config, ExitCode, FixtureRequest, Item, Parser, Session
    from pytest_cuke.model import Feature, Pickle
    from pytest_cuke.model import Step as PickleStep


class _TemplateProtocol(Protocol):
    def render(self, **data: Any) -> str: ...


STEP_TYPE_TO_STEP_PREFIX = {
    StepType.unknown: "*",
    StepType.outcome: "Then",
    StepType.context: "Given",
    StepType.action: "When",
}


STEP_TYPE_TO_STEP_METHOD_NAME = {
    StepType.unknown: "step",
    StepType.outcome: "then",
    StepType.context: "given",
    StepType.action: "when",
}


@dataclass(frozen=True)
class StepDefinitionMatch:
    """Result of matching one scenario step against registered definitions."""

    step: PickleStep
    matched: bool
    ambiguous: bool


class StepDefinitionInspectionError(RuntimeError):
    """An existing step definition could not be inspected safely."""


def iter_step_definition_matches(
    request: FixtureRequest,
    feature: Feature,
    scenario: Any,
    *,
    detect_ambiguity: bool = False,
) -> Iterable[StepDefinitionMatch]:
    """Match scenario steps in order using pytest-cuke's active definition hook."""
    previous_step: PickleStep | None = None
    for step in scenario.steps:
        ambiguous = False
        try:
            with RunContext().inspect_step(
                feature=feature,
                scenario=scenario,
                step=step,
                previous_step=previous_step,
                nodeid="<step-definition-inspection>",
            ) as run:
                if detect_ambiguity:
                    with warnings.catch_warnings(record=True) as observed:
                        warnings.simplefilter("always", PytestBDDStepDefinitionWarning)
                        request.config.hook.pytest_cuke_match_step_definition_to_step(
                            request=request,
                            run=run,
                        )
                    ambiguous = any(
                        warning.category is PytestBDDStepDefinitionWarning
                        and "Alternative step definitions" in str(warning.message)
                        for warning in observed
                    )
                else:
                    request.config.hook.pytest_cuke_match_step_definition_to_step(
                        request=request,
                        run=run,
                    )
        except Matcher.MatchNotFoundError:
            yield StepDefinitionMatch(step=step, matched=False, ambiguous=False)
        except Exception as error:
            raise StepDefinitionInspectionError(
                f"could not inspect existing parser for {step.keyword.strip()} {step.text!r}: {error}"
            ) from error
        else:
            yield StepDefinitionMatch(step=step, matched=True, ambiguous=ambiguous)
        finally:
            previous_step = step


def check_existense(file_name: str) -> Path:
    """Check file or directory name for existence."""
    if not os.path.exists(file_name):
        msg = f"{file_name} is an invalid file or directory name"
        raise argparse.ArgumentTypeError(msg)
    return Path(file_name)


def add_options(parser: Parser) -> None:
    """Add canonical pytest-cuke generation options."""
    group = parser.getgroup("cuke", "Generation")

    group._addoption(
        "--cuke-generate-missing",
        action="store_true",
        dest="cuke_generate_missing",
        default=None,
        help="Generate missing bdd test code for given feature files and exit.",
    )

    group._addoption(
        "--cuke-generate",
        action="store_true",
        dest="cuke_generate",
        default=None,
        help="Generate bdd test code for given feature files and exit.",
    )

    group._addoption(
        "--cuke-feature",
        metavar="FILE_OR_DIR",
        action="append",
        type=check_existense,
        dest="cuke_feature",
        default=None,
        help="Feature file or directory to generate code for. Multiple allowed.",
    )
    parser.addini("cuke_generate_missing", "Generate missing step code.", default=False, type="bool")
    parser.addini("cuke_generate", "Generate step code.", default=False, type="bool")
    parser.addini("cuke_feature", "Feature paths used by the pytest generator.", default=[], type="args")


def cmdline_main(config: Config) -> int | ExitCode | None:
    """Check config option to show missing code."""
    generate_missing = config.option.cuke_generate_missing
    if generate_missing is None:
        generate_missing = config.getini("cuke_generate_missing")
    generate = config.option.cuke_generate
    if generate is None:
        generate = config.getini("cuke_generate")
    if generate_missing:
        return generate_and_print_missing_code(config)
    if generate:
        return generate_and_print_code(config)
    return None


def _feature_paths(config: Config) -> Sequence[Path]:
    paths = config.option.cuke_feature
    if paths is None:
        paths = config.getini("cuke_feature")
    return cast("Sequence[Path]", paths)


def generate_code(
    features: Sequence[Feature],
    feature_pickles: Sequence[tuple[Feature, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]],
) -> str:
    """Generate test code for the given filenames."""
    with as_file(files("pytest_cuke.template").joinpath("test.py.mak")) as path:
        template_factory = cast("Callable[..., _TemplateProtocol]", Template)
        template = template_factory(filename=str(path))
    return template.render(
        features=features,
        feature_pickles=feature_pickles,
        feature_pickle_steps=feature_pickle_steps,
        make_python_name=make_python_name,
        make_python_docstring=make_python_docstring,
        make_string_literal=make_string_literal,
        step_type_to_method_name=step_type_to_method_name,
    )


def generate_and_print_missing_code(config: Config) -> int | ExitCode:
    """Wrap pytest session to show missing code."""

    def _(config: Config, session: Session) -> None:
        """Preparing fixture duplicates for output."""
        tw = py.io.TerminalWriter()
        config.hook.pytest_collection(session=session)

        feature_paths = _feature_paths(config)
        if not feature_paths:
            tw.line("The --cuke-feature parameter is required.", red=True)
            session.exitstatus = 100
            return

        seen_feature_pickles_ids = set()
        non_matched_feature_pickle_steps = []

        for item in session.items:
            is_legacy_pytest = compare_distribution_version("pytest", "7.0", lt)

            method_name = "prepare" if is_legacy_pytest else "setup"
            methodcaller(method_name, item)(item.session._setupstate)

            item = cast("Item", item)
            item_request: FixtureRequest = item._request
            pickle: Pickle = item_request.getfixturevalue("scenario")
            feature: Feature = item_request.getfixturevalue("feature")

            seen_feature_pickles_ids.add((feature.uri, pickle.name))

            for match in iter_step_definition_matches(item_request, feature, pickle):
                if not match.matched:
                    non_matched_feature_pickle_steps.append(((feature, pickle), match.step))

            item.session._setupstate.teardown_exact(  # type: ignore[call-arg]  # Pytest's private teardown signature varies by supported version.
                *((item,) if is_legacy_pytest else ()), None
            )

        features = list(FileScenarioLocator(feature_paths=list(feature_paths)).resolve_features(config))

        seen_features_uris = set()
        for feature_uri, _pickle_name in seen_feature_pickles_ids:
            if feature_uri not in seen_features_uris:
                seen_features_uris.add(feature_uri)

        non_seen_features = list(filterfalse(lambda feature: feature.uri in seen_features_uris, features))

        non_seen_feature_pickles = [
            (feature, pickle)
            for feature in features
            for pickle in feature.pickles
            if (feature.uri, pickle.name) not in seen_feature_pickles_ids
        ]

        unique_step_defs_ids = {(step.type, step.text) for _, step in non_matched_feature_pickle_steps}
        unique_non_matched_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]] = []
        for step_def_id in unique_step_defs_ids:
            unique_non_matched_feature_pickle_steps.append(
                next(
                    feature_pickle_step
                    for feature_pickle_step in non_matched_feature_pickle_steps
                    if feature_pickle_step[1].type == step_def_id[0] and feature_pickle_step[1].text == step_def_id[1]
                )
            )

        print_missing_code(
            non_seen_features,
            non_seen_feature_pickles,
            non_matched_feature_pickle_steps,
            unique_non_matched_feature_pickle_steps,
        )

        session.exitstatus = 0

    return wrap_session(config=config, doit=_)


def generate_and_print_code(config: Config) -> int | ExitCode:
    """Wrap pytest session to show missing code."""

    def _(config: Config, session: Session) -> None:
        """Preparing fixture duplicates for output."""
        tw = py.io.TerminalWriter()

        feature_paths = _feature_paths(config)
        if not feature_paths:
            tw.line("The --cuke-feature parameter is required.", red=True)
            session.exitstatus = 100
            return

        features = list(FileScenarioLocator(feature_paths=list(feature_paths)).resolve_features(config))

        feature_pickles: Sequence[tuple[Feature, Pickle]] = list(
            chain.from_iterable(
                cast(
                    "Iterable[tuple[Feature, Pickle]]",
                    zip_longest((), feature.pickles, fillvalue=feature),
                )
                for feature in features
            )
        )

        feature_pickles_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]] = list(
            chain.from_iterable(
                cast(
                    "Iterable[tuple[tuple[Feature, Pickle], PickleStep]]",
                    zip_longest((), feature_pickle[1].steps, fillvalue=feature_pickle),
                )
                for feature_pickle in feature_pickles
            )
        )

        unique_step_defs_ids = {(step.type, step.text) for (feature, pickle), step in feature_pickles_steps}
        unique_feature_pickle_steps: list[tuple[tuple[Feature, Pickle], PickleStep]] = sorted(
            [
                next(
                    pair
                    for pair in feature_pickles_steps
                    if pair[1].type == step_def_id[0] and pair[1].text == step_def_id[1]
                )
                for step_def_id in unique_step_defs_ids
            ],
            key=lambda feature_pickle_step: feature_pickle_step[1].text,
        )

        code = generate_code(features, feature_pickles, unique_feature_pickle_steps)
        tw.write(code)

    verbosity = config.option.verbose
    try:
        config.option.verbose = -2
        exit_code = wrap_session(config=config, doit=_)
    finally:
        config.option.verbose = verbosity

    return exit_code


def print_missing_code(
    features: Sequence[Feature],
    feature_pickles: Sequence[tuple[Feature, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]],
    unique_steps: Sequence[tuple[tuple[Feature, Pickle], PickleStep]],
) -> None:
    """Print missing code with TerminalWriter."""
    tw = py.io.TerminalWriter()
    scenario = step = None

    for feature, pickle in feature_pickles:
        tw.line()
        tw.line(
            f'Scenario "{pickle.name}" is not bound to any test in the feature "{feature.name}"'
            f" in the file {feature.filename}:{feature._get_pickle_line_number(pickle)}",
            red=True,
        )

    if scenario:
        tw.sep("-", red=True)

    for (feature, pickle), step in feature_pickle_steps:
        tw.line()
        step_type = STEP_TYPE_TO_STEP_PREFIX[cast("StepType", step.type) if step.type is not None else StepType.unknown]
        tw.line(
            f'StepHandler {step_type} "{step.text}" is not defined in the scenario "{pickle.name}" in the feature'
            f' "{feature.name}" in the file {feature.filename}:{feature._get_step_line_number(step)}',
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
    return ascii(f"{string}.")


def make_string_literal(string: str) -> str:
    """Make python string literal out of a given string."""
    return ascii(string)
