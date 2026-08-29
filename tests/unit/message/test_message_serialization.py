from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest

import messages
from pytest_bdd.model import message_converter as mc
from pytest_bdd.model import message_serialization as ms

if TYPE_CHECKING:
    from pathlib import Path


def test_serialize_and_deserialize_envelope() -> None:
    env = mc.make_test_run_started(100.0)
    json_str = ms.serialize_envelope(env)
    assert "testRunStarted" in json_str
    assert ms.deserialize_envelope(json_str).test_run_started.timestamp.seconds == 100
    assert ms.deserialize_envelope(mc.envelope_to_dict(env)) == env
    with pytest.raises(TypeError, match="exactly one payload"):
        ms.serialize_envelope(messages.Envelope())


def test_dump_and_load_ndjson(tmp_path: Path) -> None:
    envelopes = [
        mc.make_test_run_started(100.0),
        mc.make_test_case_started("tc-1", id="tcs-1", timestamp=101.0),
        mc.make_test_case_finished("tcs-1", timestamp=102.0),
        mc.make_test_run_finished(timestamp=103.0, success=True),
    ]
    ndjson_str = ms.dump_ndjson(envelopes)
    assert len(ms.load_ndjson(ndjson_str)) == 4

    stream = io.StringIO()
    ms.dump_ndjson(envelopes, stream)
    stream.seek(0)
    assert len(ms.load_ndjson(stream)) == 4

    target = tmp_path / "test.ndjson"
    ms.dump_ndjson(envelopes, target)
    assert len(ms.load_ndjson(target)) == 4
