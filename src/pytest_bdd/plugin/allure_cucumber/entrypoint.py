"""Provide entrypoint helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.plugin.allure_cucumber.plugin import AllureCucumberPlugin

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, Parser


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Allure Cucumber")
    group.addoption(
        "--allure-cucumber-output",
        action="store",
        dest="allure_cucumber_output_dir",
        metavar="PATH",
        default=None,
        help="Output directory for Allure result JSON files.",
    )
    group.addoption(
        "--allure-cucumber-messages",
        action="store",
        dest="allure_cucumber_messages_path",
        metavar="PATH",
        default=None,
        help="Path to Cucumber Messages NDJSON file.",
    )
    parser.addini(
        "allure_cucumber_output_dir",
        help="Output directory for Allure result JSON files.",
        default="allure-results",
    )


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    if hasattr(config, "workerinput"):
        return

    output_dir = getattr(config.option, "allure_cucumber_output_dir", None) or config.getini(
        "allure_cucumber_output_dir",
    )
    messages_path = getattr(config.option, "allure_cucumber_messages_path", None)

    plugin = AllureCucumberPlugin(
        config=config,
        output_dir=output_dir,
        messages_path=messages_path,
    )
    config._allure_cucumber_plugin = plugin  # type: ignore[attr-defined]  # noqa: SLF001
    config.pluginmanager.register(plugin, "allure-cucumber-converter")


def pytest_unconfigure(config: Config) -> None:
    """Handle unconfigure."""
    plugin = getattr(config, "_allure_cucumber_plugin", None)
    if plugin is not None:
        del config._allure_cucumber_plugin  # type: ignore[attr-defined]  # noqa: SLF001
        config.pluginmanager.unregister(plugin)
