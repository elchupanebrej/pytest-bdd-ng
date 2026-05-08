"""Provide entrypoint helpers."""

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager

from .const import PYTEST_BDD_MARK, FeatureAutoLoad, FeatureBaseLoad
from .hook import ScenarioTestCollectorHookSpec
from .plugin import ScenarioTestCollector


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Handle addhooks."""
    pluginmanager.add_hookspecs(ScenarioTestCollectorHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Scenario")
    group.addoption(
        "--disable-feature-autoload",
        action="store_false",
        dest=str(FeatureAutoLoad.Cli.DISABLE_OPTION),
        default=None,
        help="Turn off feature files autoload",
    )
    parser.addini(
        str(FeatureAutoLoad.Ini.DISABLE_OPTION),
        default=False,
        type="bool",
        help="Turn off feature files autoload",
    )

    parser.addini(str(FeatureBaseLoad.Ini.DIR_OPTION), "Base features directory.")
    parser.addini(str(FeatureBaseLoad.Ini.URL_OPTION), "Base features url.")


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    config.addinivalue_line("markers", f"{PYTEST_BDD_MARK}: marker to identify pytest_bdd tests")
    config.addinivalue_line("markers", "scenarios: marker to provide scenarios locator")

    config.pluginmanager.register(ScenarioTestCollector())
