from __future__ import annotations

import configparser
from pathlib import Path

import pytest
import yaml

from pytest_cuke.compatibility.matrix import _expand_tox_expression

pytestmark = pytest.mark.unit

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _configured_tox_environments() -> set[str]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(_PROJECT_ROOT / "tox.ini", encoding="utf-8")
    names: set[str] = set()
    for expression in parser.get("tox", "env_list").splitlines():
        if expression.strip():
            names.update(_expand_tox_expression(expression.strip(), _PROJECT_ROOT / "tox.ini"))
    return names


def test_floor_cells_exist_in_tox_and_are_selected_by_the_inventory() -> None:
    configured = _configured_tox_environments()
    assert "py314-pytest842-coverage-lin" in configured
    assert "py315-pytest911-coverage-lin" in configured

    inventory = yaml.safe_load((_PROJECT_ROOT / "config" / "env-matrix.yaml").read_text(encoding="utf-8"))
    selected = {str(environment) for cell in inventory["workflow_cells"] for environment in cell.get("tox_envs", [])}
    assert "py314-pytest842-coverage-lin" in selected
    assert "py315-pytest911-coverage-lin" in selected
