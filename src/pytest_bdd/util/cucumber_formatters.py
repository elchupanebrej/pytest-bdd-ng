"""
Provide cucumber formatters helpers.

Responsibility:
    Provide cucumber formatters helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.cucumber_formatters` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - cucumber_formatter_definitions: owns nested behavior below this boundary
    - register_cucumber_formatter_options: owns nested behavior below this boundary
    - terminal_formatter_cli_flags: owns nested behavior below this boundary
    - terminal_formatter_flags_requested: owns nested behavior below this boundary
    - pytest_capture_already_configured: owns nested behavior below this boundary
    - any_cucumber_formatter_requested: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `cucumber_formatters`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `cucumber_formatters`

State and side effects:
    mutates FormatterDefinition, CAPTURE_OPTION_PREFIXES, CAPTURE_OPTION_FLAGS, _FORMATTER_DEFINITIONS,
    _TERMINAL_FORMATTER_CLI_FLAGS; depends on __future__.annotations, typing.TYPE_CHECKING, collections.abc.Sequence,
    pytest_bdd.compatibility.pytest.Parser, pytest_bdd.util.cucumber_formatter_support.base._coerce_cli_aliases.

Invariants:
    - `pytest_bdd.util.cucumber_formatters` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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
    Return all cucumber formatter definitions.

    Returns:
        Tuple of formatter definitions.

    Responsibility:
        Return all cucumber formatter definitions. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.cucumber_formatters.cucumber_formatter_definitions`
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
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `cucumber_formatter_definitions`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `cucumber_formatter_definitions`

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
        #arch-eval:locational_stability=3

    """
    return _FORMATTER_DEFINITIONS


def register_cucumber_formatter_options(parser: Parser) -> None:
    """
    Register cucumber formatter options with pytest.

    Responsibility:
        Register cucumber formatter options with pytest. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatters.register_cucumber_formatter_options` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - FormatterPluginCatalog.discover: collaborator call used by this boundary
        - parser.getgroup: collaborator call used by this boundary
        - plugin.build_addoption_kwargs: collaborator call used by this boundary
        - _coerce_cli_aliases: collaborator call used by this boundary
        - addoption_kwargs.pop: collaborator call used by this boundary
        - group.addoption: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `register_cucumber_formatter_options`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references
          `register_cucumber_formatter_options`

    State and side effects:
        mutates catalog, group, addoption_kwargs, cli_aliases; depends on
        pytest_bdd.util.cucumber_formatter_support.base._coerce_cli_aliases,
        pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.

    Invariants:
        - `pytest_bdd.util.cucumber_formatters.register_cucumber_formatter_options` keeps its documented import path,
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
    from pytest_bdd.util.cucumber_formatter_support.base import _coerce_cli_aliases  # noqa: PLC0415
    from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog  # noqa: PLC0415

    catalog = FormatterPluginCatalog.discover()
    group = parser.getgroup("bdd", "Cucumber Formatters")
    for plugin in catalog.plugins:
        addoption_kwargs = plugin.build_addoption_kwargs()
        cli_aliases = _coerce_cli_aliases(addoption_kwargs.pop("cli_aliases", ()))
        group.addoption(plugin.cli_flag, *cli_aliases, **addoption_kwargs)


def terminal_formatter_cli_flags() -> frozenset[str]:
    """
    Return all terminal formatter CLI flags.

    Returns:
        Frozenset of CLI flag strings.

    Responsibility:
        Return all terminal formatter CLI flags. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.cucumber_formatters.terminal_formatter_cli_flags`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - frozenset: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `terminal_formatter_cli_flags`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `terminal_formatter_cli_flags`

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
    return frozenset((*_TERMINAL_FORMATTER_CLI_FLAGS, *_OPTIONAL_PATH_TERMINAL_FLAGS))


def terminal_formatter_flags_requested(args: Sequence[str]) -> bool:
    """
    Check if any terminal formatter flags are requested.

    Args:
        args: Command-line arguments.

    Returns:
        True if terminal formatter flag is present.

    Responsibility:
        Check if any terminal formatter flags are requested. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatters.terminal_formatter_flags_requested` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - terminal_formatter_cli_flags: collaborator call used by this boundary
        - arg.startswith: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `terminal_formatter_flags_requested`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references
          `terminal_formatter_flags_requested`

    State and side effects:
        mutates requested_stdout_flags.

    Invariants:
        - `pytest_bdd.util.cucumber_formatters.terminal_formatter_flags_requested` keeps its documented import path,
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
    requested_stdout_flags = terminal_formatter_cli_flags()
    for arg in args:
        if arg in requested_stdout_flags:
            return True
        if arg.startswith("--cucumber-usage=") and arg != "--cucumber-usage=-":
            continue
    return False


def pytest_capture_already_configured(args: Sequence[str]) -> bool:
    """
    Check if pytest capture is already configured.

    Args:
        args: Command-line arguments.

    Returns:
        True if capture is already configured.

    Responsibility:
        Check if pytest capture is already configured. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatters.pytest_capture_already_configured` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `pytest_capture_already_configured`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `pytest_capture_already_configured`

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
    return any(
        arg in CAPTURE_OPTION_FLAGS or any(arg.startswith(prefix) for prefix in CAPTURE_OPTION_PREFIXES) for arg in args
    )


def any_cucumber_formatter_requested(options: object) -> bool:
    """
    Check if any cucumber formatter is requested.

    Returns:
        True if any cucumber formatter is requested.

    Responsibility:
        Check if any cucumber formatter is requested. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.cucumber_formatters.any_cucumber_formatter_requested`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - any: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - cucumber_formatter_definitions: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `any_cucumber_formatter_requested`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `any_cucumber_formatter_requested`

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
    return any(
        getattr(options, option_attr, None) not in {None, False}
        for option_attr, *_rest in cucumber_formatter_definitions()
    )
