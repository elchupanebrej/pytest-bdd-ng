from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from queue import Queue
from threading import Event
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from messages import ContentEncoding, Envelope as Message, TestCase
from pytest_bdd.compatibility.pytest import Exit
from pytest_bdd.message_plugin import MessagePlugin

from pytest import mark

pytestmark = mark.unit


TestCase.__test__ = False


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


def test_message_plugin_build_source_without_readable_file(tmp_path) -> None:
    assert MessagePlugin.build_source(SimpleNamespace(filename=None)) is None
    assert MessagePlugin.build_source(SimpleNamespace(filename=str(tmp_path / "missing.feature"))) is None


def test_message_plugin_disabled_is_a_noop() -> None:
    config = MagicMock()
    config.option.messages_ndjson_path = None
    config.option.cucumber_html_path = None
    plugin = MessagePlugin(config=config)
    request = MagicMock()
    request.config = config

    plugin.pytest_bdd_message(config, Message(test_case=TestCase(id="tc-1", pickle_id="p-1", test_steps=[])))
    plugin.pytest_bdd_attach(request, "text attachment", None, None)
    plugin.pytest_bdd_step_error(
        request,
        feature=None,
        scenario=None,
        step=None,
        step_func=None,
        step_func_args={},
        exception=AssertionError("boom"),
        step_definition=None,
    )
    plugin.generate_html_report()

    config.hook.pytest_bdd_message.assert_not_called()


def test_message_plugin_pytest_bdd_attach_bytearray_and_plain_object() -> None:
    config = _enabled_config()
    plugin = MessagePlugin(config=config)
    plugin.current_test_case = TestCase(id="tc-1", pickle_id="p-1", test_steps=[])
    request = MagicMock()
    request.config = config

    plugin.pytest_bdd_attach(request, bytearray(b"hello"), None, None)
    plugin.pytest_bdd_attach(request, 12345, None, None)

    attachments = [call.kwargs["message"].attachment for call in config.hook.pytest_bdd_message.call_args_list]
    assert attachments[0].body == b64encode(b"hello").decode("ascii")
    assert ContentEncoding(attachments[0].content_encoding) == ContentEncoding.base64
    assert attachments[1].body == "12345"
    assert attachments[1].media_type == "text/plain;charset=UTF-8"
    assert ContentEncoding(attachments[1].content_encoding) == ContentEncoding.identity


def test_check_npm_and_cucumber_packages_exits_when_dependencies_missing(monkeypatch) -> None:
    plugin = MessagePlugin(config=_enabled_config())

    monkeypatch.setattr("pytest_bdd.message_plugin.check_npm", lambda: False)
    with pytest.raises(Exit):
        plugin.check_npm_and_cucumber_packages()

    monkeypatch.setattr("pytest_bdd.message_plugin.check_npm", lambda: True)
    monkeypatch.setattr(
        "pytest_bdd.message_plugin.check_npm_package", lambda package, global_install=False: False
    )
    with pytest.raises(Exit):
        plugin.check_npm_and_cucumber_packages()


def test_process_messages_writes_valid_and_drops_invalid(tmp_path, caplog) -> None:
    messages_file = tmp_path / "messages.ndjson"
    queue: Queue[str] = Queue()
    valid = Message(test_case=TestCase(id="tc-1", pickle_id="p-1", test_steps=[])).model_dump_json(
        exclude_none=True, by_alias=True
    )
    queue.put_nowait(valid)
    queue.put_nowait('{"source": 1}')
    queue.put_nowait(valid)

    stop_event = Event()
    stop_event.set()
    MessagePlugin.process_messages(queue, stop_event, messages_file)

    lines = messages_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all("tc-1" in line for line in lines)
    assert "Failed to parse" in caplog.text


def test_message_plugin_generates_html_report_and_removes_temp_messages_file(tmp_path, monkeypatch) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "formatter.js").write_text("window.formatter = 1;", encoding="utf-8")
    (assets / "formatter.css").write_text("body { color: red; }", encoding="utf-8")
    (assets / "index.mustache.html").write_text(
        "<html><head><style>{{css}}</style></head><body>"
        "<script>{{script}}</script><script>window.CUCUMBER_MESSAGES = [{{messages}}];</script>"
        "</body></html>",
        encoding="utf-8",
    )

    def fake_find_resource(_package, resource):
        mapping = {
            "main.js": "formatter.js",
            "main.css": "formatter.css",
            "index.mustache.html": "index.mustache.html",
        }
        name = Path(resource).name
        return iter([str(assets / mapping[name])] if name in mapping else [])

    monkeypatch.setattr(MessagePlugin, "check_npm_and_cucumber_packages", lambda self: None)
    monkeypatch.setattr("pytest_bdd.message_plugin.find_resource", fake_find_resource)

    html_path = tmp_path / "report" / "cucumber.html"
    config = _enabled_config(messages_ndjson_path=None, cucumber_html_path=str(html_path))
    plugin = MessagePlugin(config=config)

    assert plugin.is_messages_file_temp is True
    temp_messages_file = Path(plugin.messages_file_path)
    assert temp_messages_file.exists()

    plugin.start_process_messages_thread()
    plugin.pytest_bdd_message(config, Message(test_case=TestCase(id="tc-1", pickle_id="p-1", test_steps=[])))
    plugin.pytest_sessionfinish(SimpleNamespace(config=config), exitstatus=0)

    html = html_path.read_text(encoding="utf-8")
    assert "window.formatter = 1;" in html
    assert "body { color: red; }" in html
    assert "tc-1" in html
    assert temp_messages_file.exists() is False
