"""Provide test governance cli contract helpers."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validators

from pytest_bdd.script import message_capability_governance

CLI_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "008-maximize-messages-coverage"
    / "contracts"
    / "message-capability-governance-cli.schema.json"
)


def _validator():
    schema = json.loads(CLI_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    return validator_class(schema)


def test_governance_cli_contract_file_exists() -> None:
    """Verify governance cli contract file exists."""
    assert CLI_SCHEMA_PATH.exists()


def test_governance_cli_contract_accepts_valid_report_payload(tmp_path: Path) -> None:
    """Verify governance cli contract accepts valid report payload."""
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
    """Verify governance cli contract requires runtime required file when flag enabled."""
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
    monkeypatch,
) -> None:
    """Verify discover governance schema path prefers canonical repo contract."""
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
