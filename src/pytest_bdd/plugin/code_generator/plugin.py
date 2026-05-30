"""pytest-bdd missing test code generation plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING

import py
from cucumber_messages import PickleStepType  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import wrap_session

from .collection import (
    collect_features_and_seen_uris,
    collect_generation_inputs,
    find_non_seen_features_and_pickles,
    find_unique_non_matched_steps,
    process_session_items,
)
from .rendering import STEP_TYPE_TO_STEP_PREFIX, generate_code
from .request import validate_feature_option

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cucumber_messages import Pickle, PickleStep  # type:ignore[attr-defined, import-untyped]

    from pytest_bdd.compatibility.pytest import Config, ExitCode, Session
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding


class CodeGeneratorPlugin:
    """Coordinate pytest-bdd code generation CLI behavior."""

    def pytest_cmdline_main(self, config: Config) -> int | ExitCode | None:
        """
        Check a config option to show generated code.

        Returns:
            Exit code or None.

        """
        if config.option.generate_missing:
            return self.generate_and_print_missing_code(config)
        if config.option.generate:
            return self.generate_and_print_code(config)
        return None

    def generate_and_print_missing_code(self, config: Config) -> int | ExitCode:
        """
        Wrap pytest session to show missing code.

        Returns:
            Exit code.

        """
        if self._feature_option_missing(config):
            return 100
        return wrap_session(config=config, doit=self.generate_and_print_missing_code_callback)

    def generate_and_print_code(self, config: Config) -> int | ExitCode:
        """
        Wrap pytest session to show generated code.

        Returns:
            Exit code.

        """
        if self._feature_option_missing(config):
            return 100

        verbosity = config.option.verbose
        try:
            config.option.verbose = -2
            exit_code = wrap_session(config=config, doit=self.generate_and_print_code_callback)
        finally:
            config.option.verbose = verbosity

        return exit_code

    @staticmethod
    def _feature_option_missing(config: Config) -> bool:
        """
        Report a missing --feature option before starting a pytest session.

        Returns:
            True when the feature option is missing.

        """
        if config.option.features is not None:
            return False
        py.io.TerminalWriter().line("The --feature parameter is required.", red=True)
        return True

    def generate_and_print_missing_code_callback(self, config: Config, session: Session) -> None:
        """Prepare fixture duplicates for missing-code output."""
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

        unique_non_matched_feature_steps = find_unique_non_matched_steps(non_matched_feature_pickle_steps)

        self.print_missing_code(
            features=non_seen_features,
            feature_pickles=non_seen_feature_pickles,  # type: ignore[arg-type]
            feature_pickle_steps=non_matched_feature_pickle_steps,
            unique_steps=unique_non_matched_feature_steps,
        )

        if non_seen_feature_pickles or non_matched_feature_pickle_steps:
            session.exitstatus = 100

    @staticmethod
    def generate_and_print_code_callback(config: Config, session: Session) -> None:
        """Prepare generated code output."""
        tw = py.io.TerminalWriter()

        if not validate_feature_option(config, session, tw):
            return

        features, feature_pickles, unique_feature_pickle_steps = collect_generation_inputs(config)
        code = generate_code(features, feature_pickles, unique_feature_pickle_steps)
        tw.write(code)

    @staticmethod
    def print_missing_code(
        *,
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
