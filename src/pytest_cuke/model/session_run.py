"""Session-owned mutable execution state for collection, hooks, and reporters."""

from __future__ import annotations

import os
import time
from typing import Any, ClassVar, Literal, cast
from uuid import uuid4

from attrs import define, field

from pytest_cuke.model import Feature, Scenario, Step
from pytest_cuke.model.feature_binding import FeatureRuntimeBinding, normalize_feature_uri
from pytest_cuke.model.scenario_run import ScenarioRun, StepRun
from pytest_cuke.model.stash_access import ConfigStash, StashBound, StashAccess

RuntimeStage = Literal["inactive", "collection", "setup", "running", "step", "teardown", "finished"]
RuntimeHookPhase = Literal[
    "inactive",
    "pytest_collection",
    "pytest_runtest_call",
    "pytest_runtest_setup",
    "pytest_cuke_before_scenario",
    "pytest_cuke_run_scenario",
    "pytest_cuke_before_step",
    "pytest_cuke_step_call",
    "pytest_cuke_step_func_lookup_error",
    "pytest_cuke_step_error",
    "pytest_cuke_after_step",
    "pytest_cuke_after_scenario",
    "pytest_runtest_teardown",
]
RuntimeStatus = Literal["inactive", "pending", "running", "passed", "failed", "skipped", "undefined"]


@define(slots=True)
class RunContext(StashBound):
    """The authoritative mutable runtime root for one pytest session."""

    STASH_KEY: ClassVar[str] = "pytest_cuke_run_context"

    run_id: str = field(factory=lambda: uuid4().hex)
    worker_id: str = field(factory=lambda: os.environ.get("PYTEST_XDIST_WORKER", "master"))
    feature_bindings_by_uri: dict[str, FeatureRuntimeBinding] = field(factory=dict)
    scenario_runs_by_nodeid: dict[str, ScenarioRun] = field(factory=dict)
    scenario_runs_by_attempt: dict[tuple[str, int], ScenarioRun] = field(factory=dict)
    active_feature_binding: FeatureRuntimeBinding | None = None
    active_scenario_run: ScenarioRun | None = None
    stage: RuntimeStage = "inactive"
    hook_phase: RuntimeHookPhase = "inactive"
    status: RuntimeStatus = "inactive"
    transition_index: int = 0
    last_error: BaseException | None = None

    @classmethod
    def from_config(cls, config: Any) -> RunContext:
        stash = ConfigStash.from_config(config)._stash
        existing = StashAccess.get_optional(stash, cls)
        if existing is not None:
            return existing
        context = cls()
        return StashAccess.set(stash, context)

    @classmethod
    def find_in_config(cls, config: Any) -> RunContext | None:
        stash = ConfigStash.from_config(config)._stash
        return StashAccess.get_optional(stash, cls)

    def bind_feature(self, feature: Feature) -> FeatureRuntimeBinding:
        uri = normalize_feature_uri(feature)
        binding = self.feature_bindings_by_uri.get(uri)
        if binding is None:
            binding = FeatureRuntimeBinding.from_feature(feature)
            self.feature_bindings_by_uri[uri] = binding
        elif binding.feature is not feature:
            if binding.source != feature.source_content or binding.source_media_type != feature.source_media_type:
                raise ValueError(f"Feature source {uri!r} resolved to different parsed content within one session.")
            # Prefer the first parsed source binding but keep later expanded rows in the same index.
            for scenario in feature.all_scenarios:
                binding.register_scenario(scenario)
        return binding

    def begin_collection(self) -> None:
        self.transition(stage="collection", hook_phase="pytest_collection", status="inactive")

    def start_scenario(
        self,
        *,
        nodeid: str,
        feature: Feature,
        scenario: Scenario,
        attempt: int = 0,
    ) -> ScenarioRun:
        if self.active_scenario_run is not None and self.active_scenario_run.nodeid != nodeid:
            self.finish_active(status="failed", exception=RuntimeError("A previous scenario was left active."))
            self.clear_active()
        binding = self.bind_feature(feature)
        binding.register_scenario(scenario)
        scenario_run = ScenarioRun(
            feature=feature,
            scenario=scenario,
            feature_binding=binding,
            nodeid=nodeid,
            run_id=self.run_id,
            attempt=attempt,
            status="running",
            start_time=time.perf_counter(),
        )
        self.scenario_runs_by_nodeid[nodeid] = scenario_run
        self.scenario_runs_by_attempt[(nodeid, attempt)] = scenario_run
        self.last_error = None
        self.active_feature_binding = binding
        self.active_scenario_run = scenario_run
        self.transition(stage="setup", hook_phase="pytest_runtest_setup", status="running")
        return scenario_run

    def start_step(self, step: Step) -> StepRun:
        scenario_run = self._require_active_scenario()
        step_index = len(scenario_run.steps)
        step_run = StepRun(
            step=step,
            id=f"{scenario_run.run_id}:{scenario_run.nodeid}:{scenario_run.attempt}:{step_index}",
            test_step_id=scenario_run.test_step_ids[step_index]
            if step_index < len(scenario_run.test_step_ids)
            else None,
            previous_step_run=scenario_run.previous_step_run,
            index=step_index,
        )
        if step_run.previous_step_run is not None:
            step_run.previous_step_run.children.append(step_run)
        scenario_run.add_step_run(step_run)
        scenario_run.current_step_run = step_run
        self.transition(stage="step", hook_phase="pytest_cuke_before_step", status="running")
        step_run.start()
        return step_run

    def finish_step(
        self,
        step_run: StepRun,
        *,
        status: Literal["passed", "failed", "skipped", "undefined"] = "passed",
        result: Any = None,
        exception: BaseException | None = None,
        failure_reason: str | None = None,
    ) -> None:
        duration = max(0.0, time.perf_counter() - (step_run.start_time or time.perf_counter()))
        step_run.finish(
            status=status,
            duration=duration,
            result=result,
            exception=exception,
            failure_reason=failure_reason,
        )
        scenario_run = self._require_active_scenario()
        scenario_run.previous_step_run = step_run
        scenario_run.current_step_run = None
        self.transition(stage="running", hook_phase="pytest_cuke_after_step", status="running")

    def finish_active(
        self,
        *,
        status: Literal["passed", "failed", "skipped", "undefined"],
        exception: BaseException | None = None,
        hook_phase: RuntimeHookPhase = "pytest_cuke_after_scenario",
    ) -> None:
        scenario_run = self.active_scenario_run
        if scenario_run is None:
            if exception is not None:
                self.last_error = exception
            return
        duration = max(0.0, time.perf_counter() - (scenario_run.start_time or time.perf_counter()))
        scenario_run.finish(status=status, duration=duration, exception=exception)
        if exception is not None:
            self.last_error = exception
        self.transition(stage="finished", hook_phase=hook_phase, status=status)

    def enter_teardown(self) -> None:
        self.transition(stage="teardown", hook_phase="pytest_runtest_teardown", status=self._active_status())

    def record_teardown_error(self, exception: BaseException) -> None:
        self.last_error = exception
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            scenario_run.fail(exception, duration=scenario_run.duration)
        self.transition(stage="teardown", hook_phase="pytest_runtest_teardown", status="failed")

    def record_setup_error(self, exception: BaseException, status: Literal["failed", "skipped", "undefined"]) -> None:
        self.last_error = exception
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            scenario_run.finish(
                status=status,
                duration=max(0.0, time.perf_counter() - (scenario_run.start_time or time.perf_counter())),
                exception=exception,
            )
        self.transition(stage="setup", hook_phase="pytest_runtest_setup", status=status)

    def clear_active(self) -> None:
        self.active_feature_binding = None
        self.active_scenario_run = None
        self.transition(stage="inactive", hook_phase="inactive", status="inactive")

    def get_scenario_run(self, nodeid: str, attempt: int | None = None) -> ScenarioRun | None:
        if attempt is not None:
            return self.scenario_runs_by_attempt.get((nodeid, attempt))
        return self.scenario_runs_by_nodeid.get(nodeid)

    def set_test_case(
        self,
        *,
        test_case_id: str,
        test_step_ids: list[str],
        test_steps: list[Any] | None = None,
        test_case_started_id: str | None = None,
    ) -> None:
        scenario_run = self._require_active_scenario()
        scenario_run.test_case_id = test_case_id
        scenario_run.test_step_ids = list(test_step_ids)
        scenario_run.message_state.test_steps = list(test_steps or ())
        if test_case_started_id is not None:
            scenario_run.test_case_started_id = test_case_started_id
            scenario_run.attempt_id = test_case_started_id

    def set_attempt_id(self, test_case_started_id: str) -> None:
        scenario_run = self._require_active_scenario()
        scenario_run.test_case_started_id = test_case_started_id
        scenario_run.attempt_id = test_case_started_id

    def transition(
        self,
        *,
        stage: RuntimeStage,
        hook_phase: RuntimeHookPhase,
        status: RuntimeStatus,
    ) -> None:
        self.transition_index += 1
        self.stage = stage
        self.hook_phase = hook_phase
        self.status = status
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            scenario_run.stage = stage
            scenario_run.hook_phase = hook_phase
            scenario_run.transition_index = self.transition_index
            scenario_run.status = status

    def _active_status(self) -> RuntimeStatus:
        if self.active_scenario_run is None:
            return "inactive"
        return cast("RuntimeStatus", self.active_scenario_run.status)

    def _require_active_scenario(self) -> ScenarioRun:
        if self.active_scenario_run is None:
            raise RuntimeError("There is no active pytest-cuke scenario in this session.")
        return self.active_scenario_run


__all__ = ["RunContext", "RuntimeHookPhase", "RuntimeStage", "RuntimeStatus"]
