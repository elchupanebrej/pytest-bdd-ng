"""Cucumber json output formatter."""

from typing import TYPE_CHECKING, Protocol, Union, cast, runtime_checkable

from pytest_bdd.compatibility.pytest import Parser

from .const import CucumberJson
from .plugin import CucumberJsonPlugin

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Config as BaseConfig

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
        """Define the log bddcucumber jsonprotocol contract."""

        _bddcucumberjson: "CucumberJsonPlugin"

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # type: ignore[misc]
        """Represent config state."""


else:
    from pytest_bdd.compatibility.pytest import Config


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    parser.getgroup("bdd", "Cucumber JSON")
    help_ = "create cucumber json style report file at given path."
    parser.addini(
        str(CucumberJson.Ini.PATH_OPTION),
        default="",
        type="string",
        help=help_,
    )


def pytest_configure(config: Union[Config, "BaseConfig"]) -> None:
    """Handle configure."""
    cucumber_json_path = config.getini(str(CucumberJson.Ini.PATH_OPTION))
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        cast("Config", config)._bddcucumberjson = CucumberJsonPlugin(cucumber_json_path)  # noqa: SLF001
        config.pluginmanager.register(cast("Config", config)._bddcucumberjson)  # noqa: SLF001


def pytest_unconfigure(config: Union[Config, "BaseConfig"]) -> None:
    """Handle unconfigure."""
    plugin = getattr(config, "_bddcucumberjson", None)
    if plugin is not None:
        config_ = cast("Config", config)
        del config_._bddcucumberjson  # noqa: SLF001
        config.pluginmanager.unregister(plugin)
