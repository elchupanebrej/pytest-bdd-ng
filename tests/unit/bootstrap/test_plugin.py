from __future__ import annotations

from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from pytest_cuke import hooks
from pytest_cuke.plugin import (
    attach,
    pytest_addhooks,
    pytest_cuke_is_collectible,
    pytest_configure,
    pytest_unconfigure,
    pytestbdd_id_generator,
    pytestbdd_step_runner,
    step_matcher,
    step_registry,
    steps_left,
)
from pytest_cuke.runner import ScenarioRunner
from pytest_cuke.steps import Matcher, Registry
from pytest_cuke.utils import IdGenerator

from pytest import mark

pytestmark = mark.unit


def test_pytest_addhooks() -> None:
    pluginmanager = MagicMock()
    pytest_addhooks(pluginmanager)
    pluginmanager.add_hookspecs.assert_called_once_with(hooks)


def test_pytest_configure_lifecycle() -> None:
    config = MagicMock()
    config.stash = {}
    config.pluginmanager = MagicMock()
    config.option = MagicMock()
    config.option.cuke_json = None
    config.option.cuke_progress = False
    config.option.cuke_summary = False

    pytest_configure(config)

    config.addinivalue_line.assert_any_call("markers", "pytest_cuke_scenario: marker to identify pytest_cuke tests")
    config.addinivalue_line.assert_any_call("markers", "scenarios: marker to provide scenarios locator")
    assert IdGenerator.pytest_cuke_id_generator in config.stash
    assert config.pluginmanager.register.call_count >= 2


def test_pytest_unconfigure_lifecycle() -> None:
    config = MagicMock()
    config.pluginmanager = MagicMock()
    config.__allure_plugin__ = MagicMock()

    pytest_unconfigure(config)
    config.pluginmanager.unregister.assert_any_call(name="pytest_cuke_messages")
    config.pluginmanager.unregister.assert_any_call(name="pytest_cuke_summary")
    config.__allure_plugin__.unregister.assert_called_once_with(config)


def _unwrap_fixture(fixture_obj):
    return getattr(fixture_obj, "_fixture_function", getattr(fixture_obj, "__wrapped__", fixture_obj))


def test_builtin_fixtures() -> None:
    config = MagicMock()
    config.stash = {}
    config.pytest_cuke_id_generator = IdGenerator()

    assert isinstance(_unwrap_fixture(pytestbdd_step_runner)(), ScenarioRunner)
    assert isinstance(_unwrap_fixture(pytestbdd_id_generator)(config), IdGenerator)
    assert isinstance(_unwrap_fixture(step_registry)(), Registry)
    assert isinstance(_unwrap_fixture(step_matcher)(config), Matcher)
    assert isinstance(_unwrap_fixture(steps_left)(), deque)

    request = MagicMock()
    attach_fn = _unwrap_fixture(attach)(request)
    attach_fn(b"data", media_type="text/plain")
    request.config.hook.pytest_cuke_attach.assert_called_once()

    assert pytest_cuke_is_collectible(config, Path("test.feature")) is True
    assert pytest_cuke_is_collectible(config, Path("test.py")) is None
