from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _runner(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(_PROJECT_ROOT / "scripts"))
    return runpy.run_path(str(_PROJECT_ROOT / "scripts" / "run_env_matrix_cell.py"))


@pytest.mark.parametrize(
    "command_text",
    [
        "python -m pytest -q tests/unit",
        "pytest -q tests/unit",
        "./.tox/native-go-parser/bin/pytest -q tests/unit/pytest_cases.py",
        r"C:\host\Python\Scripts\pytest.exe -q tests",
    ],
)
def test_rendered_commands_that_run_pytest_are_recognized(monkeypatch: pytest.MonkeyPatch, command_text: str) -> None:
    runner = _runner(monkeypatch)

    assert runner["_runs_pytest"](command_text) is True


@pytest.mark.parametrize(
    "command_text",
    [
        "python -m build --sdist --outdir /home/runner/work/pytest-bdd-ng/pytest-bdd-ng/.tox/native-go-parser/tmp/source",
        r"python -m build --sdist --outdir D:\a\pytest-bdd-ng\pytest-bdd-ng\.tox\native-go-parser\tmp/source",
        "python scripts/test_native_go_parser.py /home/runner/work/pytest-bdd-ng/pytest-bdd-ng/.tox/tmp/source",
    ],
)
def test_checkout_paths_that_contain_pytest_are_not_pytest_commands(
    monkeypatch: pytest.MonkeyPatch, command_text: str
) -> None:
    runner = _runner(monkeypatch)

    assert runner["_runs_pytest"](command_text) is False
