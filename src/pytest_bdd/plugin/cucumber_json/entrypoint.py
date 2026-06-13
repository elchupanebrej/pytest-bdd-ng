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

from typing import TYPE_CHECKING, Protocol, Union, cast, runtime_checkable

from pytest_bdd.compatibility.pytest import Parser

from .const import CucumberJson
from .plugin import CucumberJsonPlugin

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Config as BaseConfig

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
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
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """

        _bddcucumberjson: "CucumberJsonPlugin"

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # mypy limitation with singledispatchmethod/dynamic typing
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
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """


else:
    from pytest_bdd.compatibility.pytest import Config


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
    parser.getgroup("bdd", "Cucumber JSON")
    help_ = "create cucumber json style report file at given path."
    parser.addini(
        str(CucumberJson.Ini.PATH_OPTION),
        default="",
        type="string",
        help=help_,
    )


def pytest_configure(config: Union[Config, "BaseConfig"]) -> None:
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
    cucumber_json_path = config.getini(str(CucumberJson.Ini.PATH_OPTION))
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        cast("Config", config)._bddcucumberjson = CucumberJsonPlugin(cucumber_json_path)  # noqa: SLF001  -- suppressed warning
        config.pluginmanager.register(cast("Config", config)._bddcucumberjson)  # noqa: SLF001  -- suppressed warning


def pytest_unconfigure(config: Union[Config, "BaseConfig"]) -> None:
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
    plugin = getattr(config, "_bddcucumberjson", None)
    if plugin is not None:
        config_ = cast("Config", config)
        del config_._bddcucumberjson  # noqa: SLF001  -- suppressed warning
        config.pluginmanager.unregister(plugin)
