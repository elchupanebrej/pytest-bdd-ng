"""Provide entrypoint helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, Parser


def _parse_import_mode_args(args: list[str]) -> tuple[str | None, str | None]:
    """Parse messages-in and output from args."""
    messages_in = None
    output_dir = None
    for i, arg in enumerate(args):
        if arg == "--allure-cucumber-messages-in" and i + 1 < len(args):
            messages_in = args[i + 1]
        elif arg.startswith("--allure-cucumber-messages-in="):
            messages_in = arg.split("=", 1)[1]
        elif arg == "--allure-cucumber-out" and i + 1 < len(args):
            output_dir = args[i + 1]
        elif arg.startswith("--allure-cucumber-out="):
            output_dir = arg.split("=", 1)[1]
    return messages_in, output_dir


def pytest_load_initial_conftests(
    early_config: Config,
    parser: Parser,  # noqa: ARG001
    args: list[str],
) -> None:
    """Register the facade plugin early so that it is present before gherkin_message_reporter configure."""
    _, output_dir = _parse_import_mode_args(args)
    ini_output = early_config.getini("allure_cucumber_output_dir")
    output_dir = output_dir or ini_output

    if output_dir:
        import os
        from pathlib import Path

        from pytest_bdd.plugin.allure_formatter.plugin import AllureFormatterPlugin

        output_path = Path(os.path.expandvars(output_dir)).expanduser().resolve()

        plugin = AllureFormatterPlugin(
            config=early_config,
            output_dir=str(output_path),
        )
        early_config.pluginmanager.register(plugin, "allure-cucumber-plugin")
        plugin.start()


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Allure Formatter")
    group.addoption(
        "--allure-cucumber-out",
        action="store",
        dest="allure_cucumber_output_dir",
        metavar="PATH",
        default=None,
        help="Output directory for Allure result JSON files.",
    )
    group.addoption(
        "--allure-cucumber-messages-in",
        action="store",
        dest="allure_cucumber_messages_in",
        metavar="PATH",
        default=None,
        help="Read Cucumber Messages NDJSON from PATH and write Allure result JSON files.",
    )
    parser.addini(
        "allure_cucumber_output_dir",
        help="Output directory for Allure result JSON files.",
        default="",
    )


def pytest_addhooks(pluginmanager: object) -> None:
    """Register allure-cucumber hookspecs."""
    from pytest_bdd.compatibility.pytest import PytestPluginManager
    from pytest_bdd.plugin.allure_formatter.hook import AllureFormatterHookSpec

    if isinstance(pluginmanager, PytestPluginManager):
        pluginmanager.add_hookspecs(AllureFormatterHookSpec)


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    messages_in = getattr(config.option, "allure_cucumber_messages_in", None)
    if messages_in is not None:
        config.option.cucumber_messages_path = messages_in

    output_dir = getattr(config.option, "allure_cucumber_output_dir", None) or config.getini(
        "allure_cucumber_output_dir",
    )

    if not output_dir:
        return

    from pytest_bdd.plugin.allure_formatter.plugin import AllureFormatterPlugin

    output_path = Path(os.path.expandvars(output_dir or "allure-results")).expanduser().resolve()

    # Check if already registered by pytest_load_initial_conftests
    plugin = config.pluginmanager.get_plugin("allure-cucumber-plugin")
    if plugin is None:
        plugin = AllureFormatterPlugin(
            config=config,
            output_dir=str(output_path),
        )
        config.pluginmanager.register(plugin, "allure-cucumber-plugin")
        config.add_cleanup(plugin.stop)
        plugin.start()
    else:
        # Already registered early, just add cleanup
        config.add_cleanup(plugin.stop)


def pytest_unconfigure(config: Config) -> None:
    """Handle unconfigure — all cleanup handled by config.add_cleanup."""
