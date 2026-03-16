from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytest_bdd.plugin.cucumber_formatter_support.base import FormatterOutputMode
from pytest_bdd.plugin.cucumber_formatter_support.registry import FormatterPluginCatalog

if TYPE_CHECKING:
    from collections.abc import Sequence

FormatterDefinition = tuple[str, str, str, str, str]

CAPTURE_OPTION_PREFIXES = ("--capture=",)
CAPTURE_OPTION_FLAGS = frozenset({"-s", "--capture"})


def cucumber_formatter_definitions() -> tuple[FormatterDefinition, ...]:
    catalog = FormatterPluginCatalog.discover()
    return tuple(
        (
            plugin.option_attr,
            plugin.cli_flag,
            plugin.formatter,
            plugin.package_name,
            plugin.output_mode.value,
        )
        for plugin in catalog.plugins
    )


def register_cucumber_formatter_options(parser) -> None:
    catalog = FormatterPluginCatalog.discover()
    group = parser.getgroup("bdd", "Cucumber Formatters")
    for plugin in catalog.plugins:
        addoption_kwargs = plugin.build_addoption_kwargs()
        cli_aliases = addoption_kwargs.pop("cli_aliases", ())
        group.addoption(plugin.cli_flag, *cli_aliases, **addoption_kwargs)


def terminal_formatter_cli_flags() -> frozenset[str]:
    catalog = FormatterPluginCatalog.discover()
    flags: set[str] = set()
    for plugin in catalog.plugins:
        if plugin.output_mode == FormatterOutputMode.stdout:
            flags.add(plugin.cli_flag)
        elif plugin.output_mode == FormatterOutputMode.optional_path:
            flags.update({plugin.cli_flag, f"{plugin.cli_flag}=-"})
    return frozenset(flags)


def terminal_formatter_flags_requested(args: Sequence[str]) -> bool:
    requested_stdout_flags = terminal_formatter_cli_flags()
    for arg in args:
        if arg in requested_stdout_flags:
            return True
        if arg.startswith("--cucumber-usage=") and arg != "--cucumber-usage=-":
            continue
    return False


def pytest_capture_already_configured(args: Sequence[str]) -> bool:
    return any(
        arg in CAPTURE_OPTION_FLAGS or any(arg.startswith(prefix) for prefix in CAPTURE_OPTION_PREFIXES) for arg in args
    )


def any_cucumber_formatter_requested(options: Any) -> bool:
    return any(
        getattr(options, option_attr, None) not in (None, False)
        for option_attr, *_rest in cucumber_formatter_definitions()
    )
