"""Public-facade step definitions used by the Cucumber Summary example."""

from __future__ import annotations

from pytest_cuke import given, parsers, then, when

_STATE: dict[str, str] = {}


@given("the Summary example starts a clean ledger")
def start_clean_ledger() -> None:
    _STATE.clear()


@when(
    parsers.cucumber_expression("the Summary example records {word}"),
    anonymous_group_names=["entry"],
)
def record_entry(entry: str) -> None:
    _STATE["entry"] = entry


@then(
    parsers.cucumber_expression("the Summary example confirms {word}"),
    anonymous_group_names=["expected"],
)
def confirm_entry(expected: str) -> None:
    assert _STATE.get("entry") == expected
