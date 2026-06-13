"""Cucumber formatter output assertions backed by PyHamcrest."""

from __future__ import annotations

from hamcrest import assert_that, contains_string, empty, is_not

from pytest_bdd_testing.tool.cucumber_formatter.registry import (
    _SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS,
    expected_formatter_visible_line,
)


def assert_pytest_terminal_reporter_suppressed(output: str) -> None:
    """Assert that no known pytest terminal reporter fragments appear in output."""
    unexpected = [f for f in _SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS if f in output]
    assert_that(
        unexpected,
        empty(),
        f"Expected pytest terminal reporter output to be suppressed, but found: {unexpected!r}",
    )


def assert_pytest_terminal_reporter_visible(output: str) -> None:
    """Assert that at least one pytest terminal reporter fragment appears in output."""
    expected = [f for f in _SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS if f in output]
    assert_that(
        expected,
        is_not(empty()),
        "Expected pytest terminal reporter output to be visible, but no known terminal fragments were found.",
    )


def assert_formatter_output_is_not_mixed_with_pytest_terminal(output: str, *, formatter_name: str) -> None:
    """Assert formatter output is present AND pytest terminal output is suppressed."""
    assert_that(
        output,
        contains_string(expected_formatter_visible_line(formatter_name)),
        output,
    )
    assert_pytest_terminal_reporter_suppressed(output)
