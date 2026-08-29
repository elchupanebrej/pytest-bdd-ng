from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest_bdd.allure_logging as allure_mod
from pytest_bdd.allure_logging import AllurePytestBDD

if TYPE_CHECKING:
    import pytest


def test_allure_pytest_bdd_helpers() -> None:
    feature = MagicMock()
    feature.rel_filename = "features/foo.feature"
    feature.name = "Foo Feature"

    scenario = MagicMock()
    scenario.name = "Bar Scenario"

    full_name = AllurePytestBDD.get_full_name(feature, scenario)
    assert full_name == "features/foo.feature:Bar Scenario"

    node = MagicMock()
    del node.callspec
    assert AllurePytestBDD.get_name(node, scenario) == "Bar Scenario"
    assert AllurePytestBDD.get_params(node) is None

    node_with_params = MagicMock()
    node_with_params.nodeid = "test_file.py::test[1-2]"
    node_with_params.callspec.params = {"a": 1, "b": "2"}
    assert AllurePytestBDD.get_name(node_with_params, scenario) == "Bar Scenario [1-2]"
    params = AllurePytestBDD.get_params(node_with_params)
    assert params is not None
    assert len(params) == 2


def test_allure_pytest_bdd_lifecycle_hooks(monkeypatch: pytest.MonkeyPatch) -> None:
    # Provide mocks for allure objects if not installed
    monkeypatch.setattr(allure_mod, "ALLURE_INSTALLED", True)
    monkeypatch.setattr(allure_mod, "TestStepResult", MagicMock())
    monkeypatch.setattr(allure_mod, "md5", lambda s: "md5-hash")
    monkeypatch.setattr(allure_mod, "now", lambda: 12345.0)
    monkeypatch.setattr(allure_mod, "Status", MagicMock(BROKEN="broken"))

    allure_logger = MagicMock()
    allure_cache = MagicMock()
    allure_cache.get.return_value = None
    allure_cache.push.return_value = "scenario-uuid"

    bdd = AllurePytestBDD(allure_logger, allure_cache)

    request = MagicMock()
    request.node.nodeid = "node-id-123"
    feature = MagicMock()
    feature.rel_filename = "test.feature"
    feature.name = "My Feature"
    scenario = MagicMock()
    scenario.name = "My Scenario"

    bdd.pytest_bdd_before_scenario(request, feature, scenario)
    allure_logger.start_step.assert_called_once()

    bdd.pytest_bdd_after_scenario(request, feature, scenario)
    allure_logger.stop_step.assert_called_once()

    exc = ValueError("lookup error")
    step = MagicMock()
    bdd.pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exc)
    assert allure_logger.stop_step.call_count == 2
