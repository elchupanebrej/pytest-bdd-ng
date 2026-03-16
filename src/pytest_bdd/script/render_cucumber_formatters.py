"""Render cucumber formatter outputs from an existing NDJSON message stream."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pytest_bdd.plugin.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer import (
    CucumberFormatterConfigurationError,
    StandaloneCucumberFormatterRenderer,
)
from pytest_bdd.util.cucumber_formatters import any_cucumber_formatter_requested


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
        argparse_kwargs = dict(plugin.build_addoption_kwargs())
        cli_aliases = tuple(argparse_kwargs.pop("cli_aliases", ()))
        parser.add_argument(plugin.cli_flag, *cli_aliases, **argparse_kwargs)
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
