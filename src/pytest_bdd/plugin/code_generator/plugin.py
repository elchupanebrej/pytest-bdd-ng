"""
pytest-bdd missing test code generation plugin.

Responsibility:
    pytest-bdd missing test code generation plugin. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.plugin` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - CodeGeneratorPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py: imports or references `plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `plugin`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `plugin`

State and side effects:
    mutates tw, target_file, session.exitstatus, terminal_reporter, config.option.verbose; depends on
    __future__.annotations, pathlib.Path, typing.TYPE_CHECKING, typing.cast, py.

Invariants:
    - `pytest_bdd.plugin.code_generator.plugin` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import py
from cucumber_messages import (
    PickleStepType,  # upstream library missing type stubs
)

from pytest_bdd.compatibility.pytest import wrap_session

from .collection import (
    collect_features_and_seen_uris,
    collect_generation_inputs,
    find_non_seen_features_and_pickles,
    find_unique_non_matched_steps,
    process_session_items,
)
from .events import CodeGenerationEvent, MissingScenarioBindingEvent, MissingStepDefinitionEvent, to_ndjson
from .rendering import STEP_TYPE_TO_STEP_PREFIX, generate_code, render_legacy_stdout_code
from .request import get_invocation_feature_paths, validate_feature_option
from .rewrite import TargetRewriteError, append_missing_step_skeletons, bind_features_to_target, validate_target_file

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cucumber_messages import (  # upstream library missing type stubs
        Pickle,
        PickleStep,
    )

    from pytest_bdd.compatibility.pytest import Config, ExitCode, Session
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding


class CodeGeneratorPlugin:
    """
    Coordinate pytest-bdd code generation CLI behavior.

    Responsibility:
        Coordinate pytest-bdd code generation CLI behavior. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_cmdline_main: owns nested behavior below this boundary
        - generate_and_print_missing_code: owns nested behavior below this boundary
        - generate_and_print_code: owns nested behavior below this boundary
        - _feature_option_missing: owns nested behavior below this boundary
        - _capture_feature_paths: owns nested behavior below this boundary
        - _silence_pytest_terminal: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `CodeGeneratorPlugin`

    State and side effects:
        mutates tw, target_file, session.exitstatus, terminal_reporter, config.option.verbose.

    Invariants:
        - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    def pytest_cmdline_main(self, config: Config) -> int | ExitCode | None:
        """
        Check a config option to show generated code.

        Returns:
            Exit code or None.

        Responsibility:
            Check a config option to show generated code. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.pytest_cmdline_main` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.bind_feature: collaborator call used by this boundary
            - self.generate_and_print_code: collaborator call used by this boundary
            - self.generate_and_print_missing_code: collaborator call used by this boundary
            - self.generate_missing_steps: collaborator call used by this boundary
            - self.gather_and_print_missing_events: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `pytest_cmdline_main`
            - src/pytest_bdd/plugin/gherkin_message_reporter/xdist_worker.py: imports or references
              `pytest_cmdline_main`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        if config.option.bind_feature:
            return self.bind_feature(config)
        if config.option.generate:
            return self.generate_and_print_code(config)
        if config.option.generate_missing:
            return self.generate_and_print_missing_code(config)
        if config.option.generate_missing_steps:
            return self.generate_missing_steps(config)
        if config.option.gather_missing_steps:
            return self.gather_and_print_missing_events(config)
        return None

    def generate_and_print_missing_code(self, config: Config) -> int | ExitCode:
        """
        Wrap pytest session to show generated missing code.

        Returns:
            Exit code.

        Responsibility:
            Wrap pytest session to show generated missing code. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_missing_code` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._feature_option_missing: collaborator call used by this boundary
            - self._capture_feature_paths: collaborator call used by this boundary
            - self._silence_pytest_terminal: collaborator call used by this boundary
            - config.pluginmanager.getplugin: collaborator call used by this boundary
            - config.pluginmanager.unregister: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates terminal_reporter.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_missing_code` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self._feature_option_missing(config):
            return 100

        self._capture_feature_paths(config)
        self._silence_pytest_terminal(config)
        terminal_reporter = config.pluginmanager.getplugin("terminalreporter")
        if terminal_reporter is not None:
            config.pluginmanager.unregister(terminal_reporter)
        return cast(
            "int | ExitCode",
            wrap_session(config=config, doit=self.generate_and_print_missing_code_callback),
        )

    def generate_and_print_code(self, config: Config) -> int | ExitCode:
        """
        Wrap pytest session to show generated code.

        Returns:
            Exit code.

        Responsibility:
            Wrap pytest session to show generated code. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_code` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._feature_option_missing: collaborator call used by this boundary
            - wrap_session: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates config.option.verbose, verbosity, exit_code.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_code` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        if self._feature_option_missing(config):
            return 100

        verbosity = config.option.verbose
        try:
            config.option.verbose = -2
            exit_code = wrap_session(config=config, doit=self.generate_and_print_code_callback)
        finally:
            config.option.verbose = verbosity

        return cast("int | ExitCode", exit_code)

    @staticmethod
    def _feature_option_missing(config: Config) -> bool:
        """
        Report a missing --feature option before starting a pytest session.

        Returns:
            True when the feature option is missing.

        Responsibility:
            Report a missing --feature option before starting a pytest session. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._feature_option_missing` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - get_invocation_feature_paths: collaborator call used by this boundary
            - py.io.TerminalWriter.line: collaborator call used by this boundary
            - py.io.TerminalWriter: collaborator call used by this boundary

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
        if get_invocation_feature_paths(config):
            return False
        py.io.TerminalWriter().line("At least one feature path is required.", red=True)
        return True

    @staticmethod
    def _capture_feature_paths(config: Config) -> None:
        """
        Capture positional feature paths without letting pytest collect them.

        Responsibility:
            Capture positional feature paths without letting pytest collect them. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._capture_feature_paths` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - get_invocation_feature_paths: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - ignored.append: collaborator call used by this boundary
            - Path.resolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates config.option.codegen_feature_paths, config.args, config.option.feature_autoload, target_file,
            ignored.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._capture_feature_paths` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        config.option.codegen_feature_paths = get_invocation_feature_paths(config)
        config.args = ["."]
        config.option.feature_autoload = False
        target_file = getattr(config.option, "target_file", None)
        if target_file:
            ignored = list(getattr(config.option, "ignore", None) or [])
            ignored.append(str(Path(str(target_file)).resolve()))
            config.option.ignore = ignored

    @staticmethod
    def _silence_pytest_terminal(config: Config) -> None:
        """
        Suppress pytest terminal prose so stdout remains machine-readable.

        Responsibility:
            Suppress pytest terminal prose so stdout remains machine-readable. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._silence_pytest_terminal` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - max: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates config.option.no_header, config.option.no_summary, config.option.quiet, config.option.verbose.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._silence_pytest_terminal` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        config.option.no_header = True
        config.option.no_summary = True
        config.option.quiet = max(getattr(config.option, "quiet", 0), 2)
        config.option.verbose = -2

    def gather_and_print_missing_events(self, config: Config) -> int | ExitCode:
        """
        Wrap pytest session to show missing artifact events.

        Returns:
            Exit code.

        Responsibility:
            Wrap pytest session to show missing artifact events. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.gather_and_print_missing_events` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._feature_option_missing: collaborator call used by this boundary
            - self._capture_feature_paths: collaborator call used by this boundary
            - self._silence_pytest_terminal: collaborator call used by this boundary
            - config.pluginmanager.getplugin: collaborator call used by this boundary
            - config.pluginmanager.unregister: collaborator call used by this boundary
            - wrap_session: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates terminal_reporter, exit_code.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.gather_and_print_missing_events` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self._feature_option_missing(config):
            return 100
        self._capture_feature_paths(config)
        self._silence_pytest_terminal(config)
        terminal_reporter = config.pluginmanager.getplugin("terminalreporter")
        if terminal_reporter is not None:
            config.pluginmanager.unregister(terminal_reporter)
        exit_code = wrap_session(config=config, doit=self.gather_and_print_missing_events_callback)
        if getattr(config.option, "codegen_missing_events_found", False):
            return 100
        return cast("int | ExitCode", exit_code)

    def bind_feature(self, config: Config) -> int:
        """
        Bind feature paths to a target pytest module.

        Returns:
            Exit code.

        Responsibility:
            Bind feature paths to a target pytest module. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.bind_feature` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - py.io.TerminalWriter.line: collaborator call used by this boundary
            - py.io.TerminalWriter: collaborator call used by this boundary
            - get_invocation_feature_paths: collaborator call used by this boundary
            - self._target_file: collaborator call used by this boundary
            - validate_target_file: collaborator call used by this boundary
            - bind_features_to_target: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates feature_paths, target_file.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.bind_feature` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        feature_paths = get_invocation_feature_paths(config)
        if not feature_paths:
            py.io.TerminalWriter().line("At least one feature path is required.", red=True)
            return 100
        target_file = self._target_file(config)
        if target_file is None:
            return 100
        try:
            validate_target_file(target_file)
            bind_features_to_target(
                target_file,
                feature_paths,
                keep_on_error=bool(config.option.keep_generated_on_error),
            )
        except TargetRewriteError as exception:
            py.io.TerminalWriter().line(str(exception), red=True)
            return 100
        return 0

    def generate_missing_steps(self, config: Config) -> int | ExitCode:
        """
        Gather missing events and append step skeletons to a target module.

        Returns:
            Exit code.

        Responsibility:
            Gather missing events and append step skeletons to a target module. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_missing_steps` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - self._feature_option_missing: collaborator call used by this boundary
            - self._target_file: collaborator call used by this boundary
            - self._capture_feature_paths: collaborator call used by this boundary
            - self._silence_pytest_terminal: collaborator call used by this boundary
            - config.pluginmanager.getplugin: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates target_file, terminal_reporter, exit_code.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_missing_steps` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        if self._feature_option_missing(config):
            return 100
        target_file = self._target_file(config)
        if target_file is None:
            return 100

        self._capture_feature_paths(config)
        self._silence_pytest_terminal(config)
        terminal_reporter = config.pluginmanager.getplugin("terminalreporter")
        if terminal_reporter is not None:
            config.pluginmanager.unregister(terminal_reporter)
        exit_code = wrap_session(config=config, doit=self.generate_missing_steps_callback)
        if getattr(config.option, "codegen_target_rewrite_failed", False):
            return 100
        if getattr(config.option, "codegen_missing_events_found", False):
            return 100
        return cast("int | ExitCode", exit_code)

    @staticmethod
    def _target_file(config: Config) -> Path | None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._target_file`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._target_file` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - py.io.TerminalWriter.line: collaborator call used by this boundary
            - py.io.TerminalWriter: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates target.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin._target_file` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        target = getattr(config.option, "target_file", None)
        if not target:
            py.io.TerminalWriter().line("--target-file is required.", red=True)
            return None
        return Path(str(target))

    def gather_and_print_missing_events_callback(self, config: Config, session: Session) -> None:
        """
        Prepare NDJSON missing-artifact output.

        Responsibility:
            Prepare NDJSON missing-artifact output. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.gather_and_print_missing_events_callback`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - py.io.TerminalWriter: collaborator call used by this boundary
            - config.hook.pytest_collection: collaborator call used by this boundary
            - validate_feature_option: collaborator call used by this boundary
            - self.collect_missing_events: collaborator call used by this boundary
            - to_ndjson: collaborator call used by this boundary
            - tw.write: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates tw, events, ndjson, config.option.codegen_missing_events_found, session.exitstatus.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.gather_and_print_missing_events_callback`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        tw = py.io.TerminalWriter()
        config.hook.pytest_collection(session=session)

        if not validate_feature_option(config, session, tw):
            return

        events = self.collect_missing_events(config, session)
        ndjson = to_ndjson(events)
        if ndjson:
            tw.write(f"{ndjson}\n")
            config.option.codegen_missing_events_found = True
            session.exitstatus = 100

    def generate_missing_steps_callback(self, config: Config, session: Session) -> None:
        """
        Prepare missing-step target-file edits.

        Responsibility:
            Prepare missing-step target-file edits. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_missing_steps_callback` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - py.io.TerminalWriter: collaborator call used by this boundary
            - config.hook.pytest_collection: collaborator call used by this boundary
            - validate_feature_option: collaborator call used by this boundary
            - self.collect_missing_events: collaborator call used by this boundary
            - self._target_file: collaborator call used by this boundary
            - append_missing_step_skeletons: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates session.exitstatus, config.option.codegen_target_rewrite_failed, tw, events,
            config.option.codegen_missing_events_found.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_missing_steps_callback` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        tw = py.io.TerminalWriter()
        config.hook.pytest_collection(session=session)

        if not validate_feature_option(config, session, tw):
            return

        events = self.collect_missing_events(config, session)
        if events:
            config.option.codegen_missing_events_found = True
            session.exitstatus = 100
        target_file = self._target_file(config)
        if target_file is None:
            config.option.codegen_target_rewrite_failed = True
            session.exitstatus = 100
            return

        try:
            append_missing_step_skeletons(
                target_file,
                events,
                keep_on_error=bool(config.option.keep_generated_on_error),
            )
        except TargetRewriteError as exception:
            tw.line(str(exception), red=True)
            config.option.codegen_target_rewrite_failed = True
            session.exitstatus = 100

    def collect_missing_events(self, config: Config, session: Session) -> list[CodeGenerationEvent]:
        """
        Collect missing scenario/step events from a pytest session.

        Returns:
            Missing artifact events.

        Responsibility:
            Collect missing scenario/step events from a pytest session. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.collect_missing_events` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - process_session_items: collaborator call used by this boundary
            - collect_features_and_seen_uris: collaborator call used by this boundary
            - find_non_seen_features_and_pickles: collaborator call used by this boundary
            - self.build_missing_events: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates seen_feature_pickles_ids, non_matched_feature_pickle_steps, features, seen_features_uris,
            _non_seen_features.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.collect_missing_events` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        seen_feature_pickles_ids, non_matched_feature_pickle_steps = process_session_items(session)
        features, seen_features_uris = collect_features_and_seen_uris(config, seen_feature_pickles_ids)

        _non_seen_features, non_seen_feature_pickles = find_non_seen_features_and_pickles(
            features,
            seen_feature_pickles_ids,
            seen_features_uris,
        )

        return self.build_missing_events(
            feature_pickles=non_seen_feature_pickles,  # list[FeatureRuntimeBinding|Pickle] vs expected
            feature_pickle_steps=non_matched_feature_pickle_steps,
        )

    def generate_and_print_missing_code_callback(self, config: Config, session: Session) -> None:
        """
        Prepare fixture duplicates for missing-code output.

        Responsibility:
            Prepare fixture duplicates for missing-code output. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_missing_code_callback`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - py.io.TerminalWriter: collaborator call used by this boundary
            - config.hook.pytest_collection: collaborator call used by this boundary
            - validate_feature_option: collaborator call used by this boundary
            - process_session_items: collaborator call used by this boundary
            - collect_features_and_seen_uris: collaborator call used by this boundary
            - find_non_seen_features_and_pickles: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates tw, seen_feature_pickles_ids, non_matched_feature_pickle_steps, features, seen_features_uris.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_missing_code_callback`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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

        non_seen_feature_pickle_steps = [
            ((feature, pickle), step) for feature, pickle in non_seen_feature_pickles for step in pickle.steps
        ]
        all_missing_feature_steps = [
            *non_matched_feature_pickle_steps,
            *non_seen_feature_pickle_steps,
        ]
        unique_non_matched_feature_steps = find_unique_non_matched_steps(all_missing_feature_steps)

        self.print_missing_code(
            features=non_seen_features,
            feature_pickles=[],
            feature_pickle_steps=all_missing_feature_steps,
            unique_steps=unique_non_matched_feature_steps,
        )

    @staticmethod
    def generate_and_print_code_callback(config: Config, session: Session) -> None:
        """
        Prepare generated code output.

        Responsibility:
            Prepare generated code output. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_code_callback` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - py.io.TerminalWriter: collaborator call used by this boundary
            - validate_feature_option: collaborator call used by this boundary
            - collect_generation_inputs: collaborator call used by this boundary
            - generate_code: collaborator call used by this boundary
            - tw.write: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates tw, features, feature_pickles, unique_feature_pickle_steps, code.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.generate_and_print_code_callback` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        """
        Print missing code with TerminalWriter.

        Responsibility:
            Print missing code with TerminalWriter. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.print_missing_code` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - tw.line: collaborator call used by this boundary
            - tw.sep: collaborator call used by this boundary
            - py.io.TerminalWriter: collaborator call used by this boundary
            - feature.pickle_line_number: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - feature.step_line_number: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates tw, scenario, step, step_type, code.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.print_missing_code` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        tw.write(render_legacy_stdout_code(code))

    @staticmethod
    def build_missing_events(
        *,
        feature_pickles: Sequence[tuple[FeatureRuntimeBinding, Pickle]],
        feature_pickle_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
    ) -> list[CodeGenerationEvent]:
        """
        Build deterministic missing-artifact events.

        Returns:
            Missing artifact events.

        Responsibility:
            Build deterministic missing-artifact events. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.build_missing_events` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - MissingScenarioBindingEvent: collaborator call used by this boundary
            - feature.pickle_line_number: collaborator call used by this boundary
            - events.extend: collaborator call used by this boundary
            - MissingStepDefinitionEvent: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates events.

        Invariants:
            - `pytest_bdd.plugin.code_generator.plugin.CodeGeneratorPlugin.build_missing_events` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        events: list[CodeGenerationEvent] = [
            MissingScenarioBindingEvent(
                feature=str(feature.filename),
                scenario=pickle.name,
                line=feature.pickle_line_number(pickle),
            )
            for feature, pickle in feature_pickles
        ]
        events.extend(
            MissingStepDefinitionEvent(
                feature=str(feature.filename),
                scenario=pickle.name,
                keyword=STEP_TYPE_TO_STEP_PREFIX[step.type if step.type is not None else PickleStepType.unknown],
                text=step.text,
                line=getattr(step, "line_number", None) or feature.step_line_number(step),
            )
            for (feature, pickle), step in feature_pickle_steps
        )
        return events
