"""
Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.

Responsibility:
    Reporting functionality. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.scenario_reporter.plugin` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _ScenarioReportTestReport: owns nested behavior below this boundary
    - ScenarioReporter: owns nested behavior below this boundary
    - ScenarioReporterPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py: imports or references `plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `plugin`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `plugin`

State and side effects:
    mutates scenario_report, self.current_report, msg, scenario, item; depends on collections.abc.Generator,
    typing.Protocol, typing.cast, pytest, pluggy.Result.

Invariants:
    - `pytest_bdd.plugin.scenario_reporter.plugin` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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
    #arch-eval:locational_stability=4
"""

from collections.abc import Generator
from typing import Protocol, cast

import pytest
from pluggy import Result

from pytest_bdd.compatibility.pytest import CallInfo, FixtureRequest, Item
from pytest_bdd.model.run import Run
from pytest_bdd.model.run_access import (
    build_reporting_context_snapshot,
    require_feature_binding,
    require_pickle_object,
    require_step_object,
)
from pytest_bdd.model.scenario_report import ScenarioReport, ScenarioReportData, StepReport


class _ScenarioReportTestReport(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_reporter.plugin._ScenarioReportTestReport` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.scenario_reporter.plugin._ScenarioReportTestReport`
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
        mutates scenario, item, execution_context_snapshot.

    Invariants:
        - `pytest_bdd.plugin.scenario_reporter.plugin._ScenarioReportTestReport` keeps its documented import path,
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

    scenario: ScenarioReportData
    item: dict[str, str]
    execution_context_snapshot: object


class ScenarioReporter:
    """
    Represent scenario reporter state.

    Yields:
        Generated values.

    Raises:
        RuntimeError: If the operation cannot be completed.

    Responsibility:
        Represent scenario reporter state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _derive_scenario_report: owns nested behavior below this boundary
        - _store_context_snapshot: owns nested behavior below this boundary
        - _require_current_report: owns nested behavior below this boundary
        - pytest_runtest_makereport: owns nested behavior below this boundary
        - pytest_bdd_before_scenario: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates scenario_report, self.current_report, msg, outcome, rep.

    Invariants:
        - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """

    def __init__(self) -> None:
        """
        Initialize the scenario reporter.

        Responsibility:
            Initialize the scenario reporter. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.__init__` because it keeps the nearest code,
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
            mutates self.current_report.

        Invariants:
            - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.__init__` keeps its documented import path,
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
        self.current_report: ScenarioReport | None = None

    @staticmethod
    def _derive_scenario_report(scenario_report: ScenarioReport) -> ScenarioReportData:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._derive_scenario_report` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._derive_scenario_report` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - scenario_report.serialize: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        # Canonical scenario report derivation path: one serializer used for both test reports and downstream renderers.
        return scenario_report.serialize()

    def _store_context_snapshot(self, *, request: FixtureRequest, fallback_reason: str) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._store_context_snapshot` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._store_context_snapshot` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - scenario_report.set_context_snapshot: collaborator call used by this boundary
            - build_reporting_context_snapshot: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates scenario_report.

        Invariants:
            - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._store_context_snapshot` keeps its documented
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
        scenario_report = self.current_report
        if scenario_report is None:
            return
        scenario_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason=fallback_reason,
            ),
        )

    def _require_current_report(self) -> ScenarioReport:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._require_current_report` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._require_current_report` because it keeps the
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
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates scenario_report, msg.

        Invariants:
            - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter._require_current_report` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        scenario_report = self.current_report
        if scenario_report is None:
            msg = "Scenario report is unavailable before pytest_bdd_before_scenario."
            raise RuntimeError(msg)
        return scenario_report

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo) -> Generator[None, Result, None]:
        """
        Handle the pytest runtest makereport pytest hook.

        Yields:
            Generated values.

        Raises:
            RuntimeError: If the operation cannot be completed.

        Responsibility:
            Handle the pytest runtest makereport pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_runtest_makereport` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - outcome.get_result: collaborator call used by this boundary
            - self._derive_scenario_report: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary
            - context_snapshot.as_dict: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_runtest_makereport`

        State and side effects:
            mutates outcome, rep, scenario_report, rep.scenario, rep.item.

        Invariants:
            - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_runtest_makereport` keeps its
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
        outcome = yield
        if call.when != "setup":
            rep = cast("_ScenarioReportTestReport", outcome.get_result())
            """Store item in the report object."""
            scenario_report = self.current_report
            if scenario_report is not None:
                rep.scenario = self._derive_scenario_report(scenario_report)
                rep.item = {"name": item.name}
                context_snapshot = scenario_report.context_snapshot
                if context_snapshot is None:
                    msg = "Scenario report context snapshot is unavailable before report finalization."
                    raise RuntimeError(msg)
                rep.execution_context_snapshot = context_snapshot.as_dict()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_scenario(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """
        Create scenario report for the item.

        Responsibility:
            Create scenario report for the item. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_before_scenario` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - require_pickle_object: collaborator call used by this boundary
            - require_feature_binding: collaborator call used by this boundary
            - ScenarioReport: collaborator call used by this boundary
            - self._store_context_snapshot: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates pickle, feature_binding, self.current_report.

        Invariants:
            - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_before_scenario` keeps its
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
        pickle = require_pickle_object(run, hook_name="pytest_bdd_before_scenario")
        feature_binding = require_feature_binding(run, hook_name="pytest_bdd_before_scenario")
        self.current_report = ScenarioReport(
            feature_binding=feature_binding,
            pickle=pickle,
        )
        self._store_context_snapshot(request=request, fallback_reason="before_scenario_hierarchy_not_available")

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_step_error(
        self,
        request: FixtureRequest,
        run: Run,  # noqa: ARG002
        step_func: object,  # noqa: ARG002
        step_func_args: dict[str, object],  # noqa: ARG002
        exception: Exception,  # noqa: ARG002
    ) -> None:
        """
        Finalize the step report as failed.

        Responsibility:
            Finalize the step report as failed. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_step_error` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._store_context_snapshot: collaborator call used by this boundary
            - self._require_current_report.fail: collaborator call used by this boundary
            - self._require_current_report: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._store_context_snapshot(request=request, fallback_reason="step_error_hierarchy_not_available")
        self._require_current_report().fail()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: object,  # noqa: ARG002
    ) -> None:
        """
        Store step start time.

        Responsibility:
            Store step start time. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_before_step` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - require_step_object: collaborator call used by this boundary
            - self._store_context_snapshot: collaborator call used by this boundary
            - self._require_current_report.add_step_report: collaborator call used by this boundary
            - self._require_current_report: collaborator call used by this boundary
            - StepReport: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates step.

        Invariants:
            - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_before_step` keeps its documented
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
        step = require_step_object(run, hook_name="pytest_bdd_before_step")
        self._store_context_snapshot(request=request, fallback_reason="before_step_hierarchy_not_available")
        self._require_current_report().add_step_report(StepReport(step=step))

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        run: Run,  # noqa: ARG002
        step_func: object,  # noqa: ARG002
        step_func_args: dict[str, object],  # noqa: ARG002
    ) -> None:
        """
        Finalize the step report as successful.

        Responsibility:
            Finalize the step report as successful. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_after_step` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._store_context_snapshot: collaborator call used by this boundary
            - self._require_current_report.current_step_report.finalize: collaborator call used by this boundary
            - self._require_current_report: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._store_context_snapshot(request=request, fallback_reason="after_step_hierarchy_not_available")
        self._require_current_report().current_step_report.finalize()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_after_scenario(
        self,
        request: FixtureRequest,
        run: Run,  # noqa: ARG002
    ) -> None:
        """
        Handle the pytest bdd after scenario pytest hook.

        Responsibility:
            Handle the pytest bdd after scenario pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporter.pytest_bdd_after_scenario` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._store_context_snapshot: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._store_context_snapshot(request=request, fallback_reason="after_scenario_hierarchy_not_available")


class ScenarioReporterPlugin(ScenarioReporter):
    """
    Represent scenario reporter plugin state.

    Responsibility:
        Represent scenario reporter plugin state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporterPlugin`
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
        - src/pytest_bdd/plugin/scenario_reporter/entrypoint.py: imports or references `ScenarioReporterPlugin`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.scenario_reporter.plugin.ScenarioReporterPlugin` keeps its documented import path,
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
        #arch-eval:locational_stability=3
    """
