"""BDD acceptance steps for StructBDD joined example tables."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_cuke import given, then, when
from pytest_cuke.compatibility.struct_bdd import STRUCT_BDD_INSTALLED


@given("StructBDD example tables share a parameter", target_fixture="example_tables")
def example_tables() -> list[Any]:
    if not STRUCT_BDD_INSTALLED:
        pytest.skip("StructBDD is not installed")

    from pytest_cuke.struct_bdd.model import Table

    return [
        Table(
            parameters=["plan", "account"],
            values=[
                ["free", "north"],
                ["pro", "south"],
            ],
        ),
        Table(
            parameters=["region", "plan"],
            values=[
                ["us", "free"],
                ["eu", "pro"],
                ["apac", "pro"],
            ],
        ),
    ]


@when("the examples are joined", target_fixture="joined_examples")
def joined_examples(example_tables: list[Any]) -> Any:
    from pytest_cuke.struct_bdd.model import Join

    return Join(tables=example_tables)


@then("only rows with matching shared parameter values remain")
def joined_examples_keep_matching_rows(joined_examples: Any) -> None:
    assert joined_examples.parameters == ["plan", "account", "region"]
    assert joined_examples.values == [
        ["free", "north", "us"],
        ["pro", "south", "eu"],
        ["pro", "south", "apac"],
    ]
