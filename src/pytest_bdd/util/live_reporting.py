"""
Provide live reporting helpers.

Responsibility:
    Provide live reporting helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.live_reporting` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - is_xdist_worker_process: owns nested behavior below this boundary
    - resolve_reporting_worker_identity: owns nested behavior below this boundary
    - format_reporting_worker_id: owns nested behavior below this boundary
    - node_worker_id: owns nested behavior below this boundary
    - node_gateway_mode: owns nested behavior below this boundary
    - build_reporting_worker_environment: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `live_reporting`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `live_reporting`
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `live_reporting`

State and side effects:
    mutates gateway_mode, gateway, GatewayModeResolver, workerinput, worker_id; depends on __future__.annotations, os,
    collections.abc.Callable, collections.abc.Mapping, typing.cast.

Invariants:
    - `pytest_bdd.util.live_reporting` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

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

    Responsibility:
        Check if running in an xdist worker process. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.live_reporting.is_xdist_worker_process` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - hasattr: collaborator call used by this boundary
        - os.environ.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `is_xdist_worker_process`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `is_xdist_worker_process`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `is_xdist_worker_process`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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

    Responsibility:
        Resolve the reporting worker identity. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.live_reporting.resolve_reporting_worker_identity`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - workerinput.get: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - is_xdist_worker_process: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `resolve_reporting_worker_identity`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `resolve_reporting_worker_identity`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `resolve_reporting_worker_identity`

    State and side effects:
        mutates workerinput, worker_id, gateway_mode.

    Invariants:
        - `pytest_bdd.util.live_reporting.resolve_reporting_worker_identity` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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

    Responsibility:
        Format the reporting worker ID. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.live_reporting.format_reporting_worker_id` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `format_reporting_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `format_reporting_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `format_reporting_worker_id`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4

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

    Responsibility:
        Get worker ID from a pytest node. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.live_reporting.node_worker_id` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `node_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `node_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `node_worker_id`

    State and side effects:
        mutates gateway, gateway_id.

    Invariants:
        - `pytest_bdd.util.live_reporting.node_worker_id` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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

    Responsibility:
        Get gateway mode from a pytest node. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.live_reporting.node_gateway_mode` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `node_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `node_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `node_gateway_mode`

    State and side effects:
        mutates gateway, spec.

    Invariants:
        - `pytest_bdd.util.live_reporting.node_gateway_mode` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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

    Responsibility:
        Build environment variables for reporting worker. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.live_reporting.build_reporting_worker_environment`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - workerinput.get: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `build_reporting_worker_environment`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `build_reporting_worker_environment`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `build_reporting_worker_environment`

    State and side effects:
        mutates env, gateway_mode.

    Invariants:
        - `pytest_bdd.util.live_reporting.build_reporting_worker_environment` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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
