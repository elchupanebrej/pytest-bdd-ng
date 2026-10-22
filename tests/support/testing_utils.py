import json
from functools import partial
from itertools import islice
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pytest_cuke.utils import compose


def mask_npm_package_from_node_resolution(workspace: Path, package: str) -> Path:
    """Mask an ancestor-installed npm package for a consumer preflight contract.

    Node searches parent ``node_modules`` directories, so a fresh project under a
    user's temp directory can still import packages installed in their profile.
    A local package entry with a deliberately missing export target shadows that
    ancestor package and makes the import preflight deterministic.
    """
    if not package or "\\" in package or ":" in package or "\x00" in package:
        raise ValueError(f"invalid npm package name: {package!r}")

    parts = package.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"invalid npm package name: {package!r}")

    node_modules = (workspace / "node_modules").resolve()
    package_dir = node_modules.joinpath(*parts)
    try:
        package_dir.resolve().relative_to(node_modules)
    except ValueError:
        raise ValueError(f"invalid npm package name: {package!r}") from None

    package_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "name": package,
        "version": "0.0.0-pytest-cuke-unavailable",
        "exports": {".": "./__pytest_cuke_unavailable__.js"},
    }
    (package_dir / "package.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")
    return package_dir

if TYPE_CHECKING:  # pragma: no cover
    from pytest_cuke.model.message_types import DataTable  # type:ignore[attr-defined, import-untyped]


def data_table_to_dicts(data_table: Optional["DataTable"]):
    if data_table is None:
        return {}

    data_table_keys = map(attrgetter("value"), map(compose(next, iter), map(attrgetter("cells"), data_table.rows)))
    data_table_values = map(
        compose(list, compose(partial(map, attrgetter("value")), lambda items: islice(items, 1, None), iter)),
        map(attrgetter("cells"), data_table.rows),
    )
    return dict(zip(data_table_keys, data_table_values))


def run_pytester_isolated(testdir, *args):
    """Run a pytester project with its own config instead of inheriting /tmp config."""
    project_path = Path(str(testdir.tmpdir))
    config_path = next(
        (project_path / name for name in ("pytest.ini", "tox.ini") if (project_path / name).exists()),
        project_path / "pytest.ini",
    )
    if not config_path.exists():
        config_path.write_text("[pytest]\n", encoding="utf-8")
    config_text = config_path.read_text(encoding="utf-8")
    if "cuke_features_dir" not in config_text:
        config_path.write_text(f"{config_text.rstrip()}\ncuke_features_dir = .\n", encoding="utf-8")
    return testdir.runpytest("-c", str(config_path), *args)
