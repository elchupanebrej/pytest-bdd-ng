"""Provide test heading validation snippet boundaries helpers."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from pytest_bdd.script.validate_feature_headings import run_heading_validation_scan


def _write_markdown_feature(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_validation_ignores_indented_literal_keyword_lines(tmp_path: Path) -> None:
    """Verify validation ignores indented literal keyword lines."""
    _write_markdown_feature(
        tmp_path / "indented.feature.md",
        """
        # Feature: Indented literal boundary
        ## Scenario: Parsed heading
        * Given step

            Feature:
              Scenario:
                Given this snippet must not be parsed as heading
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "pass"
    assert run.violations == ()


def test_validation_ignores_fenced_gherkin_snippets(tmp_path: Path) -> None:
    """Verify validation ignores fenced gherkin snippets."""
    _write_markdown_feature(
        tmp_path / "fenced.feature.md",
        """
        # Feature: Fenced block boundary
        ## Scenario: Parsed heading
        * Given step

        ```gherkin
        Feature:
          Scenario:
            Given snippet should stay ignored
        ```
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "pass"
    assert run.violations == ()
