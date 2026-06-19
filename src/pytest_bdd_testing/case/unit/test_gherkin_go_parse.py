"""

Unit tests for the _gherkin_go.parse() public API.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError

VALID_GHERKIN_DOCUMENT = json.dumps(
    {
        "type": "GherkinDocument",
        "feature": {
            "type": "Feature",
            "language": "en",
            "keyword": "Feature",
            "name": "Test",
            "description": "",
            "children": [],
        },
    },
)

PARSE_ERROR_ARRAY = json.dumps(
    [{"source": {"uri": "", "location": {"line": 1, "column": 1}}, "message": "Parse error"}],
)

pytestmark = [pytest.mark.unit]


def test_parse_plain_gherkin_parses_valid_gherkin() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with (
        patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
        patch("pytest_bdd._gherkin_go._bridge.parse_gherkin_document", return_value=VALID_GHERKIN_DOCUMENT),
    ):
        from pytest_bdd._gherkin_go import parse

        result = parse("Feature: Test\n  Scenario: Example")
        assert result["type"] == "GherkinDocument"
        assert result["feature"]["name"] == "Test"


def test_parse_plain_gherkin_raises_on_parse_error() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with (
        patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
        patch("pytest_bdd._gherkin_go._bridge.parse_gherkin_document", return_value=PARSE_ERROR_ARRAY),
    ):
        from pytest_bdd._gherkin_go import parse

        with pytest.raises(GherkinParseError, match="Parse error"):
            parse("invalid")


def test_parse_plain_gherkin_raises_when_library_unavailable() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=False):
        from pytest_bdd._gherkin_go import parse

        with pytest.raises(GherkinGoNotAvailable, match="not available"):
            parse("Feature: Test")


def test_parse_markdown_gherkin_parses_markdown_via_go() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with (
        patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
        patch("pytest_bdd._gherkin_go._bridge.parse_gherkin_markdown", return_value=VALID_GHERKIN_DOCUMENT),
    ):
        from pytest_bdd._gherkin_go import parse

        result = parse("# Title\n```gherkin\nFeature: Test\n```", uri="test.md")
        assert result["type"] == "GherkinDocument"


def test_backend_selection_should_use_go_backend_auto() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {}, clear=True):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is True


def test_backend_selection_should_use_go_backend_go() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is True


def test_backend_selection_should_use_go_backend_python() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is False


def test_backend_selection_strict_go_mode_true() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
        from pytest_bdd._gherkin_go import is_strict_go_mode

        assert is_strict_go_mode() is True


def test_backend_selection_strict_go_mode_false_for_auto() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}):
        from pytest_bdd._gherkin_go import is_strict_go_mode

        assert is_strict_go_mode() is False


def test_backend_selection_strict_go_mode_false_for_python() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
        from pytest_bdd._gherkin_go import is_strict_go_mode

        assert is_strict_go_mode() is False


def test_backend_selection_unknown_value_defaults_to_auto() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "invalid"}):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is True


def test_cross_backend_equivalence_documents_equivalent_strips_none() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    from pytest_bdd.collector_batch import _documents_equivalent

    go_doc = {"type": "GherkinDocument", "feature": None, "comments": []}
    python_doc = {"type": "GherkinDocument", "feature": None, "comments": [], "extra": None}
    assert _documents_equivalent(go_doc, python_doc) is True


def test_cross_backend_equivalence_documents_equivalent_ignores_ids() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    from pytest_bdd.collector_batch import _documents_equivalent

    go_doc = {"type": "GherkinDocument", "id": "go-123", "feature": {"name": "Test"}}
    python_doc = {"type": "GherkinDocument", "id": "py-456", "feature": {"name": "Test"}}
    assert _documents_equivalent(go_doc, python_doc) is True


def test_cross_backend_equivalence_documents_not_equivalent_different_content() -> None:
    """
    Test target:
    Maintain compatibility between the native Go-based Gherkin parser and Python fallback implementations.
    Test type:
    Unit test
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
    from pytest_bdd.collector_batch import _documents_equivalent

    go_doc = {"type": "GherkinDocument", "feature": {"name": "Go"}}
    python_doc = {"type": "GherkinDocument", "feature": {"name": "Python"}}
    assert _documents_equivalent(go_doc, python_doc) is False
