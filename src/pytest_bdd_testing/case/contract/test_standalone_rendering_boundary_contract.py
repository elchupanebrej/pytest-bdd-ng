"""

Provide test standalone rendering boundary contract helpers.
"""

from __future__ import annotations

from pathlib import Path

from pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer import StandaloneCucumberFormatterRenderer
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contract" / "fixtures" / "standalone_rendering_boundary.md"
STANDALONE_RENDERER_PATH = (
    Path(__file__).resolve().parents[4]
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
    """
    Verify standalone rendering boundary contract exists.

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


def test_standalone_rendering_boundary_contract_forbids_synthetic_pytest_runtime() -> None:
    """
    Verify standalone rendering boundary contract forbids synthetic pytest runtime.

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
    contract_text = _contract_text()

    assert "must not require a synthetic pytest `Config` object" in contract_text
    assert "must not require ad hoc construction of a pytest" in contract_text
    assert "must use one explicit supported" in contract_text


def test_standalone_renderer_uses_explicit_application_service_boundary() -> None:
    """
    Verify standalone renderer uses explicit application service boundary.

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
    renderer = StandaloneCucumberFormatterRenderer.discover(catalog=FormatterPluginCatalog.discover())

    assert isinstance(renderer, StandaloneCucumberFormatterRenderer)
    assert hasattr(renderer, "resolve_requests")
    assert hasattr(renderer, "render_from_messages_path")


def test_standalone_renderer_source_does_not_construct_synthetic_pytest_runtime() -> None:
    """
    Verify standalone renderer source does not construct synthetic pytest runtime.

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
    standalone_renderer_source = _standalone_renderer_source()

    assert "SimpleNamespace" not in standalone_renderer_source
    assert "PytestPluginManager" not in standalone_renderer_source
    assert "from_config(" not in standalone_renderer_source
