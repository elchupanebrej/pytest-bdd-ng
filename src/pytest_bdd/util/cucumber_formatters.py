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
    return _FORMATTER_DEFINITIONS


def register_cucumber_formatter_options(parser: Parser) -> None:
    from pytest_bdd.plugin.cucumber_formatter_support.base import _coerce_cli_aliases
    from pytest_bdd.plugin.cucumber_formatter_support.registry import FormatterPluginCatalog

    catalog = FormatterPluginCatalog.discover()
    group = parser.getgroup("bdd", "Cucumber Formatters")
    for plugin in catalog.plugins:
        addoption_kwargs = plugin.build_addoption_kwargs()
        cli_aliases = _coerce_cli_aliases(addoption_kwargs.pop("cli_aliases", ()))
        group.addoption(plugin.cli_flag, *cli_aliases, **addoption_kwargs)


def terminal_formatter_cli_flags() -> frozenset[str]:
    return frozenset((*_TERMINAL_FORMATTER_CLI_FLAGS, *_OPTIONAL_PATH_TERMINAL_FLAGS))


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


def any_cucumber_formatter_requested(options: object) -> bool:
    return any(
        getattr(options, option_attr, None) not in (None, False)
        for option_attr, *_rest in cucumber_formatter_definitions()
    )
