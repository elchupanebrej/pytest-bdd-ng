"""Public-facade step definitions used by the Usage JSON example."""

from __future__ import annotations

from pytest_cuke import given, parsers, then, when

_STATE: dict[str, str] = {}


@given("the Usage JSON example starts a clean request")
def start_clean_request() -> None:
    _STATE.clear()


@when(
    parsers.cucumber_expression("the Usage JSON example handles {word}"),
    anonymous_group_names=["value"],
)
def handle_value(value: str) -> None:
    _STATE["value"] = value


@then(
    parsers.cucumber_expression("the Usage JSON example records {word}"),
    anonymous_group_names=["expected"],
)
def record_value(expected: str) -> None:
    assert _STATE.get("value") == expected


@given("the Usage JSON example documents an unused definition")
def unused_definition() -> None:
    """This deliberately unused definition appears with an empty matches list."""
