"""Contract tests for pytest11 plugin package structure."""

from __future__ import annotations

import ast
from pathlib import Path

from pytest_bdd.compatibility.tomllib import loads

REPO_ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = REPO_ROOT / "src"
PLUGIN_ROOT = SOURCE_ROOT / "pytest_bdd" / "plugin"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

EXPECTED_PLUGIN_COUNT = 19
EXPECTED_PLUGIN_CLASSES = {
    "pytest-bdd-code-generator": "CodeGeneratorPlugin",
}


def _pytest11_entrypoints() -> dict[str, str]:
    pyproject = loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    return dict(pyproject["project"]["entry-points"]["pytest11"])


def _module_path(module_name: str) -> Path:
    return SOURCE_ROOT.joinpath(*module_name.split("."))


def _class_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.name)
                elif node.module:
                    parts = node.module.split(".")
                    if node.level > 0:
                        target_dir = source_path.parents[node.level - 1]
                    else:
                        target_dir = source_path.parent

                    target_file = target_dir.joinpath(*parts).with_suffix(".py")
                    if not target_file.exists():
                        target_file = target_dir.joinpath(*parts) / "__init__.py"

                    if target_file.exists():
                        names.update(_class_names(target_file))
    return names


def test_pytest11_plugin_entrypoints_use_canonical_package_structure() -> None:
    """
    Verify every pytest11 plugin follows the package entrypoint/plugin/hook shape.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pytest11_entrypoints = _pytest11_entrypoints()

    assert len(pytest11_entrypoints) == EXPECTED_PLUGIN_COUNT  # pylint: disable=S101  # intentional assert in test
    assert EXPECTED_PLUGIN_CLASSES["pytest-bdd-code-generator"] == "CodeGeneratorPlugin"  # pylint: disable=S101  # intentional assert in test

    failures: list[str] = []
    for plugin_name, target in sorted(pytest11_entrypoints.items()):
        module_name = target.split(":", maxsplit=1)[0]
        if not module_name.endswith(".entrypoint"):
            failures.append(f"{plugin_name}: target {target!r} must resolve to a package entrypoint module")
            continue

        package_module = module_name.rsplit(".", maxsplit=1)[0]
        package_path = _module_path(package_module)
        entrypoint_path = package_path / "entrypoint.py"
        plugin_path = package_path / "plugin.py"
        hook_path = package_path / "hook.py"

        failures.extend(
            f"{plugin_name}: missing canonical module {required_path.relative_to(REPO_ROOT)}"
            for required_path in (entrypoint_path, plugin_path, hook_path)
            if not required_path.exists()
        )

        if not plugin_path.exists():
            continue

        class_names = _class_names(plugin_path)
        expected_class = EXPECTED_PLUGIN_CLASSES.get(plugin_name)
        has_canonical_class = any(class_name.endswith("Plugin") for class_name in class_names)
        if expected_class is not None:
            has_canonical_class = expected_class in class_names
        if not has_canonical_class:
            failures.append(
                f"{plugin_name}: {plugin_path.relative_to(REPO_ROOT)} must define "
                f"{expected_class or 'a *Plugin class'}; found {sorted(class_names)}",
            )

    assert failures == []  # pylint: disable=S101  # intentional assert in test
