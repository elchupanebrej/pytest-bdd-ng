"""Message capability governance helpers."""

from __future__ import annotations

from pytest_bdd.model.coverage.inventory import generate_inventory
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capabilities,
    _load_capabilities_from_governance_report,
    _load_capability_ids,
    _validate_runtime_required_scope,
    _validate_scope_capability_ids,
)
from pytest_bdd.script.message_capability_governance.cli import (
    main,
    parse_args,
)
from pytest_bdd.script.message_capability_governance.decisions import (
    _load_baseline_diff,
    _load_decisions,
    _select_active_decisions,
    _validate_decisions,
)
from pytest_bdd.script.message_capability_governance.schema import (
    _candidate_repo_roots,
    _repo_root,
    discover_governance_schema_path,
    load_governance_report_schema,
    validate_governance_report_payload,
)

__all__ = [
    "_candidate_repo_roots",
    "_load_baseline_diff",
    "_load_capabilities",
    "_load_capabilities_from_governance_report",
    "_load_capability_ids",
    "_load_decisions",
    "_repo_root",
    "_select_active_decisions",
    "_validate_decisions",
    "_validate_runtime_required_scope",
    "_validate_scope_capability_ids",
    "discover_governance_schema_path",
    "generate_inventory",
    "load_governance_report_schema",
    "main",
    "parse_args",
    "validate_governance_report_payload",
]
