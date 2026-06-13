"""

Integration tests for Go gherkin parser collection.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest


def test_go_parser_integration_parse_feature_file_uses_python_when_go_unavailable() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    E2E/Acceptance test
    Test scenario:
    Given the relevant preconditions are met, when Maintain compatibility between the native Go-based Gherkin parser
        and Python fallback implementations., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}):
        from pytest_bdd.collector_batch import _parse_feature_file

        result = _parse_feature_file(
            Path("/fake/test.feature"),
            b"Feature: Test\n  Scenario: Example\n    Given nothing",
        )
        assert result[0] == Path("/fake/test.feature")
        assert result[1].feature is not None
        assert result[1].feature.name == "Test"


def test_go_parser_integration_parse_feature_file_python_mode_explicit() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    E2E/Acceptance test
    Test scenario:
    Given the relevant preconditions are met, when Maintain compatibility between the native Go-based Gherkin parser
        and Python fallback implementations., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
        from pytest_bdd.collector_batch import _parse_feature_file

        result = _parse_feature_file(
            Path("/fake/test.feature"),
            b"Feature: Test\n  Scenario: Example\n    Given nothing",
        )
        assert result[1].feature.name == "Test"


def test_go_parser_integration_parse_feature_file_invalid_gherkin_raises() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    E2E/Acceptance test
    Test scenario:
    Given the relevant preconditions are met, when Maintain compatibility between the native Go-based Gherkin parser
        and Python fallback implementations., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    from gherkin.errors import CompositeParserException

    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
        from pytest_bdd.collector_batch import _parse_feature_file

        with pytest.raises(CompositeParserException):
            _parse_feature_file(
                Path("/fake/test.feature"),
                b"not valid gherkin",
            )


def test_go_parser_integration_go_mode_raises_when_unavailable() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    E2E/Acceptance test
    Test scenario:
    Given the relevant preconditions are met, when Maintain compatibility between the native Go-based Gherkin parser
        and Python fallback implementations., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
        from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable
        from pytest_bdd.collector_batch import _parse_feature_file

        with pytest.raises(GherkinGoNotAvailable):
            _parse_feature_file(
                Path("/fake/test.feature"),
                b"Feature: Test",
            )
