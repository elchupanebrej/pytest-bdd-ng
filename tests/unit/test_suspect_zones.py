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
        param(
            "src/pytest_cuke/parser.py",
            ["tests/unit/parser", "tests/integration/step-parsing", "tests/integration/features"],
            id="parser",
        ),
        param(
            "src/pytest_cuke/model/feature.py",
            ["tests/unit/model", "tests/unit/parser", "tests/integration/features"],
            id="model",
        ),
        param(
            "src/pytest_cuke/reporting.py",
            ["tests/unit/reporting", "tests/unit/plugins", "tests/integration/features", "features/live-cucumber-json.feature", "features/live-cucumber-junit-xml.feature"],
            id="reporting",
        ),
        param(
            "src/pytest_cuke/compatibility/path.py",
            ["tests/unit/compatibility", "features/compatibility"],
            id="compatibility",
        ),
        param(
            "src/pytest_cuke/generation.py",
            ["tests/integration/generation", "tests/unit/generation", "tests/unit/plugins"],
            id="generation",
        ),
        param(
            "src/pytest_cuke/hooks.py",
            ["tests/integration/hooks", "tests/unit/execution"],
            id="hook",
        ),
        param(
            "src/pytest_cuke/message_plugin.py",
            ["tests/unit/message", "tests/contract/messages", "tests/unit/plugins", "features/cucumber-messages-reporting-spine.feature", "features/message-worker-consolidation.feature"],
            id="message",
        ),
        param(
            "src/pytest_cuke/plugin.py",
            ["tests/unit/bootstrap", "tests/unit/execution", "tests/contract", "tests/integration/features", "features/pytest-cuke-bootstrap.feature"],
            id="plugin",
        ),
        param(
            "src/pytest_cuke/struct_bdd/parser.py",
            ["tests/integration/struct-bdd", "tests/unit/plugins", "tests/unit/parser", "tests/unit/compatibility", "features/compatibility/optional-struct-bdd-extra.feature"],
            id="struct-bdd",
        ),
        param(
            "src/pytest_cuke/utils.py",
            ["tests/unit/core", "tests/unit/execution"],
            id="core-module",
        ),
        param(
            "tests/unit/parser/test_gherkin_parser.py",
            ["tests/unit/parser"],
            id="changed-test-own-dir",
        ),
        param(
            "tests/e2e/runtime_steps.py",
            ["features"],
            id="shared-bdd-steps",
        ),
        param(
            "features/feature/tag.feature.md",
            ["features/feature/tag.feature.md"],
            id="feature-asset",
        ),
        param(
            "tests/data/offline-formatter-replay/input.ndjson",
            ["tests/contract", "tests/integration"],
            id="testdata",
        ),
        param("README.rst", ["tests/unit/docs"], id="docs-only"),
        param("conftest.py", ["FULL"], id="root-conftest-full"),
        param("tests/unit/conftest.py", ["FULL"], id="nested-conftest-full"),
        param("pyproject.toml", ["FULL"], id="pytest-config-full"),
        param("src/pytest_cuke/brand_new_module.py", ["tests/unit", "tests/integration"], id="unknown-src-wide"),
        param("some/unknown/path.txt", ["tests/unit", "tests/integration"], id="unknown-path-wide"),
        param("stray/root.feature", ["tests/unit", "tests/integration/features"], id="unowned-feature-wide"),
    ],
)
def test_mapping_table(changed: str, expected: list[str]) -> None:
    assert suspect_zones(changed) == expected


def test_output_is_deduplicated() -> None:
    assert suspect_zones("src/pytest_cuke/parser.py", "src/pytest_cuke/parsers/base.py") == [
        "tests/unit/parser",
        "tests/integration/step-parsing",
        "tests/integration/features",
    ]
