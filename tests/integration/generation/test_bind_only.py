"""Consumer contract for binding scenarios without generating step stubs."""

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
    (features / "binding.feature").write_text(
        "Feature: Binding\n  Scenario: Selected scenario\n    Given a missing definition\n"
    )
    target = tmp_path / "test_binding.py"
    target.write_text('# User prefix remains byte-for-byte.\nVALUE = "retained"\n')
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
            "features/binding.feature",
            *arguments,
        ],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_bind_only_preserves_user_code_and_is_idempotent(project):
    _, target = project
    original = target.read_bytes()
    result = generate(project, "--target", str(target), "--bind-only")
    assert result.returncode == 0, result.stdout + result.stderr
    source = target.read_bytes()
    assert source.startswith(original)
    tree = ast.parse(source)
    compile(tree, str(target), "exec")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert len(functions) == 1
    assert functions[0].name == "test_selected_scenario"
    assert isinstance(functions[0].body[-1], ast.Pass)
    assert "a missing definition" not in source.decode()
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "scenario"
    ]
    assert len(calls) == 1
    assert ast.literal_eval(calls[0].args[1]) == "Selected scenario"
    result = generate(project, "--target", str(target), "--bind-only")
    assert result.returncode == 0, result.stdout + result.stderr
    assert target.read_bytes() == source


def test_bind_only_preview_leaves_target_unchanged(project):
    _, target = project
    original = target.read_bytes()
    result = generate(project, "--target", str(target), "--bind-only", "--preview")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "scenario" in result.stdout
    assert "a missing definition" not in result.stdout
    assert target.read_bytes() == original


def test_bind_only_requires_target(project):
    result = generate(project, "--bind-only")
    assert result.returncode == 2
    assert "--bind-only requires --target" in result.stderr


def test_bind_scenarios_still_generates_steps(project):
    _, target = project
    result = generate(project, "--target", str(target), "--bind-scenarios")
    assert result.returncode == 0, result.stdout + result.stderr
    tree = ast.parse(target.read_bytes())
    compile(tree, str(target), "exec")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert functions
    assert any("a missing definition" in ast.unparse(node) for node in functions)


@pytest.mark.parametrize("feature_root", ["features", "custom-features"])
def test_bind_only_does_not_execute_autouse_fixtures(project, feature_root):
    root, target = project
    if feature_root != "features":
        (root / "features").rename(root / feature_root)
        (root / "pytest.ini").write_text(f"[pytest]\ncuke_features_dir = {feature_root}\n")
    marker = root / "fixture-executed"
    (root / "conftest.py").write_text(
        "from pathlib import Path\nimport pytest\n"
        "@pytest.fixture(autouse=True)\n"
        "def no_runtime_setup():\n"
        "    Path(__file__).with_name('fixture-executed').write_text('executed')\n"
        "    raise RuntimeError('bind-only must not run fixtures')\n"
    )
    command = [
        sys.executable,
        "-m",
        "pytest_cuke.cli",
        "generate",
        "steps",
        "--feature",
        f"{feature_root}/binding.feature",
        "--target",
        str(target),
        "--bind-only",
    ]
    environment = os.environ.copy()
    environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    original = target.read_bytes()
    applied = None
    for index, arguments in enumerate([[*command, "--preview"], command, command]):
        result = subprocess.run(
            arguments, cwd=root, env=environment, check=False, capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert not marker.exists()
        if index == 0:
            assert target.read_bytes() == original
        elif index == 1:
            applied = target.read_bytes()
        else:
            assert target.read_bytes() == applied
    source = target.read_bytes()
    assert source.startswith(original)
    assert "a missing definition" not in source.decode()
    tree = ast.parse(source)
    compile(tree, str(target), "exec")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert len(functions) == 1
    assert functions[0].name == "test_selected_scenario"
    assert isinstance(functions[0].body[-1], ast.Pass)
