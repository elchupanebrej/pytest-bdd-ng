"""The seam that carries test-group barrier state: local filesystem or socket relay."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class BarrierSnapshot:
    """One consistent read of barrier state, whatever carries it."""

    manifest: dict[str, Any] | None
    receipts: dict[str, dict[str, Any]]
    owners: dict[str, str] = field(default_factory=dict)
    dead_workers: tuple[str, ...] = ()
    shutdown: bool = False


class BarrierTransport(Protocol):
    """Where barrier state lives: a shared directory or a socket relay."""

    def publish_manifest(self, manifest: dict[str, Any]) -> None:
        """Publish the selected node IDs and their groups before any wait."""

    def claim(self, nodeid: str) -> None:
        """Record that this worker owns the item, for liveness diagnostics."""

    def publish_receipt(self, nodeid: str) -> None:
        """Publish one idempotent terminal receipt for a selected test."""

    def snapshot(self) -> BarrierSnapshot:
        """Read the manifest, receipts, ownership, and dead workers."""
