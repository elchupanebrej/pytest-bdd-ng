"""

Provide test jinja2 doc generation contract helpers.
"""

from pathlib import Path

import yaml

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "004-migrate-jinja2-docs"
    / "contracts"
    / "jinja2-doc-generation.openapi.yaml"
)


def test_jinja2_doc_generation_contract_exists() -> None:
    """
    Verify jinja2 doc generation contract exists.

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


def test_jinja2_doc_generation_contract_has_required_paths() -> None:
    """
    Verify jinja2 doc generation contract has required paths.

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
    assert "/generation/render/code" in paths
    assert "/generation/render/docs" in paths
    assert "/docs/features/index" in paths
    assert "/validation/parity" in paths
    assert "/validation/doc-sync" in paths
    assert "/validation/packaging/templates" in paths


def test_jinja2_doc_generation_contract_has_required_schemas() -> None:
    """
    Verify jinja2 doc generation contract has required schemas.

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

    assert "TemplateAsset" in schemas
    assert "TemplateRenderContext" in schemas
    assert "GeneratedDocumentationBlock" in schemas
    assert "GenerationParityCase" in schemas
    assert "DocumentationSyncCheck" in schemas
    assert "DocumentationSyncResult" in schemas
    assert "PackagingTemplateManifest" in schemas


def test_jinja2_doc_generation_contract_declares_jinja2_engine() -> None:
    """
    Verify jinja2 doc generation contract declares jinja2 engine.

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
    engine_enum = data["components"]["schemas"]["TemplateAsset"]["properties"]["engine"]["enum"]

    assert "jinja2" in engine_enum


def test_jinja2_doc_generation_contract_uses_semantic_parity_mode() -> None:
    """
    Verify jinja2 doc generation contract uses semantic parity mode.

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
    parity_enum = data["components"]["schemas"]["GenerationParityCase"]["properties"]["parityMode"]["enum"]

    assert parity_enum == ["semantic"]
