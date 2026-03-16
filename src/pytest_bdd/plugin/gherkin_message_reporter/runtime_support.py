from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.model.message_transport import resolve_reporting_gateway_mode
from pytest_bdd.util.live_reporting import is_xdist_worker_process, resolve_reporting_worker_identity

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config


def _is_xdist_worker_process(config: Config) -> bool:
    return is_xdist_worker_process(config)


def _resolve_reporting_worker_identity(config: Config) -> tuple[str, str | None]:
    return resolve_reporting_worker_identity(config, gateway_mode_resolver=resolve_reporting_gateway_mode)


@frozen
class HookRegistration:
    hook_message_id: str
    expression: str
    kind: str
