"""Dispatcher entrypoint: bridges INI and CLI cucumber-json config with CLI-wins precedence."""

import pytest

from pytest_bdd.compatibility.pytest import Config

from .const import CucumberJsonDispatcher


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: Config) -> None:
    """Handle configure."""
    if hasattr(config, "workerinput"):
        return

    ini_value = config.getini(str(CucumberJsonDispatcher.Ini.PATH_OPTION))
    cli_option = getattr(config, "option", None)
    cli_value = getattr(cli_option, str(CucumberJsonDispatcher.Cli.OPTION_ATTR), None)

    if ini_value and cli_value is not None:
        config._inicache[str(CucumberJsonDispatcher.Ini.PATH_OPTION)] = ""  # noqa: SLF001
