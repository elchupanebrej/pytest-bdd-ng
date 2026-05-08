"""Provide test report doc cucumber formatters helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd import scenario

pytestmark = [pytest.mark.slow]

_FEATURE_PATH = (
    Path(__file__).resolve().parents[2] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
)


@scenario(_FEATURE_PATH, "Existing NDJSON can be post-processed into formatter outputs")
def test_existing_ndjson_can_be_post_processed_into_formatter_outputs() -> None:
    """Keep standalone replay coverage targeted here; the broad sweep owns the live formatter scenarios."""
