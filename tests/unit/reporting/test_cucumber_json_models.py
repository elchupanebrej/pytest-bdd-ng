from __future__ import annotations

from pytest_bdd.cucumber_json import (
    Argument,
    CucumberJson,
    DataTableRow,
    DocString,
    Element,
    ElementType,
    Feature,
    Hook,
    Match,
    Result,
    Status,
    Step,
    Tag,
)


def test_cucumber_json_models_validation() -> None:
    arg = Argument(value="123", offset=4.0)
    assert arg.value == "123"
    assert arg.offset == 4.0

    tag = Tag(name="@smoke", line=1.0)
    assert tag.name == "@smoke"

    match = Match(location="steps/test_steps.py:10", arguments=[arg])
    assert match.location == "steps/test_steps.py:10"
    assert len(match.arguments or []) == 1

    result = Result(duration=1000000.0, status=Status.passed, error_message=None)
    assert result.status == Status.passed
    assert result.duration == 1000000.0

    doc_string = DocString(line=5.0, value="hello", content_type="text/plain")
    assert doc_string.value == "hello"

    row = DataTableRow(cells=["col1", "col2"])
    assert row.cells == ["col1", "col2"]

    step = Step(
        keyword="Given",
        line=2.0,
        match=match,
        name="a step",
        result=result,
        doc_string=doc_string,
        rows=[row],
    )
    assert step.name == "a step"

    hook = Hook(match=match, result=result)
    assert hook.result.status == Status.passed

    element = Element(
        id="scenario-1",
        keyword="Scenario",
        name="Test Scenario",
        line=1.0,
        type=ElementType.scenario,
        steps=[step],
        tags=[tag],
        before=[hook],
        after=[hook],
    )
    assert element.name == "Test Scenario"
    assert element.type == ElementType.scenario

    feature = Feature(
        uri="features/test.feature",
        id="test-feature",
        line=1.0,
        keyword="Feature",
        name="Test Feature",
        description="A feature description",
        elements=[element],
        tags=[tag],
    )
    assert feature.name == "Test Feature"
    assert len(feature.elements or []) == 1

    cuke_json = CucumberJson(implementation="pytest-bdd-ng", features=[feature])
    assert cuke_json.implementation == "pytest-bdd-ng"
    assert len(cuke_json.features or []) == 1
