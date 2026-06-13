"""

Provide test feature doc ordering contract helpers.
"""

from pathlib import Path

import yaml

CONTRACT_PATH = (
    Path(__file__).resolve().parents[5]
    / "specs"
    / "010-order-rst-docs"
    / "contracts"
    / "feature-doc-ordering.openapi.yaml"
)


def test_feature_doc_ordering_contract_exists() -> None:
    """
    Verify feature doc ordering contract exists.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    assert CONTRACT_PATH.exists()


def test_feature_doc_ordering_contract_has_required_paths() -> None:
    """
    Verify feature doc ordering contract has required paths.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    paths = data["paths"]

    assert "/generation/templates" in paths
    assert "/generation/index" in paths
    assert "/generation/page" in paths
    assert "/validation/ordering-prefixes" in paths
    assert "/conversion/markdown-headings" in paths


def test_feature_doc_ordering_contract_has_required_schemas() -> None:
    """
    Verify feature doc ordering contract has required schemas.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    schemas = data["components"]["schemas"]

    assert "DocumentationTemplate" in schemas
    assert "DocumentationSourceTopic" in schemas
    assert "NavigationScope" in schemas
    assert "GeneratedPage" in schemas
    assert "GeneratedIndexDocument" in schemas
    assert "OrderingValidationError" in schemas
    assert "MarkdownHeadingNormalizationRequest" in schemas


def test_feature_doc_ordering_contract_declares_navigation_scope_and_generated_page_path_fields() -> None:
    """
    Verify feature doc ordering contract declares navigation scope and generated page path fields.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    schemas = data["components"]["schemas"]

    navigation_scope = schemas["NavigationScope"]
    topic = schemas["DocumentationSourceTopic"]

    assert "ordered" in navigation_scope["required"]
    assert navigation_scope["properties"]["headingLabel"]["type"] == "string"
    assert navigation_scope["properties"]["ordered"]["type"] == "boolean"
    assert "generatedPagePath" in topic["required"]
    assert topic["properties"]["generatedPagePath"]["type"] == "string"


def test_feature_doc_ordering_contract_declares_deterministic_error_codes() -> None:
    """
    Verify feature doc ordering contract declares deterministic error codes.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    error_enum = data["components"]["schemas"]["OrderingValidationError"]["properties"]["errorCode"]["enum"]

    assert error_enum == ["missing_ordering_prefix", "duplicate_ordering_prefix"]


def test_feature_doc_ordering_contract_declares_template_responsibilities() -> None:
    """
    Verify feature doc ordering contract declares template responsibilities.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    responsibility_enum = data["components"]["schemas"]["DocumentationTemplate"]["properties"]["responsibility"]["enum"]

    assert responsibility_enum == ["index_wrapper", "section_toctree", "include_page", "page_title"]


def test_feature_doc_ordering_contract_declares_markdown_heading_normalization_converters() -> None:
    """
    Verify feature doc ordering contract declares markdown heading normalization converters.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    converter_enum = data["components"]["schemas"]["MarkdownHeadingNormalizationRequest"]["properties"][
        "preferredConverter"
    ]["enum"]

    assert converter_enum == ["pandoc", "other_existing_step"]
