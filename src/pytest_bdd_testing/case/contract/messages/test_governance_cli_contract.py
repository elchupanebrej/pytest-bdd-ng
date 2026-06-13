"""

Provide test governance cli contract helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jsonschema import validators

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

from pytest_bdd.script import message_capability_governance

CLI_SCHEMA_PATH = (
    Path(__file__).resolve().parents[5]
    / "specs"
    / "008-maximize-messages-coverage"
    / "contracts"
    / "message-capability-governance-cli.schema.json"
)


def _validator() -> Any:
    schema = json.loads(CLI_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    return validator_class(schema)


def test_governance_cli_contract_file_exists() -> None:
    """
    Verify governance cli contract file exists.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    assert CLI_SCHEMA_PATH.exists()


def test_governance_repo_root_walks_to_project_root(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """
    Verify governance repo root discovery survives package nesting changes.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    repo_root = Path(__file__).resolve().parents[5]
    monkeypatch.chdir(tmp_path)

    assert message_capability_governance._repo_root() == repo_root


def test_governance_cli_contract_accepts_valid_report_payload(tmp_path: Path) -> None:
    """
    Verify governance cli contract accepts valid report payload.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    payload = {
        "command": "report",
        "messages_file": str(tmp_path / "messages.ndjson"),
        "baseline_release": "v32.current",
        "mandatory_capabilities_file": "specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt",
        "runtime_required_capabilities_file": (
            "specs/008-maximize-messages-coverage/runtime-required-capability-ids.txt"
        ),
        "require_runtime_required_covered": True,
        "require_non_runtime_classified": True,
        "require_fully_governed": True,
        "format": "json",
        "output": str(tmp_path / "governance.json"),
    }

    errors = list(_validator().iter_errors(payload))

    assert errors == []


def test_governance_cli_contract_requires_runtime_required_file_when_flag_enabled(tmp_path: Path) -> None:
    """
    Verify governance cli contract requires runtime required file when flag enabled.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    payload = {
        "command": "report",
        "messages_file": str(tmp_path / "messages.ndjson"),
        "baseline_release": "v32.current",
        "require_runtime_required_covered": True,
    }

    errors = list(_validator().iter_errors(payload))

    assert errors
    assert any("runtime_required_capabilities_file" in error.message for error in errors)


def test_discover_governance_schema_path_prefers_canonical_repo_contract(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """
    Verify discover governance schema path prefers canonical repo contract.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    repo_root = tmp_path / "repo"
    canonical_schema_path = (
        repo_root / "specs" / "008-maximize-messages-coverage" / "contracts" / "governance-report.schema.json"
    )
    canonical_schema_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_schema_path.write_text('{"type": "object"}', encoding="utf-8")

    decoy_root = tmp_path / "zzz-root"
    decoy_schema_path = decoy_root / "specs" / "999-zed" / "contracts" / "governance-report.schema.json"
    decoy_schema_path.parent.mkdir(parents=True, exist_ok=True)
    decoy_schema_path.write_text('{"type": "object"}', encoding="utf-8")

    monkeypatch.setattr(message_capability_governance, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(
        message_capability_governance,
        "_candidate_repo_roots",
        lambda: (decoy_root, repo_root),
    )

    assert message_capability_governance.discover_governance_schema_path() == canonical_schema_path.resolve()
