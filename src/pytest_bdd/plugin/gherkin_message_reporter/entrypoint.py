"""
Provide entrypoint helpers.

Responsibility:
    Provide entrypoint helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.entrypoint` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _ReporterStateEntry: owns nested behavior below this boundary
    - _QuietTerminalReporter: owns nested behavior below this boundary
    - _reporting_requested: owns nested behavior below this boundary
    - _reporting_requested_from_args: owns nested behavior below this boundary
    - _terminal_formatter_flags_requested: owns nested behavior below this boundary
    - _pytest_capture_already_configured: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates reporter, stash, impl, restored, lifecycle; depends on __future__.annotations, io, logging, os,
    contextlib.suppress.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError, pytest.UsageError, re-raise; callers must treat these as boundary failures.

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

from __future__ import annotations

import io
import logging
import os
from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar, TextIO, cast

import pytest
from attrs import frozen

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager, Stash, TerminalReporter
from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.plugin.gherkin_message_reporter.runtime_contract import ReporterLifecycleContract
from pytest_bdd.util.cucumber_formatters import (
    any_cucumber_formatter_requested,
    terminal_formatter_flags_requested,
)
from pytest_bdd.util.cucumber_formatters import (
    pytest_capture_already_configured as _pytest_capture_already_configured_impl,
)

from .hook import GherkinMessageReporterHookSpec
from .plugin import (
    CucumberFormatterConfigurationError,
    GherkinMessageReporterPlugin,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

_REPORTING_OUTPUT_OPTION_FLAGS = (
    "--messagesndjson",
    "--messages-ndjson",
    "--messagesjsonl",
    "--messages-jsonl",
    "--cucumber-html",
    "--cucumberhtml",
)
_REPORTER_STATE_ATTR = "_pytest_bdd_gherkin_message_reporter_state"


@frozen
class _ReporterStateEntry(StashBound):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._ReporterStateEntry` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._ReporterStateEntry` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates STASH_KEY, reporter.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._ReporterStateEntry` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    STASH_KEY: ClassVar[str] = _REPORTER_STATE_ATTR
    reporter: object


class _QuietTerminalReporter(TerminalReporter):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - pytest_unconfigure: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates self._quiet_stream.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, config: Config, quiet_stream: TextIO) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter.__init__` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self._quiet_stream.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter.__init__` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self._quiet_stream = quiet_stream
        super().__init__(config, file=quiet_stream)  # type: ignore[call-arg]  # TerminalReporter file kwarg

    def pytest_unconfigure(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter.pytest_unconfigure` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._QuietTerminalReporter.pytest_unconfigure` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.pytest_unconfigure: collaborator call used by this boundary
            - super: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - self._quiet_stream.close: collaborator call used by this boundary

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
        super().pytest_unconfigure()  # type: ignore[misc]  # pytest TerminalReporter hook
        with suppress(OSError, ValueError):
            self._quiet_stream.close()


def _reporting_requested(config: Config) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._reporting_requested`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._reporting_requested` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - any: collaborator call used by this boundary
        - any_cucumber_formatter_requested: collaborator call used by this boundary

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
    return any(
        [
            getattr(config.option, "messages_ndjson_path", None) is not None,
            getattr(config.option, "cucumber_html_path", None) is not None,
            any_cucumber_formatter_requested(config.option),
        ],
    )


def _reporting_requested_from_args(args: list[str]) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._reporting_requested_from_args` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._reporting_requested_from_args` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - arg.startswith: collaborator call used by this boundary
        - any: collaborator call used by this boundary

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
    for arg in args:
        if arg in _REPORTING_OUTPUT_OPTION_FLAGS:
            return True
        if any(arg.startswith(f"{option_flag}=") for option_flag in _REPORTING_OUTPUT_OPTION_FLAGS):
            return True
        if arg.startswith("--cucumber-"):
            return True
    return False


def _terminal_formatter_flags_requested(args: list[str]) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._terminal_formatter_flags_requested` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._terminal_formatter_flags_requested` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - impl: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates impl.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._terminal_formatter_flags_requested` keeps its
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
    impl = cast("Callable[[list[str]], bool]", terminal_formatter_flags_requested)
    return impl(args)


def _pytest_capture_already_configured(args: list[str]) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._pytest_capture_already_configured` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._pytest_capture_already_configured` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - impl: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates impl.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._pytest_capture_already_configured` keeps its
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
    impl = cast("Callable[[list[str]], bool]", _pytest_capture_already_configured_impl)
    return impl(args)


def _running_on_windows() -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._running_on_windows` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._running_on_windows` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

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
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """
    return os.name == "nt"


def _remote_xdist_requested(args: list[str]) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._remote_xdist_requested`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._remote_xdist_requested` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - any: collaborator call used by this boundary
        - arg.startswith: collaborator call used by this boundary

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
    return any(arg in {"--tx", "--px"} or arg.startswith(("--tx=", "--px=")) for arg in args)


def _pytest_cache_already_configured(args: list[str]) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._pytest_cache_already_configured` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._pytest_cache_already_configured` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - len: collaborator call used by this boundary
        - startswith: collaborator call used by this boundary
        - enumerate: collaborator call used by this boundary
        - arg.startswith: collaborator call used by this boundary

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
    for index, arg in enumerate(args):
        if arg == "-p" and index + 1 < len(args):
            if args[index + 1] in {"cacheprovider", "no:cacheprovider"}:
                return True
            continue
        if arg.startswith("--override-ini=cache_dir="):
            return True
        if arg == "--override-ini" and index + 1 < len(args) and args[index + 1].startswith("cache_dir="):
            return True
        if arg == "-o" and index + 1 < len(args) and args[index + 1].startswith("cache_dir="):
            return True
    return False


def _replace_terminal_reporter_with_quiet_variant(config: Config) -> Callable[[], None] | None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._replace_terminal_reporter_with_quiet_variant` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._replace_terminal_reporter_with_quiet_variant` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - restore: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates restored, current_reporter, quiet_stream, quiet_reporter, current_plugin.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._replace_terminal_reporter_with_quiet_variant` keeps
          its documented import path, ownership boundary, and observable behavior stable for callers.

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
    current_reporter = config.pluginmanager.getplugin("terminalreporter")
    if current_reporter is None or current_reporter.__class__ != TerminalReporter:
        return None

    quiet_stream = io.StringIO()
    quiet_reporter = _QuietTerminalReporter(config, quiet_stream=quiet_stream)
    config.pluginmanager.unregister(current_reporter)
    config.pluginmanager.register(quiet_reporter, "terminalreporter")

    restored = False

    def restore() -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._replace_terminal_reporter_with_quiet_variant.restore`
            owns documented function behavior. It directly owns the observable contract, local decisions, and
            maintenance boundary for this function.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._replace_terminal_reporter_with_quiet_variant.restore`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - config.pluginmanager.getplugin: collaborator call used by this boundary
            - config.pluginmanager.unregister: collaborator call used by this boundary
            - config.pluginmanager.register: collaborator call used by this boundary
            - quiet_reporter.pytest_unconfigure: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates restored, current_plugin.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._replace_terminal_reporter_with_quiet_variant.restore`
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
        nonlocal restored
        if restored:
            return
        restored = True
        current_plugin = config.pluginmanager.getplugin("terminalreporter")
        if current_plugin is quiet_reporter:
            config.pluginmanager.unregister(quiet_reporter)
        if config.pluginmanager.getplugin("terminalreporter") is None:
            config.pluginmanager.register(current_reporter, "terminalreporter")
        quiet_reporter.pytest_unconfigure()

    return restore


def _config_stash(config: Config) -> Stash:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._config_stash` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._config_stash`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - Stash: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates stash, config.stash.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._config_stash` keeps its documented import path,
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
    stash = getattr(config, "stash", None)
    if stash is None:
        stash = Stash()
        config.stash = stash
    return stash


def _store_reporter_state(config: Config, reporter: object) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._store_reporter_state`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._store_reporter_state` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _ReporterStateEntry.set_in_stash: collaborator call used by this boundary
        - _ReporterStateEntry: collaborator call used by this boundary
        - _config_stash: collaborator call used by this boundary

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
    _ReporterStateEntry(reporter=reporter).set_in_stash(_config_stash(config))


def _resolve_reporter_state(config: Config) -> object | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._resolve_reporter_state`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._resolve_reporter_state` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _ReporterStateEntry.find_in_stash.value_or: collaborator call used by this boundary
        - _ReporterStateEntry.find_in_stash: collaborator call used by this boundary
        - _config_stash: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates state.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._resolve_reporter_state` keeps its documented import
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
    state = _ReporterStateEntry.find_in_stash(_config_stash(config)).value_or(None)
    return None if state is None else state.reporter


def _clear_reporter_state(config: Config) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._clear_reporter_state`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._clear_reporter_state` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates stash.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._clear_reporter_state` keeps its documented import
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
    stash = getattr(config, "stash", None)
    if stash is None:
        return
    with suppress(KeyError, AttributeError):
        del stash[_ReporterStateEntry.STASH_KEY]


def _require_reporter_lifecycle_contract(reporter: object) -> ReporterLifecycleContract:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._require_reporter_lifecycle_contract` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._require_reporter_lifecycle_contract` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._require_reporter_lifecycle_contract` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    if not isinstance(reporter, ReporterLifecycleContract):
        message = (
            "Configured gherkin message reporter does not satisfy the explicit lifecycle contract. "
            "Expected configure(pluginmanager=..., quiet_terminal_replacer=...) and "
            "unconfigure(pluginmanager=...)."
        )
        raise TypeError(message)
    return reporter


def _configure_reporter_instance(reporter: object, pluginmanager: PytestPluginManager) -> None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._configure_reporter_instance` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._configure_reporter_instance` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _require_reporter_lifecycle_contract: collaborator call used by this boundary
        - lifecycle.configure: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates lifecycle.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._configure_reporter_instance` keeps its documented
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
    lifecycle = _require_reporter_lifecycle_contract(reporter)
    lifecycle.configure(
        pluginmanager=pluginmanager,
        quiet_terminal_replacer=_replace_terminal_reporter_with_quiet_variant,
    )


def _unconfigure_reporter_instance(reporter: object, pluginmanager: PytestPluginManager) -> None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._unconfigure_reporter_instance` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._unconfigure_reporter_instance` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _require_reporter_lifecycle_contract: collaborator call used by this boundary
        - lifecycle.unconfigure: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates lifecycle.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint._unconfigure_reporter_instance` keeps its documented
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
    lifecycle = _require_reporter_lifecycle_contract(reporter)
    lifecycle.unconfigure(pluginmanager=pluginmanager)


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """
    Register plugin hooks.

    Responsibility:
        Register plugin hooks. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_addhooks` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - pluginmanager.add_hookspecs: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addhooks`

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
    pluginmanager.add_hookspecs(GherkinMessageReporterHookSpec)


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(
    early_config: Config,  # noqa: ARG001
    parser: Parser,  # noqa: ARG001
    args: list[str],
) -> None:
    """
    Handle load initial conftests.

    Responsibility:
        Handle load initial conftests. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_load_initial_conftests` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - list: collaborator call used by this boundary
        - _running_on_windows: collaborator call used by this boundary
        - _reporting_requested_from_args: collaborator call used by this boundary
        - _remote_xdist_requested: collaborator call used by this boundary
        - _pytest_cache_already_configured: collaborator call used by this boundary
        - _terminal_formatter_flags_requested: collaborator call used by this boundary

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
    if (
        _running_on_windows()
        and _reporting_requested_from_args(list(args))
        and _remote_xdist_requested(list(args))
        and not _pytest_cache_already_configured(list(args))
    ):
        args[:] = ["-p", "no:cacheprovider", *args]
    if not _terminal_formatter_flags_requested(list(args)):
        return
    if _pytest_capture_already_configured(list(args)):
        return
    args[:] = ["--capture=no", *args]


def pytest_addoption(parser: Parser) -> None:
    """
    Add pytest-bdd options.

    Responsibility:
        Add pytest-bdd options. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_addoption` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - parser.getgroup: collaborator call used by this boundary
        - group.addoption: collaborator call used by this boundary
        - parser.addini: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

    State and side effects:
        mutates group.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_addoption` keeps its documented import path,
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
    parser.addini(
        "pytest_bdd_transport_fail_workers",
        "internal testing hook for forcing xdist transport publication failures by worker id.",
        default="",
    )
    group = parser.getgroup("bdd", "Cucumber NDJSON")
    group.addoption(
        "--messagesndjson",
        "--messages-ndjson",
        "--messagesjsonl",
        "--messages-jsonl",
        action="store",
        dest="messages_ndjson_path",
        metavar="PATH",
        default=None,
        help="messages ndjson report file at given path.",
    )
    group = parser.getgroup("bdd", "Cucumber HTML")
    group.addoption(
        "--cucumber-html",
        "--cucumberhtml",
        action="store",
        dest="cucumber_html_path",
        metavar="PATH",
        default=None,
        help="cucumber html report at given path.",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """
    Handle configure.

    Raises:
        UsageError: If the operation cannot be completed.

    Responsibility:
        Handle configure. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_configure` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - GherkinMessageReporterPlugin: collaborator call used by this boundary
        - pytest.UsageError: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - _store_reporter_state: collaborator call used by this boundary
        - _configure_reporter_instance: collaborator call used by this boundary
        - logger.warning: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates reporter.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_configure` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises pytest.UsageError, re-raise; callers must treat these as boundary failures.

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
    reporter = None
    try:
        reporter = GherkinMessageReporterPlugin(config=config)
    except CucumberFormatterConfigurationError as exc:
        raise pytest.UsageError(str(exc)) from exc
    try:
        _store_reporter_state(config, reporter)
        _configure_reporter_instance(reporter, config.pluginmanager)
    except Exception:
        logger.warning("Reporter configuration failed", exc_info=True)
        if reporter is not None:
            _unconfigure_reporter_instance(reporter, config.pluginmanager)
        _clear_reporter_state(config)
        raise


@pytest.hookimpl(optionalhook=True, tryfirst=True)
def pytest_xdist_getremotemodule() -> ModuleType:
    """
    Get xdist remote module.

    Returns:
        Remote module type.

    Responsibility:
        Get xdist remote module. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_xdist_getremotemodule` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest.hookimpl: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        depends on pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.

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
    from pytest_bdd.plugin.gherkin_message_reporter import xdist_worker  # noqa: PLC0415 -- optional xdist dependency

    return xdist_worker


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    """
    Handle unconfigure.

    Responsibility:
        Handle unconfigure. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_unconfigure` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _resolve_reporter_state: collaborator call used by this boundary
        - _unconfigure_reporter_instance: collaborator call used by this boundary
        - _clear_reporter_state: collaborator call used by this boundary
        - pytest.hookimpl: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates reporter.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.entrypoint.pytest_unconfigure` keeps its documented import path,
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
    reporter = _resolve_reporter_state(config)
    if reporter is not None:
        _unconfigure_reporter_instance(reporter, config.pluginmanager)
    _clear_reporter_state(config)
