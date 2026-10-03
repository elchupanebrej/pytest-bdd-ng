from __future__ import annotations

from unittest.mock import MagicMock

from pytest_cuke.plugin import add_bdd_ini, pytest_addoption
from pytest_cuke.steps import add_options as steps_add_options

from pytest import mark

pytestmark = mark.unit


def test_add_bdd_ini() -> None:
    parser = MagicMock()
    add_bdd_ini(parser)
    parser.addini.assert_any_call("cuke_features_dir", "Base features directory.", default="features", type="string")
    parser.addini.assert_any_call("cuke_features_base_url", "Base features URL.", default="", type="string")


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
    option_kwargs = {call.args[0]: call.kwargs for call in group.addoption.call_args_list if call.args}
    assert "cuke_features_dir" in option_kwargs["--cuke-features-dir"]["help"]
    assert "pytest root" in option_kwargs["--cuke-features-dir"]["help"]
    assert "binding, CLI, then ini" in option_kwargs["--cuke-features-dir"]["help"]
    assert "cuke_features_base_url" in option_kwargs["--cuke-features-base-url"]["help"]
    assert "binding, CLI, then ini" in option_kwargs["--cuke-features-base-url"]["help"]
