"""
Options for the debug MCP pytest plugin.

Responsibility:
    Options for the debug MCP pytest plugin. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - pytest_addoption: owns nested behavior below this boundary
    - DebugMcpOptions: owns nested behavior below this boundary
    - _option_or_ini: owns nested behavior below this boundary
    - _positive_float: owns nested behavior below this boundary
    - _optional_port: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `options`
    - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `options`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `options`
    - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `options`
    - src/pytest_bdd/util/cucumber_formatters.py: imports or references `options`

State and side effects:
    mutates msg, enabled, port, LOCAL_HOSTS, MAX_PORT; depends on __future__.annotations, pathlib.Path,
    typing.TYPE_CHECKING, typing.cast, attrs.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.options` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises ValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import attrs

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, Parser

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_PORT = 65535
EMPTY_VALUES = {None, ""}
ConfigValue = object | None


def pytest_addoption(parser: Parser) -> None:
    """
    Register debug MCP command-line and ini options.

    Responsibility:
        Register debug MCP command-line and ini options. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options.pytest_addoption` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - group.addoption: collaborator call used by this boundary
        - parser.addini: collaborator call used by this boundary
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
        mutates group.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.options.pytest_addoption` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    group = parser.getgroup("mcp-pdb", "Debug MCP")
    group.addoption(
        "--mcp-pdb-on-fail",
        action="store_true",
        default=False,
        dest="mcp_pdb_on_fail",
        help="Expose failed pytest tests through debug MCP.",
    )
    group.addoption("--mcp-pdb-timeout", dest="mcp_pdb_timeout", default=None, help="No-client timeout in seconds.")
    group.addoption("--mcp-pdb-lease", dest="mcp_pdb_lease", default=None, help="Client heartbeat lease in seconds.")
    group.addoption("--mcp-pdb-artifacts", dest="mcp_pdb_artifacts", default=None, help="Debug MCP artifact root.")
    group.addoption("--mcp-pdb-host", dest="mcp_pdb_host", default=None, help="Debug MCP bind host.")
    group.addoption("--mcp-pdb-port", dest="mcp_pdb_port", default=None, help="Debug MCP fixed port.")

    parser.addini("mcp_pdb_on_fail", "Enable debug MCP failure handling.", default=False, type="bool")
    parser.addini("mcp_pdb_timeout", "Debug MCP no-client timeout in seconds.", default="", type="string")
    parser.addini("mcp_pdb_lease", "Debug MCP heartbeat lease in seconds.", default="", type="string")
    parser.addini("mcp_pdb_artifacts", "Debug MCP artifact root.", default="", type="string")
    parser.addini("mcp_pdb_host", "Debug MCP bind host.", default="", type="string")
    parser.addini("mcp_pdb_port", "Debug MCP fixed port.", default="", type="string")


@attrs.define(frozen=True, slots=True)
class DebugMcpOptions:
    """
    Resolved debug MCP options.

    Responsibility:
        Resolved debug MCP options. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options.DebugMcpOptions` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - uses_public_host: owns nested behavior below this boundary
        - from_config: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `DebugMcpOptions`
        - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `DebugMcpOptions`

    State and side effects:
        mutates enabled, timeout_seconds, lease_seconds, artifacts_path, host.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.options.DebugMcpOptions` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    enabled: bool = False
    timeout_seconds: float = 30.0
    lease_seconds: float = 10.0
    artifacts_path: Path = attrs.field(factory=lambda: Path(".pytest_cache") / "mcp-pdb" / "artifacts")
    host: str = "127.0.0.1"
    port: int | None = None

    @property
    def uses_public_host(self) -> bool:
        """
        Return whether configured host is non-local.

        Responsibility:
            Return whether configured host is non-local. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.options.DebugMcpOptions.uses_public_host` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `uses_public_host`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return self.host not in LOCAL_HOSTS

    @classmethod
    def from_config(cls, config: Config) -> DebugMcpOptions:
        """
        Build options from pytest CLI and ini state.

        Returns:
            Resolved debug MCP options.

        Responsibility:
            Build options from pytest CLI and ini state. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options.DebugMcpOptions.from_config`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _option_or_ini: collaborator call used by this boundary
            - _positive_float: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - bool: collaborator call used by this boundary
            - config.getoption: collaborator call used by this boundary
            - config.getini: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `from_config`

        State and side effects:
            mutates enabled.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.options.DebugMcpOptions.from_config` keeps its documented import path,
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
        enabled = bool(config.getoption("mcp_pdb_on_fail", default=False) or config.getini("mcp_pdb_on_fail"))
        return cls(
            enabled=enabled,
            timeout_seconds=_positive_float(_option_or_ini(config, "mcp_pdb_timeout"), "mcp_pdb_timeout", default=30.0),
            lease_seconds=_positive_float(_option_or_ini(config, "mcp_pdb_lease"), "mcp_pdb_lease", default=10.0),
            artifacts_path=Path(str(_option_or_ini(config, "mcp_pdb_artifacts") or ".pytest_cache/mcp-pdb/artifacts")),
            host=str(_option_or_ini(config, "mcp_pdb_host") or "127.0.0.1"),
            port=_optional_port(_option_or_ini(config, "mcp_pdb_port")),
        )


def _option_or_ini(config: Config, name: str) -> ConfigValue:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.options._option_or_ini` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options._option_or_ini` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - config.getoption: collaborator call used by this boundary
        - config.getini: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates option.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.options._option_or_ini` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    option = config.getoption(name, default=None)
    if option not in EMPTY_VALUES:
        return cast("ConfigValue", option)
    return cast("ConfigValue", config.getini(name))


def _positive_float(value: ConfigValue, name: str, *, default: float) -> float:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.options._positive_float` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options._positive_float` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ValueError: collaborator call used by this boundary
        - float: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates msg, parsed.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.options._positive_float` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    if value in EMPTY_VALUES:
        return default
    try:
        parsed = float(str(value))
    except (TypeError, ValueError) as error:
        msg = f"{name} must be a positive number"
        raise ValueError(msg) from error
    if parsed <= 0:
        msg = f"{name} must be a positive number"
        raise ValueError(msg)
    return parsed


def _optional_port(value: ConfigValue) -> int | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.options._optional_port` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.options._optional_port` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ValueError: collaborator call used by this boundary
        - int: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates msg, port.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.options._optional_port` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    if value in EMPTY_VALUES:
        return None
    try:
        port = int(str(value))
    except (TypeError, ValueError) as error:
        msg = "mcp_pdb_port must be an integer from 1 to 65535"
        raise ValueError(msg) from error
    if not 1 <= port <= MAX_PORT:
        msg = "mcp_pdb_port must be an integer from 1 to 65535"
        raise ValueError(msg)
    return port
