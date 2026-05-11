"""Provide entrypoint helpers."""

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager

from .const import PYTEST_BDD_MARK, PYTEST_BDD_SCENARIOS_MARK, FeatureAutoLoad, FeatureBaseLoad
from .hook import ScenarioTestCollectorHookSpec
from .plugin import ScenarioTestCollector


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Handle addhooks."""
    pluginmanager.add_hookspecs(ScenarioTestCollectorHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Scenario")
    feature_autoload_hlp = "Turn off feature files autoload"
    group.addoption(
        "--disable-feature-autoload",
        action="store_false",
        dest=str(FeatureAutoLoad.Cli.DISABLE_OPTION),
        default=None,
        help=feature_autoload_hlp,
    )
    parser.addini(
        str(FeatureAutoLoad.Ini.DISABLE_OPTION),
        default=False,
        type="bool",
        help=feature_autoload_hlp,
    )

    base_feature_dir_hlp = "Base feature collection directory."
    group.addoption(
        "--feature-base-dir",
        action="store",
        dest=str(FeatureBaseLoad.Cli.DIR_OPTION),
        metavar="PATH",
        default=None,
        help=base_feature_dir_hlp,
    )
    parser.addini(str(FeatureBaseLoad.Ini.DIR_OPTION), base_feature_dir_hlp)

    base_feature_url_hlp = "Base feature collection directory."
    group.addoption(
        "--feature-base-url",
        action="store",
        dest=str(FeatureBaseLoad.Cli.URL_OPTION),
        metavar="URL",
        default=None,
        help=base_feature_url_hlp,
    )
    parser.addini(str(FeatureBaseLoad.Ini.URL_OPTION), base_feature_url_hlp)


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    config.addinivalue_line("markers", f"{PYTEST_BDD_MARK}: marker to identify pytest_bdd tests")
    config.addinivalue_line("markers", f"{PYTEST_BDD_SCENARIOS_MARK}: marker to provide scenarios locator")

    config.pluginmanager.register(ScenarioTestCollector())
