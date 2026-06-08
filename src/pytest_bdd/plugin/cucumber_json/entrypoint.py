"""
Cucumber json output formatter.

Responsibility:
    Cucumber json output formatter. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json.entrypoint` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - pytest_addoption: owns nested behavior below this boundary
    - pytest_configure: owns nested behavior below this boundary
    - pytest_unconfigure: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates _bddcucumberjson, help_, cucumber_json_path, cast._bddcucumberjson, plugin; depends on typing.TYPE_CHECKING,
    typing.Protocol, typing.Union, typing.cast, typing.runtime_checkable.

Invariants:
    - `pytest_bdd.plugin.cucumber_json.entrypoint` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from typing import TYPE_CHECKING, Protocol, Union, cast, runtime_checkable

from pytest_bdd.compatibility.pytest import Parser

from .const import CucumberJson
from .plugin import CucumberJsonPlugin

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Config as BaseConfig

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
        """
        Define the log bddcucumber jsonprotocol contract.

        Responsibility:
            Define the log bddcucumber jsonprotocol contract. It directly owns the observable contract, local decisions,
            and maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.entrypoint.LogBDDCucumberJSONProtocol` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates _bddcucumberjson.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.entrypoint.LogBDDCucumberJSONProtocol` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=2
        """

        _bddcucumberjson: "CucumberJsonPlugin"

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # mypy limitation with singledispatchmethod/dynamic typing
        """
        Represent config state.

        Responsibility:
            Represent config state. It directly owns the observable contract, local decisions, and maintenance boundary
            for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.cucumber_json.entrypoint.Config` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/compatibility/parser.py: imports or references `Config`
            - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `Config`
            - src/pytest_bdd/feature_locator.py: imports or references `Config`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `Config`
            - src/pytest_bdd/parser.py: imports or references `Config`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.entrypoint.Config` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """


else:
    from pytest_bdd.compatibility.pytest import Config


def pytest_addoption(parser: Parser) -> None:
    """
    Add pytest-bdd options.

    Responsibility:
        Add pytest-bdd options. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.entrypoint.pytest_addoption` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.getgroup: collaborator call used by this boundary
        - parser.addini: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

    State and side effects:
        mutates help_.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.entrypoint.pytest_addoption` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    Handle configure.

    Responsibility:
        Handle configure. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.entrypoint.pytest_configure` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - config.getini: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - hasattr: collaborator call used by this boundary
        - CucumberJsonPlugin: collaborator call used by this boundary
        - config.pluginmanager.register: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates cucumber_json_path, cast._bddcucumberjson.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.entrypoint.pytest_configure` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    cucumber_json_path = config.getini(str(CucumberJson.Ini.PATH_OPTION))
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        cast("Config", config)._bddcucumberjson = CucumberJsonPlugin(cucumber_json_path)  # noqa: SLF001
        config.pluginmanager.register(cast("Config", config)._bddcucumberjson)  # noqa: SLF001


def pytest_unconfigure(config: Union[Config, "BaseConfig"]) -> None:
    """
    Handle unconfigure.

    Responsibility:
        Handle unconfigure. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.entrypoint.pytest_unconfigure`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - config.pluginmanager.unregister: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `pytest_unconfigure`

    State and side effects:
        mutates plugin, config_.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.entrypoint.pytest_unconfigure` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    plugin = getattr(config, "_bddcucumberjson", None)
    if plugin is not None:
        config_ = cast("Config", config)
        del config_._bddcucumberjson  # noqa: SLF001
        config.pluginmanager.unregister(plugin)
