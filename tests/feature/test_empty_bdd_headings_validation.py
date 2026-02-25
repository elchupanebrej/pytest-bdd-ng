from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from pytest_bdd.model.heading_validation import HeadingType
from pytest_bdd.script.validate_feature_headings import run_heading_validation_scan


def _write_feature(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_detects_empty_parsed_feature_heading(tmp_path: Path) -> None:
    _write_feature(
        tmp_path / "empty_feature.feature",
        """
        Feature:
          Scenario: Named scenario
            Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "fail"
    assert len(run.violations) == 1
    violation = run.violations[0]
    assert violation.heading_type is HeadingType.FEATURE
    assert violation.path == "empty_feature.feature"


def test_detects_empty_parsed_scenario_and_scenario_outline_headings(tmp_path: Path) -> None:
    _write_feature(
        tmp_path / "empty_scenarios.feature",
        """
        Feature: Named feature
          Scenario:
            Given step

          Scenario Outline:
            Given <value>
            Examples:
              | value |
              | data  |
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "fail"
    heading_types = [violation.heading_type for violation in run.violations]
    assert heading_types.count(HeadingType.SCENARIO) == 1
    assert heading_types.count(HeadingType.SCENARIO_OUTLINE) == 1


def test_validation_passes_for_non_empty_headings(tmp_path: Path) -> None:
    _write_feature(
        tmp_path / "valid.feature",
        """
        Feature: Named feature
          Scenario: Named scenario
            Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "pass"
    assert run.violations == ()
