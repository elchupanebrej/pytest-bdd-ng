from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from types import ModuleType, SimpleNamespace

import pytest

from pytest_cuke.debug_mcp import backend


class _Server:
    def __init__(self) -> None:
        self.response = ""
        self.tools: dict[str, Callable[..., str]] = {"send_pdb_command": self._old_tool}
        self.added: dict[str, object] = {}

    def _old_tool(self, command: str) -> str:
        """Send a command to the original fake debugger."""
        return self.response or f"original: {command}"

    def remove_tool(self, name: str) -> None:
        del self.tools[name]

    def add_tool(self, function: Callable[..., str], **kwargs: object) -> None:
        self.tools[str(kwargs["name"])] = function
        self.added = kwargs


def test_main_imports_the_mcp_pdb_submodule_when_package_exports_main_function(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _Server()
    server.settings = SimpleNamespace(host=None, port=None)
    server.run = lambda *, transport: setattr(server, "transport", transport)
    package = ModuleType("mcp_pdb")
    package.main = lambda: None
    debugger = ModuleType("mcp_pdb.main")
    debugger.mcp = server
    debugger.send_pdb_command = server._old_tool
    monkeypatch.setitem(sys.modules, "mcp_pdb", package)
    monkeypatch.setitem(sys.modules, "mcp_pdb.main", debugger)

    assert backend.main(
        ["--host", "127.0.0.1", "--port", "41001", "--inspection-url", "http://127.0.0.1:41002/mcp"]
    ) == 0

    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 41001
    assert server.transport == "streamable-http"


def test_main_retargets_debugger_host_allowlist_to_the_configured_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _Server()
    transport_security = SimpleNamespace(
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
    )
    server.settings = SimpleNamespace(host="127.0.0.1", port=8000, transport_security=transport_security)
    server.run = lambda *, transport: setattr(server, "transport", transport)
    package = ModuleType("mcp_pdb")
    package.main = lambda: None
    debugger = ModuleType("mcp_pdb.main")
    debugger.mcp = server
    debugger.send_pdb_command = server._old_tool
    monkeypatch.setitem(sys.modules, "mcp_pdb", package)
    monkeypatch.setitem(sys.modules, "mcp_pdb.main", debugger)

    assert backend.main(
        ["--host", "192.0.2.15", "--port", "41001", "--inspection-url", "http://192.0.2.15:41002/mcp"]
    ) == 0

    assert server.settings.host == "192.0.2.15"
    assert server.settings.port == 41001
    assert transport_security.allowed_hosts == ["192.0.2.15:41001"]
    assert transport_security.allowed_origins == ["http://192.0.2.15:41001"]


def _install(
    monkeypatch: pytest.MonkeyPatch,
    server: _Server,
    replies: list[dict[str, object]],
    calls: list[tuple[str, dict[str, object]]],
) -> Callable[[str], str]:
    def call_tool(endpoint: str, name: str, arguments: dict[str, object]) -> dict[str, object]:
        assert endpoint == "http://127.0.0.1:41002/mcp"
        calls.append((name, arguments))
        return replies.pop(0)

    monkeypatch.setattr(backend, "_call_inspection_tool", call_tool)
    backend.install_debugger_continuation(server, server._old_tool, "http://127.0.0.1:41002/mcp")
    return server.tools["send_pdb_command"]


def test_debugger_continue_releases_the_failure_captured_before_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _Server()
    calls: list[tuple[str, dict[str, object]]] = []

    class _Timer:
        def __init__(self, interval: float, function: Callable[..., None], *, args: tuple[object, ...]) -> None:
            self.interval = interval
            self.function = function
            self.args = args
            self.daemon = False

        def start(self) -> None:
            timers.append(self)

    timers: list[_Timer] = []
    monkeypatch.setattr(backend.threading, "Timer", _Timer)
    tool = _install(
        monkeypatch,
        server,
        [
            {"session_id": "session-1", "active_failure": {"sequence": 4}},
            {"released": True, "reason": "debugger_continuation"},
        ],
        calls,
    )

    assert tool("continue") == "original: continue"
    assert calls == [("inspect_failure", {})]
    assert len(timers) == 1
    timer = timers[0]
    assert timer.interval == 1.0
    assert timer.daemon is True
    timer.function(*timer.args)

    assert calls == [
        ("inspect_failure", {}),
        (
            "release_failure",
            {"session_id": "session-1", "sequence": 4, "reason": "debugger_continuation"},
        ),
    ]
    assert server.added["name"] == "send_pdb_command"
    assert "Send a command" in str(server.added["description"])


@pytest.mark.parametrize("command", ["n", "step", "next", "p value"])
def test_non_continuation_debugger_commands_do_not_contact_inspection(
    command: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _Server()
    calls: list[tuple[str, dict[str, object]]] = []
    tool = _install(monkeypatch, server, [], calls)

    assert tool(command) == f"original: {command}"
    assert calls == []


def test_failed_debugger_continue_does_not_release_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _Server()
    calls: list[tuple[str, dict[str, object]]] = []
    tool = _install(
        monkeypatch,
        server,
        [{"session_id": "session-1", "active_failure": {"sequence": 4}}],
        calls,
    )
    server.response = "No active debugging session."

    assert tool("c") == "No active debugging session."
    assert calls == [("inspect_failure", {})]


def test_debugger_continue_without_an_active_failure_does_not_release(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _Server()
    calls: list[tuple[str, dict[str, object]]] = []
    tool = _install(monkeypatch, server, [{"session_id": "session-1", "active_failure": None}], calls)

    assert tool("c") == "original: c"
    assert calls == [("inspect_failure", {})]


def test_inspection_mcp_call_runs_in_a_separate_loop_from_fastmcp_tool_context() -> None:
    async def value() -> dict[str, object]:
        return {"released": True}

    async def caller() -> dict[str, object]:
        return backend._run_coroutine(value)

    assert asyncio.run(caller()) == {"released": True}
