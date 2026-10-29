from __future__ import annotations

from typing import Any

from pytest_cuke.model.scenario_run import ExecutionContext, ScenarioRun
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.model.stash_access import ItemStash, SimpleStash, StashAccess


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


def _config_from_target(target: Any) -> Any | None:
    config = getattr(target, "config", None)
    if config is not None:
        return config
    request = getattr(target, "_request", None)
    if request is not None:
        config = getattr(request, "config", None)
        if config is not None:
            return config
    node = getattr(target, "node", None)
    if node is not None:
        config = getattr(node, "config", None)
        if config is not None:
            return config
    session = getattr(target, "session", None)
    return getattr(session, "config", None) if session is not None else None


def get_run_context(target: Any) -> RunContext | None:
    """Resolve the session runtime root from config, request, item, or stash."""
    config = _config_from_target(target)
    if config is not None:
        context = RunContext.find_in_config(config)
        if context is not None:
            return context
    return StashAccess.get_optional(_resolve_stash(target), RunContext)


def require_run_context(target: Any) -> RunContext:
    context = get_run_context(target)
    if context is None:
        raise RuntimeError("`RunContext` is unavailable for this pytest session.")
    return context


def get_scenario_run(target: Any) -> ScenarioRun | None:
    stash = _resolve_stash(target)
    scenario_run = StashAccess.get_optional(stash, ScenarioRun)
    if scenario_run is not None:
        return scenario_run
    run_context = get_run_context(target)
    if run_context is None:
        return None
    request = getattr(target, "_request", None)
    node = getattr(request, "node", None) if request is not None else getattr(target, "node", target)
    nodeid = getattr(node, "nodeid", None)
    return run_context.get_scenario_run(nodeid) if isinstance(nodeid, str) else None


def require_scenario_run(target: Any, missing_message: str | None = None) -> ScenarioRun:
    scenario_run = get_scenario_run(target)
    if scenario_run is not None:
        return scenario_run
    return StashAccess.require(
        _resolve_stash(target),
        ScenarioRun,
        missing_message=missing_message or ScenarioRun.stash_missing_message(),
    )


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
    "get_run_context",
    "get_scenario_run",
    "require_execution_context",
    "require_run_context",
    "require_scenario_run",
    "set_scenario_run",
]
