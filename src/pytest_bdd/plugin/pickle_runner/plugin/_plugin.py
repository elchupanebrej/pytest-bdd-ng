"""
PickleRunner plugin core — setup, teardown, and hook orchestration.

Responsibility:
    PickleRunner plugin core — setup, teardown, and hook orchestration. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._plugin` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _IdeBindingService: owns nested behavior below this boundary
    - _get_ide_binding_service: owns nested behavior below this boundary
    - _StepCaller: owns nested behavior below this boundary
    - _FixtureCaller: owns nested behavior below this boundary
    - PickleRunner: owns nested behavior below this boundary
    - PickleRunnerPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `_plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_plugin`

State and side effects:
    mutates __tracebackhide__, pickle, gherkin_document, previous_step, run; depends on __future__.annotations, logging,
    contextlib.suppress, typing.TYPE_CHECKING, typing.Protocol.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.plugin._plugin` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError, step_lookup_exception; callers must treat these as boundary failures.

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

import logging
from contextlib import suppress
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from cucumber_messages import (
    GherkinDocument,  # upstream library missing type stubs
    Pickle,  # library has no type stubs
    PickleStep,  # upstream library missing type stubs
    Source,
)

import pytest_bdd.types.exception as exceptions
from pytest_bdd.compatibility.pytest import FixtureRequest, Item
from pytest_bdd.model.run import (
    HookPhase,
    Run,
    RunStatus,
)
from pytest_bdd.model.run_access import (
    require_feature_binding,
    require_feature_object,
    require_pickle_object,
    require_step_object,
    resolve_previous_step_object,
    resolve_scenario_description,
    resolve_step_runtime_enrichment,
)
from pytest_bdd.model.scenario_collection import PYTEST_BDD_MARK
from pytest_bdd.model.scenario_run import StepRun
from pytest_bdd.steps import Matcher
from pytest_bdd.util.other import IdGenerator

from ..const import Steps
from ..run_transitions import apply_transition
from ._executor import (
    _get_step_function_kwargs,
    _inject_step_parameters_as_fixtures,
    _inject_target_fixtures,
    _match_step_or_report_lookup_error,
    _match_to_step,
    _pytest_bdd_get_step_caller,
    _run_step_body,
    _run_step_call,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections import deque
    from collections.abc import Callable, Iterator, Mapping

    from pytest_bdd.compatibility.pytest import Session


UNSET = object()


class _IdeBindingService(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.plugin._plugin._IdeBindingService` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._plugin._IdeBindingService`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - has_test_case_binding_error: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_IdeBindingService`
        - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_IdeBindingService`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._plugin._IdeBindingService` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    def has_test_case_binding_error(self, test_case_id: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.pickle_runner.plugin._plugin._IdeBindingService.has_test_case_binding_error` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin._IdeBindingService.has_test_case_binding_error` because it
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
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `has_test_case_binding_error`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `has_test_case_binding_error`

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


def _get_ide_binding_service(config: object) -> _IdeBindingService | None:
    """
    Retrieve IdeBindingService from the GherkinMessageReporter if available.

    Returns:
        IDE binding service object, or None when reporter is inactive.

    Responsibility:
        Retrieve IdeBindingService from the GherkinMessageReporter if available. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.plugin._plugin._get_ide_binding_service` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - pm.get_plugins: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_get_ide_binding_service`
        - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_get_ide_binding_service`

    State and side effects:
        mutates pm, svc.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._plugin._get_ide_binding_service` keeps its documented import path,
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
        #arch-eval:locational_stability=3

    """
    with suppress(Exception):
        pm = getattr(config, "pluginmanager", None)
        if pm is None:
            return None
        for plugin in pm.get_plugins():
            svc = cast("_IdeBindingService | None", getattr(plugin, "ide_binding_service", None))
            if svc is not None:
                return svc
    return None


class _StepCaller(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.plugin._plugin._StepCaller` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._plugin._StepCaller` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_StepCaller`
        - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_StepCaller`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._plugin._StepCaller` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=3
    """

    def __call__(self) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.plugin._plugin._StepCaller.__call__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin._StepCaller.__call__` because it keeps the nearest code,
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
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__call__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `__call__`

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


class _FixtureCaller(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.plugin._plugin._FixtureCaller` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._plugin._FixtureCaller`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_FixtureCaller`
        - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_FixtureCaller`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._plugin._FixtureCaller` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=3
    """

    def __call__(self, *, fixturefunc: object, request: FixtureRequest, kwargs: Mapping[str, object]) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.plugin._plugin._FixtureCaller.__call__`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin._FixtureCaller.__call__` because it keeps the nearest code,
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
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__call__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `__call__`

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


class PickleRunner:
    """
    Represent pickle runner state.

    Yields:
        Generated values.

    Raises:
        RuntimeError: If the operation cannot be completed.
        step_lookup_exception: If the operation cannot be completed.

    Responsibility:
        Represent pickle runner state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _require_request: owns nested behavior below this boundary
        - _require_gherkin_document: owns nested behavior below this boundary
        - _require_pickle: owns nested behavior below this boundary
        - _resolve_runtime_params: owns nested behavior below this boundary
        - pytest_sessionstart: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `PickleRunner`
        - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `PickleRunner`

    State and side effects:
        mutates __tracebackhide__, pickle, gherkin_document, previous_step, run.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError, step_lookup_exception; callers must treat these as boundary failures.

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

    plugin_name = "pytest-bdd-scenario-runner-runtime"

    def __init__(self) -> None:
        """
        Initialize the pickle runner.

        Responsibility:
            Initialize the pickle runner. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.__init__` because it keeps the nearest code,
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
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.request, self.gherkin_document, self.pickle, self.feature_source.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.__init__` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.request: FixtureRequest | None = None
        self.gherkin_document: GherkinDocument | None = None
        self.pickle: Pickle | None = None
        self.feature_source: Source | None = None

    def _require_request(self) -> FixtureRequest:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_request` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_request` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_require_request`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_require_request`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_request` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.request is None:
            msg = "Pickle runner request is unavailable before pytest_runtest_protocol."
            raise RuntimeError(msg)
        return self.request

    def _require_gherkin_document(self) -> GherkinDocument:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_gherkin_document` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_gherkin_document` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_require_gherkin_document`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_require_gherkin_document`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_gherkin_document` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.gherkin_document is None:
            msg = "Pickle runner gherkin document is unavailable before pytest_runtest_protocol."
            raise RuntimeError(msg)
        return self.gherkin_document

    def _require_pickle(self) -> Pickle:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_pickle` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_pickle` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_require_pickle`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_require_pickle`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._require_pickle` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.pickle is None:
            msg = "Pickle runner pickle is unavailable before pytest_runtest_protocol."
            raise RuntimeError(msg)
        return self.pickle

    @staticmethod
    def _resolve_runtime_params(item: Item) -> tuple[object | None, object | None, object | None]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._resolve_runtime_params` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._resolve_runtime_params` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - params.get: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_resolve_runtime_params`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_resolve_runtime_params`

        State and side effects:
            mutates callspec, params, gherkin_document, pickle, feature_source.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._resolve_runtime_params` keeps its documented
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
            #arch-eval:locational_stability=3
        """
        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", None)
        if isinstance(params, dict):
            gherkin_document = params.get("gherkin_document")
            pickle = params.get("pickle")
            feature_source = params.get("feature_source")
            if gherkin_document is not None and pickle is not None and feature_source is not None:
                return gherkin_document, pickle, feature_source
        return None, None, None

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session: Session) -> None:  # noqa: PLR6301 -- pytest hook, must be instance method
        """
        Handle the pytest sessionstart pytest hook.

        Responsibility:
            Handle the pytest sessionstart pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_sessionstart` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Run.from_stash: collaborator call used by this boundary
            - next: collaborator call used by this boundary
            - IdGenerator.from_stash: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_sessionstart`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_sessionstart`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_sessionstart`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `pytest_sessionstart`

        State and side effects:
            mutates run, run.reporting_state.run_started_id.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_sessionstart` keeps its documented
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
        run = Run.from_stash(session.config.stash)
        if run.reporting_state.run_started_id is None:
            run.reporting_state.run_started_id = next(IdGenerator.from_stash(session.config.stash))

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        """
        Handle the pytest runtest setup pytest hook.

        Responsibility:
            Handle the pytest runtest setup pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_runtest_setup` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - item.iter_markers: collaborator call used by this boundary
            - self._resolve_runtime_params: collaborator call used by this boundary
            - Run.from_stash: collaborator call used by this boundary
            - run.create_scenario_run: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_runtest_setup`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `pytest_runtest_setup`

        State and side effects:
            mutates __tracebackhide__, mark_names, request, gherkin_document, pickle.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_runtest_setup` keeps its documented
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
            #arch-eval:locational_stability=3
        """
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        request = item._request  # noqa: SLF001
        gherkin_document, pickle, feature_source = self._resolve_runtime_params(item=item)
        if gherkin_document is None or pickle is None or feature_source is None:
            return

        run = Run.from_stash(request.config.stash)
        run.create_scenario_run(
            request,
            gherkin_document=gherkin_document,  # type: ignore[arg-type]  # stash returns untyped object
            feature_source=feature_source,  # type: ignore[arg-type]  # stash returns untyped object
            pickle=pickle,  # type: ignore[arg-type]  # stash returns untyped object
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item: Item) -> None:
        """
        Handle the pytest runtest call pytest hook.

        Responsibility:
            Handle the pytest runtest call pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_runtest_call` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.request.getfixturevalue: collaborator call used by this boundary
            - self._invoke_bdd_hook: collaborator call used by this boundary
            - item.iter_markers: collaborator call used by this boundary
            - self.request.config.getoption: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - self._verify_mock_run_bindings: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_runtest_call`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `pytest_runtest_call`

        State and side effects:
            mutates __tracebackhide__, mark_names, self.request, self.gherkin_document, self.pickle.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_runtest_call` keeps its documented
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
            #arch-eval:locational_stability=3
        """
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        self.request = item._request  # noqa: SLF001
        self.gherkin_document = self.request.getfixturevalue("gherkin_document")
        self.pickle = self.request.getfixturevalue("pickle")
        self.feature_source = self.request.getfixturevalue("feature_source")

        if self.request.config.getoption(str(Steps.Cli.MOCK_RUN), default=False):
            self._verify_mock_run_bindings(item)
            return

        self._invoke_bdd_hook(
            hook_name="pytest_bdd_before_scenario",
            request=self.request,
            gherkin_document=self.gherkin_document,
            pickle=self.pickle,
        )
        try:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_run_scenario",
                request=self.request,
                gherkin_document=self.gherkin_document,
                pickle=self.pickle,
            )
        finally:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_after_scenario",
                request=self.request,
                gherkin_document=self.gherkin_document,
                pickle=self.pickle,
            )

        # Allow test function to use updated fixtures directly
        fixturenames = getattr(item, "fixturenames", [])
        for argname in fixturenames:
            item.funcargs[argname] = item._request.getfixturevalue(argname)  # type:ignore[attr-defined]  # noqa: SLF001

    def _verify_mock_run_bindings(self, item: Item) -> None:
        """
        Verify step bindings without executing scenario lifecycle.

        Responsibility:
            Verify step bindings without executing scenario lifecycle. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._verify_mock_run_bindings` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._require_request: collaborator call used by this boundary
            - Run.from_stash: collaborator call used by this boundary
            - run.require_active_scenario_run: collaborator call used by this boundary
            - self._require_gherkin_document: collaborator call used by this boundary
            - self._require_pickle: collaborator call used by this boundary
            - StepRun: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_verify_mock_run_bindings`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_verify_mock_run_bindings`

        State and side effects:
            mutates has_binding_error, previous_step, step_to_report, request, config.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._verify_mock_run_bindings` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises step_lookup_exception; callers must treat these as boundary failures.

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
        request = self._require_request()
        config = request.config
        run = Run.from_stash(config.stash)
        scenario_run = run.require_active_scenario_run(hook_name="pytest_runtest_call")
        gherkin_document = self._require_gherkin_document()
        pickle = self._require_pickle()
        previous_step: PickleStep | None = None

        # Collect test_case_id for binding error check (set during pytest_runtest_setup)
        test_case_id: str = run.reporting_state.active_test_case_id or ""

        has_binding_error = False
        step_to_report: PickleStep | None = None
        for step in pickle.steps:
            scenario_run.step_object = step
            scenario_run.previous_step_object = previous_step  # type: ignore[assignment]  # PickleStep vs NoPreviousStep variant
            scenario_run.step_run = StepRun(step=step, text=step.text)

            try:
                _match_to_step(self, run)
            except (exceptions.StepDefinitionNotFoundError, Matcher.MatchNotFoundError):
                # Missing step: diagnostic was already emitted in step_catalog_runtime setup
                has_binding_error = True
                step_to_report = step
            previous_step = step

        # Ambiguous steps succeed in _match_to_step but were flagged during setup
        ide_service = _get_ide_binding_service(config)
        if (
            ide_service is not None
            and hasattr(ide_service, "has_test_case_binding_error")
            and ide_service.has_test_case_binding_error(test_case_id)
        ):
            has_binding_error = True

        if has_binding_error:
            step_lookup_exception = exceptions.StepDefinitionNotFoundError(
                gherkin_document,  # type: ignore[arg-type]  # dynamic runtime type
                pickle,
                step_to_report or scenario_run.step_object or pickle.steps[0],
            )
            raise step_lookup_exception

        # Allow test function fixtures to be resolved after mock verification.
        for argname in getattr(item, "fixturenames", []):
            item.funcargs[argname] = item._request.getfixturevalue(argname)  # type:ignore[attr-defined]  # noqa: SLF001

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_teardown(self, item: Item, nextitem: Item | None) -> Iterator[None]:  # noqa: ARG002, PLR6301 -- pytest hook
        """
        Handle the pytest runtest teardown pytest hook.

        Yields:
            Generated values.

        Responsibility:
            Handle the pytest runtest teardown pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_runtest_teardown` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Run.pop_scenario_run: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_runtest_teardown`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `pytest_runtest_teardown`

        State and side effects:
            mutates __tracebackhide__.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_runtest_teardown` keeps its documented
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
            #arch-eval:locational_stability=3

        """
        __tracebackhide__ = True
        yield
        Run.pop_scenario_run(item._request)  # noqa: SLF001

    @staticmethod
    def _invoke_bdd_hook(  # noqa: PLR0913
        *,
        hook_name: str,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step: object = UNSET,
        previous_step: object = UNSET,
        status: RunStatus | None = None,
        **extra_kwargs: object,
    ) -> object:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._invoke_bdd_hook` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._invoke_bdd_hook` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - Run.from_stash: collaborator call used by this boundary
            - HookPhase: collaborator call used by this boundary
            - run.require_active_scenario_run: collaborator call used by this boundary
            - apply_transition: collaborator call used by this boundary
            - hook_kwargs.update: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_invoke_bdd_hook`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `_invoke_bdd_hook`

        State and side effects:
            mutates scenario_run, run, hook_phase, hook_kwargs.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner._invoke_bdd_hook` keeps its documented import
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
            #arch-eval:locational_stability=3
        """
        run = Run.from_stash(request.config.stash)
        scenario_run = run.active_scenario_run

        try:
            hook_phase = HookPhase(hook_name)
        except ValueError:
            pass
        else:
            scenario_run = run.require_active_scenario_run(hook_name=hook_name)
            apply_transition(
                scenario_run,
                hook_phase=hook_phase,
                gherkin_document=gherkin_document,
                pickle=pickle,
                step=None if step is UNSET else step,
                previous_step=None if previous_step is UNSET else previous_step,
                status=status,
            )

        hook_kwargs: dict[str, object] = {
            "request": request,
            "run": run,
        }
        hook_kwargs.update(extra_kwargs)
        return getattr(request.config.hook, hook_name)(**hook_kwargs)

    def pytest_bdd_run_scenario(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        request: FixtureRequest,
        run: Run,
    ) -> object:
        """
        Execute scenarios via step dispatcher.

        Args:
            request: Pytest fixture request.
            run: Current run.

        Returns:
            Result of step dispatch.

        Responsibility:
            Execute scenarios via step dispatcher. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_run_scenario` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - require_feature_object: collaborator call used by this boundary
            - require_pickle_object: collaborator call used by this boundary
            - request.getfixturevalue: collaborator call used by this boundary
            - steps.extend: collaborator call used by this boundary
            - request.config.hook.pytest_bdd_get_step_dispatcher: collaborator call used by this boundary
            - step_dispatcher: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_bdd_run_scenario`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `pytest_bdd_run_scenario`

        State and side effects:
            mutates __tracebackhide__, pickle, steps, step_dispatcher.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_run_scenario` keeps its documented
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
            #arch-eval:locational_stability=3

        """
        __tracebackhide__ = True
        require_feature_object(run, hook_name="pytest_bdd_run_scenario")
        pickle = require_pickle_object(run, hook_name="pytest_bdd_run_scenario")
        steps: deque[object] = request.getfixturevalue("steps_left")
        steps.extend(pickle.steps)
        step_dispatcher = request.config.hook.pytest_bdd_get_step_dispatcher(
            request=request,
            run=run,
        )
        return step_dispatcher(steps)

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_get_step_dispatcher(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> Callable[[deque[PickleStep]], None]:
        """
        Provide alternative approach to execute steps.

        Args:
            request: Pytest fixture request.
            run: Current run.

        Returns:
            Step dispatcher function.

        Responsibility:
            Provide alternative approach to execute steps. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_get_step_dispatcher` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - dispatcher: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `pytest_bdd_get_step_dispatcher`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references
              `pytest_bdd_get_step_dispatcher`

        State and side effects:
            mutates __tracebackhide__, previous_step, gherkin_document, pickle, step.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_get_step_dispatcher` keeps its
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
            #arch-eval:locational_stability=3

        """
        __tracebackhide__ = True

        def dispatcher(left_steps: deque[PickleStep]) -> None:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_get_step_dispatcher.dispatcher`
                owns documented method behavior. It directly owns the observable contract, local decisions, and
                maintenance boundary for this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_get_step_dispatcher.dispatcher`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - require_feature_object: collaborator call used by this boundary
                - require_pickle_object: collaborator call used by this boundary
                - left_steps.popleft: collaborator call used by this boundary
                - self._invoke_bdd_hook: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `dispatcher`
                - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `dispatcher`

            State and side effects:
                mutates previous_step, __tracebackhide__, gherkin_document, pickle, step.

            Invariants:
                - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_get_step_dispatcher.dispatcher`
                  keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
            __tracebackhide__ = True
            previous_step = None
            gherkin_document = require_feature_object(run, hook_name="pytest_bdd_run_step")
            pickle = require_pickle_object(run, hook_name="pytest_bdd_run_step")
            while left_steps:
                step = left_steps.popleft()
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_run_step",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                )
                previous_step = step

        return dispatcher

    def pytest_bdd_run_step(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """
        Handle the pytest bdd run step pytest hook.

        Responsibility:
            Handle the pytest bdd run step pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_run_step` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - step_runtime_enrichment.get: collaborator call used by this boundary
            - run.require_active_scenario_run: collaborator call used by this boundary
            - require_feature_object: collaborator call used by this boundary
            - require_pickle_object: collaborator call used by this boundary
            - require_step_object: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_bdd_run_step`
            - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `pytest_bdd_run_step`

        State and side effects:
            mutates __tracebackhide__, scenario_run, gherkin_document, pickle, step.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunner.pytest_bdd_run_step` keeps its documented
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
            #arch-eval:locational_stability=3
        """
        __tracebackhide__ = True
        scenario_run = run.require_active_scenario_run(hook_name="pytest_bdd_run_step")
        gherkin_document = require_feature_object(run, hook_name="pytest_bdd_run_step")
        pickle = require_pickle_object(run, hook_name="pytest_bdd_run_step")
        step = require_step_object(run, hook_name="pytest_bdd_run_step")
        previous_step = resolve_previous_step_object(run)
        feature_binding = require_feature_binding(run, hook_name="pytest_bdd_run_step")

        scenario_run.step_run = StepRun(
            step=step if isinstance(step, PickleStep) else None,
            text=getattr(step, "text", ""),
        )
        if isinstance(step, PickleStep):
            step_runtime_enrichment = resolve_step_runtime_enrichment(
                step=step,
                feature_binding=feature_binding,
                scenario_run=scenario_run,
            )
            scenario_run.step_run.step = step
            keyword = step_runtime_enrichment.get("keyword")
            scenario_run.step_run.keyword = keyword if isinstance(keyword, str) else None
            scenario_run.step_run.doc_string = step_runtime_enrichment.get("doc_string")
            scenario_run.step_run.data_table = step_runtime_enrichment.get("data_table")
            line_number = step_runtime_enrichment.get("line_number")
            scenario_run.step_run.line_number = line_number if isinstance(line_number, int) else None

        scenario_description = resolve_scenario_description(
            pickle=pickle,
            feature_binding=feature_binding,
            scenario_run=scenario_run,
        )
        pickle.__dict__["description"] = scenario_description

        try:
            _run_step_body(
                self,
                request=request,
                run=run,
                gherkin_document=gherkin_document,
                pickle=pickle,
                step=step,
                previous_step=previous_step,
                scenario_run=scenario_run,
            )
        finally:
            # TODO: Seems that this field must be put into scenario run
            pickle.__dict__["description"] = None

    # Assign methods extracted to _executor module
    _run_step_body = _run_step_body  # overwritten above, but matches type
    _match_step_or_report_lookup_error = _match_step_or_report_lookup_error
    _run_step_call = _run_step_call
    pytest_bdd_get_step_caller = _pytest_bdd_get_step_caller
    _inject_step_parameters_as_fixtures = _inject_step_parameters_as_fixtures
    _get_step_function_kwargs = _get_step_function_kwargs
    _inject_target_fixtures = _inject_target_fixtures
    _match_to_step = _match_to_step


class PickleRunnerPlugin(PickleRunner):
    """
    Represent pickle runner plugin state.

    Responsibility:
        Represent pickle runner plugin state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunnerPlugin`
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
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `PickleRunnerPlugin`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `PickleRunnerPlugin`
        - src/pytest_bdd/plugin/pickle_runner/plugin/facade.py: imports or references `PickleRunnerPlugin`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.plugin._plugin.PickleRunnerPlugin` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
