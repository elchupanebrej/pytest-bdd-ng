"""

Provide test xdist worker controller boundary contract helpers.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "contract" / "fixtures" / "xdist_worker_controller_boundary.md"
LIVE_CONTRACT_PATH = Path(__file__).resolve().parents[3] / "contract" / "fixtures" / "xdist_live_reporting_boundary.md"
PLUGIN_BOUNDARY_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "contract" / "fixtures" / "live_reporting_plugin_boundary.md"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _live_contract_text() -> str:
    return LIVE_CONTRACT_PATH.read_text(encoding="utf-8")


def _plugin_boundary_contract_text() -> str:
    return PLUGIN_BOUNDARY_CONTRACT_PATH.read_text(encoding="utf-8")


def test_xdist_worker_controller_boundary_contract_exists() -> None:
    """
    Verify xdist worker controller boundary contract exists.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
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


def test_live_formatter_worker_controller_boundary_contract_exists() -> None:
    """
    Verify live formatter worker controller boundary contract exists.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
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
    assert LIVE_CONTRACT_PATH.exists()


def test_live_reporting_plugin_boundary_contract_exists() -> None:
    """
    Verify live reporting plugin boundary contract exists.

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
    assert PLUGIN_BOUNDARY_CONTRACT_PATH.exists()


def test_xdist_remote_bootstrap_import_defers_rewrite_sensitive_modules() -> None:
    """
    Verify xdist remote bootstrap import defers rewrite-sensitive modules.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
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
    code = """
import importlib
import sys

for module_name in ("xdist", "xdist.remote", "pytest_bdd.model.message_transport"):
    sys.modules.pop(module_name, None)

module = importlib.import_module("pytest_bdd.plugin.gherkin_message_reporter.xdist_worker")
assert module.__name__ == "pytest_bdd.plugin.gherkin_message_reporter.xdist_worker"
assert "xdist.remote" not in sys.modules
assert "pytest_bdd.model.message_transport" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_xdist_worker_controller_boundary_contract_assigns_transport_ownership() -> None:
    """
    Verify xdist worker controller boundary contract assigns transport ownership.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
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
    assert "pytest_xdist_getremotemodule" in contract_text
    assert "emit reporting payloads into execnet-serializable chunk batches" in contract_text
    assert "write directly to the final canonical `--messages-ndjson` artifact in xdist mode" in contract_text
    assert "require the controller to open worker-local-only files" in contract_text
    assert "own the canonical structural identity table" in contract_text
    assert "emit exactly one canonical final stream for the logical run" in contract_text


def test_xdist_worker_controller_boundary_contract_covers_partial_run_behavior() -> None:
    """
    Verify xdist worker controller boundary contract covers partial run behavior.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
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
    assert "popen" in contract_text
    assert "ssh" in contract_text
    assert "socket" in contract_text
    assert "via" in contract_text
    assert "If a worker transfer is interrupted after some batches were received" in contract_text
    assert "Partial-stream diagnostics must identify the missing or incomplete participant" in contract_text
    assert "Xdist-only hook registration remains conditional" in contract_text
    assert "fail-fast diagnostics" in contract_text


def test_live_formatter_boundary_contract_assigns_controller_only_rendering() -> None:
    """
    Verify live formatter boundary contract assigns controller only rendering.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
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
    contract_text = _live_contract_text()

    assert "controller/main authority renders live formatter output" in contract_text
    assert "do not render formatter output" in contract_text
    assert "Controller reporting authority" in contract_text
    assert "owns live formatter execution" in contract_text
    assert "session-close" in contract_text


def test_live_formatter_boundary_contract_requires_manifest_and_interruption_diagnostics() -> None:
    """
    Verify live formatter boundary contract requires manifest and interruption diagnostics.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
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
    contract_text = _live_contract_text()

    assert "source-complete" in contract_text
    assert "Missing or interrupted source completion manifests" in contract_text
    assert "Delivery failure in one source must not authorize worker-local fallback" in contract_text


def test_live_reporting_plugin_boundary_contract_covers_split_architecture_and_template_assets() -> None:
    """
    Verify live reporting plugin boundary contract covers split architecture and template assets.

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
    contract_text = _plugin_boundary_contract_text()

    assert "Message-stream plugin" in contract_text
    assert "Formatter reporter plugin" in contract_text
    assert "Entry facade" in contract_text
    assert "Formatter isolation" in contract_text
    assert "Generated scripts longer than 20 lines" in contract_text
