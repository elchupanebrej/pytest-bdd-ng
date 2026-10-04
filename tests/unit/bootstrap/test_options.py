from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_cuke.plugin import add_bdd_ini, pytest_addoption
from pytest_cuke.runner import ScenarioRunner
from pytest_cuke.steps import add_options as steps_add_options

pytestmark = pytest.mark.unit


def test_add_bdd_ini() -> None:
    parser = MagicMock()
    add_bdd_ini(parser)
    parser.addini.assert_any_call("cuke_features_dir", "Base features directory.", default="features", type="string")
    parser.addini.assert_any_call("cuke_features_base_url", "Base features URL.", default="", type="string")
    parser.addini.assert_any_call(
        "cuke_mock_run",
        "Validate scenario step bindings without running BDD hooks or step bodies.",
        default=False,
        type="bool",
    )
    parser.addini.assert_any_call(
        "cuke_allow_empty_scenarios",
        "Skip explicitly bound non-empty scenarios when none of their steps match a step definition.",
        default=False,
        type="bool",
    )
    parser.addini.assert_any_call(
        "cuke_tolerant_status",
        "Status policy for ordinary exceptions in @tolerant steps: failed or ignored.",
        default="failed",
        type="string",
    )
    parser.addini.assert_any_call(
        "cuke_wip_status",
        "Status policy for @not_implemented steps: passed, skipped, or failed.",
        default="failed",
        type="string",
    )


def test_steps_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    steps_add_options(parser)
    parser.getgroup.assert_called_once_with("cuke", "Steps")
    group.addoption.assert_called_once()
    args, kwargs = group.addoption.call_args
    assert "--cuke-liberal-steps" in args
    assert kwargs["dest"] == "cuke_liberal_steps"
    parser.addini.assert_any_call(
        "cuke_liberal_steps", default=False, type="bool", help="Allow use different keywords with same step definition"
    )


def test_pytest_addoption_calls_all_submodules() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    pytest_addoption(parser)

    parser.addini.assert_any_call("cuke_features_dir", "Base features directory.", default="features", type="string")
    parser.addini.assert_any_call("cuke_features_base_url", "Base features URL.", default="", type="string")
    assert parser.getgroup.call_count >= 5
    group = parser.getgroup.return_value
    option_calls = [call.args[0] for call in group.addoption.call_args_list if call.args]
    assert "--cuke-features-dir" in option_calls
    assert "--cuke-features-base-url" in option_calls
    assert "--cuke-tolerant-status" in option_calls
    assert "--cuke-wip-status" in option_calls
    assert "--cuke-mock-run" in option_calls
    assert "--cuke-allow-empty-scenarios" in option_calls
    option_kwargs = {call.args[0]: call.kwargs for call in group.addoption.call_args_list if call.args}
    assert "cuke_features_dir" in option_kwargs["--cuke-features-dir"]["help"]
    assert "pytest root" in option_kwargs["--cuke-features-dir"]["help"]
    assert "binding, CLI, then ini" in option_kwargs["--cuke-features-dir"]["help"]
    assert "cuke_features_base_url" in option_kwargs["--cuke-features-base-url"]["help"]
    assert "binding, CLI, then ini" in option_kwargs["--cuke-features-base-url"]["help"]
    assert option_kwargs["--cuke-tolerant-status"]["choices"] == ("failed", "ignored")
    assert option_kwargs["--cuke-wip-status"]["choices"] == ("passed", "skipped", "failed")
    assert option_kwargs["--cuke-mock-run"]["dest"] == "cuke_mock_run"
    assert option_kwargs["--cuke-mock-run"]["action"] == "store_true"
    assert option_kwargs["--cuke-mock-run"]["default"] is None
    assert option_kwargs["--cuke-allow-empty-scenarios"]["dest"] == "cuke_allow_empty_scenarios"
    assert option_kwargs["--cuke-allow-empty-scenarios"]["action"] == "store_true"
    assert option_kwargs["--cuke-allow-empty-scenarios"]["default"] is None


@pytest.mark.parametrize(
    ("cli_value", "ini_value", "expected"),
    ((True, False, True), (None, True, True), (None, False, False)),
)
def test_mock_run_option_overrides_or_falls_back_to_ini(
    cli_value: bool | None,
    ini_value: bool,
    expected: bool,
) -> None:
    config = MagicMock()
    config.option.cuke_mock_run = cli_value
    config.getini.return_value = ini_value

    assert ScenarioRunner._mock_run_enabled(config) is expected
