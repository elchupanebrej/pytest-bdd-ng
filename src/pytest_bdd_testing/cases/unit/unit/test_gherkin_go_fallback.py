"""Unit tests for backend selection and fallback behavior."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError

pytestmark = [pytest.mark.unit]


def test_backend_auto_env_var_defaults_to_auto() -> None:
    with patch.dict(os.environ, {}, clear=True):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is True


def test_backend_auto_env_var_case_insensitive() -> None:
    from pytest_bdd._gherkin_go import should_use_go_backend

    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "Auto"}):
        assert should_use_go_backend() is True


def test_backend_go_env_var_go_selects_go() -> None:
    from pytest_bdd._gherkin_go import is_strict_go_mode, should_use_go_backend

    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
        assert should_use_go_backend() is True
        assert is_strict_go_mode() is True


def test_backend_go_go_mode_raises_on_unavailable() -> None:

    with (
        patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}),
        patch("pytest_bdd._gherkin_go._bridge.gherkin_go_available", return_value=False),
    ):
        from pytest_bdd._gherkin_go import parse

        with pytest.raises(GherkinGoNotAvailable):
            parse("Feature: Test")


def test_backend_python_env_var_python_selects_python() -> None:
    from pytest_bdd._gherkin_go import should_use_go_backend

    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
        assert should_use_go_backend() is False


def test_backend_python_python_mode_skips_go_import() -> None:
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is False


def test_collector_batch_integration_should_use_go_backend_auto() -> None:
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}, clear=True):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is True


def test_collector_batch_integration_should_use_go_backend_go() -> None:
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}, clear=True):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is True


def test_collector_batch_integration_should_use_go_backend_python() -> None:
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}, clear=True):
        from pytest_bdd._gherkin_go import should_use_go_backend

        assert should_use_go_backend() is False


def test_collector_batch_integration_resolve_mimetype_plain() -> None:
    from pytest_bdd.collector_batch import _resolve_mimetype

    assert _resolve_mimetype(Path("/x/test.feature")) == "text/x.cucumber.gherkin+plain"


def test_collector_batch_integration_resolve_mimetype_markdown() -> None:
    from pytest_bdd.collector_batch import _resolve_mimetype

    assert _resolve_mimetype(Path("/x/test.feature.md")) == "text/x.cucumber.gherkin+markdown"


def test_collector_batch_integration_try_go_parse_returns_none_when_unavailable() -> None:

    with (
        patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}),
        patch("pytest_bdd._gherkin_go._bridge.gherkin_go_available", return_value=False),
    ):
        from pytest_bdd._gherkin_go import parse

        with pytest.raises(GherkinGoNotAvailable):
            parse("Feature: Test")


def test_collector_batch_integration_strict_go_mode_raises() -> None:
    with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
        from pytest_bdd._gherkin_go import is_strict_go_mode

        assert is_strict_go_mode() is True


def test_try_go_parse_gherkin_parse_error_injects_uri_and_reraises() -> None:
    import pytest_bdd._gherkin_go as go_mod

    with patch.object(go_mod, "parse") as mock_parse:
        mock_parse.side_effect = GherkinParseError(
            [{"source": {"uri": "", "location": {"line": 3, "column": 1}}, "message": "bad syntax"}],
        )
        with pytest.raises(GherkinParseError):
            go_mod.parse("Feature: Test", uri=str(Path("/x/test.feature")))


def test_try_go_parse_runtime_error_falls_back_in_auto_mode() -> None:
    import pytest_bdd._gherkin_go as go_mod

    with patch.object(go_mod, "parse", side_effect=RuntimeError("Go crashed")):
        with pytest.raises(RuntimeError, match="Go crashed"):
            go_mod.parse("Feature: Test")


def test_try_go_parse_os_error_falls_back_in_auto_mode() -> None:
    import pytest_bdd._gherkin_go as go_mod

    with patch.object(go_mod, "parse", side_effect=OSError("library missing")):
        with pytest.raises(OSError, match="library missing"):
            go_mod.parse("Feature: Test")
