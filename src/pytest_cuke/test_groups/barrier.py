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


@dataclass(frozen=True, slots=True)
class _ExpectedItem:
    nodeid: str
    group: str
    ordinal: int


class TestGroupBarrier:
    """Coordinate selected xdist test completion through per-run atomic receipts."""

    __test__ = False

    def __init__(self, state_dir: Path, *, timeout: float, groups: tuple[str, ...]) -> None:
        self.state_dir = state_dir
        self.timeout = timeout
        self.groups = groups
        self.manifest_path = state_dir / "manifest.json"
        self.receipts_dir = state_dir / "receipts"
        self.lock_path = state_dir / "state.lock"

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

        payload = {
            "groups": self.groups,
            "items": [
                {"nodeid": item.nodeid, "group": item.group, "ordinal": item.ordinal}
                for item in expected_by_nodeid.values()
            ],
        }
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.lock_path), timeout=self.timeout):
            _write_json_atomically(self.manifest_path, payload)

    def record_terminal(self, nodeid: str) -> None:
        """Publish one idempotent receipt for a selected test's terminal outcome."""
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

    def wait_for_earlier_groups(self, assignment: TestGroupAssignment) -> None:
        """Wait until every selected item from an earlier configured group settled."""
        deadline = time.monotonic() + self.timeout
        manifest: dict[str, Any] | None = None
        missing: list[str] = []
        earlier_groups = self.groups[: assignment.ordinal]

        while time.monotonic() < deadline:
            manifest = _read_json_with_retry(self.manifest_path, timeout=min(0.2, self.timeout))
            if manifest is not None:
                expected = [item for item in manifest["items"] if item["ordinal"] < assignment.ordinal]
                missing = [item["nodeid"] for item in expected if not self._has_matching_receipt(item)]
                if not missing:
                    return
            time.sleep(min(0.05, max(0.001, deadline - time.monotonic())))

        group_names = ", ".join(repr(group) for group in earlier_groups) or "(none)"
        details = f"; still waiting for {', '.join(missing[:3])}" if missing else "; run manifest was not published"
        raise TestGroupBarrierTimeout(
            f"Timed out after {self.timeout:g}s waiting for earlier test group(s) {group_names} "
            f"to settle before group {assignment.group!r} at {assignment.nodeid!r}{details}. "
            "Check worker health and the shared filesystem prerequisite for all local xdist workers. "
            "Non-shared remote workers are unsupported."
        )

    def _has_matching_receipt(self, expected: dict[str, Any]) -> bool:
        receipt = _read_json_with_retry(self._receipt_path(expected["nodeid"]), timeout=0.2)
        return bool(
            receipt is not None
            and receipt.get("nodeid") == expected["nodeid"]
            and receipt.get("group") == expected["group"]
            and receipt.get("ordinal") == expected["ordinal"]
        )

    def _receipt_path(self, nodeid: str) -> Path:
        digest = hashlib.sha256(nodeid.encode("utf-8")).hexdigest()
        return self.receipts_dir / f"{digest}.json"


def _write_json_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    deadline = time.monotonic() + 2.0
    last_error: OSError | None = None

    while time.monotonic() < deadline:
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
            last_error = error
            if error.errno not in _RETRYABLE_FILESYSTEM_ERRORS:
                raise
            time.sleep(0.02)
        finally:
            if temporary_path is not None:
                with suppress(OSError):
                    temporary_path.unlink(missing_ok=True)

    if last_error is not None:
        raise last_error
    raise OSError(f"Could not atomically publish test-group state at {path}")


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
