"""Provide test jinja2 doc generation contract helpers."""

from pathlib import Path

import yaml

CONTRACT_PATH = (
    Path(__file__).resolve().parents[5]
    / "specs"
    / "004-migrate-jinja2-docs"
    / "contracts"
    / "jinja2-doc-generation.openapi.yaml"
)


def test_jinja2_doc_generation_contract_exists() -> None:
    """Verify jinja2 doc generation contract exists."""
    assert CONTRACT_PATH.exists()


def test_jinja2_doc_generation_contract_has_required_paths() -> None:
    """Verify jinja2 doc generation contract has required paths."""
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    paths = data["paths"]

    assert "/generation/templates" in paths
    assert "/generation/render/code" in paths
    assert "/generation/render/docs" in paths
    assert "/docs/features/index" in paths
    assert "/validation/parity" in paths
    assert "/validation/doc-sync" in paths
    assert "/validation/packaging/templates" in paths


def test_jinja2_doc_generation_contract_has_required_schemas() -> None:
    """Verify jinja2 doc generation contract has required schemas."""
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    schemas = data["components"]["schemas"]

    assert "TemplateAsset" in schemas
    assert "TemplateRenderContext" in schemas
    assert "GeneratedDocumentationBlock" in schemas
    assert "GenerationParityCase" in schemas
    assert "DocumentationSyncCheck" in schemas
    assert "DocumentationSyncResult" in schemas
    assert "PackagingTemplateManifest" in schemas


def test_jinja2_doc_generation_contract_declares_jinja2_engine() -> None:
    """Verify jinja2 doc generation contract declares jinja2 engine."""
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    engine_enum = data["components"]["schemas"]["TemplateAsset"]["properties"]["engine"]["enum"]

    assert "jinja2" in engine_enum


def test_jinja2_doc_generation_contract_uses_semantic_parity_mode() -> None:
    """Verify jinja2 doc generation contract uses semantic parity mode."""
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    parity_enum = data["components"]["schemas"]["GenerationParityCase"]["properties"]["parityMode"]["enum"]

    assert parity_enum == ["semantic"]
