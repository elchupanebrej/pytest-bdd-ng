from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytest_bdd.model.scenario_run import (
        ActiveObjectSet,
        RunStage,
        RunStatus,
        HookPhase,
        Run,
    )


@dataclass(slots=True)
class ScenarioRunView:
    run: Run
    context_id: str
    active_set: ActiveObjectSet
    active_hook: HookPhase
    stage: RunStage
    status: RunStatus
    transition_index: int
    node_context: Any | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run": self.run.as_dict(),
            "context_id": self.context_id,
            "active_set": self.active_set.as_dict(),
            "active_hook": self.active_hook.value,
            "stage": self.stage.value,
            "status": self.status.value,
            "transition_index": self.transition_index,
        }


@dataclass(slots=True)
class HookParameterModel:
    request: Any
    feature: Any | None
    scenario: Any | None
    step: Any | None
    previous_step: Any | None
    scenario_run_view: ScenarioRunView

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_ref": getattr(getattr(self.request, "node", None), "nodeid", None),
            "feature_ref": getattr(self.feature, "name", None),
            "scenario_ref": getattr(self.scenario, "name", None),
            "step_ref": getattr(self.step, "text", None),
            "scenario_run_view": self.scenario_run_view.as_dict(),
        }
