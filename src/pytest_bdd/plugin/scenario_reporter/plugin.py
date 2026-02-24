"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from collections.abc import Callable

import pytest
from cucumber_messages import Pickle, PickleStep  # type:ignore[import-untyped]

from pytest_bdd.compatibility.pytest import CallInfo, FixtureRequest, Item
from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.plugin.scenario_reporter.report import ScenarioReport, StepReport
from pytest_bdd.plugin.scenario_runner.context_access import build_reporting_context_snapshot


class ScenarioReporter:
    def __init__(self):
        self.current_report = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo):
        outcome = yield
        if call.when != "setup":
            rep = outcome.get_result()
            """Store item in the report object."""
            scenario_report: ScenarioReport = self.current_report

            if scenario_report is not None:
                rep.scenario = scenario_report.serialize()
                rep.item = {"name": item.name}
                if scenario_report.context_snapshot is not None:
                    rep.execution_context_snapshot = scenario_report.context_snapshot.as_dict()

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_scenario(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Pickle,
    ) -> None:
        """Create scenario report for the item."""
        self.current_report = ScenarioReport(feature=feature, scenario=scenario)  # type: ignore[call-arg]
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
        feature: Feature,  # noqa: ARG002 hookspec
        scenario: Pickle,  # noqa: ARG002 hookspec
        step: PickleStep,  # noqa: ARG002 hookspec
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
        feature: Feature,  # noqa: ARG002 hookspec
        scenario: Pickle,  # noqa: ARG002 hookspec
        step: PickleStep,
        step_func: Callable,  # noqa: ARG002 hookspec
    ) -> None:
        """Store step start time."""
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
        feature: Feature,  # noqa: ARG002 hookspec
        scenario: Pickle,  # noqa: ARG002 hookspec
        step: PickleStep,  # noqa: ARG002 hookspec
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
        feature: Feature,  # noqa: ARG002 hookspec
        scenario: Pickle,  # noqa: ARG002 hookspec
    ) -> None:
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="after_scenario_hierarchy_not_available",
            )
        )
