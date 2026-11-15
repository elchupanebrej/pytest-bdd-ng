from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from attrs import evolve

from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.formatter_catalog import FormatterCatalogError
from pytest_cuke.formatter_replay import replay_messages
from pytest_cuke.formatter_runtime import FormatterRuntimeError
from pytest_cuke.model.message_types import Envelope, Meta, Product, message_to_dict


def _messages_file(path: Path) -> bytes:
    product = Product(name="pytest-cuke", version="2.3.1")
    meta = Envelope(
        meta=Meta(
            protocol_version="34.2.1",
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


def test_replay_filters_outcome_metadata_but_preserves_user_attachments(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    _messages_file(source)
    attachments = [
        {
            "attachment": {
                "body": '{"outcome":"xfail"}',
                "contentEncoding": "IDENTITY",
                "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
            }
        },
        {"attachment": {"body": "user data", "contentEncoding": "IDENTITY", "mediaType": "text/plain"}},
    ]
    with source.open("a", encoding="utf-8") as stream:
        for event in attachments:
            stream.write(json.dumps(event) + "\n")
    original = source.read_bytes()
    output = tmp_path / "rendered.ndjson"
    replay_messages(source, (_request(output, "import sys; sys.stdout.write(sys.stdin.read())"),))
    events = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert attachments[0] not in events
    assert attachments[1] in events
    assert source.read_bytes() == original


def _append_run(path: Path, *, finished: bool = False) -> None:
    timestamp = {"seconds": 1, "nanos": 0}
    started = {"testRunStarted": {"id": "run", "timestamp": timestamp}}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(started) + "\n")
        if finished:
            stream.write(json.dumps({"testRunFinished": {"timestamp": timestamp, "success": True}}) + "\n")


def _marker(output: Path) -> Path:
    return output.with_name(output.name + ".incomplete.json")


def test_replay_publishes_partial_output_and_marks_missing_run_finish(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    _messages_file(source)
    _append_run(source, finished=False)
    output = tmp_path / "rendered.ndjson"

    with pytest.raises(FormatterRuntimeError, match="incomplete"):
        replay_messages(source, (_request(output, "import sys; sys.stdout.write(sys.stdin.read())"),))

    rendered = output.read_text(encoding="utf-8")
    assert "testRunStarted" in rendered
    synthetic = json.loads(rendered.splitlines()[-1])["testRunFinished"]
    assert synthetic["success"] is False
    assert "incomplete Messages stream" in synthetic["message"]
    marker = json.loads(_marker(output).read_text(encoding="utf-8"))
    assert marker["incomplete"] is True
    assert "test_run_finished" in marker["reason"]


def test_replay_stops_at_a_malformed_line_and_marks_the_partial_output(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    _messages_file(source)
    _append_run(source, finished=False)
    with source.open("a", encoding="utf-8") as stream:
        stream.write("{broken-json\n")
        stream.write(json.dumps({"testRunFinished": {"timestamp": {"seconds": 2, "nanos": 0}, "success": True}}) + "\n")
    output = tmp_path / "rendered.ndjson"

    with pytest.raises(FormatterRuntimeError, match="line 3"):
        replay_messages(source, (_request(output, "import sys; sys.stdout.write(sys.stdin.read())"),))

    rendered = output.read_text(encoding="utf-8")
    assert "testRunStarted" in rendered
    synthetic = json.loads(rendered.splitlines()[-1])["testRunFinished"]
    assert synthetic["success"] is False
    assert "incomplete Messages stream" in synthetic["message"]
    marker = json.loads(_marker(output).read_text(encoding="utf-8"))
    assert marker["incomplete"] is True
    assert "line 3" in marker["reason"]


def test_replay_rejects_an_empty_stream_without_publishing(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    source.write_text("", encoding="utf-8")
    output = tmp_path / "rendered.ndjson"

    with pytest.raises(FormatterRuntimeError, match="contains no envelopes"):
        replay_messages(source, (_request(output, "import sys; sys.stdout.write(sys.stdin.read())"),))

    assert not output.exists()
    assert not _marker(output).exists()


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


def test_replay_publishes_healthy_output_when_another_formatter_fails(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    original = _messages_file(source)
    healthy = tmp_path / "healthy.ndjson"
    broken = tmp_path / "broken.ndjson"
    broken.write_text("previous report", encoding="utf-8")
    healthy_request = evolve(_request(healthy, "import sys; sys.stdout.write(sys.stdin.read())"), name="healthy")
    broken_request = evolve(
        _request(broken, "import sys; sys.stdout.write('partial'); sys.exit(3)"),
        name="broken",
    )

    with pytest.raises(FormatterRuntimeError, match=r"broken.*exited with status 3"):
        replay_messages(source, (healthy_request, broken_request))

    assert json.loads(healthy.read_text(encoding="utf-8")) == json.loads(original)
    assert broken.read_text(encoding="utf-8") == "previous report"
    assert not list(tmp_path.glob(".*.pytest-cuke-tmp"))


def test_replay_timeout_kills_child_and_removes_staged_output(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    _messages_file(source)
    output = tmp_path / "rendered.ndjson"
    code = "import sys, time; sys.stdin.read(); time.sleep(10)"

    with pytest.raises(FormatterRuntimeError, match=r"Replay formatter.*did not exit within"):
        replay_messages(source, (_request(output, code, timeout=0.05),))

    assert not output.exists()
    assert not list(tmp_path.glob(".rendered.ndjson.*.pytest-cuke-tmp"))
