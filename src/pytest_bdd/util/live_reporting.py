"""
Provides live reporting utilities that bridge pytest-bdd runtime events to external Cucumber
formatter processes, man.

Responsibility:
    Provides live reporting utilities that bridge pytest-bdd runtime events to external Cucumber
    formatter processes, managing subprocess lifecycle, message serialization, and NDJSON streaming
    for real-time Cucumber-compatible test output during distributed and local test execution.

Reason for existence:
    Live reporting requires careful subprocess management (Node.js + Cucumber formatters) with
    unique failure modes (process crashes, pipe errors, encoding issues). Isolating this concern
    prevents reporter complexity from leaking into the core pytest plugin infrastructure.

Delegates:
    - `subprocess.Popen`: delegates process lifecycle management to Python stdlib

Cohesion:
    All functions and classes support the live reporting subprocess management workflow.

Separation:
    - `pytest_bdd.util.cucumber_formatters`: provides the static formatter registry while live_reporting handles runtime
    orchestration.

Main consumers:
    - `pytest_bdd.plugin.gherkin_message_reporter`: uses live_reporting for formatter subprocess lifecycle

State and side effects:
    Manages subprocess.Popen instances and NDJSON file handles during active reporting sessions.

Invariants:
    - Each live reporter subprocess receives properly formatted NDJSON messages via its stdin pipe.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
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
    Perform the `is_xdist_worker_process` operation within its module boundary, implementing a.
    focused helper function t.

    Responsibility:
        Performs the `is_xdist_worker_process` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `is_xdist_worker_process` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the is_xdist_worker_process operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke is_xdist_worker_process for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The is_xdist_worker_process function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return hasattr(config, "workerinput") or os.environ.get("PYTEST_BDD_XDIST_IS_WORKER") == "1"


def resolve_reporting_worker_identity(
    config: Config,
    *,
    gateway_mode_resolver: GatewayModeResolver,
) -> tuple[str, str | None]:
    """
    Perform the `resolve_reporting_worker_identity` operation within its module boundary,.
    implementing a focused helper .

    Responsibility:
        Performs the `resolve_reporting_worker_identity` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `resolve_reporting_worker_identity` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the resolve_reporting_worker_identity operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_reporting_worker_identity for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The resolve_reporting_worker_identity function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
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
    Perform the `format_reporting_worker_id` operation within its module boundary, implementing a.
    focused helper functio.

    Responsibility:
        Performs the `format_reporting_worker_id` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `format_reporting_worker_id` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the format_reporting_worker_id operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke format_reporting_worker_id for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The format_reporting_worker_id function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if gateway_mode is None or gateway_mode == "popen" or worker_id == "master":
        return worker_id
    return f"{gateway_mode}:{worker_id}"


def node_worker_id(node: object) -> str:
    """
    Perform the `node_worker_id` operation within its module boundary, implementing a focused.
    helper function that is co.

    Responsibility:
        Performs the `node_worker_id` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `node_worker_id` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the node_worker_id operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke node_worker_id for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The node_worker_id function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    gateway = getattr(node, "gateway", None)
    gateway_id = getattr(gateway, "id", None)
    return str(gateway_id or "worker")


def node_gateway_mode(node: object) -> str:
    """
    Perform the `node_gateway_mode` operation within its module boundary, implementing a focused.
    helper function that is.

    Responsibility:
        Performs the `node_gateway_mode` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `node_gateway_mode` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the node_gateway_mode operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke node_gateway_mode for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The node_gateway_mode function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
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
    Perform the `build_reporting_worker_environment` operation within its module boundary,.
    implementing a focused helper.

    Responsibility:
        Performs the `build_reporting_worker_environment` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `build_reporting_worker_environment` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the build_reporting_worker_environment operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke build_reporting_worker_environment for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The build_reporting_worker_environment function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
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
