from __future__ import annotations

from unittest.mock import MagicMock

from pytest_bdd import hooks
from pytest_bdd.plugin import pytest_addhooks, pytest_configure, pytest_unconfigure
from pytest_bdd.utils import IdGenerator


def test_pytest_addhooks() -> None:
    pluginmanager = MagicMock()
    pytest_addhooks(pluginmanager)
    pluginmanager.add_hookspecs.assert_called_once_with(hooks)


def test_pytest_configure_lifecycle() -> None:
    config = MagicMock()
    config.stash = {}
    config.pluginmanager = MagicMock()
    config.option = MagicMock()
    config.option.cucumber_json_path = None
    config.option.gherkin_terminal_reporter = None

    pytest_configure(config)

    config.addinivalue_line.assert_any_call("markers", "pytest_bdd_scenario: marker to identify pytest_bdd tests")
    config.addinivalue_line.assert_any_call("markers", "scenarios: marker to provide scenarios locator")
    assert IdGenerator.pytest_bdd_id_generator in config.stash
    assert config.pluginmanager.register.call_count >= 2


def test_pytest_unconfigure_lifecycle() -> None:
    config = MagicMock()
    config.pluginmanager = MagicMock()
    config.__allure_plugin__ = MagicMock()

    pytest_unconfigure(config)
    config.pluginmanager.unregister.assert_any_call(name="pytest_bdd_messages")
    config.__allure_plugin__.unregister.assert_called_once_with(config)
