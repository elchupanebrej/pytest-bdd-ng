"""
Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from collections.abc import Generator
from typing import Protocol, cast

import pytest
from pluggy import Result

from pytest_bdd.compatibility.pytest import CallInfo, FixtureRequest, Item, TestReport
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.plugin.pickle_runner.run_access import (
    build_reporting_context_snapshot,
    require_feature_binding,
    require_pickle_object,
    require_step_object,
)
from pytest_bdd.plugin.scenario_reporter.report import ScenarioReport, ScenarioReportData, StepReport


class _ScenarioReportTestReport(Protocol):
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

    """

    def __init__(self) -> None:
        """Initialize the scenario reporter."""
        self.current_report: ScenarioReport | None = None

    @staticmethod
    def _derive_scenario_report(scenario_report: ScenarioReport) -> ScenarioReportData:
        # Canonical scenario report derivation path: one serializer used for both test reports and downstream renderers.
        return scenario_report.serialize()

    def _store_context_snapshot(self, *, request: FixtureRequest, fallback_reason: str) -> None:
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
        scenario_report = self.current_report
        if scenario_report is None:
            msg = "Scenario report is unavailable before pytest_bdd_before_scenario."
            raise RuntimeError(msg)
        return scenario_report

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo) -> Generator[None, Result[TestReport], None]:
        """
        Handle the pytest runtest makereport pytest hook.

        Yields:
            Generated values.

        Raises:
            RuntimeError: If the operation cannot be completed.

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
        """Create scenario report for the item."""
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
        _run: Run,
        _step_func: object,
        _step_func_args: dict[str, object],
        _exception: Exception,
    ) -> None:
        """Finalize the step report as failed."""
        self._store_context_snapshot(request=request, fallback_reason="step_error_hierarchy_not_available")
        self._require_current_report().fail()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        run: Run,
        _step_func: object,
    ) -> None:
        """Store step start time."""
        step = require_step_object(run, hook_name="pytest_bdd_before_step")
        self._store_context_snapshot(request=request, fallback_reason="before_step_hierarchy_not_available")
        self._require_current_report().add_step_report(StepReport(step=step))

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        _run: Run,
        _step_func: object,
        _step_func_args: dict[str, object],
    ) -> None:
        """Finalize the step report as successful."""
        self._store_context_snapshot(request=request, fallback_reason="after_step_hierarchy_not_available")
        self._require_current_report().current_step_report.finalize()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_after_scenario(
        self,
        request: FixtureRequest,
        _run: Run,
    ) -> None:
        """Handle the pytest bdd after scenario pytest hook."""
        self._store_context_snapshot(request=request, fallback_reason="after_scenario_hierarchy_not_available")
