from __future__ import annotations

import ast
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[no-redef]
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            import tomllib  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LAYERS_CONFIG_PATH = REPO_ROOT / "docs" / "architecture" / "layers.toml"
SRC_PATH = REPO_ROOT / "src" / "pytest_bdd"


def load_layers_config() -> dict:
    assert LAYERS_CONFIG_PATH.exists(), f"Missing layers.toml at {LAYERS_CONFIG_PATH}"
    with LAYERS_CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def test_layers_toml_dag_properties() -> None:
    config = load_layers_config()
    layers = config.get("layers", {})
    assert len(layers) >= 8, f"Expected at least 8 layers, found {len(layers)}"

    for layer_id, info in layers.items():
        assert "order" in info, f"Layer {layer_id} missing order"
        assert "allowed_imports" in info, f"Layer {layer_id} missing allowed_imports"
        current_order = info["order"]
        for allowed in info["allowed_imports"]:
            assert allowed in layers, f"Layer {layer_id} references unknown allowed layer {allowed}"
            allowed_order = layers[allowed]["order"]
            assert allowed_order < current_order, (
                f"DAG violation: {layer_id} (order {current_order}) allows import from "
                f"{allowed} (order {allowed_order})"
            )


def test_modules_mapping_validity() -> None:
    config = load_layers_config()
    layers = config.get("layers", {})
    modules = config.get("modules", {})
    assert len(modules) > 0, "No modules defined in layers.toml"

    for mod_name, layer_id in modules.items():
        assert layer_id in layers, f"Module {mod_name} mapped to unknown layer {layer_id}"


def get_layer_for_module(mod_name: str, modules_map: dict[str, str]) -> str | None:
    candidates = [prefix for prefix in modules_map if mod_name == prefix or mod_name.startswith(prefix + ".")]
    if not candidates:
        return None
    longest = max(candidates, key=len)
    return modules_map[longest]


def test_layer_import_enforcement() -> None:
    config = load_layers_config()
    layers = config.get("layers", {})
    modules = config.get("modules", {})

    violations: list[str] = []

    if not SRC_PATH.exists():
        return

    for py_file in SRC_PATH.rglob("*.py"):
        rel_path = py_file.relative_to(REPO_ROOT / "src")
        mod_parts = list(rel_path.with_suffix("").parts)
        if mod_parts[-1] == "__init__":
            mod_parts = mod_parts[:-1]
        mod_name = ".".join(mod_parts) if mod_parts else "pytest_bdd"

        current_layer = get_layer_for_module(mod_name, modules)
        if not current_layer:
            continue

        allowed_layers = set(layers[current_layer]["allowed_imports"]) | {current_layer}

        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            imported_mod: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("pytest_bdd"):
                        imported_mod = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pytest_bdd"):
                imported_mod = node.module

            if imported_mod:
                target_layer = get_layer_for_module(imported_mod, modules)
                if target_layer and target_layer not in allowed_layers:
                    violations.append(
                        f"{mod_name} ({current_layer}) imports {imported_mod} ({target_layer}) at line {node.lineno}"
                    )

    assert not violations, "Layer boundary violations found:\n" + "\n".join(violations)
