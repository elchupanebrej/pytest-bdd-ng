from __future__ import annotations

from unittest.mock import MagicMock

from pytest_bdd.plugin import add_bdd_ini, pytest_addoption
from pytest_bdd.steps import add_options as steps_add_options


def test_add_bdd_ini() -> None:
    parser = MagicMock()
    add_bdd_ini(parser)
    parser.addini.assert_any_call("bdd_features_base_dir", "Base features directory.")
    parser.addini.assert_any_call("bdd_features_base_url", "Base features url.")


def test_steps_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    steps_add_options(parser)
    parser.getgroup.assert_called_once_with("bdd", "Steps")
    group.addoption.assert_called_once()
    args, kwargs = group.addoption.call_args
    assert "--liberal-steps" in args
    assert kwargs["dest"] == "liberal_steps"
    parser.addini.assert_any_call(
        "liberal_steps", default=False, type="bool", help="Allow use different keywords with same step definition"
    )


def test_pytest_addoption_calls_all_submodules() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    pytest_addoption(parser)

    parser.addini.assert_any_call("bdd_features_base_dir", "Base features directory.")
    parser.addini.assert_any_call("bdd_features_base_url", "Base features url.")
    assert parser.getgroup.call_count >= 5
