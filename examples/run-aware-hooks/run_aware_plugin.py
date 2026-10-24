"""Consumer hooks that observe pytest-cuke's session-owned run context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pytest import hookimpl


def _step_name(step: Any) -> str | None:
    return getattr(step, "name", None) if step is not None else None


def _step_index(run: Any) -> int | None:
    scenario = run.scenario
    current_step = run.step
    if scenario is None or current_step is None:
        return None
    return next((index for index, step in enumerate(scenario.steps) if step is current_step), None)


def _serializable_step_func_args(values: dict[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    serializable: dict[str, Any] = {}
    for name, value in values.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            serializable[name] = value
        else:
            serializable[name] = getattr(value, "__name__", type(value).__name__)
    return serializable


def _record(
    event: str,
    run: Any,
    *,
    request: Any = None,
    step_func: Any = None,
    step_func_args: dict[str, Any] | None = None,
    step_definition: Any = None,
    attachment: str | None = None,
    media_type: str | None = None,
    file_name: str | None = None,
) -> None:
    definition_func = getattr(step_definition, "func", None)
    observation = {
        "event": event,
        "run_id": run.run_id,
        "worker_id": run.worker_id,
        "request_nodeid": request.node.nodeid if request is not None else None,
        "feature_name": getattr(run.feature, "name", None),
        "scenario_name": getattr(run.scenario, "name", None),
        "stage": run.stage,
        "hook_phase": run.hook_phase,
        "status": run.status,
        "transition_index": run.transition_index,
        "step_name": _step_name(run.step),
        "previous_step_name": _step_name(run.previous_step),
        "current_step_index": _step_index(run),
        "step_func": getattr(step_func, "__name__", None),
        "step_func_args": _serializable_step_func_args(step_func_args),
        "step_definition_func": getattr(definition_func, "__name__", None),
        "attachment": attachment,
        "media_type": media_type,
        "file_name": file_name,
    }
    with Path("run-aware-observations.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(observation, sort_keys=True) + "\n")


@hookimpl
def pytest_cuke_before_scenario(request, run) -> None:
    """Observe a scenario after setup has established its run context."""
    assert run.feature is not None
    assert run.scenario is not None
    assert run.stage == "setup"
    assert run.hook_phase == "pytest_cuke_before_scenario"
    assert run.status == "running"
    _record("before_scenario", run, request=request)


@hookimpl
def pytest_cuke_before_step(request, run, step_func) -> None:
    """Observe the current step and its predecessor before fixture setup."""
    current_step = run.step
    assert current_step is not None
    assert run.feature is not None
    assert run.scenario is not None
    assert run.stage == "step-running"
    assert run.hook_phase == "pytest_cuke_before_step"
    assert run.status == "running"

    current_index = _step_index(run)
    assert current_index is not None
    if current_index == 0:
        assert run.previous_step is None
    else:
        assert run.previous_step is not None
        expected_previous = run.scenario.steps[current_index - 1]
        assert run.previous_step == expected_previous

    _record("before_step", run, request=request, step_func=step_func)


@hookimpl
def pytest_cuke_before_step_call(run, step_func, step_func_args, step_definition) -> None:
    """Observe resolved function inputs; this implementation needs only the run and step data."""
    assert run.step is not None
    assert step_func_args is not None
    assert step_definition.func is step_func
    _record(
        "before_step_call",
        run,
        step_func=step_func,
        step_func_args=step_func_args,
        step_definition=step_definition,
    )


@hookimpl
def pytest_cuke_after_step(run) -> None:
    """Observe a successful step through the reduced run-only hook signature."""
    assert run.step is not None
    assert run.hook_phase == "pytest_cuke_after_step"
    _record("after_step", run)


@hookimpl
def pytest_cuke_after_scenario(run) -> None:
    """Observe the completed scenario without requesting event arguments."""
    assert run.stage == "finished"
    assert run.hook_phase == "pytest_cuke_after_scenario"
    assert run.status == "passed"
    _record("after_scenario", run)


@hookimpl
def pytest_cuke_match_step_definition_to_step(request, run):
    """Let pytest-cuke's default matcher handle the step after observing the context."""
    assert run.step is not None
    assert run.feature is not None
    assert run.scenario is not None
    _record("matcher_fallback", run, request=request)
    return None


@hookimpl
def pytest_cuke_get_step_caller(request, run, step_func, step_func_args, step_definition):
    """Use the default fixture-aware caller for this example's step functions."""
    assert run.step is not None
    _record(
        "caller_fallback",
        run,
        request=request,
        step_func=step_func,
        step_func_args=step_func_args,
        step_definition=step_definition,
    )
    return None


@hookimpl
def pytest_cuke_get_step_dispatcher(request, run):
    """Use pytest-cuke's default step dispatcher."""
    assert run.feature is not None
    assert run.scenario is not None
    _record("dispatcher_fallback", run, request=request)
    return None


@hookimpl
def pytest_cuke_attach(request, run, attachment, media_type, file_name) -> None:
    """Observe an attachment while its consumer step is active."""
    assert isinstance(attachment, str)
    assert run.feature is not None
    assert run.scenario is not None
    assert run.step is not None
    assert run.stage == "step-running"
    assert run.status == "running"
    _record(
        "attachment",
        run,
        request=request,
        attachment=attachment,
        media_type=media_type,
        file_name=file_name,
    )
