from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validators

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
    assert CLI_SCHEMA_PATH.exists()


def test_governance_cli_contract_accepts_valid_report_payload(tmp_path: Path) -> None:
    payload = {
        "command": "report",
        "messages_file": str(tmp_path / "messages.ndjson"),
        "baseline_release": "v32.current",
        "mandatory_capabilities_file": "specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt",
        "require_mandatory_implemented": True,
        "require_fully_governed": True,
        "format": "json",
        "output": str(tmp_path / "governance.json"),
    }

    errors = list(_validator().iter_errors(payload))

    assert errors == []


def test_governance_cli_contract_requires_mandatory_file_when_flag_enabled(tmp_path: Path) -> None:
    payload = {
        "command": "report",
        "messages_file": str(tmp_path / "messages.ndjson"),
        "baseline_release": "v32.current",
        "require_mandatory_implemented": True,
    }

    errors = list(_validator().iter_errors(payload))

    assert errors
    assert any("mandatory_capabilities_file" in error.message for error in errors)
