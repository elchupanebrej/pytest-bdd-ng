"""Provide test heading validation diagnostics helpers."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from pytest_bdd.model.heading_validation import EMPTY_HEADING_TITLE_CODE, HeadingType
from pytest_bdd.script.validate_feature_headings import run_heading_validation_scan


def _write_markdown_feature(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_violation_payload_fields_are_stable(tmp_path: Path) -> None:
    """Verify violation payload fields are stable."""
    _write_markdown_feature(
        tmp_path / "sample.feature.md",
        """
        # Feature: Diagnostic feature
        ## Scenario:
        * Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "fail"
    violation = run.violations[0]
    payload = violation.to_payload()

    assert payload["path"] == "sample.feature.md"
    assert payload["line"] == 2
    assert payload["heading_type"] == HeadingType.SCENARIO.value
    assert payload["code"] == EMPTY_HEADING_TITLE_CODE
    assert "empty after trimming whitespace" in str(payload["message"])


def test_violations_are_sorted_by_path_then_line(tmp_path: Path) -> None:
    """Verify violations are sorted by path then line."""
    _write_markdown_feature(
        tmp_path / "b.feature.md",
        """
        # Feature: B feature
        ## Scenario:
        * Given step
        """,
    )
    _write_markdown_feature(
        tmp_path / "a.feature.md",
        """
        # Feature: A feature
        ## Scenario:
        * Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert [violation.path for violation in run.violations] == ["a.feature.md", "b.feature.md"]
