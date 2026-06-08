"""Provide test gherkin document model compat helpers."""

from __future__ import annotations

import importlib

import pytest
from cucumber_messages import (
    GherkinDocument,  # type:ignore[attr-defined, import-untyped] — upstream library missing type stubs
)


def test_gherkin_document_module_is_no_longer_part_of_pytest_bdd_model_package() -> None:
    """Verify gherkin document module is no longer part of pytest bdd model package."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("pytest_bdd.model.gherkin_document")


def test_gherkin_document_is_imported_directly_from_cucumber_messages() -> None:
    """Verify gherkin document is imported directly from cucumber messages."""
    assert GherkinDocument.__module__.startswith("cucumber_messages")
