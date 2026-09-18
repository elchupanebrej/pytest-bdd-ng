"""Runnable check for the Suspect Zone mapper (`scripts/suspect-zones.sh`, #210).

Covers a few mapping-table rows, the ``FULL`` sentinel for conftest/config
changes, and both wide-fallback cases (unknown ``src/`` path, unknown path).
"""

from __future__ import annotations

import ntpath
import os
import shutil
import subprocess
from pathlib import Path

from pytest import mark, param


def _is_wsl_bash(path: str) -> bool:
    stub = ntpath.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32", "bash.exe")
    return ntpath.normcase(ntpath.normpath(path)) == ntpath.normcase(ntpath.normpath(stub))


def _resolve_bash() -> str | None:
    found = shutil.which("bash")
    if found is not None and not _is_wsl_bash(found):
        return found
    git_bash = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
    if git_bash.is_file():
        return str(git_bash)
    return None


BASH = _resolve_bash()

pytestmark = [
    mark.unit,
    mark.skipif(
        BASH is None,
        reason="no usable bash found (only the Windows WSL launcher stub, and no Git for Windows bash)",
    ),
]

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "suspect-zones.sh"


def suspect_zones(*changed: str) -> list[str]:
    assert BASH is not None
    result = subprocess.run(
        [BASH, str(SCRIPT)],
        input="\n".join(changed) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


def test_resolve_bash_prefers_real_bash(monkeypatch) -> None:
    monkeypatch.setenv("PROGRAMFILES", "/nonexistent")
    monkeypatch.setattr(shutil, "which", lambda _: "/bin/bash")

    assert _resolve_bash() == "/bin/bash"


def test_resolve_bash_skips_wsl_stub_and_uses_git_bash(monkeypatch, tmp_path) -> None:
    git_bash = tmp_path / "Git" / "bin" / "bash.exe"
    git_bash.parent.mkdir(parents=True)
    git_bash.touch()
    monkeypatch.setenv("SYSTEMROOT", r"C:\Windows")
    monkeypatch.setenv("PROGRAMFILES", str(tmp_path))
    monkeypatch.setattr(shutil, "which", lambda _: r"C:\Windows\System32\bash.exe")

    assert _resolve_bash() == str(git_bash)


def test_resolve_bash_returns_none_when_only_wsl_stub(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SYSTEMROOT", r"C:\Windows")
    monkeypatch.setenv("PROGRAMFILES", str(tmp_path))
    monkeypatch.setattr(shutil, "which", lambda _: r"C:\Windows\System32\bash.exe")

    assert _resolve_bash() is None


def test_is_wsl_bash_detects_system32_launcher(monkeypatch) -> None:
    monkeypatch.setenv("SYSTEMROOT", r"C:\Windows")

    assert _is_wsl_bash(r"C:\Windows\System32\bash.exe") is True
    assert _is_wsl_bash(r"C:\Windows\System32\cmd.exe") is False
    assert _is_wsl_bash("/bin/bash") is False


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
