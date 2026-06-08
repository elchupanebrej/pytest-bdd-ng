"""
Provide report helpers.

Responsibility:
    Provide report helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.scenario_report` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - StepReportData: owns nested behavior below this boundary
    - FeatureReportData: owns nested behavior below this boundary
    - ScenarioReportData: owns nested behavior below this boundary
    - normalize_runtime_step_status: owns nested behavior below this boundary
    - StepReport: owns nested behavior below this boundary
    - ScenarioReport: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `scenario_report`
    - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `scenario_report`

State and side effects:
    mutates line_number, name, keyword, failed, tags; depends on time, typing.Literal, typing.TypedDict, attrs.define,
    attrs.field.

Invariants:
    - `pytest_bdd.model.scenario_report` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

import time
from typing import Literal, TypedDict

from attrs import define, field
from cucumber_messages import Pickle, PickleStep  # library has no type stubs

from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.run import ReportingContextSnapshot

RuntimeStepStatus = Literal["passed", "failed"]


class StepReportData(TypedDict):
    """
    Represent step report data state.

    Responsibility:
        Represent step report data state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_report.StepReportData` because it keeps the
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
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `StepReportData`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `StepReportData`

    State and side effects:
        mutates name, type, keyword, line_number, failed.

    Invariants:
        - `pytest_bdd.model.scenario_report.StepReportData` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    name: str
    type: str | None
    keyword: str | None
    line_number: int | None
    failed: bool
    status: RuntimeStepStatus
    duration: float


class FeatureReportData(TypedDict):
    """
    Represent feature report data state.

    Responsibility:
        Represent feature report data state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_report.FeatureReportData` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `FeatureReportData`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `FeatureReportData`

    State and side effects:
        mutates name, filename, rel_filename, line_number, description.

    Invariants:
        - `pytest_bdd.model.scenario_report.FeatureReportData` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    name: str | None
    filename: str
    rel_filename: str | None
    line_number: int | None
    description: str | None
    tags: list[str]


class ScenarioReportData(TypedDict):
    """
    Represent scenario report data state.

    Responsibility:
        Represent scenario report data state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_report.ScenarioReportData` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `ScenarioReportData`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `ScenarioReportData`

    State and side effects:
        mutates steps, name, line_number, tags, feature.

    Invariants:
        - `pytest_bdd.model.scenario_report.ScenarioReportData` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    steps: list[StepReportData]
    name: str
    line_number: int
    tags: list[str]
    feature: FeatureReportData


def normalize_runtime_step_status(status: str | None, *, failed_fallback: bool) -> RuntimeStepStatus:
    """
    Normalize runtime step status.

    Args:
        status: Raw status string.
        failed_fallback: Fallback status when status is invalid.

    Returns:
        Normalized runtime step status.

    Responsibility:
        Normalize runtime step status. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_report.normalize_runtime_step_status`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - strip.lower: collaborator call used by this boundary
        - strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references
          `normalize_runtime_step_status`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `normalize_runtime_step_status`

    State and side effects:
        mutates normalized.

    Invariants:
        - `pytest_bdd.model.scenario_report.normalize_runtime_step_status` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    normalized = (status or "").strip().lower()
    if normalized == "passed":
        return "passed"
    if normalized == "failed":
        return "failed"
    return "failed" if failed_fallback else "passed"


@define(eq=False)
class StepReport:
    """
    Step execution report.

    Responsibility:
        Step execution report. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_report.StepReport` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - serialize: owns nested behavior below this boundary
        - finalize: owns nested behavior below this boundary
        - duration: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `StepReport`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `StepReport`

    State and side effects:
        mutates line_number, step_prefix, step, started, failed.

    Invariants:
        - `pytest_bdd.model.scenario_report.StepReport` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    step: PickleStep = field()
    started: float = field(factory=time.perf_counter)
    failed: bool = field(default=False)
    stopped: float | None = field(default=None)

    def serialize(self, feature_binding: FeatureRuntimeBinding) -> StepReportData:
        """
        Serialize the step execution report.

        Args:
            feature_binding: Feature runtime binding.

        Returns:
            Serialized step execution report.

        Responsibility:
            Serialize the step execution report. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_report.StepReport.serialize` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - feature_binding.step_keyword: collaborator call used by this boundary
            - feature_binding.step_line_number: collaborator call used by this boundary
            - feature_binding.step_prefix: collaborator call used by this boundary
            - normalize_runtime_step_status: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/execution_message_adapter.py: imports or references `serialize`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `serialize`
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `serialize`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `serialize`

        State and side effects:
            mutates line_number, step_prefix, keyword.

        Invariants:
            - `pytest_bdd.model.scenario_report.StepReport.serialize` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        keyword = getattr(self.step, "keyword", None) or feature_binding.step_keyword(self.step)
        line_number = getattr(self.step, "line_number", None)
        if line_number is None:
            line_number = feature_binding.step_line_number(self.step)
        step_prefix = getattr(self.step, "prefix", None)
        if step_prefix is None:
            step_prefix = feature_binding.step_prefix(self.step)
        return {
            "name": self.step.text,
            "type": step_prefix,
            "keyword": keyword,
            "line_number": line_number,
            "failed": self.failed,
            "status": normalize_runtime_step_status(None, failed_fallback=self.failed),
            "duration": self.duration,
        }

    def finalize(self, *, failed: bool = False) -> None:
        """
        Stop collecting information and finalize the report.

        :param bool failed: Whether the step execution is failed.

        Responsibility:
            Stop collecting information and finalize the report. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_report.StepReport.finalize` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - time.perf_counter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `finalize`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `finalize`

        State and side effects:
            mutates self.stopped, self.failed.

        Invariants:
            - `pytest_bdd.model.scenario_report.StepReport.finalize` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """
        Step execution duration.

        :return: Step execution duration.
        :rtype: float

        Responsibility:
            Step execution duration. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_report.StepReport.duration` because it
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
            - src/pytest_bdd/model/scenario_run.py: imports or references `duration`
            - src/pytest_bdd/plugin/cucumber_json/model.py: imports or references `duration`
            - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `duration`
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `duration`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `duration`

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
        if self.stopped is None:
            return 0.0

        return self.stopped - self.started


@define
class ScenarioReport:
    """
    Pickle execution report.

    Responsibility:
        Pickle execution report. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_report.ScenarioReport` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - current_step_report: owns nested behavior below this boundary
        - add_step_report: owns nested behavior below this boundary
        - set_context_snapshot: owns nested behavior below this boundary
        - serialize: owns nested behavior below this boundary
        - fail: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `ScenarioReport`
        - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `ScenarioReport`

    State and side effects:
        mutates feature_binding, pickle, step_reports, context_snapshot, self.context_snapshot.

    Invariants:
        - `pytest_bdd.model.scenario_report.ScenarioReport` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    feature_binding: FeatureRuntimeBinding = field()
    pickle: Pickle = field()
    step_reports: list[StepReport] = field(factory=list)
    context_snapshot: ReportingContextSnapshot | None = field(default=None)

    @property
    def current_step_report(self) -> StepReport:
        """
        Get current step report.

        :return: Last or current step report.
        :rtype: pytest_bdd.reporting.StepReport

        Responsibility:
            Get current step report. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.scenario_report.ScenarioReport.current_step_report` because it keeps the nearest code,
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
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `current_step_report`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `current_step_report`

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
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """
        Add new step report.

        :param step_report: New current step report.
        :type step_report: pytest_bdd.reporting.StepReport

        Responsibility:
            Add new step report. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_report.ScenarioReport.add_step_report`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.step_reports.append: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `add_step_report`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `add_step_report`

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
            #arch-eval:locational_stability=3
        """
        self.step_reports.append(step_report)

    def set_context_snapshot(self, context_snapshot: ReportingContextSnapshot | None) -> None:
        """
        Handle set context snapshot.

        Responsibility:
            Handle set context snapshot. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.scenario_report.ScenarioReport.set_context_snapshot` because it keeps the nearest code,
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
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `set_context_snapshot`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `set_context_snapshot`

        State and side effects:
            mutates self.context_snapshot.

        Invariants:
            - `pytest_bdd.model.scenario_report.ScenarioReport.set_context_snapshot` keeps its documented import path,
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
            #arch-eval:locational_stability=3
        """
        self.context_snapshot = context_snapshot

    def serialize(self) -> ScenarioReportData:
        """
        Serialize scenario execution report for distributed mode.

        Returns:
            Serialized scenario report.

        Responsibility:
            Serialize scenario execution report for distributed mode. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_report.ScenarioReport.serialize`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - step_report.serialize: collaborator call used by this boundary
            - feature_binding.pickle_line_number: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - difference: collaborator call used by this boundary
            - tag.name.lstrip: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/execution_message_adapter.py: imports or references `serialize`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `serialize`
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `serialize`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `serialize`

        State and side effects:
            mutates pickle, feature_binding.

        Invariants:
            - `pytest_bdd.model.scenario_report.ScenarioReport.serialize` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        pickle = self.pickle
        feature_binding = self.feature_binding

        return {
            "steps": [step_report.serialize(self.feature_binding) for step_report in self.step_reports],
            "name": pickle.name,
            "line_number": feature_binding.pickle_line_number(pickle),
            "tags": sorted({tag.name.lstrip("@") for tag in pickle.tags}.difference(feature_binding.tag_names)),
            "feature": {
                "name": feature_binding.name,
                "filename": feature_binding.filename,
                "rel_filename": feature_binding.rel_filename,
                "line_number": feature_binding.line_number,
                "description": feature_binding.description,
                "tags": feature_binding.tag_names,
            },
        }

    def fail(self) -> None:
        """
        Stop collecting information and finalize the report as failed.

        Responsibility:
            Stop collecting information and finalize the report as failed. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_report.ScenarioReport.fail` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.current_step_report.finalize: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - StepReport: collaborator call used by this boundary
            - report.finalize: collaborator call used by this boundary
            - self.add_step_report: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `fail`
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references `fail`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `fail`
            - src/pytest_bdd/util/pytest_extra.py: imports or references `fail`

        State and side effects:
            mutates remaining_steps, report.

        Invariants:
            - `pytest_bdd.model.scenario_report.ScenarioReport.fail` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.pickle.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)
