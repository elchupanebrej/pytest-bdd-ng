from __future__ import annotations

import json
from base64 import b64encode
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from unittest.mock import MagicMock

from messages import Envelope as Message
from messages import TestCase, TestCaseStarted, TestStep, Timestamp
from pytest_cuke.message_plugin import MessagePlugin
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.model.step import Step

TestCase.__test__ = False
TestCaseStarted.__test__ = False
TestStep.__test__ = False


def _enabled_config(**overrides):
    config = MagicMock()
    config.option.messages_ndjson_path = "messages.ndjson"
    config.option.cucumber_html_path = None
    for key, value in overrides.items():
        setattr(config.option, key, value)
    return config


def test_message_plugin_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    MessagePlugin.add_options(parser)
    assert parser.getgroup.call_count == 3
    assert group.addoption.call_count == 4


def test_message_plugin_disabled_when_no_options() -> None:
    config = MagicMock()
    config.option.cuke_messages_ndjson = None
    config.option.cuke_html = None
    config.getini.return_value = ""

    plugin = MessagePlugin(config=config)
    assert plugin.is_disabled is True


def test_message_plugin_get_timestamp() -> None:
    ts = MessagePlugin.get_timestamp()
    assert ts.seconds > 0
    assert ts.nanos >= 0


def test_message_plugin_pytest_cuke_message_queue() -> None:
    config = MagicMock()
    config.option.cuke_messages_ndjson = "messages.ndjson"
    config.option.cuke_html = None

    plugin = MessagePlugin(config=config)
    assert plugin.is_disabled is False
    plugin.process_messages_io_queue = Queue()

    msg = Message(test_case=TestCase(id="tc-1", pickle_id="p-1", test_steps=[]))
    plugin.pytest_cuke_message(config, msg)

    assert not plugin.process_messages_io_queue.empty()
    item = plugin.process_messages_io_queue.get_nowait()
    assert "tc-1" in item


def test_message_plugin_pytest_cuke_attach() -> None:
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="test.feature::Scenario",
        feature=Feature(name="Attachment", uri="attachment.feature"),
        scenario=Scenario(name="Attachment"),
    )
    scenario_run.message_state.test_case = TestCase(id="tc-1", pickle_id="p-1", test_steps=[])
    scenario_run.message_state.test_case_started = TestCaseStarted(
        attempt=0,
        id="tcs-1",
        test_case_id="tc-1",
        worker_id="master",
        timestamp=Timestamp(seconds=1, nanos=0),
    )
    config = SimpleNamespace(
        stash={RunContext.STASH_KEY: context},
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=MagicMock(),
    )

    plugin = MessagePlugin(config=config)

    request = SimpleNamespace(config=config)

    plugin.pytest_cuke_attach(request, "hello attachment", "text/plain", "file.txt")
    config.hook.pytest_cuke_message.assert_called_once()


def test_tolerated_step_error_keeps_later_message_steps_executable() -> None:
    failed_step = Step(name="tolerated failure", keyword="When ")
    later_step = Step(name="later real step", keyword="Then ")
    scenario = Scenario(name="Tolerated", steps=(failed_step, later_step))
    feature = Feature(name="Tolerant messages", uri="tolerant.feature")
    context = RunContext()
    scenario_run = context.start_scenario(nodeid="tolerant.feature::Tolerated", feature=feature, scenario=scenario)
    failed_test_step = TestStep(id="ts-failed", pickle_step_id="ps-failed", step_definition_ids=[])
    later_test_step = TestStep(id="ts-later", pickle_step_id="ps-later", step_definition_ids=[])
    scenario_run.message_state.test_case_started = TestCaseStarted(
        attempt=0,
        id="attempt-1",
        test_case_id="tc-1",
        worker_id="master",
        timestamp=Timestamp(seconds=1, nanos=0),
    )
    scenario_run.message_state.test_steps = [failed_test_step, later_test_step]
    scenario_run.message_state.test_steps_by_identity = {
        id(failed_step): failed_test_step,
        id(later_step): later_test_step,
    }
    config = SimpleNamespace(
        stash={RunContext.STASH_KEY: context},
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=MagicMock(),
    )
    plugin = MessagePlugin(config=config)

    plugin.pytest_cuke_step_error(
        request=SimpleNamespace(config=config),
        feature=feature,
        scenario=scenario,
        step=failed_step,
        step_func=lambda: None,
        step_func_args={},
        exception=AssertionError("tolerated failure"),
        step_definition=object(),
        tolerated=True,
    )

    assert scenario_run.message_state.finished_test_step_ids == {"ts-failed"}
    assert len(config.hook.pytest_cuke_message.call_args_list) == 2


def test_message_plugin_ignores_ordinary_pytest_tests() -> None:
    config = MagicMock()
    config.option.cuke_messages_ndjson = "messages.ndjson"
    config.option.cuke_html = None

    plugin = MessagePlugin(config=config)
    request = MagicMock()
    item = MagicMock()
    item.fixturenames = ["pytestconfig"]
    item._request = request

    list(plugin.pytest_runtest_setup(item))

    request.getfixturevalue.assert_not_called()
