from __future__ import annotations

import os
import threading
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from pytest_cuke.debug_mcp.json_io import write_json_atomically

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class DiscoveryPublisher:
    """Atomically publish the endpoints and current failure for one pytest process."""

    def __init__(
        self,
        *,
        path: Path,
        session_id: str,
        host: str,
        debugger_endpoint: str,
        inspection_endpoint: str,
        debugger_pid: int,
        worker_id: str | None = None,
        root_session_id: str | None = None,
        on_publish: Callable[[dict[str, Any]], None] | None = None,
        on_remove: Callable[[str], None] | None = None,
    ) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._worker_id = worker_id
        self._on_publish = on_publish
        self._on_remove = on_remove
        self._record: dict[str, Any] = {
            "session_id": session_id,
            "status": "waiting",
            "host": host,
            "process_id": os.getpid(),
            "debugger_pid": debugger_pid,
            "debugger_endpoint": debugger_endpoint,
            "inspection_endpoint": inspection_endpoint,
            "active_failure": None,
            "last_release": None,
        }
        if worker_id is not None:
            if not root_session_id or on_publish is None or on_remove is None:
                raise ValueError("worker discovery requires a root session ID and index callbacks")
            self._record["root_session_id"] = root_session_id
            self._record["worker_id"] = worker_id

    def write_initial(self) -> None:
        with self._lock:
            self._write_locked()

    def publish_queue_state(self, state: dict[str, Any]) -> None:
        with self._lock:
            self._record.update(state)
            if state.get("status") == "closed":
                self._record["debugger_endpoint"] = None
                self._record["inspection_endpoint"] = None
            self._write_locked()

    def close(self, last_release: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._record.update(
                status="closed",
                debugger_endpoint=None,
                inspection_endpoint=None,
                active_failure=None,
            )
            if last_release is not None:
                self._record["last_release"] = last_release
            self._write_locked()

    def remove(self) -> None:
        with self._lock:
            if self._worker_id is not None and self._on_remove is not None:
                self._on_remove(self._worker_id)
            else:
                self.path.unlink(missing_ok=True)

    def _write_locked(self) -> None:
        if self._on_publish is None:
            write_json_atomically(self.path, self._record)
        else:
            self._on_publish(deepcopy(self._record))
