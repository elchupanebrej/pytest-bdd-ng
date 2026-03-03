from __future__ import annotations

from pathlib import Path

import pytest
from cucumber_expressions.parameter_type import ParameterType
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.hook import after_tag, around_mark, before_mark, before_tag

test_scenarios = scenarios(Path(__file__).with_name("fixtures") / "mandatory_coverage.feature")


class Coordinate:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return (
            isinstance(other, Coordinate)
            and self.x == other.x
            and self.y == other.y
            and self.z == other.z
        )


def _build_parameter_type_registry() -> ParameterTypeRegistry:
    registry = ParameterTypeRegistry()
    registry.define_parameter_type(
        ParameterType(
            "coordinate",
            r"(\d+),\s*(\d+),\s*(\d+)",
            Coordinate,
            lambda x, y, z: Coordinate(int(x), int(y), int(z)),
            True,
            False,
        )
    )
    return registry


MANDATORY_PARAMETER_TYPE_REGISTRY = _build_parameter_type_registry()


@pytest.fixture
def parameter_type_registry():
    return MANDATORY_PARAMETER_TYPE_REGISTRY


@before_tag("@scenario_tag", name="before")
def _before_tag_hook(request):  # noqa: ARG001 - runtime hook emission coverage
    return None


@before_mark("scenario_tag")
def _before_mark_hook(request):  # noqa: ARG001 - runtime hook emission coverage
    return None


@after_tag("@scenario_tag", name="after")
def _after_tag_hook(request):  # noqa: ARG001 - runtime hook emission coverage
    return None


@around_mark("scenario_tag", "around")
def _around_mark_hook(request):  # noqa: ARG001 - runtime hook emission coverage
    yield


@given(parsers.parse('a background value "{value}"'))
def _background_value(value: str) -> str:
    return value


@given(parsers.parse('a rule background value "{value}"'))
def _rule_background_value(value: str) -> str:
    return value


@given("a background table:")
def _background_table(step) -> None:
    assert step.data_table is not None


@given("a background doc string:")
def _background_doc_string(step) -> None:
    assert step.doc_string is not None


@given("a rule background doc string:")
def _rule_background_doc_string(step) -> None:
    assert step.doc_string is not None


@given("a rule background table:")
def _rule_background_table(step) -> None:
    assert step.data_table is not None


@given(parsers.parse("a number {number:d}"))
def _number(number: int) -> int:
    return number


@given(
    parsers.cucumber_expression(
        "a coordinate {coordinate}",
        parameter_type_registry=MANDATORY_PARAMETER_TYPE_REGISTRY,
    ),
    anonymous_group_names=("coordinate",),
)
def _coordinate_step(coordinate: Coordinate) -> None:
    assert coordinate == Coordinate(10, 20, 30)


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
def _result(result: str) -> None:
    assert result == "pass"
