"""
Dispatcher entrypoint: bridges INI and CLI cucumber-json config with CLI-wins precedence.

Responsibility:
    Dispatcher entrypoint: bridges INI and CLI cucumber-json config with CLI-wins precedence. It directly owns the
    observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
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
    mutates ini_value, cli_option, cli_value; depends on pytest, pytest_bdd.compatibility.pytest.Config,
    const.CucumberJsonDispatcher.

Invariants:
    - `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

import pytest

from pytest_bdd.compatibility.pytest import Config

from .const import CucumberJsonDispatcher


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: Config) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint.pytest_configure` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint.pytest_configure` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - hasattr: collaborator call used by this boundary
        - config.getini: collaborator call used by this boundary
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
        mutates ini_value, cli_option, cli_value.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint.pytest_configure` keeps its documented import path,
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
    # noqa: D103
    if hasattr(config, "workerinput"):
        return

    ini_value = config.getini(str(CucumberJsonDispatcher.Ini.PATH_OPTION))
    cli_option = getattr(config, "option", None)
    cli_value = getattr(cli_option, str(CucumberJsonDispatcher.Cli.OPTION_ATTR), None)

    if ini_value and cli_value is not None:
        config._inicache[str(CucumberJsonDispatcher.Ini.PATH_OPTION)] = ""  # noqa: SLF001
