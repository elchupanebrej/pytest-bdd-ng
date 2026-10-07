from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_cuke.debug_mcp.server import DebugMcpDependencyError, InspectionMcpServer


class _UnstoppableThread:
    def __init__(self) -> None:
        self.join_calls: list[float] = []

    def join(self, timeout: float) -> None:
        self.join_calls.append(timeout)

    def is_alive(self) -> bool:
        return True


def test_inspection_server_close_reports_and_retains_a_thread_that_did_not_stop() -> None:
    inspection = InspectionMcpServer(queue=SimpleNamespace(), host="127.0.0.1", port=41002)
    server = SimpleNamespace(should_exit=False, force_exit=False)
    thread = _UnstoppableThread()
    inspection._server = server
    inspection._thread = thread  # type: ignore[assignment]

    with pytest.raises(DebugMcpDependencyError, match="inspection MCP server did not stop"):
        inspection.close(timeout=0.25)

    assert server.should_exit is True
    assert server.force_exit is True
    assert thread.join_calls == [0.25, 0.25]
    assert inspection._server is server
    assert inspection._thread is thread
