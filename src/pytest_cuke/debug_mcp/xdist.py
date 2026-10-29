from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from filelock import FileLock, Timeout

from pytest_cuke.debug_mcp.json_io import write_json_atomically

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class XdistDiscoveryError(RuntimeError):
    """A worker discovery record could not be published or read safely."""


class XdistDiscoveryIndex:
    """Publish a deterministic root index for independently managed xdist workers."""

    def __init__(self, *, path: Path, workers_dir: Path, session_id: str, lock_timeout: float = 5.0) -> None:
        self.path = path
        self.workers_dir = workers_dir
        self.session_id = session_id
        self.lock_timeout = lock_timeout
        self.lock_path = path.with_suffix(".lock")

    def initialize(self) -> None:
        """Replace stale discovery with an empty index for the current pytest run."""
        self._ensure_directory(self.path.parent, "worker discovery root directory")
        self._ensure_directory(self.workers_dir, "worker discovery workers directory")
        with self._locked():
            for path in self.workers_dir.iterdir():
                if path.is_file() or path.is_symlink():
                    path.unlink(missing_ok=True)
            self._write_index_locked([], "waiting")

    def clear_previous(self) -> None:
        """Remove an old xdist index before a standalone Debug MCP session starts."""
        self._ensure_directory(self.path.parent, "worker discovery root directory")
        with self._locked():
            self.path.unlink(missing_ok=True)
            if self.workers_dir.exists():
                for path in self.workers_dir.glob("*.json"):
                    path.unlink(missing_ok=True)

    def register_worker(self, worker_id: str) -> None:
        """Publish a bounded starting record before xdist starts the worker process."""
        self._validate_worker_id(worker_id)
        record: dict[str, Any] = {
            "root_session_id": self.session_id,
            "worker_id": worker_id,
            "session_id": None,
            "status": "starting",
            "debugger_endpoint": None,
            "inspection_endpoint": None,
            "active_failure": None,
            "last_release": None,
        }
        self._write_worker(record)

    def publish_worker(self, record: dict[str, Any]) -> None:
        """Refresh the root index after one worker atomically publishes its own state."""
        worker_id = self._record_worker_id(record)
        if record.get("root_session_id") != self.session_id:
            raise XdistDiscoveryError(f"worker {worker_id!r} belongs to a different pytest session")
        self._write_worker(record)

    def mark_worker_down(self, worker_id: str, error: str) -> None:
        """Stop advertising a worker's endpoints after xdist reports process termination."""
        self._validate_worker_id(worker_id)
        with self._locked():
            index = self._read_index_locked()
            if index.get("session_id") != self.session_id:
                raise XdistDiscoveryError("the root discovery index belongs to a different pytest session")
            cached_workers = index.get("workers")
            cached_record = next(
                (
                    dict(record)
                    for record in cached_workers
                    if isinstance(record, dict) and record.get("worker_id") == worker_id
                ),
                None,
            ) if isinstance(cached_workers, list) else None
            if cached_record is not None and cached_record.get("root_session_id") != self.session_id:
                raise XdistDiscoveryError(f"worker {worker_id!r} has a stale root discovery record")
            worker_path = self.worker_path(worker_id)
            invalid_record_error: str | None = None
            if worker_path.exists():
                try:
                    record = self._read_json(worker_path)
                except XdistDiscoveryError as read_error:
                    invalid_record_error = str(read_error)
                    record = cached_record or {
                        "root_session_id": self.session_id,
                        "worker_id": worker_id,
                        "session_id": None,
                        "active_failure": None,
                        "last_release": None,
                    }
                    try:
                        worker_path.unlink(missing_ok=True)
                    except OSError as unlink_error:
                        raise XdistDiscoveryError(
                            f"could not replace invalid worker discovery file {worker_path}: {unlink_error}"
                        ) from unlink_error
                else:
                    record_worker_id = record.get("worker_id")
                    record_matches = (
                        record_worker_id == worker_id
                        and record.get("root_session_id") == self.session_id
                    )
                    if not record_matches:
                        if (
                            isinstance(record_worker_id, str)
                            and record_worker_id != worker_id
                            and self.worker_path(record_worker_id) == worker_path
                        ):
                            raise XdistDiscoveryError(f"worker discovery identity collision at {worker_path}")
                        if cached_record is None:
                            raise XdistDiscoveryError(f"worker discovery identity mismatch at {worker_path}")
                        invalid_record_error = f"worker discovery identity mismatch at {worker_path}"
                        record = cached_record
                        try:
                            worker_path.unlink(missing_ok=True)
                        except OSError as unlink_error:
                            raise XdistDiscoveryError(
                                f"could not replace invalid worker discovery file {worker_path}: {unlink_error}"
                            ) from unlink_error
                    elif cached_record is not None and record.get("session_id") != cached_record.get("session_id"):
                        invalid_record_error = f"worker discovery session ID mismatch at {worker_path}"
                        record = cached_record
                        try:
                            worker_path.unlink(missing_ok=True)
                        except OSError as unlink_error:
                            raise XdistDiscoveryError(
                                f"could not replace invalid worker discovery file {worker_path}: {unlink_error}"
                            ) from unlink_error
            else:
                record = cached_record or {
                    "root_session_id": self.session_id,
                    "worker_id": worker_id,
                    "session_id": None,
                    "active_failure": None,
                    "last_release": None,
            }
            worker_error = error[:500]
            if invalid_record_error is not None:
                worker_error = (
                    f"{worker_error}; recovered cached state after an invalid worker record: "
                    f"{invalid_record_error}"
                )[:500]
            record.update(
                status="worker_crashed",
                debugger_endpoint=None,
                inspection_endpoint=None,
                worker_error=worker_error,
            )
            self._write_worker_locked(worker_id, record)
            workers = self._read_workers_locked()
            self._write_index_locked(workers, _combined_status(workers))

    def remove_worker(self, worker_id: str) -> None:
        """Remove a worker that failed startup before it exposed usable endpoints."""
        self._validate_worker_id(worker_id)
        with self._locked():
            index = self._read_index_locked()
            if index.get("session_id") != self.session_id:
                raise XdistDiscoveryError("the root discovery index belongs to a different pytest session")
            self.worker_path(worker_id).unlink(missing_ok=True)
            workers = self._read_workers_locked()
            self._write_index_locked(workers, _combined_status(workers))

    def worker_is_closed(self, worker_id: str) -> bool:
        """Check whether a worker left a valid closed record before its process exited."""
        self._validate_worker_id(worker_id)
        with self._locked():
            index = self._read_index_locked()
            if index.get("session_id") != self.session_id:
                raise XdistDiscoveryError("the root discovery index belongs to a different pytest session")
            cached_workers = index.get("workers")
            cached_record = next(
                (
                    worker
                    for worker in cached_workers
                    if isinstance(worker, dict) and worker.get("worker_id") == worker_id
                ),
                None,
            ) if isinstance(cached_workers, list) else None
            worker_path = self.worker_path(worker_id)
            record = self._read_json(worker_path) if worker_path.exists() else cached_record
            if record is None:
                return False
            if record.get("worker_id") != worker_id or record.get("root_session_id") != self.session_id:
                raise XdistDiscoveryError(f"worker {worker_id!r} has an invalid discovery identity")
            if cached_record is None:
                return False
            if cached_record.get("root_session_id") != self.session_id:
                raise XdistDiscoveryError(f"worker {worker_id!r} has a stale root discovery record")
            session_id = record.get("session_id")
            if not isinstance(session_id, str) or not session_id or cached_record.get("session_id") != session_id:
                return False
            return (
                record.get("status") == "closed"
                and record.get("debugger_endpoint") is None
                and record.get("inspection_endpoint") is None
                and cached_record.get("status") == "closed"
                and cached_record.get("debugger_endpoint") is None
                and cached_record.get("inspection_endpoint") is None
            )

    def close(self) -> None:
        """Mark the index closed after worker shutdown and remove all live endpoints."""
        with self._locked():
            index = self._read_index_locked()
            if index.get("session_id") != self.session_id:
                raise XdistDiscoveryError("refusing to close another pytest session's worker index")
            workers = self._read_workers_locked()
            for worker in workers:
                if worker.get("status") not in {"closed", "worker_crashed"}:
                    worker.update(
                        status="worker_crashed",
                        debugger_endpoint=None,
                        inspection_endpoint=None,
                        worker_error="worker did not publish a closed discovery record",
                    )
                    self._write_worker_locked(self._record_worker_id(worker), worker)
            workers = self._read_workers_locked()
            self._write_index_locked(workers, "closed")

    def remove(self) -> None:
        """Remove this run's root index when Debug MCP startup fails."""
        with self._locked():
            if self.path.exists():
                index = self._read_index_locked()
                if index.get("session_id") != self.session_id:
                    raise XdistDiscoveryError("refusing to remove another pytest session's worker index")
                self.path.unlink(missing_ok=True)
            if self.workers_dir.exists():
                for path in self.workers_dir.glob("*.json"):
                    record = self._read_json(path)
                    if record.get("root_session_id") == self.session_id:
                        path.unlink(missing_ok=True)

    def worker_path(self, worker_id: str) -> Path:
        """Return a traversal-safe path while preserving the original ID in the record."""
        return self.workers_dir / f"{safe_worker_id(worker_id)}.json"

    def _write_worker(self, record: dict[str, Any]) -> None:
        worker_id = self._record_worker_id(record)
        with self._locked():
            index = self._read_index_locked()
            if index.get("session_id") != self.session_id:
                raise XdistDiscoveryError("the root discovery index belongs to a different pytest session")
            self._write_worker_locked(worker_id, record)
            workers = self._read_workers_locked()
            self._write_index_locked(workers, _combined_status(workers))

    def _write_worker_locked(self, worker_id: str, record: dict[str, Any]) -> None:
        self._ensure_directory(self.workers_dir, "worker discovery workers directory")
        path = self.worker_path(worker_id)
        if path.exists():
            previous = self._read_json(path)
            previous_id = previous.get("worker_id")
            if previous_id != worker_id:
                raise XdistDiscoveryError(
                    f"worker IDs {previous_id!r} and {worker_id!r} map to the same safe discovery filename"
                )
        self._write_atomically(path, record)

    def _read_workers_locked(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if not self.workers_dir.exists():
            return records
        for path in sorted(self.workers_dir.glob("*.json")):
            record = self._read_json(path)
            worker_id = record.get("worker_id")
            if not isinstance(worker_id, str) or not worker_id:
                raise XdistDiscoveryError(f"worker discovery record has no worker ID: {path}")
            self._validate_worker_id(worker_id)
            if record.get("root_session_id") != self.session_id:
                raise XdistDiscoveryError(f"stale worker discovery record belongs to another session: {path}")
            if path != self.worker_path(worker_id):
                raise XdistDiscoveryError(f"worker discovery filename does not match its identity: {path}")
            records.append(record)
        records.sort(key=lambda record: str(record["worker_id"]))
        return records

    def _read_index_locked(self) -> dict[str, Any]:
        if not self.path.exists():
            raise XdistDiscoveryError(f"root worker discovery index is missing: {self.path}")
        return self._read_json(self.path)

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise XdistDiscoveryError(f"could not read worker discovery file {path}: {error}") from error
        if not isinstance(payload, dict):
            raise XdistDiscoveryError(f"worker discovery file must contain a JSON object: {path}")
        return payload

    @staticmethod
    def _ensure_directory(path: Path, description: str) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise XdistDiscoveryError(f"could not create {description} {path}: {error}") from error

    def _write_index_locked(self, workers: list[dict[str, Any]], status: str) -> None:
        self._ensure_directory(self.path.parent, "worker discovery root directory")
        self._write_atomically(
            self.path,
            {
                "session_id": self.session_id,
                "process_id": os.getpid(),
                "status": status,
                "workers": workers,
            },
        )

    @staticmethod
    def _write_atomically(path: Path, payload: dict[str, Any]) -> None:
        try:
            write_json_atomically(path, payload)
        except OSError as error:
            raise XdistDiscoveryError(f"could not publish worker discovery file {path}: {error}") from error

    @contextmanager
    def _locked(self) -> Iterator[None]:
        lock = FileLock(str(self.lock_path), timeout=self.lock_timeout)
        try:
            lock.acquire(timeout=self.lock_timeout)
        except (OSError, Timeout) as error:
            raise XdistDiscoveryError(f"could not acquire worker discovery lock {self.lock_path}: {error}") from error
        try:
            yield
        finally:
            try:
                lock.release()
            except OSError as error:
                raise XdistDiscoveryError(
                    f"could not release worker discovery lock {self.lock_path}: {error}"
                ) from error

    @staticmethod
    def _record_worker_id(record: dict[str, Any]) -> str:
        worker_id = record.get("worker_id")
        if not isinstance(worker_id, str) or not worker_id:
            raise XdistDiscoveryError("worker discovery record must include a non-empty worker ID")
        XdistDiscoveryIndex._validate_worker_id(worker_id)
        return worker_id

    @staticmethod
    def _validate_worker_id(worker_id: str) -> None:
        if not worker_id.strip():
            raise XdistDiscoveryError("worker ID cannot be empty")


def safe_worker_id(worker_id: str) -> str:
    """Keep normal xdist IDs readable and hash any transformed or truncated gateway ID."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", worker_id).strip("-._")
    if not slug:
        slug = "worker"
    if slug == worker_id and len(slug) <= 80:
        return slug
    digest = hashlib.sha256(worker_id.encode("utf-8")).hexdigest()[:16]
    return f"{slug[:60].rstrip('-._') or 'worker'}-{digest}"


def xdist_worker_id(config: Any) -> str | None:
    """Read the xdist identity while retaining gateway-provided names when present."""
    worker_input = getattr(config, "workerinput", None)
    if not isinstance(worker_input, dict):
        return None
    for key in ("workerid", "gateway", "gateway_id"):
        worker_id = worker_input.get(key)
        if isinstance(worker_id, str) and worker_id.strip():
            return worker_id
    raise XdistDiscoveryError("pytest-xdist worker configuration has no worker or gateway identity")


def xdist_root_session_id(config: Any) -> str | None:
    """Read the controller-generated run identity propagated to an xdist worker."""
    worker_input = getattr(config, "workerinput", None)
    if not isinstance(worker_input, dict):
        return None
    session_id = worker_input.get("cuke_debug_mcp_root_session_id")
    if not isinstance(session_id, str) or not session_id:
        raise XdistDiscoveryError("pytest-xdist worker did not receive the Debug MCP root session ID")
    return session_id


def is_xdist_controller(config: Any) -> bool:
    """Detect the xdist controller without importing or requiring pytest-xdist."""
    pluginmanager = getattr(config, "pluginmanager", None)
    if pluginmanager is not None and pluginmanager.get_plugin("dsession") is not None:
        return True
    option = getattr(config, "option", None)
    numprocesses = getattr(option, "numprocesses", 0)
    if isinstance(numprocesses, str):
        if numprocesses.strip().lower() not in {"", "0", "none"}:
            return True
    elif numprocesses not in {None, 0}:
        return True
    transactions = getattr(option, "tx", ()) or ()
    return bool(transactions)


def is_local_xdist_spec(spec: Any) -> bool:
    """Recognize xdist's local popen gateways without importing its optional API."""
    popen = getattr(spec, "popen", None)
    if popen is not None:
        return bool(popen)
    value = str(spec)
    if "'" in value:
        value = value.split("'", 1)[1].rsplit("'", 1)[0]
    return value.startswith("popen")


def _combined_status(workers: list[dict[str, Any]]) -> str:
    if any(worker.get("status") == "holding_failure" for worker in workers):
        return "holding_failure"
    if workers and all(worker.get("status") in {"closed", "worker_crashed"} for worker in workers):
        return "closed"
    return "waiting"


__all__ = [
    "XdistDiscoveryError",
    "XdistDiscoveryIndex",
    "is_local_xdist_spec",
    "is_xdist_controller",
    "safe_worker_id",
    "xdist_root_session_id",
    "xdist_worker_id",
]
