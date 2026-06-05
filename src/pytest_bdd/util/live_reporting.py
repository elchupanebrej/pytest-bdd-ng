"""Provide live reporting helpers."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import cast

from pytest_bdd.compatibility.pytest import Config

GatewayModeResolver = Callable[[Config], str | None]


def is_xdist_worker_process(config: Config) -> bool:
    # Nested standalone pytest subprocesses can inherit PYTEST_XDIST_* environment
    # variables from an outer xdist worker. Treat only configs with workerinput as
    # real xdist workers so regular child runs keep local reporting behavior.
    """
    Check if running in an xdist worker process.

    Args:
        config: Pytest config object.

    Returns:
        True if running in xdist worker.

    """
    return hasattr(config, "workerinput") or os.environ.get("PYTEST_BDD_XDIST_IS_WORKER") == "1"


def resolve_reporting_worker_identity(
    config: Config,
    *,
    gateway_mode_resolver: GatewayModeResolver,
) -> tuple[str, str | None]:
    """
    Resolve the reporting worker identity.

    Args:
        config: Pytest config object.
        gateway_mode_resolver: Callback to resolve gateway mode.

    Returns:
        Tuple of (worker_id, gateway_mode).

    """
    if not is_xdist_worker_process(config):
        return "master", None
    workerinput = cast("Mapping[str, object]", getattr(config, "workerinput", {}))
    worker_id = str(
        workerinput.get("pytest_bdd_messages_fragment_worker_id") or workerinput.get("workerid") or "worker",
    )
    gateway_mode = str(workerinput.get("pytest_bdd_messages_gateway_mode") or "").strip() or gateway_mode_resolver(
        config,
    )
    return worker_id, gateway_mode or None


def format_reporting_worker_id(worker_id: str, gateway_mode: str | None) -> str:
    """
    Format the reporting worker ID.

    Args:
        worker_id: Worker identifier.
        gateway_mode: Gateway mode string.

    Returns:
        Formatted worker ID string.

    """
    if gateway_mode is None or gateway_mode == "popen" or worker_id == "master":
        return worker_id
    return f"{gateway_mode}:{worker_id}"


def node_worker_id(node: object) -> str:
    """
    Get worker ID from a pytest node.

    Args:
        node: Pytest node object.

    Returns:
        Worker ID string.

    """
    gateway = getattr(node, "gateway", None)
    gateway_id = getattr(gateway, "id", None)
    return str(gateway_id or "worker")


def node_gateway_mode(node: object) -> str:
    """
    Get gateway mode from a pytest node.

    Args:
        node: Pytest node object.

    Returns:
        Gateway mode string.

    """
    gateway = getattr(node, "gateway", None)
    spec = getattr(gateway, "spec", None)
    if spec is None:
        return "popen"
    if getattr(spec, "via", None):
        return "via"
    if getattr(spec, "ssh", None):
        return "ssh"
    if getattr(spec, "socket", None):
        return "socket"
    return "popen"


def build_reporting_worker_environment(workerinput: Mapping[str, object]) -> dict[str, str]:
    """
    Build environment variables for reporting worker.

    Args:
        workerinput: Worker input dictionary from xdist.

    Returns:
        Dictionary of environment variables.

    """
    env = {
        "PYTEST_XDIST_TESTRUNUID": str(workerinput["testrunuid"]),
        "PYTEST_XDIST_WORKER": str(workerinput["workerid"]),
        "PYTEST_XDIST_WORKER_COUNT": str(workerinput["workercount"]),
        "PYTEST_BDD_XDIST_IS_WORKER": "1",
        "PYTEST_BDD_REPORTING_WORKER_ID": str(
            workerinput.get("pytest_bdd_messages_fragment_worker_id") or workerinput["workerid"],
        ),
    }
    gateway_mode = str(workerinput.get("pytest_bdd_messages_gateway_mode") or "").strip()
    if gateway_mode:
        env["PYTEST_BDD_REPORTING_GATEWAY_MODE"] = gateway_mode
    return env
