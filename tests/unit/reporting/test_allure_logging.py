from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest_bdd.allure_logging as allure_mod
from pytest_bdd.allure_logging import AllurePytestBDD
from pytest_bdd.compatibility.allure import ALLURE_INSTALLED

from pytest import mark

pytestmark = mark.unit


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


@mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")
def test_report_result_serializes_pydantic_models_and_nested_attrs() -> None:
    import allure_commons.logger
    from attrs import define
    from pydantic import BaseModel as PydanticBaseModel

    class Payload(PydanticBaseModel):
        amount: int = 3

    @define
    class Nested:
        label: str = "inner"

    @define
    class Wrapper:
        payload: Payload
        nested: Nested
        plain: str = "raw"

    wrapper = Wrapper(payload=Payload(), nested=Nested())
    bdd = AllurePytestBDD(MagicMock(), MagicMock())

    hook = bdd.report_result(None)
    next(hook)
    try:
        dumped = allure_commons.logger.asdict(wrapper)
        assert dumped["payload"] == {"amount": 3}
        assert dumped["nested"] == {"label": "inner"}
        assert dumped["plain"] == "raw"

        shallow = allure_commons.logger.asdict(wrapper, recurse=False)
        assert shallow["payload"] == {"amount": 3}
        assert shallow["plain"] == "raw"
    finally:
        with contextlib.suppress(StopIteration):
            next(hook)


def test_register_and_unregister_are_noops_without_allure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(allure_mod, "ALLURE_INSTALLED", False)
    config = MagicMock()

    assert AllurePytestBDD.register_if_allure_accessible(config) is None
    AllurePytestBDD(MagicMock(), MagicMock()).unregister(config)
    config.pluginmanager.unregister.assert_not_called()


def test_register_returns_none_when_no_listener_is_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyListener:
        pass

    plugin_manager = MagicMock()
    plugin_manager.get_plugins.return_value = []

    monkeypatch.setattr(allure_mod, "ALLURE_INSTALLED", True)
    monkeypatch.setattr(allure_mod, "AllureListener", DummyListener)
    monkeypatch.setattr(allure_mod, "allure_plugin_manager", plugin_manager)
    monkeypatch.setattr(allure_mod, "PYTEST81", False)

    config = MagicMock()

    assert AllurePytestBDD.register_if_allure_accessible(config) is None


def test_lifecycle_guards_and_param_fallback_without_allure_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(allure_mod, "TestStepResult", None)
    monkeypatch.setattr(allure_mod, "md5", None)
    monkeypatch.setattr(allure_mod, "now", None)
    monkeypatch.setattr(allure_mod, "Status", None)
    monkeypatch.setattr(allure_mod, "Parameter", None)

    bdd = AllurePytestBDD(MagicMock(), MagicMock())
    request = MagicMock()

    bdd.pytest_bdd_before_scenario(request, MagicMock(), MagicMock())
    bdd.pytest_bdd_after_scenario(request, MagicMock(), MagicMock())
    bdd.pytest_bdd_step_func_lookup_error(request, MagicMock(), MagicMock(), MagicMock(), ValueError("boom"))

    node = MagicMock()
    node.callspec.params = {"a": 1}
    assert AllurePytestBDD.get_params(node) == [{"name": "a", "value": 1}]
