from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def assert_unique(values: list[T]) -> None:
    assert len(values) == len(set(values))


def assert_contains_all(values: set[str], expected: set[str]) -> None:
    missing = expected.difference(values)
    assert not missing, f"Missing expected values: {sorted(missing)}"


def assert_non_empty_text(value: str | None, *, field_name: str) -> None:
    assert value is not None, f"{field_name} must be non-empty"
    assert value.strip(), f"{field_name} must be non-empty"
