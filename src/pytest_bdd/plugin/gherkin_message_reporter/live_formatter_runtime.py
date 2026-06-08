"""
Provide live formatter runtime coordinator.

Responsibility:
    Provide live formatter runtime coordinator. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime`
    because it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - LiveFormatterService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `live_formatter_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `live_formatter_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `live_formatter_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
      `live_formatter_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
      `live_formatter_runtime`

State and side effects:
    depends on __future__.annotations,
    pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin,
    pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin,
    pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcess,
    pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node import LiveFormatterNodeMixin
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload import LiveFormatterPayloadMixin
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process import (  # noqa: F401
    LiveFormatterProcess,
    LiveFormatterProcessMixin,
)
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner import LiveFormatterRunnerMixin
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase


class LiveFormatterService(
    LiveFormatterRunnerMixin,
    LiveFormatterNodeMixin,
    LiveFormatterPayloadMixin,
    LiveFormatterProcessMixin,
    ReporterServiceBase,
):
    """
    Coordinate live formatter runtime behavior.

    Responsibility:
        Coordinate live formatter runtime behavior. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime.LiveFormatterService` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `LiveFormatterService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `LiveFormatterService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `LiveFormatterService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `LiveFormatterService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `LiveFormatterService`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime.LiveFormatterService` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
