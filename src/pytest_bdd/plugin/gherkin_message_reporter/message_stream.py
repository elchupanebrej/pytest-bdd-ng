"""Provide message stream helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, cast

import pytest

from pytest_bdd.model.message_transport import REPORTING_BATCH_EVENT

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class _WorkerControllerConfigProtocol(Protocol):
    hook: _WorkerControllerHookProtocol

    def notify_exception(self, excinfo: pytest.ExceptionInfo[BaseException]) -> None: ...


class _WorkerControllerHookProtocol(Protocol):
    def pytest_bdd_xdist_message_batch(
        self,
        *,
        config: _WorkerControllerConfigProtocol,
        node: _WorkerControllerProtocol,
        batch: dict[str, object],
    ) -> None: ...


class _WorkerControllerProtocol(Protocol):
    config: _WorkerControllerConfigProtocol

    def shutdown(self) -> None: ...

    def notify_inproc(self, event: str, **kwargs: object) -> None: ...


class _PatchedProcessFromRemote(Protocol):
    __pytest_bdd_reporting_patch__: bool

    def __call__(self, controller: _WorkerControllerProtocol, eventcall: object) -> None: ...


def coerce_reporting_batch_payload(batch_payload: object) -> dict[str, object]:
    """
    Coerce reporting batch payload to dictionary.

    Returns:
        Batch payload as dictionary.

    Raises:
        TypeError: If the operation cannot be completed.

    """
    if isinstance(batch_payload, dict):
        return batch_payload
    msg = "xdist reporter batch payload must be a dictionary"
    raise TypeError(msg)


def ensure_xdist_controller_batch_patch() -> bool:
    """
    Ensure xdist controller batch patch.

    Returns:
        True if patched, False otherwise.

    """
    try:
        from xdist import workermanage  # noqa: PLC0415 -- optional xdist dependency
    except ImportError:
        return False

    original = cast("Callable[[object, object], None]", workermanage.WorkerController.process_from_remote)
    if getattr(original, "__pytest_bdd_reporting_patch__", False):
        return True

    marker_end = workermanage.Marker.END

    def patched_process_from_remote(self: _WorkerControllerProtocol, eventcall: object) -> None:
        if eventcall is not marker_end and isinstance(eventcall, tuple) and len(eventcall) == 2:  # noqa: PLR2004
            event_name, kwargs = eventcall
            if event_name == REPORTING_BATCH_EVENT and isinstance(kwargs, dict):
                try:
                    batch_payload = coerce_reporting_batch_payload(kwargs.get("batch"))
                    self.config.hook.pytest_bdd_xdist_message_batch(
                        config=self.config,
                        node=self,
                        batch=batch_payload,
                    )
                except KeyboardInterrupt:
                    raise
                except Exception:
                    excinfo = pytest.ExceptionInfo.from_current()
                    logger.exception("Failed to process pytest-bdd xdist reporter batch.")
                    self.config.notify_exception(excinfo)
                    self.shutdown()
                    self.notify_inproc("errordown", node=self, error=excinfo)
                return
        original(self, eventcall)

    patched_process_from_remote_with_attr = cast("_PatchedProcessFromRemote", patched_process_from_remote)
    patched_process_from_remote_with_attr.__pytest_bdd_reporting_patch__ = True
    workermanage.WorkerController.process_from_remote = cast(
        "Callable[[object, object], None]",
        patched_process_from_remote_with_attr,
    )
    return True
