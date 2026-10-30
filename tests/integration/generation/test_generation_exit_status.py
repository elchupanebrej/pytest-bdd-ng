"""Installed CLI consumers for opt-in historical generation exit codes."""

import ast
import os
import subprocess
import sys

import pytest


@pytest.fixture
def project(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]\ncuke_features_dir = features\n")
    features = tmp_path / "features"
    features.mkdir()
    (features / "status.feature").write_text(
        "Feature: Exit policy\n  Scenario: Generate missing step\n    Given a missing definition\n"
    )
    target = tmp_path / "test_status.py"
    target.write_text('# Retain original source.\nVALUE = "retained"\n')
    return tmp_path, target


def generate(project, *arguments):
    root, _ = project
    environment = os.environ.copy()
    environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_cuke.cli",
            "generate",
            "steps",
            "--feature",
            "features/status.feature",
            *arguments,
        ],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize(("policy", "changed_status"), [("current", 0), ("legacy100", 100)])
def test_generation_changed_and_unchanged_status(project, policy, changed_status):
    _, target = project
    original = target.read_bytes()
    arguments = ["--target", str(target), "--exit-status", policy]
    result = generate(project, *arguments)
    assert result.returncode == changed_status, result.stdout + result.stderr
    generated = target.read_bytes()
    assert generated.startswith(original)
    assert b"a missing definition" in generated
    compile(ast.parse(generated), str(target), "exec")
    result = generate(project, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    assert target.read_bytes() == generated


def test_legacy_stdout_generation_returns_100(project):
    result = generate(project, "--exit-status=legacy100")
    assert result.returncode == 100, result.stdout + result.stderr
    assert "a missing definition" in result.stdout
    compile(ast.parse(result.stdout), "stdout-generation.py", "exec")


def test_legacy_preview_reports_changes_without_writing(project):
    _, target = project
    original = target.read_bytes()
    result = generate(project, "--target", str(target), "--preview", "--exit-status=legacy100")
    assert result.returncode == 100, result.stdout + result.stderr
    assert "a missing definition" in result.stdout
    assert target.read_bytes() == original


@pytest.mark.parametrize("invalid_source", [False, True])
def test_legacy_handled_errors_return_100_without_writes(project, invalid_source):
    root, target = project
    if invalid_source:
        target.write_text("def invalid(:\n")
        original = target.read_bytes()
    else:
        target = root / "missing.py"
        original = None
    result = generate(project, "--target", str(target), "--exit-status=legacy100")
    assert result.returncode == 100
    assert "cuke generate steps:" in result.stderr
    if original is None:
        assert not target.exists()
    else:
        assert target.read_bytes() == original


def test_legacy_missing_required_target_is_handled_error(project):
    result = generate(project, "--bind-only", "--exit-status=legacy100")
    assert result.returncode == 100
    assert "--bind-only requires --target" in result.stderr


def test_argument_parser_errors_keep_usage_status_2(project):
    result = generate(project, "--exit-status=unsupported")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
