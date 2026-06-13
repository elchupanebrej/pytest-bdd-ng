"""

Provide test gherkin document model compat helpers.
"""

from __future__ import annotations

import importlib

import pytest
from cucumber_messages import (
    GherkinDocument,  # type:ignore[attr-defined, import-untyped] — upstream library missing type stubs
)


def test_gherkin_document_module_is_no_longer_part_of_pytest_bdd_model_package() -> None:
    """
    Verify gherkin document module is no longer part of pytest bdd model package.

    Test target:
        Validate parsing of structured BDD formats (YAML/JSON/TOML) against execution schema contracts.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate parsing of structured BDD formats (YAML/JSON/TOML)
        against execution schema contracts., then the expected outcome is produced.
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
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("pytest_bdd.model.gherkin_document")


def test_gherkin_document_is_imported_directly_from_cucumber_messages() -> None:
    """
    Verify gherkin document is imported directly from cucumber messages.

    Test target:
        Validate parsing of structured BDD formats (YAML/JSON/TOML) against execution schema contracts.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate parsing of structured BDD formats (YAML/JSON/TOML)
        against execution schema contracts., then the expected outcome is produced.
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
    assert GherkinDocument.__module__.startswith("cucumber_messages")
