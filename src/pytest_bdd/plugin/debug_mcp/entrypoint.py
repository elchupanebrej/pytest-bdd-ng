"""
pytest entrypoint for debug MCP support.

Responsibility:
    pytest entrypoint for debug MCP support. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.entrypoint` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - DebugMcpPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates self._mcp_server_process, msg, self._mcp_server_ready, python_exe, cmd; depends on __future__.annotations,
    atexit, subprocess, sys, threading.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.entrypoint` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises pytest.UsageError, RuntimeError; callers must treat these as boundary failures.

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

from __future__ import annotations

import atexit
import subprocess  # noqa: S404
import sys
import threading
import time
from typing import TYPE_CHECKING

import pytest

from . import hook as debug_mcp_hook
from .discovery import SessionDiscovery, allocate_local_port, format_terminal_line
from .hookspec import DebugMcpHookSpec
from .mcp_pdb_adapter import McpPdbAdapter
from .options import DebugMcpOptions
from .options import pytest_addoption as _pytest_addoption
from .queue import FailureQueue
from .state import DebugMcpState
from .xdist import debug_mcp_discovery_path, write_debug_mcp_discovery

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest_bdd.compatibility.pytest import CallInfo, Config, Item, Parser, PytestPluginManager, Session


class DebugMcpPlugin:
    """
    Plugin managing the debug MCP lifecycle — server subprocess, discovery, and hooks.

    Responsibility:
        Plugin managing the debug MCP lifecycle — server subprocess, discovery, and hooks. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _start_mcp_server: owns nested behavior below this boundary
        - _stop_mcp_server: owns nested behavior below this boundary
        - pytest_addoption: owns nested behavior below this boundary
        - pytest_addhooks: owns nested behavior below this boundary
        - pytest_sessionstart: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates self._mcp_server_process, msg, self._mcp_server_ready, python_exe, cmd.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises pytest.UsageError, RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    def __init__(self) -> None:
        """
        Initialize the plugin, register atexit cleanup for the MCP server.

        Responsibility:
            Initialize the plugin, register atexit cleanup for the MCP server. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - threading.Event: collaborator call used by this boundary
            - atexit.register: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self._mcp_server_process, self._mcp_server_ready.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.__init__` keeps its documented import path,
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
            #arch-eval:locational_stability=4
        """
        self._mcp_server_process: subprocess.Popen[bytes] | None = None
        self._mcp_server_ready: threading.Event = threading.Event()
        atexit.register(self._stop_mcp_server)

    # -- MCP server lifecycle ------------------------------------------------

    def _start_mcp_server(self, host: str, port: int) -> subprocess.Popen[bytes]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._start_mcp_server`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._start_mcp_server` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - subprocess.Popen: collaborator call used by this boundary
            - time.sleep: collaborator call used by this boundary
            - proc.poll: collaborator call used by this boundary
            - proc.communicate: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates python_exe, cmd, proc, _stdout, stderr.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._start_mcp_server` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        python_exe = sys.executable
        cmd = [python_exe, "-m", "mcp_pdb.main", "--host", host, "--port", str(port)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)  # noqa: S603
        time.sleep(1.0)
        if proc.poll() is not None:
            _stdout, stderr = proc.communicate()
            msg = f"MCP server failed to start: {stderr}"
            raise RuntimeError(msg)
        self._mcp_server_ready.set()
        self._mcp_server_process = proc  # type: ignore[assignment]  # Popen[str] vs Popen[bytes] with text=True
        return proc  # type: ignore[return-value]  # Popen[str] vs Popen[bytes] with text=True

    def _stop_mcp_server(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._stop_mcp_server`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._stop_mcp_server` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self._mcp_server_process.wait: collaborator call used by this boundary
            - self._mcp_server_process.terminate: collaborator call used by this boundary
            - self._mcp_server_process.kill: collaborator call used by this boundary
            - self._mcp_server_ready.clear: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates self._mcp_server_process.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._stop_mcp_server` keeps its documented import path,
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
        if self._mcp_server_process is None:
            return
        self._mcp_server_process.terminate()
        try:
            self._mcp_server_process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            self._mcp_server_process.kill()
            self._mcp_server_process.wait()
        self._mcp_server_process = None
        self._mcp_server_ready.clear()

    # -- pytest hooks --------------------------------------------------------

    @staticmethod
    def pytest_addoption(parser: Parser) -> None:
        """
        Register debug MCP command-line options.

        Responsibility:
            Register debug MCP command-line options. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.pytest_addoption` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - _pytest_addoption: collaborator call used by this boundary

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
        _pytest_addoption(parser)

    @staticmethod
    def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
        """
        Register debug MCP hook specifications.

        Responsibility:
            Register debug MCP hook specifications. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.pytest_addhooks` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - pluginmanager.add_hookspecs: collaborator call used by this boundary

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
        pluginmanager.add_hookspecs(DebugMcpHookSpec)

    def pytest_sessionstart(self, session: Session) -> None:
        """
        Initialize debug MCP state, start the MCP server, and write discovery.

        Raises:
            pytest.UsageError: If options are invalid or the MCP server fails to start.

        Responsibility:
            Initialize debug MCP state, start the MCP server, and write discovery. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.pytest_sessionstart` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.UsageError: collaborator call used by this boundary
            - allocate_local_port: collaborator call used by this boundary
            - write_debug_mcp_discovery: collaborator call used by this boundary
            - self._write_terminal_line: collaborator call used by this boundary
            - DebugMcpOptions.from_config: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_sessionstart`

        State and side effects:
            mutates config, options, mcp_port, sidecar_port, discovery_path.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.pytest_sessionstart` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises pytest.UsageError; callers must treat these as boundary failures.

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
        config = session.config
        try:
            options = DebugMcpOptions.from_config(config)
        except ValueError as error:
            raise pytest.UsageError(str(error)) from error
        if not options.enabled:
            return

        mcp_port = options.port if options.port is not None else allocate_local_port(options.host)
        sidecar_port = allocate_local_port(options.host)
        discovery_path = debug_mcp_discovery_path(config)

        try:
            mcp_proc = self._start_mcp_server(options.host, mcp_port)
        except RuntimeError as exc:
            msg = f"Failed to start mcp-pdb MCP server: {exc}"
            raise pytest.UsageError(msg) from exc

        state = DebugMcpState.from_options(
            options,
            mcp_port=mcp_port,
            sidecar_port=sidecar_port,
            queue=FailureQueue(
                discovery_path=discovery_path,
                adapter=McpPdbAdapter(),
                discovery_writer=lambda current_state, current_discovery: write_debug_mcp_discovery(
                    config,
                    current_state,
                    current_discovery,
                ),
            ),
        ).initialize_in_stash(config.stash)
        state.mcp_server_process = mcp_proc

        discovery = SessionDiscovery.waiting(state)
        write_debug_mcp_discovery(config, state, discovery)
        self._write_terminal_line(config, format_terminal_line(discovery, path=discovery_path))
        if options.uses_public_host:
            self._write_terminal_line(
                config,
                "debug-mcp trusted environment warning: non-local host exposes live debugger access.",
            )

    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:  # noqa: ARG002
        """
        Stop the MCP server subprocess on session finish.

        Responsibility:
            Stop the MCP server subprocess on session finish. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.pytest_sessionfinish` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._stop_mcp_server: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_sessionfinish`

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
        self._stop_mcp_server()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo) -> Generator[None, object, None]:  # noqa: PLR6301
        """
        Delegate report handling to the debug MCP hook module.

        Responsibility:
            Delegate report handling to the debug MCP hook module. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin.pytest_runtest_makereport` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - debug_mcp_hook.pytest_runtest_makereport: collaborator call used by this boundary
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
        yield from debug_mcp_hook.pytest_runtest_makereport(item, call)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _write_terminal_line(config: Config, line: str) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._write_terminal_line`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._write_terminal_line` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - config.pluginmanager.get_plugin: collaborator call used by this boundary
            - reporter.write_line: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates reporter.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.entrypoint.DebugMcpPlugin._write_terminal_line` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        reporter = config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            reporter.write_line(line)


_plugin = DebugMcpPlugin()

# Module-level hooks delegate to the plugin instance so that pytest can
# discover them both when this module is auto-loaded as an entry-point
# plugin and when it is manually passed via ``plugins=[module]``.

pytest_addoption = _plugin.pytest_addoption
pytest_addhooks = _plugin.pytest_addhooks
pytest_sessionstart = _plugin.pytest_sessionstart
pytest_sessionfinish = _plugin.pytest_sessionfinish
pytest_runtest_makereport = _plugin.pytest_runtest_makereport
