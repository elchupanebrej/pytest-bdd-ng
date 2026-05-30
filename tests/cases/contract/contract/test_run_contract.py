"""Provide test run contract helpers."""

from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "003-unify-run-context"
    / "contracts"
    / "hook-execution-context.openapi.yaml"
)


def test_run_contract_exists() -> None:
    """Verify run contract exists."""
    assert CONTRACT_PATH.exists()


def test_run_contract_has_required_paths() -> None:
    """Verify run contract has required paths."""
    contract_text = CONTRACT_PATH.read_text()
    assert "/execution-context/session-root:" in contract_text
    assert "/execution-context/session-fixture:" in contract_text
    assert "/execution-context/config-stash:" in contract_text
    assert "/execution-context/active-set:" in contract_text
    assert "/execution-context/transitions:" in contract_text
    assert "/hooks/{hookName}/parameter-model:" in contract_text
    assert "/reporting/context-snapshot:" in contract_text
    assert "/compatibility/external-api:" in contract_text


def test_run_contract_has_minimal_change_constraints() -> None:
    """Verify run contract has minimal change constraints."""
    contract_text = CONTRACT_PATH.read_text()
    assert "consumerMigrationRequired:" in contract_text
    assert "- false" in contract_text
    assert "maxItems: 0" in contract_text
    assert "previousStep:" in contract_text
    assert "activeSet:" in contract_text
