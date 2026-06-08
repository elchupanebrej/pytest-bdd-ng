"""
Provide entrypoint helpers.

Responsibility:
    Provide entrypoint helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.entrypoint` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - config.pluginmanager.register: collaborator call used by this boundary
    - StructBDDPlugin: collaborator call used by this boundary
    - pytest.hookimpl: collaborator call used by this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    depends on pytest, pytest_bdd.compatibility.pytest.Config, pytest_bdd.compatibility.struct_bdd.STRUCT_BDD_INSTALLED,
    pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.entrypoint` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
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
        Handle configure.

        Responsibility:
            Handle configure. It directly owns the observable contract, local decisions, and maintenance boundary for
            this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.entrypoint.pytest_configure` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - config.pluginmanager.register: collaborator call used by this boundary
            - StructBDDPlugin: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        config.pluginmanager.register(StructBDDPlugin())
