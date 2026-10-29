from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_cuke.model.background import Background
    from pytest_cuke.model.feature import Feature
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.model.step import Step


def execution_steps(feature: Feature, scenario: Scenario) -> tuple[Step, ...]:
    """Return the ordered steps the runner executes for a scenario."""
    backgrounds: list[Background] = []
    seen_background_ids: set[str] = set()
    steps: list[Step] = []
    seen_step_ids: set[str] = set()
    seen_step_objects: set[int] = set()

    for background in (feature.background, scenario.background):
        if background is None:
            continue
        if any(background is seen for seen in backgrounds):
            continue
        if background.id is not None and background.id in seen_background_ids:
            continue
        backgrounds.append(background)
        if background.id is not None:
            seen_background_ids.add(background.id)
        for step in background.steps:
            if step.id is not None:
                if step.id in seen_step_ids:
                    continue
                seen_step_ids.add(step.id)
            elif id(step) in seen_step_objects:
                continue
            seen_step_objects.add(id(step))
            steps.append(step)

    return tuple(steps) + tuple(scenario.steps)


__all__ = ["execution_steps"]
