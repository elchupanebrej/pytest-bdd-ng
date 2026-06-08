"""
Provide runtime support helpers.

Responsibility:
    Provide runtime support helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.runtime_support` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _is_xdist_worker_process: owns nested behavior below this boundary
    - _resolve_reporting_gateway_mode: owns nested behavior below this boundary
    - _resolve_reporting_worker_identity: owns nested behavior below this boundary
    - _format_reporting_worker_id: owns nested behavior below this boundary
    - HookRegistration: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `runtime_support`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
      `runtime_support`
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `runtime_support`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `runtime_support`
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `runtime_support`

State and side effects:
    mutates gateway_mode, worker_id, hook_message_id, expression, kind; depends on __future__.annotations,
    typing.TYPE_CHECKING, attrs.frozen, pytest_bdd.model.message_transport.resolve_reporting_gateway_mode,
    pytest_bdd.util.live_reporting.is_xdist_worker_process.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.runtime_support` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

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

from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.model.message_transport import resolve_reporting_gateway_mode
from pytest_bdd.util.live_reporting import is_xdist_worker_process, resolve_reporting_worker_identity

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config


def _is_xdist_worker_process(config: Config) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._is_xdist_worker_process` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._is_xdist_worker_process` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - bool: collaborator call used by this boundary
        - is_xdist_worker_process: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_is_xdist_worker_process`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `_is_xdist_worker_process`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_is_xdist_worker_process`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_is_xdist_worker_process`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_is_xdist_worker_process`

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
    return bool(is_xdist_worker_process(config))


def _resolve_reporting_gateway_mode(config: Config) -> str:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._resolve_reporting_gateway_mode` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._resolve_reporting_gateway_mode` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve_reporting_gateway_mode: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `_resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `_resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_resolve_reporting_gateway_mode`

    State and side effects:
        mutates gateway_mode.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._resolve_reporting_gateway_mode` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

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
    gateway_mode = resolve_reporting_gateway_mode(config)
    return "" if gateway_mode is None else str(gateway_mode)


def _resolve_reporting_worker_identity(config: Config) -> tuple[str, str | None]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._resolve_reporting_worker_identity` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._resolve_reporting_worker_identity` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - resolve_reporting_worker_identity: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_resolve_reporting_worker_identity`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `_resolve_reporting_worker_identity`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `_resolve_reporting_worker_identity`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_resolve_reporting_worker_identity`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_resolve_reporting_worker_identity`

    State and side effects:
        mutates worker_id, gateway_mode.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._resolve_reporting_worker_identity` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

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
    worker_id, gateway_mode = resolve_reporting_worker_identity(
        config,
        gateway_mode_resolver=_resolve_reporting_gateway_mode,
    )
    return str(worker_id), None if gateway_mode is None else str(gateway_mode)


def _format_reporting_worker_id(worker_id: str, gateway_mode: str | None) -> str:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._format_reporting_worker_id` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support._format_reporting_worker_id` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_format_reporting_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `_format_reporting_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_format_reporting_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_format_reporting_worker_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_format_reporting_worker_id`

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


@frozen
class HookRegistration:
    """
    Represent hook registration state.

    Responsibility:
        Represent hook registration state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_support.HookRegistration` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `HookRegistration`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `HookRegistration`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `HookRegistration`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `HookRegistration`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `HookRegistration`

    State and side effects:
        mutates hook_message_id, expression, kind.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_support.HookRegistration` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    hook_message_id: str
    expression: str
    kind: str
