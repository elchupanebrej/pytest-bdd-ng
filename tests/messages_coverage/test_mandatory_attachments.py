from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

test_scenarios = scenarios(Path(__file__).with_name("fixtures") / "mandatory_coverage.feature")


@given(parsers.parse('a background value "{value}"'))
def _background_value(value: str) -> str:
    return value


@given(parsers.parse('a rule background value "{value}"'))
def _rule_background_value(value: str) -> str:
    return value


@given("a background table:")
def _background_table(step) -> None:
    assert step.data_table is not None


@given(parsers.parse("a number {number:d}"))
def _number(number: int) -> int:
    return number


@given("a payload doc string:")
def _payload_doc_string(step) -> None:
    assert step.doc_string is not None


@given("a payload table:")
def _payload_table(step) -> None:
    assert step.data_table is not None


@when(parsers.parse('I attach textual and binary evidence for "{name}"'))
def _attach_payloads(attach, name: str, mandatory_attachment_log) -> None:
    text_value = f"text-{name}"
    binary_value = f"bytes-{name}".encode()

    attach(
        text_value,
        media_type="text/plain;charset=UTF-8",
        source_data=f"Feature: source for {name}",
        source_media_type="text/x.cucumber.gherkin+plain",
        source_uri=f"features/{name}.feature",
        url=f"https://example.invalid/{name}.txt",
        test_run_hook_started_id="audit-run-hook-id",
        test_run_started_id="audit-run-id",
    )
    attach(
        binary_value,
        media_type="application/octet-stream",
        file_name=f"{name}.bin",
        source_data=f"Feature: source for {name}",
        source_media_type="text/x.cucumber.gherkin+plain",
        source_uri=f"features/{name}.feature",
        url=f"https://example.invalid/{name}.bin",
        as_external=True,
        test_run_hook_started_id="audit-run-hook-id",
        test_run_started_id="audit-run-id",
    )

    mandatory_attachment_log[name].append(text_value)


@then(parsers.parse('result should be "{result}"'))
def _result(result: str, mandatory_attachment_log) -> None:
    assert result == "pass"
    assert mandatory_attachment_log
