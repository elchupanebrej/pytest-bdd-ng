from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_cuke.debug_mcp.options import (
    DebugMcpOptions,
    _host,
    parse_duration,
    parse_port,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("30s", 30.0), ("250ms", 0.25), ("2m", 120.0), ("1.5", 1.5)],
)
def test_parse_duration_accepts_positive_finite_seconds(value: str, expected: float) -> None:
    assert parse_duration(value) == expected


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf", "nonsense", "1sec", "2min", "1hr"])
def test_parse_duration_rejects_non_positive_or_non_finite_values(value: str) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        parse_duration(value)


@pytest.mark.parametrize(("value", "expected"), [("auto", "auto"), ("65535", 65535), ("1", 1)])
def test_parse_port_accepts_auto_or_valid_port(value: str, expected: int | str) -> None:
    assert parse_port(value) == expected


@pytest.mark.parametrize("value", ["0", "65536", "-1", "1.5", "nope"])
def test_parse_port_rejects_values_outside_the_port_range(value: str) -> None:
    with pytest.raises(ValueError, match=r"auto.*1.*65535"):
        parse_port(value)


def test_debug_mcp_options_use_cli_values_before_ini_values() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(
            cuke_mcp_on_fail=True,
            cuke_mcp_timeout=45.0,
            cuke_mcp_lease=None,
            cuke_mcp_host=None,
            cuke_mcp_port=8765,
        ),
        getini=lambda name: {
            "cuke_mcp_on_fail": False,
            "cuke_mcp_timeout": "30s",
            "cuke_mcp_lease": "12s",
            "cuke_mcp_host": "localhost",
            "cuke_mcp_port": "9000",
        }[name],
    )

    options = DebugMcpOptions.from_config(config)

    assert options.enabled is True
    assert options.timeout_seconds == 45.0
    assert options.lease_seconds == 12.0
    assert options.host == "localhost"
    assert options.port == 8765


def test_debug_mcp_options_have_inert_loopback_defaults() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(
            cuke_mcp_on_fail=None,
            cuke_mcp_timeout=None,
            cuke_mcp_lease=None,
            cuke_mcp_host=None,
            cuke_mcp_port=None,
        ),
        getini=lambda name: {
            "cuke_mcp_on_fail": False,
            "cuke_mcp_timeout": "30s",
            "cuke_mcp_lease": "10s",
            "cuke_mcp_host": "127.0.0.1",
            "cuke_mcp_port": "auto",
        }[name],
    )

    options = DebugMcpOptions.from_config(config)

    assert options.enabled is False
    assert options.timeout_seconds == 30.0
    assert options.lease_seconds == 10.0
    assert options.host == "127.0.0.1"
    assert options.port is None


def test_debug_mcp_options_reject_invalid_ini_values() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(
            cuke_mcp_on_fail=None,
            cuke_mcp_timeout=None,
            cuke_mcp_lease=None,
            cuke_mcp_host=None,
            cuke_mcp_port=None,
        ),
        getini=lambda name: {
            "cuke_mcp_on_fail": False,
            "cuke_mcp_timeout": "nan",
            "cuke_mcp_lease": "10s",
            "cuke_mcp_host": "127.0.0.1",
            "cuke_mcp_port": "auto",
        }[name],
    )

    with pytest.raises(ValueError, match="positive finite"):
        DebugMcpOptions.from_config(config)


def test_bracketed_ipv6_host_is_normalized_for_bind_and_url_use() -> None:
    assert _host("[::1]") == "::1"


@pytest.mark.parametrize("value", ["0.0.0.0", "::"])
def test_wildcard_host_is_rejected_because_it_cannot_be_advertised(value: str) -> None:
    with pytest.raises(ValueError, match=r"wildcard.*advertised"):
        _host(value)


@pytest.mark.parametrize("value", ["[localhost]", "[::1", "::1]"])
def test_invalid_bracketed_host_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match=r"IPv6 brackets|IPv6 address"):
        _host(value)
