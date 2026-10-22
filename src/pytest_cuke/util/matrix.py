from __future__ import annotations

import itertools
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def substitute_parameters(text: str, parameters: Mapping[str, Any]) -> str:
    """Substitute <param> placeholders in text with values from parameters mapping."""
    if not text or not parameters:
        return text

    def replacer(match: re.Match[str]) -> str:
        param_name = match.group(1)
        if param_name in parameters:
            return str(parameters[param_name])
        return match.group(0)

    return re.sub(r"<([^>]+)>", replacer, text)


def expand_example_rows(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    """Expand table headers and row values into a list of dictionaries."""
    if not headers or not rows:
        return []
    return [dict(zip(headers, row, strict=False)) for row in rows]


def expand_parameter_matrix(param_matrix: Mapping[str, Sequence[Any]]) -> list[dict[str, Any]]:
    """Expand a dictionary of parameter sequences into all combinations (Cartesian product)."""
    if not param_matrix:
        return []
    keys = list(param_matrix.keys())
    value_lists = [list(param_matrix[k]) for k in keys]
    return [dict(zip(keys, combo, strict=False)) for combo in itertools.product(*value_lists)]


def expand_examples(examples_list: Sequence[Any]) -> list[dict[str, Any]]:
    """Expand a sequence of Examples models or row dicts into a flat list of dicts."""
    results: list[dict[str, Any]] = []
    for ex in examples_list:
        if hasattr(ex, "as_dicts") and callable(ex.as_dicts):
            results.extend(ex.as_dicts())
        elif hasattr(ex, "header") and hasattr(ex, "rows"):
            header_vals = ex.header.values if hasattr(ex.header, "values") else tuple(ex.header)
            row_vals = [r.values if hasattr(r, "values") else tuple(r) for r in ex.rows]
            results.extend(expand_example_rows(header_vals, row_vals))
        elif isinstance(ex, dict):
            results.append(ex)
        elif isinstance(ex, list | tuple):
            results.extend(ex)
    return results


def build_parametrization(
    column_names: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> tuple[tuple[str, ...], list[tuple[Any, ...]]]:
    """Build (argnames, argvalues) tuple suitable for pytest parametrization."""
    names = tuple(column_names)
    values = [tuple(r) for r in rows]
    return names, values


def build_scenario_parametrization(
    scenario: Any,
) -> tuple[tuple[str, ...], list[tuple[Any, ...]], list[str]]:
    """Extract parametrization argnames, argvalues, and ids for a Scenario object."""
    examples = getattr(scenario, "examples", ())
    if not examples:
        return (), [], []

    all_dicts = expand_examples(examples)
    if not all_dicts:
        return (), [], []

    keys = list(all_dicts[0].keys())
    for d in all_dicts[1:]:
        for k in d:
            if k not in keys:
                keys.append(k)

    names = tuple(keys)
    values = [tuple(d.get(k, "") for k in names) for d in all_dicts]
    ids = [f"row{idx}-{'-'.join(f'{k}_{d.get(k, bytes)}' for k in names)}" for idx, d in enumerate(all_dicts)]
    return names, values, ids
