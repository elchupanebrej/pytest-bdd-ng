"""Provide test standalone rendering boundary contract helpers."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd.plugin.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer import StandaloneCucumberFormatterRenderer

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "contract" / "fixtures" / "standalone_rendering_boundary.md"
)
STANDALONE_RENDERER_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "pytest_bdd"
    / "plugin"
    / "gherkin_message_reporter"
    / "standalone_renderer.py"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _standalone_renderer_source() -> str:
    return STANDALONE_RENDERER_PATH.read_text(encoding="utf-8")


def test_standalone_rendering_boundary_contract_exists() -> None:
    """Verify standalone rendering boundary contract exists."""
    assert CONTRACT_PATH.exists()


def test_standalone_rendering_boundary_contract_forbids_synthetic_pytest_runtime() -> None:
    """Verify standalone rendering boundary contract forbids synthetic pytest runtime."""
    contract_text = _contract_text()

    assert "must not require a synthetic pytest `Config` object" in contract_text
    assert "must not require ad hoc construction of a pytest" in contract_text
    assert "must use one explicit supported" in contract_text


def test_standalone_renderer_uses_explicit_application_service_boundary() -> None:
    """Verify standalone renderer uses explicit application service boundary."""
    renderer = StandaloneCucumberFormatterRenderer.discover(catalog=FormatterPluginCatalog.discover())

    assert isinstance(renderer, StandaloneCucumberFormatterRenderer)
    assert hasattr(renderer, "resolve_requests")
    assert hasattr(renderer, "render_from_messages_path")


def test_standalone_renderer_source_does_not_construct_synthetic_pytest_runtime() -> None:
    """Verify standalone renderer source does not construct synthetic pytest runtime."""
    standalone_renderer_source = _standalone_renderer_source()

    assert "SimpleNamespace" not in standalone_renderer_source
    assert "PytestPluginManager" not in standalone_renderer_source
    assert "from_config(" not in standalone_renderer_source
