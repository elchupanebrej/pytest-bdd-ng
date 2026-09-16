"""Runnable check for the Suspect Zone mapper (`scripts/suspect-zones.sh`, #210).

Covers a few mapping-table rows, the ``FULL`` sentinel for conftest/config
changes, and both wide-fallback cases (unknown ``src/`` path, unknown path).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from pytest import mark, param

pytestmark = [
    mark.unit,
    mark.skipif(shutil.which("bash") is None, reason="suspect-zones.sh is a bash script"),
]

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "suspect-zones.sh"


def suspect_zones(*changed: str) -> list[str]:
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        input="\n".join(changed) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


@mark.parametrize(
    ("changed", "expected"),
    [
        param("src/pytest_bdd/parser.py", ["tests/unit/parser", "tests/args", "tests/feature"], id="parser"),
        param(
            "src/pytest_bdd/model/feature.py",
            ["tests/unit/model", "tests/unit/parser", "tests/feature"],
            id="model",
        ),
        param("src/pytest_bdd/reporting.py", ["tests/unit/reporting", "tests/feature"], id="reporting"),
        param("src/pytest_bdd/compatibility/path.py", ["tests/unit/compatibility"], id="compatibility"),
        param("src/pytest_bdd/generation.py", ["tests/generation", "tests/unit/plugins"], id="generation"),
        param(
            "src/pytest_bdd/hook.py",
            ["tests/hook", "tests/unit/execution", "tests/test_hooks.py"],
            id="hook",
        ),
        param(
            "src/pytest_bdd/message_plugin.py",
            ["tests/unit/message", "tests/messages", "tests/unit/plugins"],
            id="message",
        ),
        param(
            "src/pytest_bdd/struct_bdd/parser.py",
            ["tests/struct_bdd", "tests/unit/plugins", "tests/unit/parser", "tests/unit/compatibility"],
            id="struct-bdd",
        ),
        param("src/pytest_bdd/utils.py", ["tests/unit/core", "tests/unit/execution"], id="core-module"),
        param("tests/unit/parser/test_gherkin_parser.py", ["tests/unit/parser"], id="changed-test-own-dir"),
        param("features/Feature/Tag.feature.md", ["tests/e2e"], id="feature-asset-e2e"),
        param("testdata/allure_/outline.feature", ["tests/allure_"], id="allure-testdata"),
        param("README.rst", ["tests/doc"], id="docs-only"),
        param("conftest.py", ["FULL"], id="root-conftest-full"),
        param("tests/unit/conftest.py", ["FULL"], id="nested-conftest-full"),
        param("pyproject.toml", ["FULL"], id="pytest-config-full"),
        param("src/pytest_bdd/brand_new_module.py", ["tests/unit", "tests/feature"], id="unknown-src-wide"),
        param("some/unknown/path.txt", ["tests/unit", "tests/feature"], id="unknown-path-wide"),
        param("stray/root.feature", ["tests/unit", "tests/feature"], id="unowned-feature-wide"),
    ],
)
def test_mapping_table(changed: str, expected: list[str]) -> None:
    assert suspect_zones(changed) == expected


def test_output_is_deduplicated() -> None:
    assert suspect_zones("src/pytest_bdd/parser.py", "src/pytest_bdd/parsers/base.py") == [
        "tests/unit/parser",
        "tests/args",
        "tests/feature",
    ]
