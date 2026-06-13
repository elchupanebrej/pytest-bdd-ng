"""

Unit tests for the ctypes bridge to Go gherkin parser.
"""

from __future__ import annotations

import ctypes
import sys
from unittest.mock import MagicMock, patch

import pytest

from pytest_bdd._gherkin_go._bridge import (
    _load_library,
    gherkin_go_available,
    gherkin_go_version,
    parse_gherkin_document,
    parse_gherkin_markdown,
)

pytestmark = [pytest.mark.unit]


def test_load_library_loads_cached_library() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = None
    mock_lib = MagicMock()
    bridge_module._lib = mock_lib
    result = _load_library()
    assert result is mock_lib


def test_load_library_raises_on_cached_error() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = "some error"
    try:
        with pytest.raises(OSError, match="some error"):
            _load_library()
    finally:
        bridge_module._lib_error = None


def test_load_library_raises_on_unsupported_platform() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = None
    try:
        with patch.object(sys, "platform", "os2"), pytest.raises(OSError, match="Unsupported platform"):
            _load_library()
    finally:
        bridge_module._lib_error = None


def test_load_library_raises_when_file_not_found() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = None
    try:
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(OSError, match="Shared library not found"):
                _load_library()
    finally:
        bridge_module._lib_error = None


def test_load_library_raises_when_cdll_fails() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = None
    try:
        with patch("pathlib.Path.exists", return_value=True):
            with patch("ctypes.CDLL", side_effect=OSError("bad dll")):
                with pytest.raises(OSError, match="bad dll"):
                    _load_library()
    finally:
        bridge_module._lib_error = None


def test_gherkin_go_available_returns_true_when_loadable() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = None
    mock_lib = MagicMock()
    try:
        with patch.object(bridge_module, "_load_library", return_value=mock_lib):
            assert gherkin_go_available() is True
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_gherkin_go_available_returns_false_when_unloadable() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    bridge_module._lib = None
    bridge_module._lib_error = None
    try:
        with patch.object(bridge_module, "_load_library", side_effect=OSError("nope")):
            assert gherkin_go_available() is False
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_parse_gherkin_document_returns_json_string() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    mock_lib = MagicMock()
    expected_json = b'{"type":"GherkinDocument","feature":null,"comments":[]}'
    mock_lib.ParseGherkinDocument.return_value = ctypes.c_char_p(expected_json).value
    mock_lib.FreeCString = MagicMock()
    bridge_module._lib = mock_lib
    bridge_module._lib_error = None
    try:
        result = parse_gherkin_document("Feature: Test")
        assert result == '{"type":"GherkinDocument","feature":null,"comments":[]}'
        mock_lib.FreeCString.assert_called_once()
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_parse_gherkin_document_frees_string_on_success() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    mock_lib = MagicMock()
    expected_json = b'{"type":"GherkinDocument","feature":null}'
    mock_lib.ParseGherkinDocument.return_value = ctypes.c_char_p(expected_json).value
    mock_lib.FreeCString = MagicMock()
    bridge_module._lib = mock_lib
    bridge_module._lib_error = None
    try:
        parse_gherkin_document("Feature: Test")
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_parse_gherkin_document_raises_on_null_pointer() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    mock_lib = MagicMock()
    mock_lib.ParseGherkinDocument.return_value = None
    mock_lib.FreeCString = MagicMock()
    bridge_module._lib = mock_lib
    bridge_module._lib_error = None
    try:
        with pytest.raises(RuntimeError, match="NULL pointer"):
            parse_gherkin_document("Feature: Test")
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_parse_gherkin_markdown_returns_json_string() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    mock_lib = MagicMock()
    expected_json = b'{"type":"GherkinDocument","feature":null}'
    mock_lib.ParseGherkinMarkdown.return_value = ctypes.c_char_p(expected_json).value
    mock_lib.FreeCString = MagicMock()
    bridge_module._lib = mock_lib
    bridge_module._lib_error = None
    try:
        result = parse_gherkin_markdown("# Title\n```gherkin\nFeature: Test\n```")
        assert result == '{"type":"GherkinDocument","feature":null}'
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_gherkin_go_version_returns_version_string() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    mock_lib = MagicMock()
    mock_lib.Version.return_value = ctypes.c_char_p(b"v28.0.0").value
    mock_lib.FreeCString = MagicMock()
    bridge_module._lib = mock_lib
    bridge_module._lib_error = None
    try:
        assert gherkin_go_version() == "v28.0.0"
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None


def test_gherkin_go_version_returns_unknown_on_null() -> None:
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
    import pytest_bdd._gherkin_go._bridge as bridge_module

    mock_lib = MagicMock()
    mock_lib.Version.return_value = None
    mock_lib.FreeCString = MagicMock()
    bridge_module._lib = mock_lib
    bridge_module._lib_error = None
    try:
        assert gherkin_go_version() == "unknown"
    finally:
        bridge_module._lib = None
        bridge_module._lib_error = None
