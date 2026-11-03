"""Integration tests for empty localized heading validation (G23)."""

from __future__ import annotations

import pytest

from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.parser import GherkinParser


pytestmark = pytest.mark.integration


def test_english_empty_scenario_heading_rejected() -> None:
    feature_text = """\
Feature: English test
  Scenario:
    Given a working step
"""
    parser = GherkinParser()
    with pytest.raises(FeatureConcreteParseError) as exc_info:
        parser.parse_text(feature_text, uri="english.feature")

    assert "EMPTY_HEADING_TITLE" in str(exc_info.value)
    assert exc_info.value.line == 2


def test_french_empty_scenario_heading_rejected() -> None:
    feature_text = """\
# language: fr
Fonctionnalité: Test français
  Scénario:
    Etant donné une étape
"""
    parser = GherkinParser()
    with pytest.raises(FeatureConcreteParseError) as exc_info:
        parser.parse_text(feature_text, uri="french.feature")

    assert "EMPTY_HEADING_TITLE" in str(exc_info.value)
    assert exc_info.value.line == 3


def test_whitespace_only_scenario_heading_rejected() -> None:
    feature_text = """\
Feature: Whitespace scenario
  Scenario:    \t  
    Given a step
"""
    parser = GherkinParser()
    with pytest.raises(FeatureConcreteParseError) as exc_info:
        parser.parse_text(feature_text, uri="whitespace.feature")

    assert "EMPTY_HEADING_TITLE" in str(exc_info.value)


def test_empty_feature_heading_rejected() -> None:
    feature_text = """\
Feature:   
  Scenario: Valid scenario
    Given a step
"""
    parser = GherkinParser()
    with pytest.raises(FeatureConcreteParseError) as exc_info:
        parser.parse_text(feature_text, uri="empty_feature.feature")

    assert "EMPTY_HEADING_TITLE" in str(exc_info.value)


def test_pytest_run_rejects_empty_localized_headings(testdir) -> None:
    testdir.makefile(
        ".feature",
        french="""\
# language: fr
Fonctionnalité: Test français
  Scénario:
    Etant donné une étape
""",
    )
    result = testdir.runpytest()
    assert result.ret != 0
    result.stdout.fnmatch_lines(["*EMPTY_HEADING_TITLE*"])
