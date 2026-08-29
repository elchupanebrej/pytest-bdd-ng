from __future__ import annotations

from typing import Any

from pytest_bdd.model.scenario_run import ExecutionContext, ScenarioRun
from pytest_bdd.model.stash_access import ItemStash, SimpleStash, StashAccess


def _resolve_stash(target: Any) -> Any:
    if hasattr(target, "raw_stash"):
        return target.raw_stash
    if hasattr(target, "_stash"):
        return target._stash
    if hasattr(target, "stash"):
        return target.stash
    if isinstance(target, dict | SimpleStash):
        return target
    return ItemStash.from_item(target)._stash


def get_scenario_run(target: Any) -> ScenarioRun | None:
    stash = _resolve_stash(target)
    return StashAccess.get_optional(stash, ScenarioRun)


def require_scenario_run(target: Any, missing_message: str | None = None) -> ScenarioRun:
    stash = _resolve_stash(target)
    msg = missing_message or ScenarioRun.stash_missing_message()
    return StashAccess.require(stash, ScenarioRun, missing_message=msg)


def set_scenario_run(target: Any, scenario_run: ScenarioRun) -> ScenarioRun:
    stash = _resolve_stash(target)
    return scenario_run.set_in_stash(stash)


def bind_scenario_run(target: Any, scenario_run: ScenarioRun) -> ScenarioRun:
    return set_scenario_run(target, scenario_run)


def get_execution_context(target: Any) -> ExecutionContext | None:
    sc_run = get_scenario_run(target)
    return sc_run.context if sc_run is not None else None


def require_execution_context(target: Any) -> ExecutionContext:
    sc_run = require_scenario_run(target)
    return sc_run.context


__all__ = [
    "bind_scenario_run",
    "get_execution_context",
    "get_scenario_run",
    "require_execution_context",
    "require_scenario_run",
    "set_scenario_run",
]
