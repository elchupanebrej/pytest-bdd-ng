"""
Render cucumber formatter outputs from an existing NDJSON message stream.

Responsibility:
    Render cucumber formatter outputs from an existing NDJSON message stream. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.render_cucumber_formatters` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _require_str: owns nested behavior below this boundary
    - _register_formatter_argument: owns nested behavior below this boundary
    - parse_args: owns nested behavior below this boundary
    - _emit_error: owns nested behavior below this boundary
    - _build_formatter_option_values: owns nested behavior below this boundary
    - main: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates message, catalog, args, messages_path, addoption_kwargs; depends on __future__.annotations, argparse, sys,
    pathlib.Path, pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.CucumberFormatterConfigurationError.

Invariants:
    - `pytest_bdd.script.render_cucumber_formatters` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError, SystemExit; callers must treat these as boundary failures.

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

import argparse
import sys
from pathlib import Path

from pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer import (
    CucumberFormatterConfigurationError,
    StandaloneCucumberFormatterRenderer,
)
from pytest_bdd.util.cucumber_formatter_support.base import FormatterReporterPlugin, _coerce_cli_aliases
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.util.cucumber_formatters import any_cucumber_formatter_requested


def _require_str(value: object, field_name: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.render_cucumber_formatters._require_str` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.render_cucumber_formatters._require_str` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

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
        - `pytest_bdd.script.render_cucumber_formatters._require_str` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    if isinstance(value, str):
        return value
    message = f"Formatter option field {field_name} must be a string: {value!r}"
    raise TypeError(message)


def _register_formatter_argument(parser: argparse.ArgumentParser, plugin: FormatterReporterPlugin) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.render_cucumber_formatters._register_formatter_argument` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.render_cucumber_formatters._register_formatter_argument` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _require_str: collaborator call used by this boundary
        - parser.add_argument: collaborator call used by this boundary
        - plugin.build_addoption_kwargs: collaborator call used by this boundary
        - _coerce_cli_aliases: collaborator call used by this boundary
        - addoption_kwargs.pop: collaborator call used by this boundary
        - addoption_kwargs.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates addoption_kwargs, cli_aliases, dest, help_text, action.

    Invariants:
        - `pytest_bdd.script.render_cucumber_formatters._register_formatter_argument` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    addoption_kwargs = plugin.build_addoption_kwargs()
    cli_aliases = _coerce_cli_aliases(addoption_kwargs.pop("cli_aliases", ()))
    dest = _require_str(addoption_kwargs["dest"], "dest")
    help_text = _require_str(addoption_kwargs["help"], "help")
    action = _require_str(addoption_kwargs["action"], "action")
    if action == "store_true":
        parser.add_argument(
            plugin.cli_flag,
            *cli_aliases,
            dest=dest,
            help=help_text,
            action="store_true",
            default=False,
        )
        return
    if action == "store":
        metavar = _require_str(addoption_kwargs["metavar"], "metavar")
        if addoption_kwargs.get("nargs") == "?":
            const = _require_str(addoption_kwargs["const"], "const")
            parser.add_argument(
                plugin.cli_flag,
                *cli_aliases,
                dest=dest,
                help=help_text,
                action="store",
                nargs="?",
                const=const,
                metavar=metavar,
                default=None,
            )
            return
        parser.add_argument(
            plugin.cli_flag,
            *cli_aliases,
            dest=dest,
            help=help_text,
            action="store",
            metavar=metavar,
            default=None,
        )
        return
    message = f"Unsupported formatter option action: {action!r}"
    raise TypeError(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Command-line arguments (defaults to sys.argv).

    Returns:
        Parsed arguments namespace.

    Responsibility:
        Parse command-line arguments. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.render_cucumber_formatters.parse_args` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - FormatterPluginCatalog.discover: collaborator call used by this boundary
        - argparse.ArgumentParser: collaborator call used by this boundary
        - parser.add_argument: collaborator call used by this boundary
        - _register_formatter_argument: collaborator call used by this boundary
        - parser.parse_args: collaborator call used by this boundary
        - any_cucumber_formatter_requested: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `parse_args`
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `parse_args`
        - src/pytest_bdd/scenario.py: imports or references `parse_args`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `parse_args`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `parse_args`

    State and side effects:
        mutates catalog, parser, args.

    Invariants:
        - `pytest_bdd.script.render_cucumber_formatters.parse_args` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    catalog = FormatterPluginCatalog.discover()
    parser = argparse.ArgumentParser(description="Render cucumber formatter outputs from an NDJSON message stream")
    parser.add_argument(
        "--messages-ndjson",
        dest="messages_ndjson_path",
        type=Path,
        required=True,
        help="Path to an existing canonical cucumber messages NDJSON file.",
    )
    for plugin in catalog.plugins:
        _register_formatter_argument(parser, plugin)
    args = parser.parse_args(argv)

    if not any_cucumber_formatter_requested(args):
        parser.error("at least one cucumber formatter output flag is required")
    return args


def _emit_error(message: str) -> None:
    """
    Emit error message to stderr.

    Responsibility:
        Emit error message to stderr. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.render_cucumber_formatters._emit_error` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sys.stderr.write: collaborator call used by this boundary

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
    sys.stderr.write(message)
    sys.stderr.write("\n")


def _build_formatter_option_values(
    args: argparse.Namespace,
    *,
    catalog: FormatterPluginCatalog,
) -> dict[str, object]:
    """
    Build formatter option values from parsed args.

    Args:
        args: Parsed arguments.
        catalog: Plugin catalog.

    Returns:
        Dictionary of option values.

    Responsibility:
        Build formatter option values from parsed args. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.render_cucumber_formatters._build_formatter_option_values` because it keeps the nearest code,
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
    return {plugin.option_attr: getattr(args, plugin.option_attr) for plugin in catalog.plugins}


def main(argv: list[str] | None = None) -> int:
    """
    Run the cucumber formatter renderer.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code.

    Raises:
        SystemExit: If the operation cannot be completed.

    Responsibility:
        Run the cucumber formatter renderer. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.render_cucumber_formatters.main` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _emit_error: collaborator call used by this boundary
        - parse_args: collaborator call used by this boundary
        - FormatterPluginCatalog.discover: collaborator call used by this boundary
        - StandaloneCucumberFormatterRenderer.discover: collaborator call used by this boundary
        - Path.cwd.resolve: collaborator call used by this boundary
        - Path.cwd: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `main`
        - src/pytest_bdd/script/__init__.py: imports or references `main`
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__main__.py: imports or references `main`

    State and side effects:
        mutates messages_path, args, catalog, renderer, rootpath.

    Invariants:
        - `pytest_bdd.script.render_cucumber_formatters.main` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises SystemExit; callers must treat these as boundary failures.

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
    args = parse_args(argv)
    catalog = FormatterPluginCatalog.discover()
    renderer = StandaloneCucumberFormatterRenderer.discover(catalog=catalog)
    rootpath = Path.cwd().resolve()
    messages_path = args.messages_ndjson_path
    if not messages_path.is_absolute():
        messages_path = (rootpath / messages_path).resolve()
    if not messages_path.exists():
        _emit_error(f"Messages NDJSON file was not found: {messages_path}")
        return 1

    args.messages_ndjson_path = messages_path
    try:
        render_result = renderer.render_from_messages_path(
            messages_path,
            rootpath=rootpath,
            formatter_option_values=_build_formatter_option_values(args, catalog=catalog),
        )
    except CucumberFormatterConfigurationError as exc:
        _emit_error(str(exc))
        raise SystemExit(1) from exc
    except (OSError, TypeError, ValueError) as exc:
        _emit_error(f"Unable to parse cucumber messages from {messages_path}: {exc}")
        return 1

    return 0 if render_result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
