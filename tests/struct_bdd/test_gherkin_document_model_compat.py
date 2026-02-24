from __future__ import annotations

from pytest_bdd.model.gherkin_document import Feature


def test_gherkin_document_feature_import_compatibility() -> None:
    assert Feature is not None
    assert Feature.__name__ == "Feature"
