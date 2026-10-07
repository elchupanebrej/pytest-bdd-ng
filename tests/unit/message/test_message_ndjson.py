from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_cuke.message_ndjson import iter_validated_ndjson, read_validated_ndjson
from pytest_cuke.model.message_converter import make_test_case_started, make_test_run_started
from pytest_cuke.model.message_types import message_to_dict


def test_reader_skips_blank_lines_and_reports_json_location(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    started = message_to_dict(make_test_run_started(100.0))
    source.write_text("\n" + json.dumps(started) + "\n\n{not json\n", encoding="utf-8")

    iterator = iter_validated_ndjson(source)
    assert next(iterator) == make_test_run_started(100.0)
    with pytest.raises(ValueError, match=r"messages\.ndjson at line 4:.*Expecting property name"):
        next(iterator)


def test_reader_reports_reference_errors_at_the_input_line(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    messages = (
        make_test_run_started(100.0),
        make_test_case_started(test_case_id="missing-case", id="attempt-1", timestamp=101.0),
    )
    source.write_text("\n".join(json.dumps(message_to_dict(item)) for item in messages) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"messages\.ndjson at line 2 \(ORPHAN_REFERENCE\)"):
        read_validated_ndjson(source)


def test_reader_reports_unsupported_protocol_at_the_input_line(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    product = {"name": "pytest-cuke", "version": "2.3.1"}
    meta = {
        "meta": {
            "protocolVersion": "99.0.0",
            "implementation": product,
            "runtime": product,
            "os": product,
            "cpu": product,
        }
    }
    source.write_text(json.dumps(meta) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"messages\.ndjson at line 1 \(UNSUPPORTED_PROTOCOL_VERSION\)"):
        read_validated_ndjson(source)


def test_reader_reports_incomplete_stream_at_end_of_file(tmp_path: Path) -> None:
    source = tmp_path / "messages.ndjson"
    source.write_text(json.dumps(message_to_dict(make_test_run_started(100.0))) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"messages\.ndjson at end of file after line 1"):
        read_validated_ndjson(source)
