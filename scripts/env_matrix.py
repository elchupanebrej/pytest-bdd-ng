"""Emit a GitHub Actions matrix from the checked-in environment inventory."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any


def load_cells(inventory_path: Path, job: str) -> list[dict[str, Any]]:
    """Return the concrete cells assigned to ``job`` in the YAML inventory."""
    try:
        yaml = importlib.import_module("yaml")
    except ModuleNotFoundError as error:
        raise RuntimeError("PyYAML is required; install `pytest-cuke[env-matrix]`.") from error

    try:
        inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise RuntimeError(f"cannot read environment inventory {inventory_path}: {error}") from error
    if not isinstance(inventory, dict):
        raise RuntimeError(f"environment inventory {inventory_path} must contain a YAML object")

    cells = inventory.get("workflow_cells")
    if not isinstance(cells, list):
        raise RuntimeError(f"environment inventory {inventory_path} has no workflow_cells list")
    selected = [cell for cell in cells if isinstance(cell, dict) and cell.get("job") == job]
    if not selected:
        raise RuntimeError(f"environment inventory has no cells for workflow job {job!r}")
    for cell in selected:
        if not isinstance(cell.get("tox_envs"), list) or not cell["tox_envs"]:
            raise RuntimeError(f"workflow cell {cell.get('id')!r} has no tox_envs list")
        for key in ("id", "runner", "python", "platform"):
            if not cell.get(key):
                raise RuntimeError(f"workflow cell {cell.get('id')!r} is missing {key!r}")
    return selected


def split_cell_environments(cells: list[dict[str, Any]], cell_ids: list[str]) -> list[dict[str, Any]]:
    """Expand selected cells into rows that each carry one tox environment."""
    requested_ids = set(cell_ids)
    available_ids = {str(cell.get("id")) for cell in cells}
    unknown_ids = requested_ids - available_ids
    if unknown_ids:
        unknown = ", ".join(sorted(unknown_ids))
        raise RuntimeError(f"cannot split unknown workflow cell(s): {unknown}")

    rows: list[dict[str, Any]] = []
    for cell in cells:
        if cell.get("id") not in requested_ids:
            rows.append(cell)
            continue
        for tox_environment in cell["tox_envs"]:
            row = dict(cell)
            row["tox_environment"] = tox_environment
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, help="workflow job key from workflow_cells")
    parser.add_argument(
        "--split-cells",
        nargs="+",
        default=[],
        metavar="CELL_ID",
        help="expand each named cell into one matrix row per tox environment",
    )
    parser.add_argument(
        "--split-tox-envs",
        action="store_true",
        help="expand every selected cell into one matrix row per tox environment",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("config/env-matrix.yaml"),
        help="YAML environment inventory (default: config/env-matrix.yaml)",
    )
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="append the compact JSON matrix to the GITHUB_OUTPUT file",
    )
    args = parser.parse_args()
    try:
        cells = load_cells(args.inventory, args.job)
        if args.split_cells and args.split_tox_envs:
            raise RuntimeError("--split-cells and --split-tox-envs cannot be used together")
        if args.split_tox_envs:
            cells = split_cell_environments(
                cells,
                [str(cell["id"]) for cell in cells],
            )
        if args.split_cells:
            if args.job != "full-matrix":
                raise RuntimeError("--split-cells is supported only for the full-matrix job")
            cells = split_cell_environments(cells, args.split_cells)
    except RuntimeError as error:
        print(f"env-matrix: {error}", file=sys.stderr)
        return 2

    matrix = json.dumps(cells, separators=(",", ":"), ensure_ascii=False)
    if args.github_output:
        output_path = os.environ.get("GITHUB_OUTPUT")
        if not output_path:
            print("env-matrix: --github-output requires GITHUB_OUTPUT", file=sys.stderr)
            return 2
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"cells={matrix}\n")
    else:
        print(matrix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
