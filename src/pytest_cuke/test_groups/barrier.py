from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from filelock import FileLock

from pytest_cuke.test_groups.relay import RelayBarrierClient
from pytest_cuke.test_groups.transport import BarrierSnapshot, BarrierTransport

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_cuke.test_groups.assignment import TestGroupAssignment


_RETRYABLE_FILESYSTEM_ERRORS = {
    errno.EACCES,
    errno.EBUSY,
    errno.EEXIST,
    getattr(errno, "ETXTBSY", 26),
    getattr(errno, "EPIPE", 32),
    getattr(errno, "EDQUOT", 33),
}


class TestGroupBarrierTimeout(TimeoutError):
    """Raised when selected earlier-group tests fail to publish terminal receipts."""

    __test__ = False


class TestGroupBarrierWorkerDeath(TestGroupBarrierTimeout):
    """Raised when a worker died while it still owed earlier-group receipts."""

    __test__ = False


@dataclass(frozen=True, slots=True)
class _ExpectedItem:
    nodeid: str
    group: str
    ordinal: int


class FilesystemBarrierState:
    """Barrier state carried by a directory shared by local xdist workers."""

    __test__ = False

    def __init__(self, state_dir: Path, *, timeout: float) -> None:
        self.state_dir = state_dir
        self.timeout = timeout
        self.manifest_path = state_dir / "manifest.json"
        self.receipts_dir = state_dir / "receipts"
        self.lock_path = state_dir / "state.lock"

    def publish_manifest(self, manifest: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.lock_path), timeout=self.timeout):
            _write_json_atomically(self.manifest_path, manifest)

    def claim(self, nodeid: str) -> None:
        pass

    def publish_receipt(self, nodeid: str) -> None:
        manifest = _read_json_with_retry(self.manifest_path, timeout=self.timeout)
        if manifest is None:
            return
        item = next((entry for entry in manifest["items"] if entry["nodeid"] == nodeid), None)
        if item is None:
            return

        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = self._receipt_path(nodeid)
        with FileLock(str(self.lock_path), timeout=self.timeout):
            existing = _read_json_with_retry(receipt_path, timeout=self.timeout)
            if existing is not None:
                return
            _write_json_atomically(
                receipt_path,
                {"nodeid": nodeid, "group": item["group"], "ordinal": item["ordinal"]},
            )

    def snapshot(self) -> BarrierSnapshot:
        manifest = _read_json_with_retry(self.manifest_path, timeout=min(0.2, self.timeout))
        receipts: dict[str, dict[str, Any]] = {}
        if manifest is not None:
            for item in manifest["items"]:
                receipt = _read_json_with_retry(self._receipt_path(item["nodeid"]), timeout=0.2)
                if receipt is not None:
                    receipts[item["nodeid"]] = receipt
        return BarrierSnapshot(manifest=manifest, receipts=receipts)

    def _receipt_path(self, nodeid: str) -> Path:
        digest = hashlib.sha256(nodeid.encode("utf-8")).hexdigest()
        return self.receipts_dir / f"{digest}.json"


class TestGroupBarrier:
    """Coordinate selected xdist test completion through a transport of receipts."""

    __test__ = False

    def __init__(self, transport: BarrierTransport, *, timeout: float, groups: tuple[str, ...]) -> None:
        self.transport = transport
        self.timeout = timeout
        self.groups = groups

    @classmethod
    def for_state_directory(cls, state_dir: Path, *, timeout: float, groups: tuple[str, ...]) -> TestGroupBarrier:
        """Coordinate through the default shared state directory."""
        return cls(FilesystemBarrierState(state_dir, timeout=timeout), timeout=timeout, groups=groups)

    @classmethod
    def for_relay(
        cls,
        address: tuple[str, int],
        *,
        timeout: float,
        groups: tuple[str, ...],
        worker_id: str,
    ) -> TestGroupBarrier:
        """Coordinate through a socket relay when workers share no filesystem."""
        return cls(
            RelayBarrierClient(address, worker_id=worker_id, timeout=timeout),
            timeout=timeout,
            groups=groups,
        )

    @property
    def relay_label(self) -> str:
        """The relay address, or an empty string for the filesystem transport."""
        label = getattr(self.transport, "label", "")
        return label if isinstance(label, str) else ""

    def initialize(self, assignments: Iterable[TestGroupAssignment]) -> None:
        """Publish the selected node IDs and their groups before any barrier wait."""
        expected_by_nodeid: dict[str, _ExpectedItem] = {}
        for assignment in assignments:
            expected_by_nodeid.setdefault(
                assignment.nodeid,
                _ExpectedItem(assignment.nodeid, assignment.group, assignment.ordinal),
            )
        if not expected_by_nodeid:
            return

        self.transport.publish_manifest(
            {
                "groups": self.groups,
                "items": [
                    {"nodeid": item.nodeid, "group": item.group, "ordinal": item.ordinal}
                    for item in expected_by_nodeid.values()
                ],
            }
        )

    def claim(self, nodeid: str) -> None:
        """Record this worker as the owner of a selected item."""
        self.transport.claim(nodeid)

    def record_terminal(self, nodeid: str) -> None:
        """Publish one idempotent receipt for a selected test's terminal outcome."""
        self.transport.publish_receipt(nodeid)

    def wait_for_earlier_groups(self, assignment: TestGroupAssignment) -> None:
        """Wait until every selected item from an earlier configured group settled."""
        deadline = time.monotonic() + self.timeout
        missing: list[str] = []

        while time.monotonic() < deadline:
            snapshot = self.transport.snapshot()
            if snapshot.manifest is not None:
                expected = [item for item in snapshot.manifest["items"] if item["ordinal"] < assignment.ordinal]
                unfinished = [
                    item for item in expected if not _receipt_matches(snapshot.receipts.get(item["nodeid"]), item)
                ]
                missing = [item["nodeid"] for item in unfinished]
                if not missing:
                    return
                dead = sorted(
                    {
                        snapshot.owners.get(nodeid, "")
                        for nodeid in missing
                        if snapshot.owners.get(nodeid) in snapshot.dead_workers
                    }
                )
                deaths = [diagnostic for worker in dead if (diagnostic := dead_worker_diagnostic(snapshot, worker))]
                if deaths:
                    raise TestGroupBarrierWorkerDeath(
                        f"{'; '.join(deaths)} before group {assignment.group!r} at {assignment.nodeid!r}. "
                        f"The next group will not open; check the worker crash output and the barrier relay "
                        f"at {self.relay_label}."
                    )
            time.sleep(min(0.05, max(0.001, deadline - time.monotonic())))

        group_names = ", ".join(repr(group) for group in self.groups[: assignment.ordinal]) or "(none)"
        details = f"; still waiting for {', '.join(missing[:3])}" if missing else "; run manifest was not published"
        if self.relay_label:
            raise TestGroupBarrierTimeout(
                f"Timed out after {self.timeout:g}s waiting for earlier test group(s) {group_names} "
                f"to settle before group {assignment.group!r} at {assignment.nodeid!r}{details}. "
                f"Check worker health and the barrier relay at {self.relay_label}; later groups stay closed "
                "until every earlier selected test publishes a terminal receipt."
            )
        raise TestGroupBarrierTimeout(
            f"Timed out after {self.timeout:g}s waiting for earlier test group(s) {group_names} "
            f"to settle before group {assignment.group!r} at {assignment.nodeid!r}{details}. "
            "Check worker health and the shared filesystem prerequisite for all local xdist workers. "
            "Non-shared remote workers are unsupported."
        )


def dead_worker_diagnostic(snapshot: BarrierSnapshot, worker: str) -> str | None:
    """Name the group and tests a dead worker still owed receipts for, if any."""
    if snapshot.manifest is None:
        return None
    pending = [
        item
        for item in snapshot.manifest["items"]
        if snapshot.owners.get(item["nodeid"]) == worker
        and not _receipt_matches(snapshot.receipts.get(item["nodeid"]), item)
    ]
    if not pending:
        return None
    groups = ", ".join(repr(group) for group in dict.fromkeys(item["group"] for item in pending))
    nodeids = ", ".join(item["nodeid"] for item in pending[:3])
    return (
        f"xdist worker {worker!r} stopped before publishing terminal receipts "
        f"for earlier test group(s) {groups}: {nodeids}"
    )


def _receipt_matches(receipt: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
    return bool(
        receipt is not None
        and receipt.get("nodeid") == expected["nodeid"]
        and receipt.get("group") == expected["group"]
        and receipt.get("ordinal") == expected["ordinal"]
    )


def _write_json_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    deadline: float | None = None

    while True:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(encoded)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, path)
            return
        except OSError as error:
            if error.errno not in _RETRYABLE_FILESYSTEM_ERRORS:
                raise
            now = time.monotonic()
            if deadline is None:
                deadline = now + 2.0
            elif now >= deadline:
                raise
            time.sleep(0.02)
        finally:
            if temporary_path is not None:
                with suppress(OSError):
                    temporary_path.unlink(missing_ok=True)


def _read_json_with_retry(path: Path, *, timeout: float) -> dict[str, Any] | None:
    deadline = time.monotonic() + max(timeout, 0.0)
    while True:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, UnicodeDecodeError):
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.01)
        except OSError as error:
            if error.errno not in _RETRYABLE_FILESYSTEM_ERRORS or time.monotonic() >= deadline:
                if error.errno in _RETRYABLE_FILESYSTEM_ERRORS:
                    return None
                raise
            time.sleep(0.01)
