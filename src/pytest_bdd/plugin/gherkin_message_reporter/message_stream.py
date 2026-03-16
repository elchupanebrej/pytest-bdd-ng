from __future__ import annotations

import logging
from typing import Any

import pytest

from pytest_bdd.model.message_transport import REPORTING_BATCH_EVENT

logger = logging.getLogger(__name__)


def coerce_reporting_batch_payload(batch_payload: object) -> dict[str, Any]:
    if isinstance(batch_payload, dict):
        return batch_payload
    msg = "xdist reporter batch payload must be a dictionary"
    raise TypeError(msg)


def ensure_xdist_controller_batch_patch() -> bool:
    try:
        import xdist.workermanage as workermanage
    except ImportError:
        return False

    original = workermanage.WorkerController.process_from_remote
    if getattr(original, "__pytest_bdd_reporting_patch__", False):
        return True

    marker_end = workermanage.Marker.END

    def patched_process_from_remote(self: Any, eventcall: Any) -> None:
        if eventcall is not marker_end:
            event_name, kwargs = eventcall
            if event_name == REPORTING_BATCH_EVENT:
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
        return

    patched_process_from_remote.__pytest_bdd_reporting_patch__ = True
    workermanage.WorkerController.process_from_remote = patched_process_from_remote
    return True
