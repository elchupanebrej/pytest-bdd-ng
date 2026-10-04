from __future__ import annotations

import json
import os
import threading
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
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
    ) -> None:
        self.path = path
        self._lock = threading.Lock()
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
            self.path.unlink(missing_ok=True)

    def _write_locked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump(self._record, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
