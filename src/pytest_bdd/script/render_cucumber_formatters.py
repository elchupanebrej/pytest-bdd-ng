"""Render cucumber formatter outputs from an existing NDJSON message stream."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pytest_bdd.plugin.cucumber_formatter_support.base import FormatterReporterPlugin, _coerce_cli_aliases
from pytest_bdd.plugin.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer import (
    CucumberFormatterConfigurationError,
    StandaloneCucumberFormatterRenderer,
)
from pytest_bdd.util.cucumber_formatters import any_cucumber_formatter_requested


def _require_str(value: object, field_name: str) -> str:
    if isinstance(value, str):
        return value
    message = f"Formatter option field {field_name} must be a string: {value!r}"
    raise TypeError(message)


def _register_formatter_argument(parser: argparse.ArgumentParser, plugin: FormatterReporterPlugin) -> None:
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
    sys.stderr.write(message)
    sys.stderr.write("\n")


def _build_formatter_option_values(
    args: argparse.Namespace,
    *,
    catalog: FormatterPluginCatalog,
) -> dict[str, object]:
    return {plugin.option_attr: getattr(args, plugin.option_attr) for plugin in catalog.plugins}


def main(argv: list[str] | None = None) -> int:
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
