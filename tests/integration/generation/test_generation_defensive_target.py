"""Integration tests for generator defensive target validation (G18)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration


SYNTAX_ERROR_CONTENT = 'def invalid(:\n    return "broken"\n'


@pytest.fixture
def syntax_error_project(tmp_path: Path):
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    feature_file = features_dir / "sample.feature"
    feature_file.write_text(
        "Feature: Sample\n  Scenario: Do something\n    Given a missing step to generate\n",
        encoding="utf-8",
    )
    target_file = tmp_path / "test_target.py"
    target_file.write_text(SYNTAX_ERROR_CONTENT, encoding="utf-8")
    return tmp_path, feature_file, target_file


def _run_generator(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_cuke.cli",
            "generate",
            "steps",
            *arguments,
        ],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_generation_target_with_syntax_error_exits_2_and_leaves_file_intact(syntax_error_project) -> None:
    root, feature_file, target_file = syntax_error_project
    result = _run_generator(
        root,
        "--feature",
        str(feature_file),
        "--target",
        str(target_file),
    )

    assert result.returncode == 2
    assert "target file contains syntax errors" in result.stderr
    assert target_file.read_text(encoding="utf-8") == SYNTAX_ERROR_CONTENT


def test_generation_target_with_syntax_error_and_keep_on_error_leaves_file_intact(syntax_error_project) -> None:
    root, feature_file, target_file = syntax_error_project
    result = _run_generator(
        root,
        "--feature",
        str(feature_file),
        "--target",
        str(target_file),
        "--keep-on-error",
    )

    assert result.returncode == 2
    assert "target file contains syntax errors" in result.stderr
    assert target_file.read_text(encoding="utf-8") == SYNTAX_ERROR_CONTENT


def test_generation_target_with_bind_scenarios_and_syntax_error_leaves_file_intact(syntax_error_project) -> None:
    root, feature_file, target_file = syntax_error_project
    result = _run_generator(
        root,
        "--feature",
        str(feature_file),
        "--target",
        str(target_file),
        "--bind-scenarios",
        "--keep-on-error",
    )

    assert result.returncode == 2
    assert "target file contains syntax errors" in result.stderr
    assert target_file.read_text(encoding="utf-8") == SYNTAX_ERROR_CONTENT
