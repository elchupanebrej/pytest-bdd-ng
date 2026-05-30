"""Provide entrypoint helpers."""

from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager
from pytest_bdd.model.scenario_collection import (
    PYTEST_BDD_MARK,
    PYTEST_BDD_SCENARIOS_MARK,
    EmptyScenarios,
    FeatureAutoLoad,
    FeatureBaseLoad,
)
from pytest_bdd.util.temp_root import prefer_posix_temp_root

from .hook import ScenarioTestCollectorHookSpec
from .plugin import ScenarioTestCollectorPlugin


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

    batch_disable_hlp = "Disable lazy-batched async feature file collection"
    group.addoption(
        "--disable-batch-collection",
        action="store_true",
        dest="disable_batch_collection",
        default=None,
        help=batch_disable_hlp,
    )
    parser.addini("disable_batch_collection", default=False, type="bool", help=batch_disable_hlp)

    batch_threshold_hlp = "Minimum feature file count to enable parallel collection (auto: 50 Linux, 1000 Windows)"
    parser.addini("batch_threshold", default="-1", help=batch_threshold_hlp)

    empty_scenarios_hlp = "Allow scenarios with no matching step definitions"
    group.addoption(
        "--allow-empty-scenarios",
        action="store_true",
        dest=str(EmptyScenarios.Cli.ALLOW_OPTION),
        default=False,
        help=empty_scenarios_hlp,
    )
    parser.addini(
        str(EmptyScenarios.Ini.ALLOW_OPTION),
        default=False,
        type="bool",
        help=empty_scenarios_hlp,
    )


def pytest_load_initial_conftests(early_config: Config, parser: Parser, args: list[str]) -> None:
    """Normalize WSL temp roots before pytest capture opens temp files."""
    _ = early_config
    _ = parser
    _ = args
    prefer_posix_temp_root()


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    config.addinivalue_line("markers", f"{PYTEST_BDD_MARK}: marker to identify pytest_bdd tests")
    config.addinivalue_line("markers", f"{PYTEST_BDD_SCENARIOS_MARK}: marker to provide scenarios locator")

    config.pluginmanager.register(ScenarioTestCollectorPlugin())

    if not config.getini("disable_batch_collection") and not config.getoption(
        "disable_batch_collection",
        default=False,
    ):
        parser = FeatureBatchParser()
        ini_threshold = int(config.getini("batch_threshold"))
        if ini_threshold > 0:
            parser.set_threshold(ini_threshold)
        parser.initialize_in_stash(config.stash)
