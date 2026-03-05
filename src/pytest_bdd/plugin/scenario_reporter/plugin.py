"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from collections.abc import Callable

import pytest
from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import CallInfo, FixtureLookupError, FixtureRequest, Item
from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.model.gherkin_document.core import build_feature_adapter
from pytest_bdd.plugin.scenario_reporter.report import ScenarioReport, StepReport
from pytest_bdd.plugin.scenario_runner.context_access import build_reporting_context_snapshot


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

    @staticmethod
    def _coerce_feature_adapter(
        *,
        request: FixtureRequest,
        gherkin_document: Feature | GherkinDocument,
        pickle: Pickle,
    ) -> Feature:
        if isinstance(gherkin_document, Feature):
            return gherkin_document

        feature_source: Source | None
        try:
            feature_source = request.getfixturevalue("feature_source")
        except FixtureLookupError:
            feature_source = None

        return build_feature_adapter(
            gherkin_document=gherkin_document,
            source=feature_source,
            pickles=[pickle],
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_bdd_before_scenario(
        self,
        request: FixtureRequest,
        gherkin_document: Feature | GherkinDocument,
        pickle: Pickle,
    ) -> None:
        """Create scenario report for the item."""
        feature_adapter = self._coerce_feature_adapter(
            request=request,
            gherkin_document=gherkin_document,
            pickle=pickle,
        )
        self.current_report = ScenarioReport(
            feature=feature_adapter,
            scenario=pickle,
            config=request.config,
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
        gherkin_document: Feature | GherkinDocument,  # noqa: ARG002 hookspec
        pickle: Pickle,  # noqa: ARG002 hookspec
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
        gherkin_document: Feature | GherkinDocument,  # noqa: ARG002 hookspec
        pickle: Pickle,  # noqa: ARG002 hookspec
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
        gherkin_document: Feature | GherkinDocument,  # noqa: ARG002 hookspec
        pickle: Pickle,  # noqa: ARG002 hookspec
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
        gherkin_document: Feature | GherkinDocument,  # noqa: ARG002 hookspec
        pickle: Pickle,  # noqa: ARG002 hookspec
    ) -> None:
        self.current_report.set_context_snapshot(
            build_reporting_context_snapshot(
                request=request,
                fallback_reason="after_scenario_hierarchy_not_available",
            )
        )
