"""Provide test report doc gathering html helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd import scenario

pytestmark = [pytest.mark.slow]


@scenario(
    Path(__file__).resolve().parents[5] / "features" / "07 Report" / "02 Gathering.feature.md",
    "HTML report could be produced on the feature run",
)
def test_html_report_generation_from_markdown_doc():
    """Verify html report generation from markdown doc."""
