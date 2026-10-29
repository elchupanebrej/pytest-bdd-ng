"""Public-facade step definitions used by the Cucumber JSON example."""

from __future__ import annotations

import json
from typing import Any

from pytest_cuke import given, parsers, then, when

_STATE: dict[str, Any] = {}


@given("the Cucumber JSON example prepares a request")
def prepare_request() -> None:
    _STATE.clear()
    _STATE["request_ready"] = True


@given("the Cucumber JSON example resets its output")
def reset_output() -> None:
    _STATE.pop("response", None)


@given("the Cucumber JSON example receives a document")
def receive_document(step: Any) -> None:
    assert step.doc_string is not None
    assert step.doc_string.media_type == "application/json"
    _STATE["document"] = json.loads(step.doc_string.content)


@given("the Cucumber JSON example receives a table")
def receive_table(step: Any) -> None:
    assert step.data_table is not None
    _STATE["table"] = step.data_table.as_dicts()


@when("the Cucumber JSON example processes the request")
def process_request() -> None:
    assert _STATE.get("request_ready") is True
    assert _STATE.get("document", {}).get("ready") is True
    assert _STATE.get("table") == [{"field": "café", "value": "alpha"}]
    _STATE["response"] = _STATE["document"]["message"]


@then(parsers.parse('the Cucumber JSON example response is "{expected}"'))
def assert_response(expected: str) -> None:
    assert _STATE.get("response") == expected


@then("the Cucumber JSON example attaches a report")
def attach_report(attach: Any) -> None:
    attach(
        "checked-in Cucumber JSON example attachment café",
        media_type="text/plain",
        file_name="cucumber-json-example.txt",
    )


@given(parsers.parse('the Cucumber JSON example records "{label}"'))
def record_outline_row(label: str) -> None:
    assert label in {"alpha", "bravo"}
    _STATE["response"] = label
