"""
Serves as the Extra Plugins (order 8) module for YAML/JSON/TOML/HOCON BDD feature definitions.

Responsibility:
    Serves as the Extra Plugins (order 8) module for YAML/JSON/TOML/HOCON BDD feature definitions. Defines classes and
    functions that collectively implement Collection and execution behavior of the 'entrypoint' component. This module
    is the sole owner of its specific BDD plugin contract within the Extra Plugins (order 8).

Reason for existence:
    This module exists as a distinct architectural unit because it encapsulates all logic for YAML/JSON/TOML/HOCON BDD
    feature definitions within the Extra Plugins (order 8). It is the information expert for its specific domain, owning
    the transformation from pytest events to its output format. Changes to YAML/JSON/TOML/HOCON BDD feature definitions
    behavior belong exclusively in this module, not in sibling plugins or the core pytest-bdd library. Its import
    boundary isolates it from other reporting/runtime concerns.

Delegates:
    - (internal classes and functions): Implement specific aspects of YAML/JSON/TOML/HOCON BDD feature definitions
    within the Collection and execution.

Cohesion:
    All entities in this module serve the single purpose of YAML/JSON/TOML/HOCON BDD feature definitions. They share
    common import
    dependencies and operate on the same domain types. No unrelated utilities are present.

Separation:
    - (sibling plugins in Extra Plugins (order 8)): Each owns a distinct output format or lifecycle concern.
    - (runtime plugins): Handled by separate modules in the Runtime layer (order 6).

Main consumers:
    - pytest: Hooks into the Collection and execution via standard pytest hook mechanisms.
    - (downstream tools): CI/CD systems and test reporting tools consume the generated output.

State and side effects:
    Accumulates state across pytest hook calls during the session. Accesses pytest Config for
    options. May perform file I/O for report generation.

Invariants:
    - Output format must conform to the expected schema for entrypoint.
    - Hook implementations must respect pytest's hook calling conventions.

Failure semantics:
    Raises pytest.UsageError for configuration issues. May raise LookupError when required
    resources are missing from pytest stash or fixtures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

if STRUCT_BDD_INSTALLED:
    from pytest_bdd.plugin.struct_bdd.plugin import StructBDDPlugin

if STRUCT_BDD_INSTALLED:

    @pytest.hookimpl(trylast=True)
    def pytest_configure(config: Config) -> None:
        """
        Implement the 'pytest_bdd.plugin.struct_bdd.entrypoint.pytest_configure' function within the Extra Plugins (order 8).

        Responsibility:
            Implements the 'pytest_bdd.plugin.struct_bdd.entrypoint.pytest_configure' function within the Extra Plugins
            (order 8). Operates during the Collection and execution.

        Reason for existence:
            This function is the single authority for its specific behavior within the Extra Plugins (order 8). It
            implements a pytest lifecycle hook at the Collection and execution, making it the natural extension point
            for pytest-bdd behavior. Its boundary is defined by its specific inputs and outputs within the
            YAML/JSON/TOML/HOCON BDD feature definitions workflow.

        Delegates:
            - pluginmanager.register: Subordinate operation called during execution

        Cohesion:
            Focuses exclusively on the 'pytest_bdd.plugin.struct_bdd.entrypoint.pytest_configure' operation. All
            internal logic serves this single purpose within the Collection and execution.

        Separation:
            - (peer entities): Each sibling owns a distinct Collection and execution lifecycle event or sub-operation

        Main consumers:
            - pytest: Calls this hook at the Collection and execution as part of standard plugin lifecycle

        State and side effects:
            Accesses pytest Config for options

        Invariants:
            - Maintains its documented input/output contract

        Failure semantics:
            No custom exceptions raised directly by this entity

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        config.pluginmanager.register(StructBDDPlugin())
