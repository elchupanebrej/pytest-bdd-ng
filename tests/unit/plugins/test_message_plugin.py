from __future__ import annotations

from queue import Queue
from unittest.mock import MagicMock

from messages import Envelope as Message
from messages import TestCase
from pytest_bdd.message_plugin import MessagePlugin

TestCase.__test__ = False


def test_message_plugin_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    MessagePlugin.add_options(parser)
    assert parser.getgroup.call_count == 2
    assert group.addoption.call_count == 2


def test_message_plugin_disabled_when_no_options() -> None:
    config = MagicMock()
    config.option.messages_ndjson_path = None
    config.option.cucumber_html_path = None

    plugin = MessagePlugin(config=config)
    assert plugin.is_disabled is True


def test_message_plugin_get_timestamp() -> None:
    ts = MessagePlugin.get_timestamp()
    assert ts.seconds > 0
    assert ts.nanos >= 0


def test_message_plugin_pytest_bdd_message_queue() -> None:
    config = MagicMock()
    config.option.messages_ndjson_path = "messages.ndjson"
    config.option.cucumber_html_path = None

    plugin = MessagePlugin(config=config)
    assert plugin.is_disabled is False
    plugin.process_messages_io_queue = Queue()

    msg = Message(test_case=TestCase(id="tc-1", pickle_id="p-1", test_steps=[]))
    plugin.pytest_bdd_message(config, msg)

    assert not plugin.process_messages_io_queue.empty()
    item = plugin.process_messages_io_queue.get_nowait()
    assert "tc-1" in item


def test_message_plugin_pytest_bdd_attach() -> None:
    config = MagicMock()
    config.option.messages_ndjson_path = "messages.ndjson"
    config.option.cucumber_html_path = None

    plugin = MessagePlugin(config=config)
    plugin.current_test_case = TestCase(id="tc-1", pickle_id="p-1", test_steps=[])

    request = MagicMock()
    request.config = config

    plugin.pytest_bdd_attach(request, "hello attachment", "text/plain", "file.txt")
    config.hook.pytest_bdd_message.assert_called_once()
