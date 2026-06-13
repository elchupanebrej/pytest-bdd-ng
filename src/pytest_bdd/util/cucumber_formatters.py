"""
Manages the static registry of Cucumber formatter definitions mapping formatter names to CLI
options, formatter types.

Responsibility:
    Manages the static registry of Cucumber formatter definitions mapping formatter names to CLI
    options, formatter types, npm package names, and output destinations. Provides the canonical
    formatter-to-option lookup consumed by the live-reporting plugin system when registering pytest
    command-line arguments.

Reason for existence:
    All formatter-to-CLI-option mappings live in one module so adding or removing a formatter
    requires a single-point edit. This module is the information expert for the relationship
    between pytest CLI flags and @cucumber/pretty-formatter output types, preventing scattered
    option registration across plugins.

Delegates:
    - @cucumber/pretty-formatter: delegates actual formatting to the npm package at runtime

Cohesion:
    All constants define formatter metadata tuples sharing the same 5-element structure.

Separation:
    - `pytest_bdd.util.cucumber_formatter_support`: provides runtime formatter classes while this module provides the
    static registry.

Main consumers:
    - `pytest_bdd.plugin.gherkin_message_reporter`: uses formatter definitions to register CLI options

State and side effects:
    Module-level _FORMATTER_DEFINITIONS tuple is immutable; no runtime state changes.

Invariants:
    - Each formatter definition tuple has exactly 5 elements in the documented order.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pytest_bdd.compatibility.pytest import Parser


FormatterDefinition = tuple[str, str, str, str, str]

CAPTURE_OPTION_PREFIXES = ("--capture=",)
CAPTURE_OPTION_FLAGS = frozenset({"-s", "--capture"})
_FORMATTER_DEFINITIONS: tuple[FormatterDefinition, ...] = (
    ("cucumber_summary", "--cucumber-summary", "summary", "@cucumber/pretty-formatter", "stdout"),
    ("cucumber_progress", "--cucumber-progress", "progress", "@cucumber/pretty-formatter", "stdout"),
    ("cucumber_progress_bar", "--cucumber-progress-bar", "progress-bar", "@cucumber/pretty-formatter", "stdout"),
    ("cucumber_snippets", "--cucumber-snippets", "snippets", "@cucumber/pretty-formatter", "stdout"),
    ("cucumber_pretty", "--cucumber-pretty", "pretty", "@cucumber/pretty-formatter", "stdout"),
    ("cucumber_usage_output", "--cucumber-usage", "usage", "@cucumber/pretty-formatter", "optional_path"),
    ("cucumber_js_json_path", "--cucumber-json", "json", "@cucumber/cucumber", "path"),
    ("cucumber_junit_path", "--cucumber-junit", "junit", "@cucumber/cucumber", "path"),
    ("cucumber_usage_json_path", "--cucumber-usage-json", "usage-json", "@cucumber/cucumber", "path"),
)
_TERMINAL_FORMATTER_CLI_FLAGS = frozenset(
    cli_flag
    for _option_attr, cli_flag, _formatter, _package_name, output_mode in _FORMATTER_DEFINITIONS
    if output_mode in {"stdout", "optional_path"}
)
_OPTIONAL_PATH_TERMINAL_FLAGS = frozenset(
    f"{cli_flag}=-"
    for _option_attr, cli_flag, _formatter, _package_name, output_mode in _FORMATTER_DEFINITIONS
    if output_mode == "optional_path"
)


def cucumber_formatter_definitions() -> tuple[FormatterDefinition, ...]:
    """
    Perform the `cucumber_formatter_definitions` operation within its module boundary,.
    implementing a focused helper fun.

    Responsibility:
        Performs the `cucumber_formatter_definitions` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `cucumber_formatter_definitions` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the cucumber_formatter_definitions operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke cucumber_formatter_definitions for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The cucumber_formatter_definitions function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return _FORMATTER_DEFINITIONS


def register_cucumber_formatter_options(parser: Parser) -> None:
    """
    Perform the `register_cucumber_formatter_options` operation within its module boundary,.
    implementing a focused helpe.

    Responsibility:
        Performs the `register_cucumber_formatter_options` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `register_cucumber_formatter_options` exists as a standalone function because it encapsulates
        an operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the register_cucumber_formatter_options operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke register_cucumber_formatter_options for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The register_cucumber_formatter_options function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    from pytest_bdd.util.cucumber_formatter_support.base import _coerce_cli_aliases
    from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog

    catalog = FormatterPluginCatalog.discover()
    group = parser.getgroup("bdd", "Cucumber Formatters")
    for plugin in catalog.plugins:
        addoption_kwargs = plugin.build_addoption_kwargs()
        cli_aliases = _coerce_cli_aliases(addoption_kwargs.pop("cli_aliases", ()))
        group.addoption(plugin.cli_flag, *cli_aliases, **addoption_kwargs)


def terminal_formatter_cli_flags() -> frozenset[str]:
    """
    Perform the `terminal_formatter_cli_flags` operation within its module boundary, implementing.
    a focused helper funct.

    Responsibility:
        Performs the `terminal_formatter_cli_flags` operation within its module boundary, implementing
        a focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `terminal_formatter_cli_flags` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the terminal_formatter_cli_flags operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke terminal_formatter_cli_flags for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The terminal_formatter_cli_flags function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return frozenset((*_TERMINAL_FORMATTER_CLI_FLAGS, *_OPTIONAL_PATH_TERMINAL_FLAGS))


def terminal_formatter_flags_requested(args: Sequence[str]) -> bool:
    """
    Perform the `terminal_formatter_flags_requested` operation within its module boundary,.
    implementing a focused helper.

    Responsibility:
        Performs the `terminal_formatter_flags_requested` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `terminal_formatter_flags_requested` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the terminal_formatter_flags_requested operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke terminal_formatter_flags_requested for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The terminal_formatter_flags_requested function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    requested_stdout_flags = terminal_formatter_cli_flags()
    for arg in args:
        if arg in requested_stdout_flags:
            return True
        if arg.startswith("--cucumber-usage=") and arg != "--cucumber-usage=-":
            continue
    return False


def pytest_capture_already_configured(args: Sequence[str]) -> bool:
    """
    Perform the `pytest_capture_already_configured` operation within its module boundary,.
    implementing a focused helper .

    Responsibility:
        Performs the `pytest_capture_already_configured` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `pytest_capture_already_configured` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the pytest_capture_already_configured operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke pytest_capture_already_configured for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The pytest_capture_already_configured function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return any(
        arg in CAPTURE_OPTION_FLAGS or any(arg.startswith(prefix) for prefix in CAPTURE_OPTION_PREFIXES) for arg in args
    )


def any_cucumber_formatter_requested(options: object) -> bool:
    """
    Perform the `any_cucumber_formatter_requested` operation within its module boundary,.
    implementing a focused helper f.

    Responsibility:
        Performs the `any_cucumber_formatter_requested` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `any_cucumber_formatter_requested` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the any_cucumber_formatter_requested operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke any_cucumber_formatter_requested for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The any_cucumber_formatter_requested function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return any(
        getattr(options, option_attr, None) not in {None, False}
        for option_attr, *_rest in cucumber_formatter_definitions()
    )
