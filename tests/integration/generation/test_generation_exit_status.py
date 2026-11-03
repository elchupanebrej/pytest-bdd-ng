"""POSIX generation exit status assertions for cuke generate steps."""

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


def test_generation_changed_and_unchanged_status(project):
    _, target = project
    original = target.read_bytes()
    arguments = ["--target", str(target)]
    result = generate(project, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    generated = target.read_bytes()
    assert generated.startswith(original)
    assert b"a missing definition" in generated
    compile(ast.parse(generated), str(target), "exec")
    result = generate(project, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    assert target.read_bytes() == generated


def test_stdout_generation_with_additions_returns_0(project):
    result = generate(project)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "a missing definition" in result.stdout
    compile(ast.parse(result.stdout), "stdout-generation.py", "exec")


def test_preview_mode_returns_0_without_modifying_target(project):
    _, target = project
    original = target.read_bytes()
    result = generate(project, "--target", str(target), "--preview")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "a missing definition" in result.stdout
    assert target.read_bytes() == original


@pytest.mark.parametrize("invalid_source", [False, True])
def test_handled_errors_return_2_without_writes(project, invalid_source):
    root, target = project
    if invalid_source:
        target.write_text("def invalid(:\n")
        original = target.read_bytes()
    else:
        target = root / "missing.py"
        original = None
    result = generate(project, "--target", str(target))
    assert result.returncode == 2
    assert "cuke generate steps:" in result.stderr
    if original is None:
        assert not target.exists()
    else:
        assert target.read_bytes() == original


def test_missing_required_target_with_bind_only_returns_2(project):
    result = generate(project, "--bind-only")
    assert result.returncode == 2
    assert "--bind-only requires --target" in result.stderr


@pytest.mark.parametrize("invalid_arg", ["--unrecognized-option", "--exit-status=legacy100"])
def test_argument_parser_errors_return_2(project, invalid_arg):
    result = generate(project, invalid_arg)
    assert result.returncode == 2
    assert "unrecognized arguments" in result.stderr
