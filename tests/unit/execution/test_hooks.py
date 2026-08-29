from __future__ import annotations

from unittest.mock import MagicMock

from pytest_bdd.hook import (
    HookCaller,
    HookConjunction,
    HookKind,
    after_mark,
    after_tag,
    around_mark,
    around_tag,
    before_mark,
    before_tag,
)
from pytest_bdd.hooks import (
    pytest_bdd_after_scenario,
    pytest_bdd_after_step,
    pytest_bdd_apply_tag,
    pytest_bdd_before_scenario,
    pytest_bdd_before_step,
    pytest_bdd_step_error,
)


def test_hook_enums_and_decorators() -> None:
    assert HookKind.mark.value == "mark"
    assert HookKind.tag.value == "tag"
    assert HookConjunction.before.value == "before"
    assert HookConjunction.after.value == "after"
    assert HookConjunction.around.value == "around"

    assert callable(before_mark)
    assert callable(before_tag)
    assert callable(after_mark)
    assert callable(after_tag)
    assert callable(around_mark)
    assert callable(around_tag)


def test_hook_specifications_exist() -> None:
    specs = [
        pytest_bdd_before_scenario,
        pytest_bdd_after_scenario,
        pytest_bdd_before_step,
        pytest_bdd_after_step,
        pytest_bdd_step_error,
        pytest_bdd_apply_tag,
    ]
    assert all(callable(s) for s in specs)


def test_hook_caller_dispatch() -> None:
    mock_relay = MagicMock()
    caller = HookCaller(mock_relay)

    req, feat, scen, step, step_fn, step_def = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    caller.before_scenario(req, feat, scen)
    mock_relay.pytest_bdd_before_scenario.assert_called_once_with(request=req, feature=feat, scenario=scen)

    caller.after_scenario(req, feat, scen)
    mock_relay.pytest_bdd_after_scenario.assert_called_once_with(request=req, feature=feat, scenario=scen)

    caller.before_step(req, feat, scen, step, step_fn)
    mock_relay.pytest_bdd_before_step.assert_called_once_with(
        request=req, feature=feat, scenario=scen, step=step, step_func=step_fn
    )

    caller.after_step(req, feat, scen, step, step_fn, {}, step_def)
    mock_relay.pytest_bdd_after_step.assert_called_once_with(
        request=req,
        feature=feat,
        scenario=scen,
        step=step,
        step_func=step_fn,
        step_func_args={},
        step_definition=step_def,
    )

    exc = RuntimeError("step failed")
    caller.step_error(req, feat, scen, step, step_fn, {}, exc, step_def)
    mock_relay.pytest_bdd_step_error.assert_called_once_with(
        request=req,
        feature=feat,
        scenario=scen,
        step=step,
        step_func=step_fn,
        step_func_args={},
        exception=exc,
        step_definition=step_def,
    )
