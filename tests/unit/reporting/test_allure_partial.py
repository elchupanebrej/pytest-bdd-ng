import json
from pathlib import Path

import pytest

from pytest_cuke.allure_conversion import (
    AllureConversionError,
    _completed_partial_envelopes,
    _read_envelopes,
    convert_allure_messages,
)
from pytest_cuke.model.message_types import (
    Envelope,
    Pickle,
    Timestamp,
    message_to_dict,
)
from pytest_cuke.model.message_types import TestCase as Case
from pytest_cuke.model.message_types import TestCaseFinished as CaseFinished
from pytest_cuke.model.message_types import TestCaseStarted as CaseStarted
from pytest_cuke.model.message_types import TestRunStarted as RunStarted


def _write_started(path: Path) -> None:
    started = Envelope(test_run_started=RunStarted(id="run", timestamp=Timestamp(seconds=1, nanos=0)))
    path.write_text(json.dumps(message_to_dict(started)) + "\n", encoding="utf-8")


def test_partial_read_stops_at_a_malformed_line(tmp_path):
    source = tmp_path / "messages.ndjson"
    _write_started(source)
    with source.open("a", encoding="utf-8") as stream:
        stream.write("{broken-json\n")
        stream.write(json.dumps({"testRunFinished": {"timestamp": {"seconds": 2, "nanos": 0}}}) + "\n")

    parsed = _read_envelopes(source, allow_incomplete=True)

    assert len(parsed.envelopes) == 1
    assert parsed.incomplete is not None
    assert "line 2" in parsed.incomplete


def test_unpublishable_partial_stream_reports_its_cause(tmp_path):
    source = tmp_path / "messages.ndjson"
    _write_started(source)
    with source.open("a", encoding="utf-8") as stream:
        stream.write("{broken-json}\n")
    output = tmp_path / "allure-results"

    with pytest.raises(AllureConversionError, match=r"invalid JSON in .* at line 2"):
        convert_allure_messages(source, output)

    assert not output.exists()


def test_missing_run_finish_is_marked_as_incomplete(tmp_path):
    source = tmp_path / "messages.ndjson"
    _write_started(source)

    parsed = _read_envelopes(source, allow_incomplete=True)

    assert len(parsed.envelopes) == 1
    assert parsed.incomplete == "missing test_run_finished message"


def test_strict_read_still_requires_run_finish(tmp_path):
    source = tmp_path / "messages.ndjson"
    _write_started(source)

    with pytest.raises(AllureConversionError, match="test run finished"):
        _read_envelopes(source)


def test_empty_input_is_still_an_error(tmp_path):
    source = tmp_path / "messages.ndjson"
    source.write_text("", encoding="utf-8")

    with pytest.raises(AllureConversionError, match="contains no Cucumber messages"):
        _read_envelopes(source, allow_incomplete=True)


def _pickle(pickle_id: str) -> Pickle:
    return Pickle(ast_node_ids=[], id=pickle_id, language="en", name=pickle_id, steps=[], tags=[], uri="a.feature")


def _case(case_id: str, pickle_id: str) -> Case:
    return Case(id=case_id, pickle_id=pickle_id, test_steps=[])


def _time() -> Timestamp:
    return Timestamp(seconds=1, nanos=0)


def test_partial_envelopes_keep_only_completed_attempts():
    envelopes = [
        Envelope(pickle=_pickle("p1")),
        Envelope(pickle=_pickle("p2")),
        Envelope(test_case=_case("tc1", "p1")),
        Envelope(test_case=_case("tc2", "p2")),
        Envelope(test_case_started=CaseStarted(attempt=0, id="a1", test_case_id="tc1", timestamp=_time())),
        Envelope(test_case_started=CaseStarted(attempt=0, id="a2", test_case_id="tc2", timestamp=_time())),
        Envelope(test_case_finished=CaseFinished(test_case_started_id="a1", timestamp=_time(), will_be_retried=False)),
    ]

    kept = _completed_partial_envelopes(envelopes)

    assert [envelope.pickle.id for envelope in kept if envelope.pickle is not None] == ["p1"]
    assert [envelope.test_case.id for envelope in kept if envelope.test_case is not None] == ["tc1"]
    assert [envelope.test_case_started.id for envelope in kept if envelope.test_case_started is not None] == ["a1"]
    assert len([envelope for envelope in kept if envelope.test_case_finished is not None]) == 1
