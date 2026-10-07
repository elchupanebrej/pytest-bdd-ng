from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.formatter_catalog import FormatterCatalogError
from pytest_cuke.formatter_replay import replay_messages
from pytest_cuke.formatter_runtime import FormatterRuntimeError
from pytest_cuke.model.message_types import Envelope, Meta, Product, message_to_dict


def _messages_file(path: Path) -> bytes:
    product = Product(name="pytest-cuke", version="2.3.1")
    meta = Envelope(
        meta=Meta(
            protocol_version="28.0.0",
            implementation=product,
            runtime=product,
            os=product,
            cpu=product,
        )
    )
    contents = json.dumps(message_to_dict(meta)) + "\n"
    path.write_text(contents, encoding="utf-8")
    return path.read_bytes()


def _request(output: Path, code: str, *, timeout: float = 1.0) -> FormatterRequest:
    return FormatterRequest(
        name="replay-probe",
        command=(sys.executable, "-c", code),
        output_path=output,
        working_directory=output.parent,
        timeout_seconds=timeout,
    )


def test_replay_uses_common_runtime_and_preserves_saved_input(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    original = _messages_file(source)
    output = tmp_path / "rendered.ndjson"

    replay_messages(source, (_request(output, "import sys; sys.stdout.write(sys.stdin.read())"),))

    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8")) == json.loads(original)
    assert source.read_bytes() == original
    assert not list(tmp_path.glob(".rendered.ndjson.*.pytest-cuke-tmp"))


def test_replay_rejects_using_the_input_as_an_output(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    original = _messages_file(source)

    with pytest.raises(FormatterCatalogError, match="output path is the Messages input file"):
        replay_messages(source, (_request(source, "import sys; sys.stdin.read()"),))

    assert source.read_bytes() == original


def test_replay_failure_does_not_publish_a_partial_output(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    _messages_file(source)
    output = tmp_path / "rendered.ndjson"
    output.write_text("previous report", encoding="utf-8")
    code = "import sys; sys.stdout.write(sys.stdin.read()); sys.exit(3)"

    with pytest.raises(FormatterRuntimeError, match="exited with status 3"):
        replay_messages(source, (_request(output, code),))

    assert output.read_text(encoding="utf-8") == "previous report"
    assert not list(tmp_path.glob(".rendered.ndjson.*.pytest-cuke-tmp"))


def test_replay_timeout_kills_child_and_removes_staged_output(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    _messages_file(source)
    output = tmp_path / "rendered.ndjson"
    code = "import sys, time; sys.stdin.read(); time.sleep(10)"

    with pytest.raises(FormatterRuntimeError, match=r"Replay formatter.*did not exit within"):
        replay_messages(source, (_request(output, code, timeout=0.05),))

    assert not output.exists()
    assert not list(tmp_path.glob(".rendered.ndjson.*.pytest-cuke-tmp"))
