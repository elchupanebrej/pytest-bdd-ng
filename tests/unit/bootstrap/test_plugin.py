from __future__ import annotations

from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from pytest_cuke import hooks
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.message_plugin import MessagePlugin, MessageSessionFinishHookAdapter
from pytest_cuke.plugin import (
    attach,
    pytest_addhooks,
    pytest_cuke_is_collectible,
    pytest_collection_finish,
    pytest_configure,
    pytest_load_initial_conftests,
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


def test_pytest_addhooks() -> None:
    pluginmanager = MagicMock()
    pytest_addhooks(pluginmanager)
    pluginmanager.add_hookspecs.assert_called_once_with(hooks)


def test_pytest_load_initial_conftests_registers_a_deferred_session_finish_hook() -> None:
    pluginmanager = MagicMock()
    early_config = SimpleNamespace(
        known_args_namespace=SimpleNamespace(cuke_allure_messages_in=None, noconftest=False),
        getini=lambda name: "",
        pluginmanager=pluginmanager,
    )

    pytest_load_initial_conftests(early_config)

    plugin, = pluginmanager.register.call_args.args
    assert isinstance(plugin, MessageSessionFinishHookAdapter)
    assert plugin.message_plugin is None
    pluginmanager.register.assert_called_once_with(plugin, name="pytest_cuke_messages_session_finish")


def test_pytest_configure_lifecycle() -> None:
    config = MagicMock()
    config.stash = {}
    config.pluginmanager = MagicMock()
    session_finish_hook = MessageSessionFinishHookAdapter()
    config.pluginmanager.get_plugin.return_value = session_finish_hook
    config.option = MagicMock()
    config.option.cuke_json = None
    config.option.cuke_progress = False
    config.option.cuke_summary = False
    config.option.cuke_tolerant_status = None
    config.option.cuke_wip_status = None
    config.option.cuke_mcp_on_fail = None
    config.option.cuke_mcp_timeout = None
    config.option.cuke_mcp_lease = None
    config.option.cuke_mcp_host = None
    config.option.cuke_mcp_port = None
    config.getini.side_effect = lambda name: {
        "cuke_tolerant_status": "failed",
        "cuke_wip_status": "failed",
        "cuke_mcp_on_fail": False,
        "cuke_mcp_timeout": "30s",
        "cuke_mcp_lease": "10s",
        "cuke_mcp_host": "127.0.0.1",
        "cuke_mcp_port": "auto",
    }.get(name, "")

    pytest_configure(config)

    config.addinivalue_line.assert_any_call("markers", "pytest_cuke_scenario: marker to identify pytest_cuke tests")
    config.addinivalue_line.assert_any_call("markers", "scenarios: marker to provide scenarios locator")
    config.addinivalue_line.assert_any_call(
        "markers", "wip_status(value): override the not-implemented step status for this scenario"
    )
    assert IdGenerator.pytest_cuke_id_generator in config.stash
    assert IdGenerator.from_stash(config.stash).namespace == RunContext.from_config(config).run_id
    assert config.pluginmanager.register.call_count >= 2
    message_plugins = [
        call.args[0]
        for call in config.pluginmanager.register.call_args_list
        if call.args and isinstance(call.args[0], MessagePlugin)
    ]
    assert len(message_plugins) == 1
    assert session_finish_hook.message_plugin is message_plugins[0]


def test_pytest_unconfigure_lifecycle() -> None:
    config = MagicMock()
    config.pluginmanager = MagicMock()
    config.stash = {}
    config.__allure_plugin__ = MagicMock()

    pytest_unconfigure(config)
    config.pluginmanager.unregister.assert_any_call(name="pytest_cuke_messages")
    config.pluginmanager.unregister.assert_any_call(name="pytest_cuke_messages_session_finish")
    config.pluginmanager.unregister.assert_any_call(name="pytest_cuke_summary")
    config.__allure_plugin__.unregister.assert_called_once_with(config)


def test_collection_finish_leaves_a_plain_pytest_session_inactive() -> None:
    config = MagicMock()
    config.stash = {}
    context = RunContext.from_config(config)
    context.begin_collection()

    pytest_collection_finish(MagicMock(config=config))

    assert context.active_feature_binding is None
    assert context.active_scenario_run is None
    assert context.stage == "inactive"
    assert context.hook_phase == "inactive"
    assert context.status == "inactive"


def test_run_context_and_message_ids_are_scoped_to_each_config() -> None:
    first_config = SimpleNamespace(stash={})
    second_config = SimpleNamespace(stash={})

    first_context = RunContext.from_config(first_config)
    second_context = RunContext.from_config(second_config)
    first_generator = IdGenerator.from_stash(first_config.stash)
    second_generator = IdGenerator.from_stash(second_config.stash)
    first_generator.set_namespace(first_context.run_id)
    second_generator.set_namespace(second_context.run_id)

    assert RunContext.from_config(first_config) is first_context
    assert RunContext.from_config(second_config) is second_context
    assert first_context is not second_context
    assert first_generator.namespace != second_generator.namespace
    assert next(first_generator) != next(second_generator)


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
    request.config = config
    attach_fn = _unwrap_fixture(attach)(request)
    attach_fn(b"data", media_type="text/plain")
    request.config.hook.pytest_cuke_attach.assert_called_once()

    assert pytest_cuke_is_collectible(config, Path("test.feature")) is True
    assert pytest_cuke_is_collectible(config, Path("test.py")) is None
