"""Public-facade step definitions used by the Usage formatter example."""

from __future__ import annotations

from pytest_cuke import given, parsers, then, when

_STATE: dict[str, str] = {}


@given("the Usage example starts a clean request")
def start_clean_request() -> None:
    _STATE.clear()


@when(
    parsers.cucumber_expression("the Usage example handles {word}"),
    anonymous_group_names=["value"],
)
def handle_value(value: str) -> None:
    _STATE["value"] = value


@then(
    parsers.cucumber_expression("the Usage example records {word}"),
    anonymous_group_names=["expected"],
)
def record_value(expected: str) -> None:
    assert _STATE.get("value") == expected


@given("the Usage example documents an unused definition")
def unused_definition() -> None:
    """This deliberately unused definition appears in the usage report."""
