"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    pluginmanager.add_hookspecs(ScenarioTestCollectorHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    _ = early_config
    _ = parser
    _ = args
    prefer_posix_temp_root()


def pytest_configure(config: Config) -> None:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
