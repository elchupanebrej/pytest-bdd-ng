"""Lifecycle object reference helpers for the run model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Self

from attrs import define

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject

LifecycleKind = Literal["run", "feature", "scenario", "step"]


@define(slots=True)
class LifecycleObjectRef:
    """Represent lifecycle object ref state."""

    kind: LifecycleKind
    object_id: str
    name: str | None = None
    source: str | None = None
    is_active: bool = True
    empty_state_reason: str | None = None
    fail_fast_code: str | None = None

    @classmethod
    def inactive(
        cls,
        kind: LifecycleKind,
        *,
        reason: str,
        name: str | None = None,
        source: str | None = "lifecycle-slot",
        fail_fast_code: str | None = None,
    ) -> Self:
        """
        Create a LifecycleObjectRef representing an inactive state, indicating the object is not currently executing.

        Returns:
            A new LifecycleObjectRef instance marked as inactive.

        """
        return cls(
            kind=kind,
            object_id=f"{kind}:{reason}",
            name=name or kind,
            source=source,
            is_active=False,
            empty_state_reason=reason,
            fail_fast_code=fail_fast_code,
        )

    def as_dict(self) -> JSONObject:
        """
        Serialize the lifecycle object reference state into a dictionary representation.

        Returns:
            A dictionary containing the reference details.

        """
        return {
            "kind": self.kind,
            "object_id": self.object_id,
            "name": self.name,
            "source": self.source,
            "is_active": self.is_active,
            "empty_state_reason": self.empty_state_reason,
            "fail_fast_code": self.fail_fast_code,
        }


@define(slots=True)
class NoPreviousStep:
    """Represent no previous step state."""

    id: str = "step:no_previous_step"
    text: str = ""
    keyword: str = ""


def _inactive_feature_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("feature", reason="idle")


def _inactive_scenario_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("scenario", reason="idle")


def _inactive_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="idle", fail_fast_code="object_inactive")


def _no_previous_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="no_previous_step")


def _finished_feature_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("feature", reason="finished")


def _finished_scenario_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("scenario", reason="finished")


def _finished_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="finished", fail_fast_code="object_inactive")


def _finished_previous_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="finished")
