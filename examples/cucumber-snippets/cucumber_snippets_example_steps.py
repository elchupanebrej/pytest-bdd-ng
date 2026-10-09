"""Public-facade step definitions used by the Cucumber snippets example."""

from __future__ import annotations

from pytest_cuke import given


@given("the snippets example is ready")
def snippets_example_is_ready() -> None:
    """This passing setup step is omitted from the undefined-step suggestions."""
