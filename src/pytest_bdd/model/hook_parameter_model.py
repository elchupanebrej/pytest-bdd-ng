from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytest_bdd.model.execution_context import (
        ActiveObjectSet,
        ExecutionStage,
        ExecutionStatus,
        HookPhase,
        SessionExecutionContext,
    )


@dataclass(slots=True)
class ExecutionContextView:
    session: SessionExecutionContext
    context_id: str
    active_set: ActiveObjectSet
    active_hook: HookPhase
    stage: ExecutionStage
    status: ExecutionStatus
    transition_index: int
    node_context: Any | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session": self.session.as_dict(),
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
    execution_context: ExecutionContextView

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_ref": getattr(getattr(self.request, "node", None), "nodeid", None),
            "feature_ref": getattr(self.feature, "name", None),
            "scenario_ref": getattr(self.scenario, "name", None),
            "step_ref": getattr(self.step, "text", None),
            "execution_context": self.execution_context.as_dict(),
        }
