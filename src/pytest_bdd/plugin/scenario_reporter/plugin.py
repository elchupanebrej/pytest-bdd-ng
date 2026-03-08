"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from collections.abc import Callable

import pytest

from pytest_bdd.compatibility.pytest import CallInfo, FixtureRequest, Item
from pytest_bdd.plugin.pickle_runner.run_access import (
    build_reporting_context_snapshot,
    resolve_feature_binding,
    resolve_feature_object,
    resolve_pickle_object,
    resolve_step_object,
)
from pytest_bdd.plugin.scenario_reporter.report import ScenarioReport, StepReport


class ScenarioReporter:
    def __init__(self):
        self.current_report = None

    @staticmethod
    def _derive_scenario_report(scenario_report: ScenarioReport) -> dict:
        # Canonical scenario report derivation path: one serializer used for both test reports and downstream renderers.
        return scenario_report.serialize()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo):
        outcome = yield
        if call.when != "setup":
            rep = outcome.get_result()
            """Store item in the report object."""
            scenario_report: ScenarioReport = self.current_report

            if scenario_report is not None:
                rep.scenario = self._derive_scenario_report(scenario_report)
                rep.item = {"name": item.name}
                if scenario_report.context_snapshot is not None:
                    rep.execution_context_snapshot = scenario_report.context_snapshot.as_dict()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_scenario(
        self,
        request: FixtureRequest,
        run,
    ) -> None:
        """Create scenario report for the item."""
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        if gherkin_document is None or pickle is None:
            return
        feature_binding = resolve_feature_binding(run)
        if feature_binding is None:
            msg = "Run does not provide active feature binding"
            raise RuntimeError(msg)
        self.current_report = ScenarioReport(
            feature_binding=feature_binding,
            pickle=pickle,
        )  # type: ignore[call-arg]
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="before_scenario_hierarchy_not_available",
            )
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_step_error(
        self,
        request: FixtureRequest,
        run,  # noqa: ARG002 hookspec
        step_func: Callable,  # noqa: ARG002 hookspec
        step_func_args: dict,  # noqa: ARG002 hookspec
        exception: Exception,  # noqa: ARG002 hookspec
    ) -> None:
        """Finalize the step report as failed."""
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="step_error_hierarchy_not_available",
            )
        )
        self.current_report.fail()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        run,
        step_func: Callable,  # noqa: ARG002 hookspec
    ) -> None:
        """Store step start time."""
        step = resolve_step_object(run)
        if step is None:
            return
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="before_step_hierarchy_not_available",
            )
        )
        self.current_report.add_step_report(StepReport(step=step))

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        run,  # noqa: ARG002 hookspec
        step_func: Callable,  # noqa: ARG002 hookspec
        step_func_args: dict,  # noqa: ARG002 hookspec
    ) -> None:
        """Finalize the step report as successful."""
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="after_step_hierarchy_not_available",
            )
        )
        self.current_report.current_step_report.finalize()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_after_scenario(
        self,
        request: FixtureRequest,
        run,  # noqa: ARG002 hookspec
    ) -> None:
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="after_scenario_hierarchy_not_available",
            )
        )
