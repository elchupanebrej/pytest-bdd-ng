"""Public-facade step definitions used by the Cucumber progress-bar example."""

from __future__ import annotations

from pytest_cuke import given


@given("the progress-bar example is ready")
def progress_bar_example_is_ready() -> None:
    """Represent one successfully completed example scenario."""
