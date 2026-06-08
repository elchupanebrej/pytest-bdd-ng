"""
Provide session helpers.

Responsibility:
    Provide session helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.session` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _FormatterRequestHook: owns nested behavior below this boundary
    - _FormatterRuntimeAssetsHook: owns nested behavior below this boundary
    - CucumberFormatterConfigurationError: owns nested behavior below this boundary
    - format_requested_cucumber_formatter_labels: owns nested behavior below this boundary
    - terminal_output_formatter_requests: owns nested behavior below this boundary
    - normalize_cucumber_formatter_output_key: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `session`
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `session`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `session`
    - src/pytest_bdd/plugin/code_generator/request.py: imports or references `session`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `session`

State and side effects:
    mutates message, hook, msg, requested_formatters, template; depends on __future__.annotations, os, pathlib.Path,
    typing.TYPE_CHECKING, typing.Protocol.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.session` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError, CucumberFormatterConfigurationError.terminal_output_conflict,
    CucumberFormatterConfigurationError.missing_output_directory,
    CucumberFormatterConfigurationError.duplicate_output_path; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.model.cucumber_formatter_contract import (  # noqa: F401
    CucumberFormatterRenderResult,
    CucumberFormatterRequest,
    FormatterRuntimeKind,
    NodePackageProvisionResult,
    ResolveOutputPath,
)
from pytest_bdd.util.cucumber_formatter_support.base import (
    load_formatter_adapter_support_template as _load_formatter_adapter_support_template,
)
from pytest_bdd.util.cucumber_formatter_support.base import (
    load_formatter_adapter_template as _load_formatter_adapter_template,
)

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

    from pytest_bdd.compatibility.pytest import Config, PytestPluginManager

# Re-export contract types for backward compatibility within the same plugin package.


class _FormatterRequestHook(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRequestHook` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRequestHook` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_cucumber_formatter_request: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `_FormatterRequestHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_FormatterRequestHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_FormatterRequestHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_FormatterRequestHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_FormatterRequestHook`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRequestHook` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def pytest_bdd_cucumber_formatter_request(
        self,
        *,
        config: Config,
        resolve_output_path: ResolveOutputPath,
    ) -> tuple[CucumberFormatterRequest, ...]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRequestHook.pytest_bdd_cucumber_formatter_request`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRequestHook.pytest_bdd_cucumber_formatter_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_request`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...


class _FormatterRuntimeAssetsHook(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRuntimeAssetsHook`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRuntimeAssetsHook` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_cucumber_formatter_runtime_assets: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `_FormatterRuntimeAssetsHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_FormatterRuntimeAssetsHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_FormatterRuntimeAssetsHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_FormatterRuntimeAssetsHook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_FormatterRuntimeAssetsHook`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRuntimeAssetsHook` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def pytest_bdd_cucumber_formatter_runtime_assets(
        self,
        *,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],
    ) -> tuple[dict[str, str] | None, ...]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRuntimeAssetsHook.pytest_bdd_cucumber_formatter_runtime_assets`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.session._FormatterRuntimeAssetsHook.pytest_bdd_cucumber_formatter_runtime_assets`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...


class CucumberFormatterConfigurationError(ValueError):
    """
    Raised when the requested cucumber formatter configuration is invalid.

    Responsibility:
        Raised when the requested cucumber formatter configuration is invalid. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - duplicate_output_path: owns nested behavior below this boundary
        - missing_output_directory: owns nested behavior below this boundary
        - terminal_output_conflict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `CucumberFormatterConfigurationError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `CucumberFormatterConfigurationError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `CucumberFormatterConfigurationError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `CucumberFormatterConfigurationError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `CucumberFormatterConfigurationError`

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    @classmethod
    def duplicate_output_path(
        cls,
        *,
        formatter_labels: str,
        output_path: Path,
    ) -> CucumberFormatterConfigurationError:
        """
        Create error for duplicate output path.

        Returns:
            Configuration error.

        Responsibility:
            Create error for duplicate output path. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError.duplicate_output_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `duplicate_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `duplicate_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `duplicate_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `duplicate_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `duplicate_output_path`

        State and side effects:
            mutates message.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError.duplicate_output_path`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        message = f"Multiple formatter outputs target the same path {output_path}: {formatter_labels}"
        return cls(message)

    @classmethod
    def missing_output_directory(
        cls,
        *,
        cli_flag: str,
        output_dir: Path,
    ) -> CucumberFormatterConfigurationError:
        """
        Create error for missing output directory.

        Returns:
            Configuration error.

        Responsibility:
            Create error for missing output directory. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError.missing_output_directory`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `missing_output_directory`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `missing_output_directory`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `missing_output_directory`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `missing_output_directory`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `missing_output_directory`

        State and side effects:
            mutates message.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError.missing_output_directory`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        message = f"Formatter output directory does not exist for {cli_flag}: {output_dir}"
        return cls(message)

    @classmethod
    def terminal_output_conflict(
        cls,
        *,
        formatter_labels: str,
    ) -> CucumberFormatterConfigurationError:
        """
        Create error for terminal output conflict.

        Returns:
            Configuration error.

        Responsibility:
            Create error for terminal output conflict. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError.terminal_output_conflict`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `terminal_output_conflict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `terminal_output_conflict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `terminal_output_conflict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `terminal_output_conflict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `terminal_output_conflict`

        State and side effects:
            mutates message.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterConfigurationError.terminal_output_conflict`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        message = f"Only one terminal-output formatter may be active per run: {formatter_labels}"
        return cls(message)


def format_requested_cucumber_formatter_labels(
    formatter_requests: tuple[CucumberFormatterRequest, ...] | list[CucumberFormatterRequest],
) -> str:
    """
    Format requested cucumber formatter labels.

    Returns:
        Comma-separated formatter labels.

    Responsibility:
        Format requested cucumber formatter labels. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.format_requested_cucumber_formatter_labels` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `format_requested_cucumber_formatter_labels`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `format_requested_cucumber_formatter_labels`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `format_requested_cucumber_formatter_labels`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `format_requested_cucumber_formatter_labels`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `format_requested_cucumber_formatter_labels`

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
        #arch-eval:locational_stability=4

    """
    return ", ".join(request.cli_flag for request in formatter_requests)


def terminal_output_formatter_requests(
    formatter_requests: list[CucumberFormatterRequest],
) -> list[CucumberFormatterRequest]:
    """
    Filter terminal output formatter requests.

    Returns:
        List of terminal output formatter requests.

    Responsibility:
        Filter terminal output formatter requests. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.terminal_output_formatter_requests` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `terminal_output_formatter_requests`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `terminal_output_formatter_requests`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `terminal_output_formatter_requests`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `terminal_output_formatter_requests`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `terminal_output_formatter_requests`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4

    """
    return [request for request in formatter_requests if request.output_path is None]


def normalize_cucumber_formatter_output_key(output_path: Path) -> str:
    """
    Normalize cucumber formatter output key.

    Returns:
        Normalized output path string.

    Responsibility:
        Normalize cucumber formatter output key. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.normalize_cucumber_formatter_output_key` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - os.path.normcase: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - output_path.resolve: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `normalize_cucumber_formatter_output_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `normalize_cucumber_formatter_output_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `normalize_cucumber_formatter_output_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `normalize_cucumber_formatter_output_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `normalize_cucumber_formatter_output_key`

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
        #arch-eval:locational_stability=4

    """
    return os.path.normcase(str(output_path.resolve()))


def _read_template_asset(package: str, template_name: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.session._read_template_asset` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._read_template_asset` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - files.joinpath: collaborator call used by this boundary
        - files: collaborator call used by this boundary
        - template.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `_read_template_asset`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_read_template_asset`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_read_template_asset`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_read_template_asset`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_read_template_asset`

    State and side effects:
        mutates template.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session._read_template_asset` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """
    template = cast("Traversable", files(package).joinpath(template_name))
    return template.read_text(encoding="utf-8")


def _formatter_options_requested(config: Config) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.session._formatter_options_requested` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._formatter_options_requested` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - any: collaborator call used by this boundary
        - option_name.startswith: collaborator call used by this boundary
        - option_values.items: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `_formatter_options_requested`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_formatter_options_requested`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_formatter_options_requested`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_formatter_options_requested`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_formatter_options_requested`

    State and side effects:
        mutates option_values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session._formatter_options_requested` keeps its documented import
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
        #arch-eval:locational_stability=4
    """
    option_values = cast("dict[str, object]", getattr(getattr(config, "option", None), "__dict__", {}))
    return any(
        option_name.startswith("cucumber_")
        and option_name != "cucumber_html_path"
        and option_value not in {None, False}
        for option_name, option_value in option_values.items()
    )


def _formatter_hook_proxy(pluginmanager: PytestPluginManager | None) -> object | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.session._formatter_hook_proxy` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._formatter_hook_proxy` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `_formatter_hook_proxy`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_formatter_hook_proxy`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_formatter_hook_proxy`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_formatter_hook_proxy`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_formatter_hook_proxy`

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
        #arch-eval:locational_stability=4
    """
    return getattr(pluginmanager, "hook", None)


def _resolve_formatter_request_hook(config: Config) -> _FormatterRequestHook | None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.session._resolve_formatter_request_hook` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._resolve_formatter_request_hook` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _formatter_hook_proxy: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - hasattr: collaborator call used by this boundary
        - _formatter_options_requested: collaborator call used by this boundary
        - RuntimeError: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `_resolve_formatter_request_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_resolve_formatter_request_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_resolve_formatter_request_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_resolve_formatter_request_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `_resolve_formatter_request_hook`

    State and side effects:
        mutates hook, msg.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session._resolve_formatter_request_hook` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
    hook = _formatter_hook_proxy(getattr(config, "pluginmanager", None))
    if hook is None or not hasattr(hook, "pytest_bdd_cucumber_formatter_request"):
        if _formatter_options_requested(config):
            msg = (
                "Cucumber formatter plugins are unavailable because the formatter request hook registry "
                "was not configured."
            )
            raise RuntimeError(msg)
        return None
    return cast("_FormatterRequestHook", hook)


def _require_formatter_runtime_assets_hook(pluginmanager: PytestPluginManager | None) -> _FormatterRuntimeAssetsHook:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.session._require_formatter_runtime_assets_hook` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._require_formatter_runtime_assets_hook` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _formatter_hook_proxy: collaborator call used by this boundary
        - hasattr: collaborator call used by this boundary
        - RuntimeError: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `_require_formatter_runtime_assets_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_require_formatter_runtime_assets_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_require_formatter_runtime_assets_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_require_formatter_runtime_assets_hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `_require_formatter_runtime_assets_hook`

    State and side effects:
        mutates hook, msg.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session._require_formatter_runtime_assets_hook` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
    hook = _formatter_hook_proxy(pluginmanager)
    if hook is None or not hasattr(hook, "pytest_bdd_cucumber_formatter_runtime_assets"):
        msg = (
            "Cucumber formatter runtime assets are unavailable because the formatter runtime-assets hook registry "
            "was not configured."
        )
        raise RuntimeError(msg)
    return cast("_FormatterRuntimeAssetsHook", hook)


def resolve_requested_cucumber_formatters(
    config: Config,
    *,
    resolve_output_path: ResolveOutputPath,
) -> tuple[CucumberFormatterRequest, ...]:
    """
    Resolve requested cucumber formatters.

    Returns:
        Tuple of cucumber formatter requests.

    Responsibility:
        Resolve requested cucumber formatters. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.resolve_requested_cucumber_formatters` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _resolve_formatter_request_hook: collaborator call used by this boundary
        - requested_formatters.extend: collaborator call used by this boundary
        - formatter_request_hook.pytest_bdd_cucumber_formatter_request: collaborator call used by this boundary
        - _order_requested_cucumber_formatters: collaborator call used by this boundary
        - validate_requested_cucumber_formatters: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `resolve_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `resolve_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `resolve_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `resolve_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `resolve_requested_cucumber_formatters`

    State and side effects:
        mutates requested_formatters, formatter_request_hook.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session.resolve_requested_cucumber_formatters` keeps its
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
    requested_formatters: list[CucumberFormatterRequest] = []
    formatter_request_hook = _resolve_formatter_request_hook(config)
    if formatter_request_hook is not None:
        requested_formatters.extend(
            formatter_request
            for formatter_request in formatter_request_hook.pytest_bdd_cucumber_formatter_request(
                config=config,
                resolve_output_path=resolve_output_path,
            )
            if formatter_request is not None
        )
    requested_formatters = _order_requested_cucumber_formatters(requested_formatters)
    validate_requested_cucumber_formatters(requested_formatters)
    return tuple(requested_formatters)


def _order_requested_cucumber_formatters(
    requested_formatters: list[CucumberFormatterRequest],
) -> list[CucumberFormatterRequest]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.session._order_requested_cucumber_formatters` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session._order_requested_cucumber_formatters` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `_order_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_order_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_order_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_order_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `_order_requested_cucumber_formatters`

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
        #arch-eval:locational_stability=4
    """
    return sorted(
        requested_formatters,
        key=lambda formatter_request: (
            formatter_request.discovery_order,
            formatter_request.formatter,
            formatter_request.plugin_module,
        ),
    )


def validate_requested_cucumber_formatters(
    formatter_requests: list[CucumberFormatterRequest],
) -> None:
    """
    Validate requested cucumber formatters.

    Raises:
        terminal_output_conflict: If the operation cannot be completed.
        duplicate_output_path: If the operation cannot be completed.
        missing_output_directory: If the operation cannot be completed.

    Responsibility:
        Validate requested cucumber formatters. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.validate_requested_cucumber_formatters` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - len: collaborator call used by this boundary
        - format_requested_cucumber_formatter_labels: collaborator call used by this boundary
        - terminal_output_formatter_requests: collaborator call used by this boundary
        - CucumberFormatterConfigurationError.terminal_output_conflict: collaborator call used by this boundary
        - output_path.parent.exists: collaborator call used by this boundary
        - CucumberFormatterConfigurationError.missing_output_directory: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `validate_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `validate_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `validate_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `validate_requested_cucumber_formatters`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `validate_requested_cucumber_formatters`

    State and side effects:
        mutates terminal_requests, requests_by_output_key, output_path, duplicate_requests, duplicate_output_path.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session.validate_requested_cucumber_formatters` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises CucumberFormatterConfigurationError.terminal_output_conflict,
        CucumberFormatterConfigurationError.missing_output_directory,
        CucumberFormatterConfigurationError.duplicate_output_path; callers must treat these as boundary failures.

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
    terminal_requests = terminal_output_formatter_requests(formatter_requests)
    if len(terminal_requests) > 1:
        raise CucumberFormatterConfigurationError.terminal_output_conflict(
            formatter_labels=format_requested_cucumber_formatter_labels(terminal_requests),
        )

    requests_by_output_key: dict[str, list[CucumberFormatterRequest]] = {}
    for formatter_request in formatter_requests:
        output_path = formatter_request.output_path
        if output_path is None:
            continue
        if not output_path.parent.exists():
            raise CucumberFormatterConfigurationError.missing_output_directory(
                cli_flag=formatter_request.cli_flag,
                output_dir=output_path.parent,
            )
        requests_by_output_key.setdefault(normalize_cucumber_formatter_output_key(output_path), []).append(
            formatter_request,
        )

    duplicate_requests = next(
        (request_group for request_group in requests_by_output_key.values() if len(request_group) > 1),
        None,
    )
    if duplicate_requests is not None:
        duplicate_output_path = duplicate_requests[0].output_path or Path("<terminal>")
        raise CucumberFormatterConfigurationError.duplicate_output_path(
            output_path=duplicate_output_path,
            formatter_labels=format_requested_cucumber_formatter_labels(duplicate_requests),
        )


def load_live_formatter_bridge_template() -> str:
    """
    Load live formatter bridge template.

    Returns:
        Template content.

    Responsibility:
        Load live formatter bridge template. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.load_live_formatter_bridge_template` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _read_template_asset: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `load_live_formatter_bridge_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `load_live_formatter_bridge_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `load_live_formatter_bridge_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `load_live_formatter_bridge_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `load_live_formatter_bridge_template`

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
        #arch-eval:locational_stability=4

    """
    return _read_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates",
        "live_formatter_bridge.mjs.j2",
    )


def load_formatter_adapter_support_template() -> str:
    """
    Load formatter adapter support template.

    Returns:
        Template content.

    Responsibility:
        Load formatter adapter support template. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.load_formatter_adapter_support_template` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_formatter_adapter_support_template: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `load_formatter_adapter_support_template`

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
        #arch-eval:locational_stability=4

    """
    return _load_formatter_adapter_support_template()


def load_formatter_adapter_template(template_name: str) -> str:
    """
    Load formatter adapter template.

    Returns:
        Template content.

    Responsibility:
        Load formatter adapter template. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.load_formatter_adapter_template` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_formatter_adapter_template: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `load_formatter_adapter_template`

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
        #arch-eval:locational_stability=4

    """
    return _load_formatter_adapter_template(template_name)


def render_live_formatter_bridge() -> str:
    """
    Render live formatter bridge.

    Returns:
        Rendered bridge.

    Responsibility:
        Render live formatter bridge. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.render_live_formatter_bridge` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - load_live_formatter_bridge_template: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `render_live_formatter_bridge`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `render_live_formatter_bridge`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `render_live_formatter_bridge`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `render_live_formatter_bridge`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `render_live_formatter_bridge`

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
        #arch-eval:locational_stability=4

    """
    return load_live_formatter_bridge_template()


def render_live_formatter_runtime_assets(
    formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    *,
    pluginmanager: PytestPluginManager | None,
) -> dict[str, str]:
    """
    Render live formatter runtime assets.

    Returns:
        Runtime assets dictionary.

    Responsibility:
        Render live formatter runtime assets. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.session.render_live_formatter_runtime_assets` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - render_live_formatter_bridge: collaborator call used by this boundary
        - _require_formatter_runtime_assets_hook: collaborator call used by this boundary
        - runtime_assets_hook.pytest_bdd_cucumber_formatter_runtime_assets: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - assets.update: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references
          `render_live_formatter_runtime_assets`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `render_live_formatter_runtime_assets`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `render_live_formatter_runtime_assets`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `render_live_formatter_runtime_assets`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `render_live_formatter_runtime_assets`

    State and side effects:
        mutates assets, module_requests, runtime_assets_hook.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.session.render_live_formatter_runtime_assets` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    """Render live formatter runtime assets."""
    assets = {"render_cucumber_formatters.js": render_live_formatter_bridge()}
    module_requests = [
        formatter_request
        for formatter_request in formatter_requests
        if formatter_request.runtime_kind == FormatterRuntimeKind.module
    ]
    if not module_requests:
        return assets

    runtime_assets_hook = _require_formatter_runtime_assets_hook(pluginmanager)
    for formatter_request in module_requests:
        for rendered_assets in runtime_assets_hook.pytest_bdd_cucumber_formatter_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=tuple(formatter_requests),
        ):
            if rendered_assets:
                assets.update(rendered_assets)
    return assets
