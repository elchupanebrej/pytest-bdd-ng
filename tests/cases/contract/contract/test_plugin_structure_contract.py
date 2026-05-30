"""Contract tests for pytest11 plugin package structure."""

from __future__ import annotations

import ast
from pathlib import Path

from pytest_bdd.compatibility.tomllib import loads

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = REPO_ROOT / "src"
PLUGIN_ROOT = SOURCE_ROOT / "pytest_bdd" / "plugin"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

EXPECTED_PLUGIN_COUNT = 18
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
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def test_pytest11_plugin_entrypoints_use_canonical_package_structure() -> None:
    """Verify every pytest11 plugin follows the package entrypoint/plugin/hook shape."""
    pytest11_entrypoints = _pytest11_entrypoints()

    assert len(pytest11_entrypoints) == EXPECTED_PLUGIN_COUNT
    assert EXPECTED_PLUGIN_CLASSES["pytest-bdd-code-generator"] == "CodeGeneratorPlugin"

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

    assert failures == []
