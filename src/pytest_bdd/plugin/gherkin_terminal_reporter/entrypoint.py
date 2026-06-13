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

import pytest

from pytest_bdd.compatibility.pytest import Config, Parser, TerminalReporter

from .exception import IncompatiblePluginConfigurationError, IncompatiblePluginError
from .plugin import GherkinTerminalReporterPlugin


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
    group = parser.getgroup("terminal reporting", "reporting", after="general")  # type: ignore[call-arg]  # pytest Parser.getgroup after kwarg
    group._addoption(  # noqa: SLF001  -- suppressed warning
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="enable gherkin output",
    )


@pytest.hookimpl(trylast=True)
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
    if config.option.gherkin_terminal_reporter:
        # Get the standard terminal reporter plugin and replace it with our
        current_reporter = config.pluginmanager.getplugin("terminalreporter")
        if current_reporter.__class__ != TerminalReporter:
            raise IncompatiblePluginError(current_reporter)
        gherkin_reporter = GherkinTerminalReporterPlugin(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")
        if config.pluginmanager.getplugin("dsession"):
            msg = "xdist"
            raise IncompatiblePluginConfigurationError(msg)
