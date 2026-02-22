from pathlib import Path

import yaml


def test_contract_has_required_paths():
    contract_path = Path("specs/001-add-py314-pytest39-support/contracts/compatibility-matrix.openapi.yaml")
    data = yaml.safe_load(contract_path.read_text())
    paths = data["paths"]

    assert "/compatibility/policy" in paths
    assert "/compatibility/matrix" in paths
    assert "/compatibility/validate" in paths


def test_contract_declares_eol_reason_codes():
    contract_path = Path("specs/001-add-py314-pytest39-support/contracts/compatibility-matrix.openapi.yaml")
    data = yaml.safe_load(contract_path.read_text())
    reason_codes = data["components"]["schemas"]["CompatibilityMatrixEntry"]["properties"]["reasonCode"]["enum"]

    assert "eol_python" in reason_codes
    assert "eol_pytest" in reason_codes
