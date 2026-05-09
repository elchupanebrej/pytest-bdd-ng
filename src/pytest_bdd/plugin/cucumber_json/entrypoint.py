"""Cucumber json output formatter."""

from typing import TYPE_CHECKING, Protocol, Union, cast, runtime_checkable

from pytest_bdd.compatibility.pytest import Parser

from .const import CucumberJson
from .plugin import LogBDDCucumberJSON

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Config as BaseConfig

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
        """Define the log bddcucumber jsonprotocol contract."""

        _bddcucumberjson: "LogBDDCucumberJSON"

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # type: ignore[misc]
        """Represent config state."""


else:
    from pytest_bdd.compatibility.pytest import Config


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Cucumber JSON")
    help_ = "create cucumber json style report file at given path."
    # TODO: we dont't need legacy support for this option anymore
    group.addoption(
        "--cucumberjson",
        action="store",
        dest=str(CucumberJson.Cli.PATH_OPTION),
        metavar="path",
        default=None,
        help=f"{help_} Legacy alias; use --cucumber-json for the message-reporter-backed formatter.",
    )
    parser.addini(
        str(CucumberJson.Ini.PATH_OPTION),
        default="",
        type="string",
        help=help_,
    )


def pytest_configure(config: Union[Config, "BaseConfig"]) -> None:
    """Handle configure."""
    cucumber_json_path = config.option.cucumber_json_path
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        cast("Config", config)._bddcucumberjson = LogBDDCucumberJSON(cucumber_json_path)  # noqa: SLF001
        config.pluginmanager.register(cast("Config", config)._bddcucumberjson)  # noqa: SLF001


def pytest_unconfigure(config: Union[Config, "BaseConfig"]) -> None:
    """Handle unconfigure."""
    xml = getattr(config, "_bddcucumberjson", None)
    if xml is not None:
        config_ = cast("Config", config)
        del config_._bddcucumberjson  # noqa: SLF001
        config.pluginmanager.unregister(xml)
