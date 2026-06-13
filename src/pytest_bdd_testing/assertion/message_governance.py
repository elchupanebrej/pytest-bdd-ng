"""
Governance assertion primitives backed by PyHamcrest matchers.

Every function uses `hamcrest.assert_that` for expressive failure messages.
"""

from __future__ import annotations

from typing import TypeVar

from hamcrest import assert_that, empty, equal_to, has_item, is_not, none

T = TypeVar("T")


def assert_unique(values: list[T]) -> None:
    """Assert that all elements in a list are distinct (no duplicates)."""
    assert_that(
        len(values),
        equal_to(len(set(values))),
        "values must be unique",
    )


def assert_contains_all(values: set[str], expected: set[str]) -> None:
    """Assert that the values set is a superset of the expected set."""
    for item in expected:
        assert_that(
            values,
            has_item(item),
            f"Missing expected value: {item!r}",
        )


def assert_non_empty_text(value: str | None, *, field_name: str) -> None:
    """Assert that a string value is neither None nor blank."""
    assert_that(
        value,
        is_not(none()),
        f"{field_name} must be non-empty",
    )
    assert_that(
        value.strip(),  # type: ignore[union-attr]  # none() guard ensures str
        is_not(empty()),
        f"{field_name} must be non-empty",
    )
