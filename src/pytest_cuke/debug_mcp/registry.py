"""Socket registry that carries Debug MCP worker discovery without a shared filesystem.

Workers post their own discovery records to the controller-owned registry. The
controller writes those records through the same root index and file lock that
local popen workers use, so agents keep reading ``workers.json`` and each
worker record under the same paths.
"""

from __future__ import annotations

import http.client
import json
import socketserver
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any

from pytest_cuke.debug_mcp.options import parse_registry_address
from pytest_cuke.debug_mcp.redaction import redact_data, secret_values
from pytest_cuke.debug_mcp.xdist import XdistDiscoveryError, XdistDiscoveryIndex

if TYPE_CHECKING:
    from collections.abc import Mapping

_MAX_REQUEST_BYTES = 1_000_000


class DiscoveryRegistryError(ConnectionError):
    """Raised when a worker cannot reach the controller's discovery registry."""

    __test__ = False


class DiscoveryRegistryState:
    """Validate transported worker records and write them through the root index."""

    __test__ = False

    def __init__(
        self,
        index: XdistDiscoveryIndex,
        *,
        session_id: str,
        redact_patterns: tuple[str, ...] = (),
    ) -> None:
        self.index = index
        self.session_id = session_id
        self._secrets = secret_values(redact_patterns)

    def apply(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Apply one registry operation and return its JSON-ready response."""
        try:
            operation = request.get("op")
            if operation == "publish":
                self._publish(request)
                return {"ok": True}
            if operation == "remove":
                self._remove(request)
                return {"ok": True}
            raise XdistDiscoveryError(f"unknown discovery registry operation: {operation!r}")
        except XdistDiscoveryError as error:
            return {"ok": False, "error": str(error)}

    def _publish(self, request: Mapping[str, Any]) -> None:
        record = request.get("record")
        if not isinstance(record, dict):
            raise XdistDiscoveryError("publish needs a worker discovery record")
        if record.get("root_session_id") != self.session_id:
            raise XdistDiscoveryError("worker discovery record belongs to a different pytest session")
        self.index.publish_worker(redact_data(record, self._secrets))

    def _remove(self, request: Mapping[str, Any]) -> None:
        if request.get("root_session_id") != self.session_id:
            raise XdistDiscoveryError("worker removal belongs to a different pytest session")
        worker_id = request.get("worker_id")
        if not isinstance(worker_id, str) or not worker_id:
            raise XdistDiscoveryError("remove needs a worker ID")
        self.index.remove_worker(worker_id)

    def mark_worker_down(self, worker_id: str, error: str) -> None:
        """Stop advertising a worker after pytest-xdist reports its process termination."""
        self.index.mark_worker_down(worker_id, error)


class _RegistryRequestHandler(BaseHTTPRequestHandler):
    server: _RegistryHTTPServer

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length > _MAX_REQUEST_BYTES:
            response: dict[str, Any] = {"ok": False, "error": "worker discovery record is too large"}
            self.close_connection = True
        else:
            try:
                request = json.loads(self.rfile.read(length) or b"{}")
                response = self.server.state.apply(request if isinstance(request, dict) else {})
            except (OSError, ValueError) as error:
                response = {"ok": False, "error": str(error)}
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        return


class _RegistryHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], state: DiscoveryRegistryState) -> None:
        super().__init__(address, _RegistryRequestHandler)
        self.state = state

    def server_bind(self) -> None:
        # Skip BaseHTTPServer's getfqdn reverse lookup: resolving 0.0.0.0 stalls on macOS.
        socketserver.TCPServer.server_bind(self)
        self.server_name = str(self.server_address[0])
        self.server_port = int(self.server_address[1])


class DiscoveryRegistry:
    """A running discovery registry owned by the xdist controller process."""

    __test__ = False

    def __init__(self, state: DiscoveryRegistryState, server: _RegistryHTTPServer, *, host: str) -> None:
        self.state = state
        self.host = host
        self._server = server
        self._thread = threading.Thread(
            target=server.serve_forever,
            name="pytest-cuke-debug-mcp-registry",
            daemon=True,
        )

    @property
    def port(self) -> int:
        """The TCP port the registry actually bound."""
        return int(self._server.server_address[1])

    @property
    def url(self) -> str:
        """The controller address workers and agents use."""
        return f"http://{self.host}:{self.port}"

    def start(self) -> DiscoveryRegistry:
        """Serve discovery requests until ``stop`` is called."""
        self._thread.start()
        return self

    def stop(self) -> None:
        """Stop serving and release the port."""
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def start_registry(
    *,
    host: str,
    port: int,
    index: XdistDiscoveryIndex,
    session_id: str,
    redact_patterns: tuple[str, ...] = (),
) -> DiscoveryRegistry:
    """Bind a registry on every interface so remote workers can reach the controller."""
    state = DiscoveryRegistryState(index, session_id=session_id, redact_patterns=redact_patterns)
    # shortcut: binds 0.0.0.0 so independent worker containers can connect;
    # add a bind-address setting if the registry must stay on a private interface.
    server = _RegistryHTTPServer(("0.0.0.0", port), state)  # noqa: S104
    return DiscoveryRegistry(state, server, host=host).start()


class DiscoveryRegistryClient:
    """Worker-side discovery transport for one controller registry address."""

    __test__ = False

    def __init__(
        self,
        address: str | tuple[str, int],
        *,
        worker_id: str,
        root_session_id: str,
        timeout: float = 5.0,
    ) -> None:
        parsed = parse_registry_address(address)
        if parsed is None:
            raise ValueError("Debug MCP discovery registry needs a HOST:PORT address")
        self.address: tuple[str, int] = parsed
        self.worker_id = worker_id
        self.root_session_id = root_session_id
        self.timeout = timeout
        self.label = f"{self.address[0]}:{self.address[1]}"

    def publish(self, record: dict[str, Any]) -> None:
        self._call({"op": "publish", "record": record})

    def remove(self, worker_id: str) -> None:
        self._call({"op": "remove", "worker_id": worker_id, "root_session_id": self.root_session_id})

    def _call(self, request: dict[str, Any]) -> dict[str, Any]:
        deadline = time.monotonic() + min(self.timeout, 10.0)
        last_error = "no response"
        while True:
            try:
                payload = self._post(request)
            except (OSError, ValueError) as error:
                last_error = f"{type(error).__name__}: {error}"
            else:
                if payload.get("ok"):
                    return payload
                last_error = str(payload.get("error") or "registry rejected the request")
            if time.monotonic() >= deadline:
                raise DiscoveryRegistryError(
                    f"Debug MCP discovery registry {self.label} did not accept {request.get('op')!r}: "
                    f"{last_error}. Start the controller registry with --cuke-mcp-registry=HOST:PORT "
                    "or use local pytest-xdist workers on a shared filesystem."
                )
            time.sleep(0.02)

    def _post(self, request: dict[str, Any]) -> dict[str, Any]:
        connection = http.client.HTTPConnection(self.address[0], self.address[1], timeout=min(2.0, self.timeout))
        try:
            connection.request(
                "POST",
                "/",
                body=json.dumps(request),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = json.loads(response.read() or b"{}")
        finally:
            connection.close()
        if not isinstance(payload, dict):
            raise ValueError(f"unexpected discovery registry response: {payload!r}")
        return payload


__all__ = [
    "DiscoveryRegistry",
    "DiscoveryRegistryClient",
    "DiscoveryRegistryError",
    "DiscoveryRegistryState",
    "parse_registry_address",
    "start_registry",
]
