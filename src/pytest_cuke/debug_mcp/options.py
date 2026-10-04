from __future__ import annotations

import math
import re
from dataclasses import dataclass
from ipaddress import ip_address
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser

_DURATION_SUFFIXES = {
    "ms": 0.001,
    "sec": 1.0,
    "min": 60.0,
    "hr": 3600.0,
    "s": 1.0,
    "m": 60.0,
    "h": 3600.0,
}
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.IGNORECASE)


def parse_duration(value: str | float | int) -> float:
    """Parse a positive finite duration, accepting bare seconds and common suffixes."""
    text = str(value).strip().lower()
    multiplier = 1.0
    numeric_text = text
    for suffix, factor in sorted(_DURATION_SUFFIXES.items(), key=lambda item: -len(item[0])):
        if text.endswith(suffix):
            numeric_text = text[: -len(suffix)].strip()
            multiplier = factor
            break
    try:
        if not _NUMBER.fullmatch(numeric_text):
            raise ValueError
        duration = float(numeric_text) * multiplier
    except ValueError as error:
        raise ValueError(f"duration must be a positive finite value in seconds; got {value!r}") from error
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"duration must be a positive finite value in seconds; got {value!r}")
    return duration


def parse_port(value: str | int) -> int | str:
    """Parse a fixed TCP port or preserve ``auto`` so it can override ini settings."""
    text = str(value).strip().lower()
    if text == "auto":
        return "auto"
    try:
        port = int(text)
    except ValueError as error:
        raise ValueError(f"port must be 'auto' or an integer from 1 to 65535; got {value!r}") from error
    if not 1 <= port <= 65535:
        raise ValueError(f"port must be 'auto' or an integer from 1 to 65535; got {value!r}")
    return port


def _host(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("cuke_mcp_host must be a non-empty host name or IP address")
    host = value.strip()
    if host.startswith("[") or host.endswith("]"):
        if not host.startswith("[") or not host.endswith("]"):
            raise ValueError("cuke_mcp_host has mismatched IPv6 brackets")
        try:
            address = ip_address(host[1:-1])
        except ValueError as error:
            raise ValueError("bracketed cuke_mcp_host must be an IPv6 address") from error
        if address.version != 6:
            raise ValueError("bracketed cuke_mcp_host must be an IPv6 address")
        return str(address)
    return host


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dataclass(frozen=True, slots=True)
class DebugMcpOptions:
    enabled: bool = False
    timeout_seconds: float = 30.0
    lease_seconds: float = 10.0
    host: str = "127.0.0.1"
    port: int | None = None

    @classmethod
    def from_config(cls, config: Config) -> DebugMcpOptions:
        """Resolve pytest CLI values before their corresponding ini settings."""
        option = getattr(config, "option", None)

        def configured(name: str, ini_name: str) -> Any:
            cli_value = getattr(option, name, None)
            return config.getini(ini_name) if cli_value is None else cli_value

        enabled = _as_bool(configured("cuke_mcp_on_fail", "cuke_mcp_on_fail"))
        timeout = parse_duration(configured("cuke_mcp_timeout", "cuke_mcp_timeout"))
        lease = parse_duration(configured("cuke_mcp_lease", "cuke_mcp_lease"))
        host = _host(configured("cuke_mcp_host", "cuke_mcp_host"))
        raw_port = configured("cuke_mcp_port", "cuke_mcp_port")
        parsed_port = parse_port(raw_port)
        if parsed_port == "auto":
            port = None
        else:
            assert isinstance(parsed_port, int)
            port = parsed_port
        return cls(
            enabled=enabled,
            timeout_seconds=timeout,
            lease_seconds=lease,
            host=host,
            port=port,
        )

    @property
    def uses_nonlocal_host(self) -> bool:
        host = self.host.strip("[]").lower()
        if host == "localhost":
            return False
        try:
            return not ip_address(host).is_loopback
        except ValueError:
            return True


def add_options(parser: Parser) -> None:
    """Register opt-in CLI and ini controls without importing an optional backend."""
    group = parser.getgroup("cuke", "Debug MCP failure inspection")
    group.addoption(
        "--cuke-mcp-on-fail",
        action="store_true",
        dest="cuke_mcp_on_fail",
        default=None,
        help="start MCP debugger and hold failed pytest reports for external inspection",
    )
    group.addoption(
        "--cuke-mcp-timeout",
        action="store",
        dest="cuke_mcp_timeout",
        metavar="DURATION",
        type=parse_duration,
        default=None,
        help="maximum time to hold a failed report (default: 30 seconds; suffixes: ms, s, m, h)",
    )
    group.addoption(
        "--cuke-mcp-lease",
        action="store",
        dest="cuke_mcp_lease",
        metavar="DURATION",
        type=parse_duration,
        default=None,
        help="release a held report after this long without a valid heartbeat (default: 10 seconds)",
    )
    group.addoption(
        "--cuke-mcp-host",
        action="store",
        dest="cuke_mcp_host",
        metavar="HOST",
        default=None,
        help="interface used by the Debug MCP servers (default: 127.0.0.1)",
    )
    group.addoption(
        "--cuke-mcp-port",
        action="store",
        dest="cuke_mcp_port",
        metavar="PORT|auto",
        type=parse_port,
        default=None,
        help="debugger MCP port, or auto (default: auto)",
    )
    parser.addini(
        "cuke_mcp_on_fail",
        "Hold failed pytest reports for Debug MCP inspection.",
        default=False,
        type="bool",
    )
    parser.addini("cuke_mcp_timeout", "Maximum Debug MCP failure hold, as a positive duration.", default="30s")
    parser.addini("cuke_mcp_lease", "Debug MCP heartbeat lease, as a positive duration.", default="10s")
    parser.addini("cuke_mcp_host", "Debug MCP server bind host.", default="127.0.0.1")
    parser.addini("cuke_mcp_port", "Debug MCP debugger port, or auto.", default="auto")
