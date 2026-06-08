"""
Provide message stream helpers.

Responsibility:
    Provide message stream helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.message_stream` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _WorkerControllerConfigProtocol: owns nested behavior below this boundary
    - _WorkerControllerHookProtocol: owns nested behavior below this boundary
    - _WorkerControllerProtocol: owns nested behavior below this boundary
    - _PatchedProcessFromRemote: owns nested behavior below this boundary
    - coerce_reporting_batch_payload: owns nested behavior below this boundary
    - ensure_xdist_controller_batch_patch: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `message_stream`

State and side effects:
    mutates logger, hook, config, __pytest_bdd_reporting_patch__, msg; depends on __future__.annotations, logging,
    typing.TYPE_CHECKING, typing.Protocol, typing.cast.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.message_stream` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError, re-raise; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, cast

import pytest

from pytest_bdd.model.message_transport import REPORTING_BATCH_EVENT

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class _WorkerControllerConfigProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerConfigProtocol` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerConfigProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - notify_exception: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_WorkerControllerConfigProtocol`

    State and side effects:
        mutates hook.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerConfigProtocol` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    hook: _WorkerControllerHookProtocol

    def notify_exception(self, excinfo: pytest.ExceptionInfo) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerConfigProtocol.notify_exception`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerConfigProtocol.notify_exception`
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `notify_exception`

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
            #arch-eval:locational_stability=3
        """
        ...


class _WorkerControllerHookProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerHookProtocol` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerHookProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_xdist_message_batch: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_WorkerControllerHookProtocol`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerHookProtocol` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def pytest_bdd_xdist_message_batch(
        self,
        *,
        config: _WorkerControllerConfigProtocol,
        node: _WorkerControllerProtocol,
        batch: dict[str, object],
    ) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerHookProtocol.pytest_bdd_xdist_message_batch`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerHookProtocol.pytest_bdd_xdist_message_batch`
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `pytest_bdd_xdist_message_batch`

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
            #arch-eval:locational_stability=3
        """
        ...


class _WorkerControllerProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - shutdown: owns nested behavior below this boundary
        - notify_inproc: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_WorkerControllerProtocol`

    State and side effects:
        mutates config.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    config: _WorkerControllerConfigProtocol

    def shutdown(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol.shutdown` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol.shutdown` because it
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `shutdown`

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
            #arch-eval:locational_stability=3
        """
        ...

    def notify_inproc(self, event: str, **kwargs: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol.notify_inproc` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._WorkerControllerProtocol.notify_inproc` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `notify_inproc`

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
            #arch-eval:locational_stability=3
        """
        ...


class _PatchedProcessFromRemote(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._PatchedProcessFromRemote` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream._PatchedProcessFromRemote` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_PatchedProcessFromRemote`

    State and side effects:
        mutates __pytest_bdd_reporting_patch__.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.message_stream._PatchedProcessFromRemote` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    __pytest_bdd_reporting_patch__: bool

    def __call__(self, controller: _WorkerControllerProtocol, eventcall: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._PatchedProcessFromRemote.__call__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream._PatchedProcessFromRemote.__call__` because it
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
            #arch-eval:locational_stability=3
        """
        ...


def coerce_reporting_batch_payload(batch_payload: object) -> dict[str, object]:
    """
    Coerce reporting batch payload to dictionary.

    Returns:
        Batch payload as dictionary.

    Raises:
        TypeError: If the operation cannot be completed.

    Responsibility:
        Coerce reporting batch payload to dictionary. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream.coerce_reporting_batch_payload` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `coerce_reporting_batch_payload`

    State and side effects:
        mutates msg.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.message_stream.coerce_reporting_batch_payload` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

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
        #arch-eval:locational_stability=3

    """
    if isinstance(batch_payload, dict):
        return batch_payload
    msg = "xdist reporter batch payload must be a dictionary"
    raise TypeError(msg)


def ensure_xdist_controller_batch_patch() -> bool:
    """
    Ensure xdist controller batch patch.

    Returns:
        True if patched, False otherwise.

    Responsibility:
        Ensure xdist controller batch patch. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.message_stream.ensure_xdist_controller_batch_patch` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - patched_process_from_remote: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ensure_xdist_controller_batch_patch`

    State and side effects:
        mutates original, marker_end, event_name, kwargs, batch_payload; depends on xdist.workermanage.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.message_stream.ensure_xdist_controller_batch_patch` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    try:
        from xdist import workermanage  # noqa: PLC0415 -- optional xdist dependency
    except ImportError:
        return False

    original = cast("Callable[[object, object], None]", workermanage.WorkerController.process_from_remote)
    if getattr(original, "__pytest_bdd_reporting_patch__", False):
        return True

    marker_end = workermanage.Marker.END

    def patched_process_from_remote(self: _WorkerControllerProtocol, eventcall: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream.ensure_xdist_controller_batch_patch.patched_process_from_remote`
            owns documented function behavior. It directly owns the observable contract, local decisions, and
            maintenance boundary for this function.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.message_stream.ensure_xdist_controller_batch_patch.patched_process_from_remote`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - coerce_reporting_batch_payload: collaborator call used by this boundary
            - kwargs.get: collaborator call used by this boundary
            - self.config.hook.pytest_bdd_xdist_message_batch: collaborator call used by this boundary
            - pytest.ExceptionInfo.from_current: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `patched_process_from_remote`

        State and side effects:
            mutates event_name, kwargs, batch_payload, excinfo.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.message_stream.ensure_xdist_controller_batch_patch.patched_process_from_remote`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises re-raise; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        if eventcall is not marker_end and isinstance(eventcall, tuple) and len(eventcall) == 2:  # noqa: PLR2004
            event_name, kwargs = eventcall
            if event_name == REPORTING_BATCH_EVENT and isinstance(kwargs, dict):
                try:
                    batch_payload = coerce_reporting_batch_payload(kwargs.get("batch"))
                    self.config.hook.pytest_bdd_xdist_message_batch(
                        config=self.config,
                        node=self,
                        batch=batch_payload,
                    )
                except KeyboardInterrupt:
                    raise
                except Exception:
                    excinfo = pytest.ExceptionInfo.from_current()
                    logger.exception("Failed to process pytest-bdd xdist reporter batch.")
                    self.config.notify_exception(excinfo)
                    self.shutdown()
                    self.notify_inproc("errordown", node=self, error=excinfo)
                return
        original(self, eventcall)

    patched_process_from_remote_with_attr = cast("_PatchedProcessFromRemote", patched_process_from_remote)
    patched_process_from_remote_with_attr.__pytest_bdd_reporting_patch__ = True
    workermanage.WorkerController.process_from_remote = cast(  # type: ignore[assignment, method-assign]  # intentional monkeypatch for xdist
        "Callable[[object, object], None]",
        patched_process_from_remote_with_attr,
    )
    return True
