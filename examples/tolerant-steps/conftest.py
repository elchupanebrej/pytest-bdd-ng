from pathlib import Path

from pytest_cuke import then, when
from pytest_cuke.steps import tolerant


@tolerant
@when("an audited operation fails")
def audited_operation_fails() -> None:
    raise AssertionError("first tolerant assertion sentinel")


@then("the workflow continues")
def workflow_continues() -> None:
    Path("continuations.log").write_text("continued\n", encoding="utf-8")
