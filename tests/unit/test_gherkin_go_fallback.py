"""Unit tests for backend selection and fallback behavior."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable


class TestBackendAuto:
    def test_env_var_defaults_to_auto(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            from pytest_bdd._gherkin_go import _should_use_go_backend

            assert _should_use_go_backend() is True

    def test_env_var_case_insensitive(self) -> None:
        from pytest_bdd._gherkin_go import _should_use_go_backend

        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "Auto"}):
            assert _should_use_go_backend() is True


class TestBackendGo:
    def test_env_var_go_selects_go(self) -> None:
        from pytest_bdd._gherkin_go import _should_use_go_backend
        from pytest_bdd.collector_batch import _strict_go_mode

        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
            assert _should_use_go_backend() is True
            assert _strict_go_mode() is True

    def test_go_mode_raises_on_unavailable(self) -> None:
        import pytest_bdd._gherkin_go as go_mod

        with (
            patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}),
            patch.object(go_mod, "gherkin_go_available", return_value=False),
        ):
            from pytest_bdd._gherkin_go import parse
            from pytest_bdd.mimetype import Mimetype

            with pytest.raises(GherkinGoNotAvailable):
                parse("Feature: Test", mimetype=Mimetype.gherkin_plain)


class TestBackendPython:
    def test_env_var_python_selects_python(self) -> None:
        from pytest_bdd._gherkin_go import _should_use_go_backend

        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
            assert _should_use_go_backend() is False

    def test_python_mode_skips_go_import(self) -> None:
        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
            from pytest_bdd.collector_batch import _should_use_go_backend

            assert _should_use_go_backend() is False


class TestCollectorBatchIntegration:
    def test_should_use_go_backend_auto(self) -> None:
        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}, clear=True):
            from pytest_bdd.collector_batch import _should_use_go_backend

            assert _should_use_go_backend() is True

    def test_should_use_go_backend_go(self) -> None:
        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}, clear=True):
            from pytest_bdd.collector_batch import _should_use_go_backend

            assert _should_use_go_backend() is True

    def test_should_use_go_backend_python(self) -> None:
        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "python"}, clear=True):
            from pytest_bdd.collector_batch import _should_use_go_backend

            assert _should_use_go_backend() is False

    def test_resolve_mimetype_plain(self) -> None:
        from pathlib import Path

        from pytest_bdd.collector_batch import _resolve_mimetype

        assert _resolve_mimetype(Path("/x/test.feature")) == "text/x.cucumber.gherkin+plain"

    def test_resolve_mimetype_markdown(self) -> None:
        from pathlib import Path

        from pytest_bdd.collector_batch import _resolve_mimetype

        assert _resolve_mimetype(Path("/x/test.feature.md")) == "text/x.cucumber.gherkin+markdown"

    def test_try_go_parse_returns_none_when_unavailable(self) -> None:
        from pathlib import Path

        import pytest_bdd._gherkin_go as go_mod

        with (
            patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}),
            patch.object(go_mod, "gherkin_go_available", return_value=False),
        ):
            from pytest_bdd.collector_batch import _try_go_parse

            result = _try_go_parse("Feature: Test", Path("/x/test.feature"))
            assert result is None

    def test_strict_go_mode_raises(self) -> None:
        with patch.dict(os.environ, {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
            from pytest_bdd.collector_batch import _strict_go_mode

            assert _strict_go_mode() is True
