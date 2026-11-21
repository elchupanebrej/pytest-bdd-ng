"""Socket relay that carries test-group barrier state when workers share no filesystem.

The relay stores exactly what the filesystem barrier stores: the run manifest and
one terminal receipt per selected node ID. It also records which worker claimed
an item and which workers the controller saw go down, so a barrier can name the
unfinished group and test instead of waiting silently for a dead worker.
"""

from __future__ import annotations

import hmac
import http.client
import json
import threading
import time
from typing import TYPE_CHECKING, Any

from pytest_cuke.remote_http import (
    JsonRequestHandler,
    StatefulThreadingHTTPServer,
    bind_address_for,
    format_host_port,
)
from pytest_cuke.test_groups.transport import BarrierSnapshot

if TYPE_CHECKING:
    from collections.abc import Mapping


class BarrierRelayError(ConnectionError):
    """Raised when a worker cannot reach the configured barrier relay."""

    __test__ = False


class BarrierRelayState:
    """Thread-safe manifest, receipts, claims, and worker liveness for one run."""

    __test__ = False

    def __init__(self, credential: str) -> None:
        self._credential = credential
        self._lock = threading.Lock()
        self._manifest: dict[str, Any] | None = None
        self._receipts: dict[str, dict[str, Any]] = {}
        self._owners: dict[str, str] = {}
        self._dead_workers: dict[str, str] = {}

    def apply(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Apply one authenticated relay operation and return its JSON-ready response."""
        if not self._authenticated(request.get("credential")):
            return {
                "ok": False,
                "error": "barrier relay rejected the request: missing or invalid per-run credential",
            }
        with self._lock:
            return self._apply(request)

    def _apply(self, request: Mapping[str, Any]) -> dict[str, Any]:
        operation = request.get("op")
        if operation == "publish_manifest":
            return self._publish_manifest(request.get("manifest"))
        if operation == "claim":
            nodeid = request.get("nodeid")
            worker = request.get("worker")
            if isinstance(nodeid, str) and isinstance(worker, str) and self._item(nodeid) is not None:
                self._owners[nodeid] = worker
            return {"ok": True}
        if operation == "publish_receipt":
            item = self._item(request.get("nodeid"))
            if item is not None:
                self._receipts.setdefault(str(item["nodeid"]), item)
            return {"ok": True}
        if operation == "worker_down":
            worker = request.get("worker")
            if isinstance(worker, str) and worker:
                self._dead_workers[worker] = str(request.get("detail") or "")
            return {"ok": True}
        if operation == "snapshot":
            return self._snapshot_payload()
        return {"ok": False, "error": f"unknown barrier relay operation: {operation!r}"}

    def _publish_manifest(self, raw_manifest: Any) -> dict[str, Any]:
        manifest = _valid_manifest(raw_manifest)
        if manifest is None:
            return {
                "ok": False,
                "error": "publish_manifest needs string groups and items with nodeid, group, and ordinal",
            }
        self._manifest = manifest
        return {"ok": True}

    def mark_worker_down(self, worker: str, detail: str = "") -> None:
        """Record that the controller saw a worker exit before the run finished."""
        with self._lock:
            self._dead_workers[worker] = detail

    def snapshot(self) -> BarrierSnapshot:
        """Return the current barrier state."""
        with self._lock:
            payload = self._snapshot_payload()
        return BarrierSnapshot(
            manifest=payload["manifest"],
            receipts={str(receipt["nodeid"]): receipt for receipt in payload["receipts"]},
            owners=payload["owners"],
            dead_workers=tuple(payload["dead_workers"]),
        )

    def _snapshot_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "manifest": self._manifest,
            "receipts": list(self._receipts.values()),
            "owners": dict(self._owners),
            "dead_workers": sorted(self._dead_workers),
        }

    def _authenticated(self, candidate: Any) -> bool:
        return isinstance(candidate, str) and hmac.compare_digest(
            candidate.encode("utf-8"), self._credential.encode("utf-8")
        )

    def _item(self, nodeid: Any) -> dict[str, Any] | None:
        if not isinstance(nodeid, str) or self._manifest is None:
            return None
        for item in self._manifest.get("items", ()):
            if isinstance(item, dict) and item.get("nodeid") == nodeid:
                return {"nodeid": nodeid, "group": item.get("group"), "ordinal": item.get("ordinal")}
        return None


class _RelayRequestHandler(JsonRequestHandler):
    server: _RelayHTTPServer


class _RelayHTTPServer(StatefulThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], state: BarrierRelayState, *, family: int) -> None:
        super().__init__(address, _RelayRequestHandler, state, family=family)


class BarrierRelay:
    """A running relay owned by the xdist controller process."""

    __test__ = False

    def __init__(self, state: BarrierRelayState, server: _RelayHTTPServer) -> None:
        self.state = state
        self._server = server
        self._thread = threading.Thread(
            target=server.serve_forever,
            name="pytest-cuke-test-group-relay",
            daemon=True,
        )

    @property
    def port(self) -> int:
        """The TCP port the relay actually bound."""
        return int(self._server.server_address[1])

    def start(self) -> BarrierRelay:
        """Serve barrier requests until ``stop`` is called."""
        self._thread.start()
        return self

    def stop(self) -> None:
        """Stop serving and release the port."""
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def start_relay(port: int, *, credential: str, host: str = "") -> BarrierRelay:
    """Bind a relay on every interface so remote workers can reach the controller."""
    state = BarrierRelayState(credential)
    # shortcut: binds the wildcard address of the advertised host so independent
    # worker containers can connect; add a bind-address setting if the relay must
    # stay on a private interface.
    address, family = bind_address_for(host, port)
    return BarrierRelay(state, _RelayHTTPServer(address, state, family=family)).start()


class RelayBarrierClient:
    """Worker-side barrier transport for one relay address."""

    __test__ = False

    def __init__(self, address: tuple[str, int], *, worker_id: str, credential: str, timeout: float) -> None:
        self.address = address
        self.worker_id = worker_id
        self.credential = credential
        self.timeout = timeout
        self.label = format_host_port(address[0], address[1])

    def publish_manifest(self, manifest: dict[str, Any]) -> None:
        self._call({"op": "publish_manifest", "manifest": manifest})

    def claim(self, nodeid: str) -> None:
        self._call({"op": "claim", "nodeid": nodeid, "worker": self.worker_id})

    def publish_receipt(self, nodeid: str) -> None:
        self._call({"op": "publish_receipt", "nodeid": nodeid})

    def snapshot(self) -> BarrierSnapshot:
        payload = self._call({"op": "snapshot"}, swallow_errors=True)
        if payload is None:
            return BarrierSnapshot(manifest=None, receipts={}, owners={}, dead_workers=())
        manifest = payload.get("manifest")
        receipts = {
            str(receipt["nodeid"]): receipt
            for receipt in payload.get("receipts", ())
            if isinstance(receipt, dict) and isinstance(receipt.get("nodeid"), str)
        }
        owners = payload.get("owners")
        dead_workers = payload.get("dead_workers")
        return BarrierSnapshot(
            manifest=manifest if isinstance(manifest, dict) else None,
            receipts=receipts,
            owners=dict(owners) if isinstance(owners, dict) else {},
            dead_workers=tuple(dead_workers) if isinstance(dead_workers, list) else (),
        )

    def _call(self, request: dict[str, Any], *, swallow_errors: bool = False) -> dict[str, Any] | None:
        deadline = time.monotonic() + min(self.timeout, 10.0)
        last_error = "no response"
        while True:
            try:
                payload = self._post(request)
            except (OSError, ValueError) as error:
                last_error = f"{type(error).__name__}: {error}"
            else:
                if payload.get("ok"):
                    return payload
                last_error = str(payload.get("error") or "relay rejected the request")
            if swallow_errors or time.monotonic() >= deadline:
                if swallow_errors:
                    return None
                raise BarrierRelayError(
                    f"test-group barrier relay {self.label} did not accept {request.get('op')!r}: {last_error}. "
                    "Start the relay on the controller with cuke_test_group_relay=HOST:PORT or disable "
                    "cuke_test_group_order."
                )
            time.sleep(0.02)

    def _post(self, request: dict[str, Any]) -> dict[str, Any]:
        connection = http.client.HTTPConnection(*self.address, timeout=min(2.0, self.timeout))
        try:
            connection.request(
                "POST",
                "/",
                body=json.dumps({**request, "credential": self.credential}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = json.loads(response.read() or b"{}")
        finally:
            connection.close()
        if not isinstance(payload, dict):
            raise ValueError(f"unexpected relay response: {payload!r}")
        return payload


def _valid_manifest(manifest: Any) -> dict[str, Any] | None:
    if not isinstance(manifest, dict):
        return None
    groups = manifest.get("groups")
    items = manifest.get("items")
    if not isinstance(groups, list) or not all(isinstance(group, str) for group in groups):
        return None
    if not isinstance(items, list):
        return None
    parsed_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            return None
        nodeid = item.get("nodeid")
        group = item.get("group")
        ordinal = item.get("ordinal")
        if (
            not isinstance(nodeid, str)
            or not nodeid
            or not isinstance(group, str)
            or not group
            or not isinstance(ordinal, int)
            or isinstance(ordinal, bool)
            or ordinal < 0
        ):
            return None
        parsed_items.append({"nodeid": nodeid, "group": group, "ordinal": ordinal})
    return {"groups": list(groups), "items": parsed_items}
