"""
xdist worker bootstrap for pytest-bdd reporting.

This module is selected via ``pytest_xdist_getremotemodule`` by the live
reporting entrypoint. It must avoid importing ``pytest_bdd`` before
``_prepareconfig()`` runs, otherwise xdist workers can hit
``PytestAssertRewriteWarning`` for already-imported modules.

Responsibility:
    xdist worker bootstrap for pytest-bdd reporting. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _WorkerInput: owns nested behavior below this boundary
    - _WorkerOptionDict: owns nested behavior below this boundary
    - _ReportingChannel: owns nested behavior below this boundary
    - _ParserProtocol: owns nested behavior below this boundary
    - _PreparedConfig: owns nested behavior below this boundary
    - _PreparedConfigHook: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `xdist_worker`

State and side effects:
    mutates workerinput, interactor, gateway_mode, config, testrunuid; depends on __future__.annotations, os, sys,
    pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

from _pytest.config import _prepareconfig  # noqa: PLC2701

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_bdd.compatibility.pytest import Stash


class _WorkerInput(TypedDict):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._WorkerInput` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._WorkerInput`
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
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates testrunuid, workerid, workercount, mainargv, pytest_bdd_messages_fragment_worker_id.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._WorkerInput` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    testrunuid: str
    workerid: str
    workercount: int
    mainargv: list[str]
    pytest_bdd_messages_fragment_worker_id: str
    pytest_bdd_messages_gateway_mode: str
    pytest_bdd_messages_force_publish_failure: bool


class _WorkerOptionDict(TypedDict, total=False):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._WorkerOptionDict` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._WorkerOptionDict` because it keeps the nearest code,
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
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates basetemp.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._WorkerOptionDict` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    basetemp: str | Path | None


class _ReportingChannel(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingChannel` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingChannel` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - receive: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingChannel` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    def receive(self) -> tuple[_WorkerInput, list[str], _WorkerOptionDict, list[str] | None]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingChannel.receive` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingChannel.receive` because it keeps the
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
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


class _ParserProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ParserProtocol` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ParserProtocol` because it keeps the nearest code,
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
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates prog.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ParserProtocol` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    prog: str


class _PreparedConfig(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfig` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfig` because it keeps the nearest code,
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
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates _parser, stash, workerinput, workeroutput, hook.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfig` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    _parser: _ParserProtocol
    stash: Stash
    workerinput: _WorkerInput
    workeroutput: dict[str, object]
    hook: _PreparedConfigHook


class _PreparedConfigHook(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfigHook`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfigHook` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_cmdline_main: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfigHook` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    def pytest_cmdline_main(self, config: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfigHook.pytest_cmdline_main` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._PreparedConfigHook.pytest_cmdline_main` because it
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
            - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `pytest_cmdline_main`

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


class _ReportingSender(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingSender` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingSender` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - sendevent: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingSender` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    def sendevent(self, name: str, **kwargs: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingSender.sendevent` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingSender.sendevent` because it keeps the
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
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


class _ReportingEventSender(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingEventSender`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingEventSender` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingEventSender` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    def __call__(self, name: str, **kwargs: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingEventSender.__call__` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._ReportingEventSender.__call__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


class _XdistRemoteModule(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._XdistRemoteModule`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._XdistRemoteModule` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - setup_config: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates interactor.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._XdistRemoteModule` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    interactor: _ReportingSender

    def setup_config(self, config: object, basetemp: str | Path | None) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._XdistRemoteModule.setup_config` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._XdistRemoteModule.setup_config` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


def _build_reporting_worker_environment(workerinput: Mapping[str, object]) -> dict[str, str]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_worker_environment` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_worker_environment` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

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
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates env, gateway_mode.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_worker_environment` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
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


def _apply_worker_python_path(change_sys_path: list[str] | None) -> None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._apply_worker_python_path` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._apply_worker_python_path` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - Path.cwd: collaborator call used by this boundary
        - sys.path.insert: collaborator call used by this boundary
        - os.environ.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates importpath, sys.path.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._apply_worker_python_path` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if change_sys_path is None:
        importpath = str(Path.cwd())
        sys.path.insert(0, importpath)
        os.environ["PYTHONPATH"] = importpath + os.pathsep + os.environ.get("PYTHONPATH", "")
    else:
        sys.path = change_sys_path


def _prepare_worker_config(
    workerinput: _WorkerInput,
    args: list[str],
    option_dict: _WorkerOptionDict,
) -> tuple[_PreparedConfig, _XdistRemoteModule]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._prepare_worker_config`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._prepare_worker_config` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - _prepareconfig: collaborator call used by this boundary
        - typed_remote.setup_config: collaborator call used by this boundary
        - option_dict.get: collaborator call used by this boundary
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates config, prepared_config, typed_remote, prepared_config._parser.prog, prepared_config.workerinput;
        depends on xdist.remote.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._prepare_worker_config` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    config = _prepareconfig(args, None)
    import xdist.remote as upstream_remote  # noqa: PLC0415

    prepared_config = cast("_PreparedConfig", config)
    typed_remote = cast("_XdistRemoteModule", upstream_remote)
    typed_remote.setup_config(config, option_dict.get("basetemp"))
    prepared_config._parser.prog = Path(workerinput["mainargv"][0]).name  # noqa: SLF001
    prepared_config.workerinput = workerinput
    prepared_config.workeroutput = {}
    return prepared_config, typed_remote


def _build_reporting_sender(
    interactor: _ReportingSender,
    *,
    force_publish_failure: bool,
) -> _ReportingEventSender:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_sender` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_sender` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - reporter_sender: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates msg.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_sender` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    def reporter_sender(name: str, **kwargs: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_sender.reporter_sender` owns
            documented function behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this function.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_sender.reporter_sender` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary
            - interactor.sendevent: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker._build_reporting_sender.reporter_sender` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        if force_publish_failure:
            msg = "simulated reporter channel failure"
            raise RuntimeError(msg)
        interactor.sendevent(name, **kwargs)

    return reporter_sender


def channel_main(reporting_channel: _ReportingChannel) -> None:
    """
    Handle channel main.

    Responsibility:
        Handle channel main. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ReportingWorkerInteractor: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates workerinput, args, option_dict, change_sys_path, reporting_env; depends on
        xdist.remote.WorkerInteractor, pytest_bdd.model.message_transport.ReportingEventSenderBinding.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    workerinput, args, option_dict, change_sys_path = reporting_channel.receive()

    _apply_worker_python_path(change_sys_path)
    reporting_env = _build_reporting_worker_environment(workerinput)
    os.environ.update(reporting_env)
    gateway_mode = reporting_env.get("PYTEST_BDD_REPORTING_GATEWAY_MODE", "")

    config, upstream_remote = _prepare_worker_config(workerinput, args, option_dict)
    from xdist.remote import WorkerInteractor as XdistWorkerInteractor  # noqa: PLC0415

    from pytest_bdd.model.message_transport import ReportingEventSenderBinding  # noqa: PLC0415

    class ReportingWorkerInteractor(XdistWorkerInteractor):
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main.ReportingWorkerInteractor` owns
            documented class behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this class.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main.ReportingWorkerInteractor` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - sendevent: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main.ReportingWorkerInteractor` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

        def sendevent(self, name: str, **kwargs: object) -> None:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main.ReportingWorkerInteractor.sendevent`
                owns documented method behavior. It directly owns the observable contract, local decisions, and
                maintenance boundary for this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.plugin.gherkin_message_reporter.xdist_worker.channel_main.ReportingWorkerInteractor.sendevent`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - self.log: collaborator call used by this boundary
                - self.channel.send: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - None found by static import/name scan; verify dynamic use before refactor

            State and side effects:
                keeps no local persistent state beyond call-local values.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=2
                #arch-eval:state_invariants=3
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=2
            """
            self.log("sending", name, kwargs)  # type: ignore[attr-defined]  # inherited from untyped XdistWorkerInteractor
            self.channel.send((name, kwargs))  # type: ignore[attr-defined]  # inherited from untyped XdistWorkerInteractor

    interactor = ReportingWorkerInteractor(config, reporting_channel)
    upstream_remote.interactor = interactor
    force_publish_failure = bool(workerinput.get("pytest_bdd_messages_force_publish_failure"))

    sender = _build_reporting_sender(
        interactor,
        force_publish_failure=force_publish_failure,
    )
    mode = gateway_mode or None
    ReportingEventSenderBinding(
        sender=sender,
        gateway_mode=mode,
    ).set_in_stash(config.stash)
    config.hook.pytest_cmdline_main(config=config)


if __name__ == "__channelexec__":
    channel_main(globals()["channel"])
