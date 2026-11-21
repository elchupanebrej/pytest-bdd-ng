"""Bounded JSON-over-HTTP plumbing shared by controller-owned remote endpoints.

Each endpoint listens for workers that share no filesystem. The guards live
here so the relay and the debug registry cannot drift: one body cap, one socket
timeout, one address grammar, and one dual-stack bind.
"""

from __future__ import annotations

import json
import socket
import socketserver
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
from typing import Any

MAX_REQUEST_BYTES = 1_000_000
SOCKET_TIMEOUT_SECONDS = 5.0


def parse_host_port(
    value: str | tuple[str, int] | None,
    *,
    setting: str,
    example: str,
    allow_wildcard: bool = True,
) -> tuple[str, int] | None:
    """Parse a ``HOST:PORT`` setting, accepting brackets around an IPv6 host."""
    if isinstance(value, tuple):
        return value
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{setting} must be HOST:PORT or empty")
    text = (value or "").strip()
    if text.startswith("http://"):
        text = text.removeprefix("http://")
    if not text:
        return None

    host, separator, port_text = text.rpartition(":")
    port = int(port_text) if port_text.isdecimal() else 0
    if not separator or not host or not 0 < port <= 65535:
        raise ValueError(f"{setting} must be HOST:PORT, for example {example}, with a TCP port between 1 and 65535")

    host = _unbracketed_ipv6(host, setting=setting)
    if not allow_wildcard:
        try:
            address = ip_address(host)
        except ValueError:
            address = None
        if address is not None and address.is_unspecified:
            raise ValueError(f"{setting} cannot advertise a wildcard address; use a reachable controller host")
    return (host, port)


def format_host_port(host: str, port: int) -> str:
    """Format an address for diagnostics, bracketing an IPv6 host."""
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def bind_address_for(host: str, port: int) -> tuple[tuple[str, int], int]:
    """Choose the wildcard address and family that match the advertised host."""
    try:
        is_ipv6 = ip_address(host).version == 6
    except ValueError:
        is_ipv6 = False
    if is_ipv6:
        return ("::", port), socket.AF_INET6
    return ("0.0.0.0", port), socket.AF_INET  # noqa: S104


class JsonRequestHandler(BaseHTTPRequestHandler):
    """Serve one bounded JSON POST with a bounded socket timeout."""

    server: StatefulThreadingHTTPServer
    timeout = SOCKET_TIMEOUT_SECONDS

    def do_POST(self) -> None:
        length = self._content_length()
        if length is None:
            response: dict[str, Any] = {
                "ok": False,
                "error": "request body needs a non-negative decimal Content-Length",
            }
            self.close_connection = True
        elif length > MAX_REQUEST_BYTES:
            response = {"ok": False, "error": f"request body exceeds the {MAX_REQUEST_BYTES}-byte limit"}
            self.close_connection = True
        else:
            try:
                request = json.loads(self.rfile.read(length) or b"{}")
                response = self.server.state.apply(request if isinstance(request, dict) else {})
            except (OSError, ValueError) as error:
                response = {"ok": False, "error": str(error)}
        body = json.dumps(response).encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            return

    def _content_length(self) -> int | None:
        raw = self.headers.get("Content-Length")
        if raw is None:
            return 0
        try:
            length = int(raw)
        except ValueError:
            return None
        return length if length >= 0 else None

    def log_message(self, *args: Any) -> None:
        return


class StatefulThreadingHTTPServer(ThreadingHTTPServer):
    """A daemonized server whose bind family follows the advertised host."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], handler: type[JsonRequestHandler], state: Any, *, family: int) -> None:
        self.address_family = family
        super().__init__(address, handler)
        self.state = state

    def server_bind(self) -> None:
        if self.address_family == socket.AF_INET6:
            # Accept IPv4-mapped peers too where the platform allows it.
            with suppress(OSError):
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        # Skip BaseHTTPServer's getfqdn reverse lookup: resolving 0.0.0.0 stalls on macOS.
        socketserver.TCPServer.server_bind(self)
        self.server_name = str(self.server_address[0])
        self.server_port = int(self.server_address[1])


def _unbracketed_ipv6(host: str, *, setting: str) -> str:
    if not (host.startswith("[") or host.endswith("]")):
        return host
    if not (host.startswith("[") and host.endswith("]")):
        raise ValueError(f"{setting} has mismatched IPv6 brackets")
    inner = host[1:-1]
    try:
        address = ip_address(inner)
    except ValueError as error:
        raise ValueError(f"{setting} has an invalid bracketed IPv6 address") from error
    if address.version != 6:
        raise ValueError(f"{setting} brackets are only for IPv6 addresses")
    return str(address)


__all__ = [
    "MAX_REQUEST_BYTES",
    "SOCKET_TIMEOUT_SECONDS",
    "JsonRequestHandler",
    "StatefulThreadingHTTPServer",
    "bind_address_for",
    "format_host_port",
    "parse_host_port",
]
