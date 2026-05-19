"""Provide test hook lifecycle non null contract helpers."""

from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "016-strict-non-null"
    / "contracts"
    / "hook-lifecycle-non-null.openapi.yaml"
)


def test_hook_lifecycle_non_null_contract_exists() -> None:
    """Verify hook lifecycle non null contract exists."""
    assert CONTRACT_PATH.exists()


def test_hook_lifecycle_non_null_contract_has_required_paths() -> None:
    """Verify hook lifecycle non null contract has required paths."""
    contract_text = CONTRACT_PATH.read_text()
    assert "/hooks/{hookName}/run-surface:" in contract_text
    assert "/hooks/{hookName}/boundary-failure:" in contract_text
    assert "/reporting/context-snapshot:" in contract_text
    assert "/parser/parse-error-emission:" in contract_text
    assert "/compatibility/hook-plugin-public-api:" in contract_text


def test_hook_lifecycle_non_null_contract_declares_non_null_policies() -> None:
    """Verify hook lifecycle non null contract declares non null policies."""
    contract_text = CONTRACT_PATH.read_text()
    assert "guaranteed_present" in contract_text
    assert "empty_object_allowed" in contract_text
    assert "fail_fast" in contract_text
    assert "NoPreviousStep" in contract_text or "no_previous_step" in contract_text
    assert "binding_missing" in contract_text
    assert "emit_best_effort" in contract_text
    assert "best_effort" in contract_text
    assert "explicit_empty_state_when_inactive" in contract_text
