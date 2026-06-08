"""
Provide entrypoint helpers.

Responsibility:
    Provide entrypoint helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.scenario_test_collector.entrypoint` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - pytest_addhooks: owns nested behavior below this boundary
    - pytest_addoption: owns nested behavior below this boundary
    - pytest_load_initial_conftests: owns nested behavior below this boundary
    - pytest_configure: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates _, group, feature_autoload_hlp, base_feature_dir_hlp, base_feature_url_hlp; depends on
    pytest_bdd.collector_batch.FeatureBatchParser, pytest_bdd.compatibility.pytest.Config,
    pytest_bdd.compatibility.pytest.Parser, pytest_bdd.compatibility.pytest.PytestPluginManager,
    pytest_bdd.model.scenario_collection.PYTEST_BDD_MARK.

Invariants:
    - `pytest_bdd.plugin.scenario_test_collector.entrypoint` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

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
    """
    Handle addhooks.

    Responsibility:
        Handle addhooks. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_addhooks`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pluginmanager.add_hookspecs: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addhooks`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    pluginmanager.add_hookspecs(ScenarioTestCollectorHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """
    Add pytest-bdd options.

    Responsibility:
        Add pytest-bdd options. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_addoption` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - parser.addini: collaborator call used by this boundary
        - group.addoption: collaborator call used by this boundary
        - parser.getgroup: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

    State and side effects:
        mutates group, feature_autoload_hlp, base_feature_dir_hlp, base_feature_url_hlp, batch_disable_hlp.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_addoption` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
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
    """
    Normalize WSL temp roots before pytest capture opens temp files.

    Responsibility:
        Normalize WSL temp roots before pytest capture opens temp files. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_load_initial_conftests` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - prefer_posix_temp_root: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates _.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_load_initial_conftests` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    _ = early_config
    _ = parser
    _ = args
    prefer_posix_temp_root()


def pytest_configure(config: Config) -> None:
    """
    Handle configure.

    Responsibility:
        Handle configure. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_configure` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - config.addinivalue_line: collaborator call used by this boundary
        - config.getini: collaborator call used by this boundary
        - config.pluginmanager.register: collaborator call used by this boundary
        - ScenarioTestCollectorPlugin: collaborator call used by this boundary
        - config.getoption: collaborator call used by this boundary
        - FeatureBatchParser: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates parser, ini_threshold.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_configure` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
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
