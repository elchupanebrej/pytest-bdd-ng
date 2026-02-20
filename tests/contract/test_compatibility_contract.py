from pathlib import Path

import yaml


def test_contract_has_required_paths():
    contract_path = Path("specs/001-add-py314-pytest39-support/contracts/compatibility-matrix.openapi.yaml")
    data = yaml.safe_load(contract_path.read_text())
    paths = data["paths"]

    assert "/compatibility/matrix" in paths
    assert "/compatibility/validate" in paths
    assert "/compatibility/jobs/expand" in paths
