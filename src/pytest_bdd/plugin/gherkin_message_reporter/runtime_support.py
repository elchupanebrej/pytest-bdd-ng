"""Provide runtime support helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.model.message_transport import resolve_reporting_gateway_mode
from pytest_bdd.util.live_reporting import is_xdist_worker_process, resolve_reporting_worker_identity

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config


def _is_xdist_worker_process(config: Config) -> bool:
    return bool(is_xdist_worker_process(config))


def _resolve_reporting_gateway_mode(config: Config) -> str:
    gateway_mode = resolve_reporting_gateway_mode(config)
    return "" if gateway_mode is None else str(gateway_mode)


def _resolve_reporting_worker_identity(config: Config) -> tuple[str, str | None]:
    worker_id, gateway_mode = resolve_reporting_worker_identity(
        config,
        gateway_mode_resolver=_resolve_reporting_gateway_mode,
    )
    return str(worker_id), None if gateway_mode is None else str(gateway_mode)


def _format_reporting_worker_id(worker_id: str, gateway_mode: str | None) -> str:
    if gateway_mode is None or gateway_mode == "popen" or worker_id == "master":
        return worker_id
    return f"{gateway_mode}:{worker_id}"


@frozen
class HookRegistration:
    """Represent hook registration state."""

    hook_message_id: str
    expression: str
    kind: str
