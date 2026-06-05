"""Provide message governance assertions helpers."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def _raise_assertion(message: str) -> None:
    """
    Raise an assertion failure.

    Raises:
        AssertionError: Always raised with the provided message.

    """
    raise AssertionError(message)


def assert_unique(values: list[T]) -> None:
    """Assert unique."""
    if len(values) != len(set(values)):
        msg = "values must be unique"
        _raise_assertion(msg)


def assert_contains_all(values: set[str], expected: set[str]) -> None:
    """Assert contains all."""
    missing = expected.difference(values)
    if missing:
        msg = f"Missing expected values: {sorted(missing)}"
        _raise_assertion(msg)


def assert_non_empty_text(value: str | None, *, field_name: str) -> None:
    """Assert non empty text."""
    if value is None:
        msg = f"{field_name} must be non-empty"
        _raise_assertion(msg)
    if not value.strip():
        msg = f"{field_name} must be non-empty"
        _raise_assertion(msg)
