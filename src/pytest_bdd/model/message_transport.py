"""
Provide message transport helpers.

Responsibility:
    Provide message transport helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_transport` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - ReportingEventSender: owns nested behavior below this boundary
    - ReportingEventSenderBinding: owns nested behavior below this boundary
    - resolve_reporting_event_sender: owns nested behavior below this boundary
    - resolve_reporting_gateway_mode: owns nested behavior below this boundary
    - _payload_int: owns nested behavior below this boundary
    - WorkerChunkBatch: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
      `message_transport`
    - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `message_transport`
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `message_transport`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `message_transport`
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `message_transport`

State and side effects:
    mutates gateway_mode, msg, worker_id, sender, binding; depends on __future__.annotations, json, logging,
    threading.Lock, time.monotonic.

Invariants:
    - `pytest_bdd.model.message_transport` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises ValueError, TypeError, RuntimeError; callers must treat these as boundary failures.

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

import json
import logging
from threading import Lock
from time import monotonic, sleep
from typing import TYPE_CHECKING, ClassVar, Protocol

from attrs import define, field, frozen
from returns.maybe import Nothing

from pytest_bdd.model.stash_access import StashBound

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject
    from pytest_bdd.types.protocol import HasPytestStash

logger = logging.getLogger(__name__)

REPORTING_BATCH_EVENT = "pytest_bdd_message_chunk"
REPORTING_TRANSPORT_BINDING_STASH_KEY = "_pytest_bdd_xdist_transport_binding"


class ReportingEventSender(Protocol):
    """
    Represent reporting event sender state.

    Responsibility:
        Represent reporting event sender state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.ReportingEventSender` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `ReportingEventSender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `ReportingEventSender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ReportingEventSender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `ReportingEventSender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ReportingEventSender`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.model.message_transport.ReportingEventSender` keeps its documented import path, ownership
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

    def __call__(self, name: str, **kwargs: object) -> None:
        """
        Send a reporting event with its associated payload.

        Responsibility:
            Send a reporting event with its associated payload. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_transport.ReportingEventSender.__call__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `__call__`

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
        ...


@frozen
class ReportingEventSenderBinding(StashBound):
    """
    Represent reporting event sender binding state.

    Responsibility:
        Represent reporting event sender binding state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.ReportingEventSenderBinding`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `ReportingEventSenderBinding`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `ReportingEventSenderBinding`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ReportingEventSenderBinding`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `ReportingEventSenderBinding`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ReportingEventSenderBinding`

    State and side effects:
        mutates STASH_KEY, sender, gateway_mode.

    Invariants:
        - `pytest_bdd.model.message_transport.ReportingEventSenderBinding` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    STASH_KEY: ClassVar[str] = REPORTING_TRANSPORT_BINDING_STASH_KEY
    sender: ReportingEventSender
    gateway_mode: str | None = None


def resolve_reporting_event_sender(config: HasPytestStash) -> ReportingEventSender | None:
    """
    Retrieve the configured reporting event sender from the pytest stash.

    Returns:
        The registered ReportingEventSender, or None if not found or not callable.

    Responsibility:
        Retrieve the configured reporting event sender from the pytest stash. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.resolve_reporting_event_sender`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - ReportingEventSenderBinding.find_in_stash.value_or: collaborator call used by this boundary
        - ReportingEventSenderBinding.find_in_stash: collaborator call used by this boundary
        - callable: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `resolve_reporting_event_sender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `resolve_reporting_event_sender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `resolve_reporting_event_sender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `resolve_reporting_event_sender`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `resolve_reporting_event_sender`

    State and side effects:
        mutates binding, sender.

    Invariants:
        - `pytest_bdd.model.message_transport.resolve_reporting_event_sender` keeps its documented import path,
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
    binding = ReportingEventSenderBinding.find_in_stash(config.stash).value_or(None)
    if binding is None:
        return Nothing.value_or(None)
    sender = binding.sender
    return sender if callable(sender) else Nothing.value_or(None)


def resolve_reporting_gateway_mode(config: HasPytestStash) -> str | None:
    """
    Retrieve the gateway mode from the configured reporting event sender binding.

    Returns:
        The gateway mode as a string, or None if not configured.

    Responsibility:
        Retrieve the gateway mode from the configured reporting event sender binding. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.resolve_reporting_gateway_mode`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - ReportingEventSenderBinding.find_in_stash.value_or: collaborator call used by this boundary
        - ReportingEventSenderBinding.find_in_stash: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `resolve_reporting_gateway_mode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `resolve_reporting_gateway_mode`

    State and side effects:
        mutates binding, gateway_mode.

    Invariants:
        - `pytest_bdd.model.message_transport.resolve_reporting_gateway_mode` keeps its documented import path,
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
    binding = ReportingEventSenderBinding.find_in_stash(config.stash).value_or(None)
    if binding is None:
        return Nothing.value_or(None)
    gateway_mode = binding.gateway_mode
    return gateway_mode if isinstance(gateway_mode, str) and gateway_mode else Nothing.value_or(None)


def _payload_int(payload: JSONObject, key: str, default: int | None = None) -> int:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_transport._payload_int` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport._payload_int` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - payload.get: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - int: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `_payload_int`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `_payload_int`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_payload_int`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `_payload_int`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `_payload_int`

    State and side effects:
        mutates raw_value, msg.

    Invariants:
        - `pytest_bdd.model.message_transport._payload_int` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    raw_value = payload.get(key, default)
    if isinstance(raw_value, (str, int, float)):
        return int(raw_value)
    if default is not None:
        return default
    msg = f"Expected integer-compatible transport field: {key}"
    raise TypeError(msg)


@frozen
class WorkerChunkBatch:
    """
    Represent worker chunk batch state.

    Responsibility:
        Represent worker chunk batch state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.WorkerChunkBatch` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary
        - from_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `WorkerChunkBatch`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `WorkerChunkBatch`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `WorkerChunkBatch`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `WorkerChunkBatch`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `WorkerChunkBatch`

    State and side effects:
        mutates worker_id, envelopes, gateway_mode, batch_sequence, is_terminal_batch.

    Invariants:
        - `pytest_bdd.model.message_transport.WorkerChunkBatch` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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

    worker_id: str
    batch_sequence: int
    envelopes: tuple[JSONObject, ...]
    is_terminal_batch: bool = False
    byte_count: int = 0
    gateway_mode: str | None = None

    def as_dict(self) -> JSONObject:
        """
        Convert the batch state into a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the worker chunk batch.

        Responsibility:
            Convert the batch state into a JSON-serializable dictionary. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_transport.WorkerChunkBatch.as_dict`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`
            - src/pytest_bdd/plugin/code_generator/events.py: imports or references `as_dict`

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
        return {
            "worker_id": self.worker_id,
            "batch_sequence": self.batch_sequence,
            "envelopes": list(self.envelopes),
            "is_terminal_batch": self.is_terminal_batch,
            "byte_count": self.byte_count,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: JSONObject) -> WorkerChunkBatch:
        """
        Instantiate a WorkerChunkBatch from a JSON-serializable dictionary payload.

        Returns:
            A new instance of WorkerChunkBatch initialized from the payload.

        Raises:
            ValueError: If the required ``worker_id`` field is missing from the payload.

        Responsibility:
            Instantiate a WorkerChunkBatch from a JSON-serializable dictionary payload. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_transport.WorkerChunkBatch.from_dict`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - payload.get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - _payload_int: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `from_dict`
            - src/pytest_bdd/model/feature_binding.py: imports or references `from_dict`
            - src/pytest_bdd/model/message_converter.py: imports or references `from_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references `from_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `from_dict`

        State and side effects:
            mutates raw_envelopes, envelope_candidates, envelopes, gateway_mode, worker_id.

        Invariants:
            - `pytest_bdd.model.message_transport.WorkerChunkBatch.from_dict` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        raw_envelopes = payload.get("envelopes", [])
        envelope_candidates = raw_envelopes if isinstance(raw_envelopes, list) else []
        envelopes = tuple(candidate for candidate in envelope_candidates if isinstance(candidate, dict))
        gateway_mode = payload.get("gateway_mode")
        worker_id = payload.get("worker_id")
        if worker_id is None:
            msg = "Missing required field 'worker_id' in batch payload"
            raise ValueError(msg)
        return cls(
            worker_id=str(worker_id),
            batch_sequence=_payload_int(payload, "batch_sequence"),
            envelopes=envelopes,
            is_terminal_batch=bool(payload.get("is_terminal_batch")),
            byte_count=_payload_int(payload, "byte_count", 0),
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@frozen
class WorkerCompletionManifest:
    """
    Represent worker completion manifest state.

    Responsibility:
        Represent worker completion manifest state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.WorkerCompletionManifest` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary
        - from_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `WorkerCompletionManifest`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `WorkerCompletionManifest`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `WorkerCompletionManifest`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `WorkerCompletionManifest`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `WorkerCompletionManifest`

    State and side effects:
        mutates worker_id, interruption_reason, gateway_mode, complete, last_batch_sequence.

    Invariants:
        - `pytest_bdd.model.message_transport.WorkerCompletionManifest` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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

    worker_id: str
    complete: bool
    last_batch_sequence: int | None
    transferred_batch_count: int
    transferred_envelope_count: int
    interruption_reason: str | None = None
    gateway_mode: str | None = None

    def as_dict(self) -> JSONObject:
        """
        Convert the completion manifest into a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the worker completion manifest.

        Responsibility:
            Convert the completion manifest into a JSON-serializable dictionary. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.WorkerCompletionManifest.as_dict` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`
            - src/pytest_bdd/plugin/code_generator/events.py: imports or references `as_dict`

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
        return {
            "worker_id": self.worker_id,
            "complete": self.complete,
            "last_batch_sequence": self.last_batch_sequence,
            "transferred_batch_count": self.transferred_batch_count,
            "transferred_envelope_count": self.transferred_envelope_count,
            "interruption_reason": self.interruption_reason,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: JSONObject) -> WorkerCompletionManifest:
        """
        Instantiate a WorkerCompletionManifest from a JSON-serializable dictionary payload.

        Returns:
            A new instance of WorkerCompletionManifest initialized from the payload.

        Raises:
            ValueError: If the required ``worker_id`` field is missing from the payload.

        Responsibility:
            Instantiate a WorkerCompletionManifest from a JSON-serializable dictionary payload. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.WorkerCompletionManifest.from_dict` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - payload.get: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - _payload_int: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary
            - cls: collaborator call used by this boundary
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `from_dict`
            - src/pytest_bdd/model/feature_binding.py: imports or references `from_dict`
            - src/pytest_bdd/model/message_converter.py: imports or references `from_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references `from_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `from_dict`

        State and side effects:
            mutates interruption_reason, gateway_mode, worker_id, msg.

        Invariants:
            - `pytest_bdd.model.message_transport.WorkerCompletionManifest.from_dict` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        interruption_reason = payload.get("interruption_reason")
        gateway_mode = payload.get("gateway_mode")
        worker_id = payload.get("worker_id")
        if worker_id is None:
            msg = "Missing required field 'worker_id' in manifest payload"
            raise ValueError(msg)
        return cls(
            worker_id=str(worker_id),
            complete=bool(payload.get("complete")),
            last_batch_sequence=(
                _payload_int(payload, "last_batch_sequence") if payload.get("last_batch_sequence") is not None else None
            ),
            transferred_batch_count=_payload_int(payload, "transferred_batch_count", 0),
            transferred_envelope_count=_payload_int(payload, "transferred_envelope_count", 0),
            interruption_reason=str(interruption_reason) if interruption_reason is not None else None,
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@define
class ReportingTransportSnapshot:
    """
    Represent reporting transport snapshot state.

    Responsibility:
        Represent reporting transport snapshot state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.ReportingTransportSnapshot`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `ReportingTransportSnapshot`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `ReportingTransportSnapshot`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ReportingTransportSnapshot`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `ReportingTransportSnapshot`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ReportingTransportSnapshot`

    State and side effects:
        mutates expected_worker_ids, batches_by_worker, manifests_by_worker.

    Invariants:
        - `pytest_bdd.model.message_transport.ReportingTransportSnapshot` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    expected_worker_ids: tuple[str, ...]
    batches_by_worker: dict[str, tuple[WorkerChunkBatch, ...]]
    manifests_by_worker: dict[str, WorkerCompletionManifest]


@define
class ReportingTransportSession:
    """
    Represent reporting transport session state.

    Responsibility:
        Represent reporting transport session state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.ReportingTransportSession` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - register_expected_worker: owns nested behavior below this boundary
        - record_batch: owns nested behavior below this boundary
        - receive_remote_event: owns nested behavior below this boundary
        - record_manifest: owns nested behavior below this boundary
        - batches_for_worker: owns nested behavior below this boundary
        - manifest_for_worker: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `ReportingTransportSession`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `ReportingTransportSession`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ReportingTransportSession`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `ReportingTransportSession`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ReportingTransportSession`

    State and side effects:
        mutates batches, _lock, _expected_worker_ids, _batches_by_worker, _manifests_by_worker.

    Invariants:
        - `pytest_bdd.model.message_transport.ReportingTransportSession` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    _lock: Lock = field(init=False, factory=Lock, repr=False)
    _expected_worker_ids: set[str] = field(init=False, factory=set, repr=False)
    _batches_by_worker: dict[str, list[WorkerChunkBatch]] = field(init=False, factory=dict, repr=False)
    _manifests_by_worker: dict[str, WorkerCompletionManifest] = field(init=False, factory=dict, repr=False)

    def register_expected_worker(self, worker_id: str) -> None:
        """
        Register a worker identifier to track expected incoming batches.

        Responsibility:
            Register a worker identifier to track expected incoming batches. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.register_expected_worker` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._expected_worker_ids.add: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `register_expected_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `register_expected_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `register_expected_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
              `register_expected_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `register_expected_worker`

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
        with self._lock:
            self._expected_worker_ids.add(worker_id)

    def record_batch(self, batch: WorkerChunkBatch) -> None:
        """
        Store an incoming chunk batch for a specific worker.

        Responsibility:
            Store an incoming chunk batch for a specific worker. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.record_batch` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._batches_by_worker.setdefault.append: collaborator call used by this boundary
            - self._batches_by_worker.setdefault: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `record_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `record_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `record_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `record_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `record_batch`

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
        with self._lock:
            self._batches_by_worker.setdefault(batch.worker_id, []).append(batch)

    def receive_remote_event(self, event_name: str, payload: JSONObject) -> None:
        """
        Process an incoming remote event, extracting and recording the batch payload if applicable.

        Responsibility:
            Process an incoming remote event, extracting and recording the batch payload if applicable. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.receive_remote_event` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - logger.warning: collaborator call used by this boundary
            - payload.get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - self.record_batch: collaborator call used by this boundary
            - WorkerChunkBatch.from_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `receive_remote_event`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `receive_remote_event`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `receive_remote_event`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
              `receive_remote_event`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `receive_remote_event`

        State and side effects:
            mutates batch_payload.

        Invariants:
            - `pytest_bdd.model.message_transport.ReportingTransportSession.receive_remote_event` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        if event_name != REPORTING_BATCH_EVENT:
            logger.warning("Ignoring unknown reporting event '%s'.", event_name)
            return
        batch_payload = payload.get("batch")
        if not isinstance(batch_payload, dict):
            logger.warning("Ignoring malformed reporting batch payload for event '%s'.", event_name)
            return
        self.record_batch(WorkerChunkBatch.from_dict(batch_payload))

    def record_manifest(self, manifest: WorkerCompletionManifest) -> None:
        """
        Store a completion manifest for a specific worker.

        Responsibility:
            Store a completion manifest for a specific worker. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.record_manifest` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `record_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `record_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `record_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `record_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `record_manifest`

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
        with self._lock:
            self._manifests_by_worker[manifest.worker_id] = manifest

    def batches_for_worker(self, worker_id: str) -> tuple[WorkerChunkBatch, ...]:
        """
        Retrieve all recorded batches for a specified worker, sorted by batch sequence.

        Returns:
            A tuple of sorted WorkerChunkBatch instances for the requested worker.

        Responsibility:
            Retrieve all recorded batches for a specified worker, sorted by batch sequence. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.batches_for_worker` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - tuple: collaborator call used by this boundary
            - self._batches_by_worker.get: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `batches_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `batches_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `batches_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
              `batches_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `batches_for_worker`

        State and side effects:
            mutates batches.

        Invariants:
            - `pytest_bdd.model.message_transport.ReportingTransportSession.batches_for_worker` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        with self._lock:
            batches = tuple(self._batches_by_worker.get(worker_id, ()))
        return tuple(sorted(batches, key=lambda batch: batch.batch_sequence))

    def manifest_for_worker(self, worker_id: str) -> WorkerCompletionManifest | None:
        """
        Retrieve the completion manifest for a specified worker.

        Returns:
            The recorded WorkerCompletionManifest, or None if the worker has not completed.

        Responsibility:
            Retrieve the completion manifest for a specified worker. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.manifest_for_worker` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._manifests_by_worker.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `manifest_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `manifest_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `manifest_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
              `manifest_for_worker`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `manifest_for_worker`

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
        with self._lock:
            return self._manifests_by_worker.get(worker_id)

    def snapshot(self) -> ReportingTransportSnapshot:
        """
        Generate a thread-safe snapshot of the current reporting transport session state.

        Returns:
            A ReportingTransportSnapshot representing the current expected workers, batches, and manifests.

        Responsibility:
            Generate a thread-safe snapshot of the current reporting transport session state. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.snapshot` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - tuple: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - ReportingTransportSnapshot: collaborator call used by this boundary
            - self._batches_by_worker.items: collaborator call used by this boundary
            - dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `snapshot`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `snapshot`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `snapshot`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `snapshot`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `snapshot`

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
        with self._lock:
            return ReportingTransportSnapshot(
                expected_worker_ids=tuple(sorted(self._expected_worker_ids)),
                batches_by_worker={
                    worker_id: tuple(sorted(batches, key=lambda batch: batch.batch_sequence))
                    for worker_id, batches in self._batches_by_worker.items()
                },
                manifests_by_worker=dict(self._manifests_by_worker),
            )

    def wait_for_batches(
        self,
        worker_id: str,
        *,
        minimum_count: int = 1,
        timeout: float = 2.0,
    ) -> tuple[WorkerChunkBatch, ...]:
        """
        Wait for a specified number of batches to arrive from a worker within a timeout.

        Returns:
            A tuple of WorkerChunkBatch instances for the worker.

        Responsibility:
            Wait for a specified number of batches to arrive from a worker within a timeout. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportSession.wait_for_batches` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - monotonic: collaborator call used by this boundary
            - self.batches_for_worker: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - sleep: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `wait_for_batches`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `wait_for_batches`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `wait_for_batches`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
              `wait_for_batches`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `wait_for_batches`

        State and side effects:
            mutates deadline, batches.

        Invariants:
            - `pytest_bdd.model.message_transport.ReportingTransportSession.wait_for_batches` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            batches = self.batches_for_worker(worker_id)
            if len(batches) >= minimum_count:
                return batches
            sleep(0.01)
        return self.batches_for_worker(worker_id)


@define
class ReportingTransportClient:
    """
    Represent reporting transport client state.

    Raises:
        ValueError: If the operation cannot be completed.
        RuntimeError: If the operation cannot be completed.

    Responsibility:
        Represent reporting transport client state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_transport.ReportingTransportClient` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - publish_envelopes: owns nested behavior below this boundary
        - build_manifest: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `ReportingTransportClient`
        - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
          `ReportingTransportClient`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ReportingTransportClient`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
          `ReportingTransportClient`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ReportingTransportClient`

    State and side effects:
        mutates msg, worker_id, sender, gateway_mode, batch_sequence.

    Invariants:
        - `pytest_bdd.model.message_transport.ReportingTransportClient` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError, RuntimeError; callers must treat these as boundary failures.

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

    worker_id: str
    sender: ReportingEventSender
    gateway_mode: str | None = None
    batch_sequence: int = 0
    transferred_batch_count: int = 0
    transferred_envelope_count: int = 0
    last_publish_error: str | None = None

    def publish_envelopes(self, envelope_dicts: list[JSONObject]) -> WorkerChunkBatch:
        """
        Publish a batch of cucumber message envelopes via the configured sender.

        Returns:
            The generated WorkerChunkBatch representing the sent payload.

        Raises:
            ValueError: If the envelope list is empty.
            RuntimeError: If an error occurs during transmission.

        Responsibility:
            Publish a batch of cucumber message envelopes via the configured sender. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportClient.publish_envelopes` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary
            - WorkerChunkBatch: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - json.dumps.encode: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `publish_envelopes`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `publish_envelopes`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `publish_envelopes`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references
              `publish_envelopes`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `publish_envelopes`

        State and side effects:
            mutates msg, batch, self.last_publish_error, self.batch_sequence, self.transferred_batch_count.

        Invariants:
            - `pytest_bdd.model.message_transport.ReportingTransportClient.publish_envelopes` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError, RuntimeError; callers must treat these as boundary failures.

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
        if not envelope_dicts:
            msg = "Cannot publish an empty transport batch."
            raise ValueError(msg)
        batch = WorkerChunkBatch(
            worker_id=self.worker_id,
            batch_sequence=self.batch_sequence,
            envelopes=tuple(envelope_dicts),
            byte_count=len(json.dumps(envelope_dicts, separators=(",", ":"), sort_keys=True).encode("utf-8")),
            gateway_mode=self.gateway_mode,
        )
        try:
            self.sender(REPORTING_BATCH_EVENT, batch=batch.as_dict(), gateway_mode=self.gateway_mode)
        except Exception as exc:
            self.last_publish_error = str(exc)
            logger.warning("Failed to publish worker transport batch for %s", self.worker_id, exc_info=True)
            msg = f"Failed to publish worker transport batch for '{self.worker_id}'."
            raise RuntimeError(msg) from exc
        self.batch_sequence += 1
        self.transferred_batch_count += 1
        self.transferred_envelope_count += len(envelope_dicts)
        return batch

    def build_manifest(self, *, complete: bool, interruption_reason: str | None = None) -> WorkerCompletionManifest:
        """
        Construct a final manifest detailing the worker's transmission statistics and completion status.

        Returns:
            A WorkerCompletionManifest summarizing the worker's transport session.

        Responsibility:
            Construct a final manifest detailing the worker's transmission statistics and completion status. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_transport.ReportingTransportClient.build_manifest` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - WorkerCompletionManifest: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `build_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references `build_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `build_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py: imports or references `build_manifest`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `build_manifest`

        State and side effects:
            mutates resolved_reason, resolved_complete, last_batch_sequence.

        Invariants:
            - `pytest_bdd.model.message_transport.ReportingTransportClient.build_manifest` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        resolved_reason = interruption_reason or self.last_publish_error
        resolved_complete = complete and resolved_reason is None
        last_batch_sequence = self.batch_sequence - 1 if self.transferred_batch_count else None
        return WorkerCompletionManifest(
            worker_id=self.worker_id,
            complete=resolved_complete,
            last_batch_sequence=last_batch_sequence,
            transferred_batch_count=self.transferred_batch_count,
            transferred_envelope_count=self.transferred_envelope_count,
            interruption_reason=resolved_reason,
            gateway_mode=self.gateway_mode,
        )
