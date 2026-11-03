"""Integration tests for empty localized heading validation (G23)."""

from __future__ import annotations

from pathlib import Path
import pytest

from pytest_cuke.heading_scanner import (
    HeadingValidationCollectionError,
    enforce_feature_heading_policy,
    run_heading_validation_scan,
)
from pytest_cuke.heading_validation import EMPTY_HEADING_TITLE_CODE, HeadingType
from pytest_cuke.parser import GherkinParser


pytestmark = pytest.mark.integration


def test_english_empty_scenario_heading_rejected(tmp_path: Path) -> None:
    feature_file = tmp_path / "english.feature"
    feature_file.write_text(
        """\
Feature: English test
  Scenario:
    Given a working step
""",
        encoding="utf-8",
    )
    run = run_heading_validation_scan(tmp_path)
    assert run.status == "fail"
    violations = [v for v in run.violations if v.heading_type == HeadingType.SCENARIO]
    assert len(violations) == 1
    assert violations[0].code == EMPTY_HEADING_TITLE_CODE
    assert violations[0].line == 2


def test_french_empty_scenario_heading_rejected(tmp_path: Path) -> None:
    feature_file = tmp_path / "french.feature"
    feature_file.write_text(
        """\
# language: fr
Fonctionnalité: Test français
  Scénario:
    Etant donné une étape
""",
        encoding="utf-8",
    )
    run = run_heading_validation_scan(tmp_path)
    assert run.status == "fail"
    violations = [v for v in run.violations if v.heading_type == HeadingType.SCENARIO]
    assert len(violations) == 1
    assert violations[0].code == EMPTY_HEADING_TITLE_CODE
    assert violations[0].line == 3


def test_whitespace_only_scenario_heading_rejected(tmp_path: Path) -> None:
    feature_file = tmp_path / "whitespace.feature"
    feature_file.write_text(
        """\
Feature: Whitespace scenario
  Scenario:    \t  
    Given a step
""",
        encoding="utf-8",
    )
    run = run_heading_validation_scan(tmp_path)
    assert run.status == "fail"
    violations = [v for v in run.violations if v.heading_type == HeadingType.SCENARIO]
    assert len(violations) == 1
    assert violations[0].code == EMPTY_HEADING_TITLE_CODE
    assert violations[0].line == 2


def test_empty_feature_heading_rejected(tmp_path: Path) -> None:
    feature_file = tmp_path / "empty_feature.feature"
    feature_file.write_text(
        """\
Feature:   
  Scenario: Valid scenario
    Given a step
""",
        encoding="utf-8",
    )
    run = run_heading_validation_scan(tmp_path)
    assert run.status == "fail"
    violations = [v for v in run.violations if v.heading_type == HeadingType.FEATURE]
    assert len(violations) == 1
    assert violations[0].code == EMPTY_HEADING_TITLE_CODE
    assert violations[0].line == 1


def test_strict_collection_enforcement_rejects_empty_localized_headings() -> None:
    parser = GherkinParser()
    feature = parser.parse_text(
        """\
# language: fr
Fonctionnalité: Test français
  Scénario:
    Etant donné une étape
""",
        uri="french.feature",
    )
    with pytest.raises(HeadingValidationCollectionError) as exc_info:
        enforce_feature_heading_policy(feature, "french.feature")

    assert exc_info.value.violation.code == EMPTY_HEADING_TITLE_CODE
    assert exc_info.value.violation.line == 3
