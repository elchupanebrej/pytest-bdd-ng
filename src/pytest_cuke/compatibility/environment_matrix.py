"""Validate the repository's supported development and CI environment matrix."""

from __future__ import annotations

import importlib
import importlib.metadata
import platform
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeGuard

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

TOX_LIST_COMMAND = ("tox", "list", "--no-desc")
_SUPPORTED_STATUSES = {"required", "optional", "unsupported"}


def check_environment_inventory(
    inventory_path: Path | str,
    *,
    lane_id: str | None = None,
) -> dict[str, Any]:
    """Return configuration and runtime proof for an environment inventory.

    Without ``lane_id`` this validates declarations and resolved tox/CI
    selectors. With ``lane_id`` it also checks that lane's prerequisites and
    runs a collect-only probe for its declared test carrier.
    """
    diagnostics: list[dict[str, str]] = []
    selected_path = Path(inventory_path).expanduser().resolve()
    try:
        document = _load_yaml_inventory(selected_path)
    except (OSError, ValueError) as error:
        return _failure(
            [
                _diagnostic(
                    "inventory",
                    "invalid-inventory",
                    str(error),
                    "Fix the YAML inventory and run `cuke compatibility --check-environments "
                    "--inventory config/env-matrix.yaml --json` again.",
                )
            ]
        )

    project_root = selected_path.parent.parent
    lanes = document.get("lanes")
    workflow_cells = document.get("workflow_cells")
    if not isinstance(lanes, list) or not lanes:
        diagnostics.append(
            _diagnostic(
                "inventory",
                "missing-lanes",
                "inventory must contain a non-empty lanes list",
                "Add lane records to config/env-matrix.yaml.",
            )
        )
        lanes = []
    if not isinstance(workflow_cells, list) or not workflow_cells:
        diagnostics.append(
            _diagnostic(
                "inventory",
                "missing-workflow-cells",
                "inventory must contain a non-empty workflow_cells list",
                "Add the selected CI cells to config/env-matrix.yaml.",
            )
        )
        workflow_cells = []

    valid_lanes = [lane for lane in lanes if isinstance(lane, dict)]
    valid_cells = [cell for cell in workflow_cells if isinstance(cell, dict)]
    diagnostics.extend(_validate_inventory_records(valid_lanes, valid_cells))
    runtime_policy_summary, runtime_policy_diagnostics = _validate_runtime_policy(document, valid_lanes, valid_cells)
    diagnostics.extend(runtime_policy_diagnostics)

    tox_result, tox_listing = _list_tox_environments(project_root)
    if tox_result is None:
        diagnostics.append(
            _diagnostic(
                "tox",
                "tox-unavailable",
                "cannot resolve the tox environment list because `tox` is not installed or not on PATH",
                "Install the development extra with `python -m pip install 'pytest-cuke[env-matrix]'` "
                "or install tox>=4.2, then retry.",
            )
        )
        tox_listing = []
    elif tox_result.returncode != 0:
        detail = (tox_result.stderr or tox_result.stdout).strip()
        diagnostics.append(
            _diagnostic(
                "tox",
                "tox-list-failed",
                f"`tox list --no-desc` failed: {detail}",
                "Fix tox.ini and rerun `tox list --no-desc` from the repository root.",
            )
        )

    tox_environments, tox_selector_fragments, tox_listing_diagnostics = _classify_tox_listing(document, tox_listing)
    diagnostics.extend(tox_listing_diagnostics)

    support_ledger_summary, support_ledger_diagnostics = _validate_support_ledger(
        document,
        valid_lanes,
        valid_cells,
        set(tox_environments),
    )
    diagnostics.extend(support_ledger_diagnostics)
    capability_exclusions, capability_exclusion_diagnostics = _validate_capability_exclusions(document, valid_lanes)
    diagnostics.extend(capability_exclusion_diagnostics)
    historical_capability_exclusions, historical_capability_diagnostics = _validate_historical_capability_exclusions(
        document,
        valid_lanes,
    )
    diagnostics.extend(historical_capability_diagnostics)
    support_ledger_summary["historicalCapabilityExclusionCount"] = historical_capability_exclusions["count"]

    optional_integration_summary, optional_integration_diagnostics = _validate_optional_integration_inventory(
        document,
        valid_lanes,
        valid_cells,
    )
    diagnostics.extend(optional_integration_diagnostics)

    cell_index = _index_cells(valid_cells, diagnostics)
    workflow_results = _check_workflow_jobs(project_root, valid_cells, diagnostics)
    proof_lanes = _build_lane_proof(
        valid_lanes,
        cell_index,
        workflow_results,
        set(tox_environments),
        project_root,
        diagnostics,
        probe_lane_id=lane_id,
    )

    if lane_id is not None and not any(_lane_id(lane) == lane_id for lane in valid_lanes):
        diagnostics.append(
            _diagnostic(
                lane_id,
                "lane-not-found",
                f"requested environment lane {lane_id!r} is not present in the inventory",
                "Choose a lane ID listed in config/env-matrix.yaml.",
            )
        )

    report: dict[str, Any] = {
        "status": "fail" if diagnostics else "pass",
        "inventory": {
            "path": _display_inventory_path(selected_path),
            "requiredLaneCount": sum(_status(lane) == "required" for lane in valid_lanes),
            "toxEnvironments": tox_listing,
            "configuredToxEnvironments": tox_environments,
            "toxSelectorFragments": tox_selector_fragments,
            "workflowCells": valid_cells,
            "supportLedger": support_ledger_summary,
            "capabilityExclusions": capability_exclusions,
            "historicalCapabilityExclusions": historical_capability_exclusions,
            "runtimePolicy": runtime_policy_summary,
            "optionalIntegrations": optional_integration_summary,
        },
        "proof": {
            "tox": {
                "command": list(TOX_LIST_COMMAND),
                "environments": tox_listing,
                "configuredEnvironments": tox_environments,
                "selectorFragments": tox_selector_fragments,
            },
            "lanes": proof_lanes,
            "activeEnvironment": _active_environment(),
        },
    }
    if diagnostics:
        report["diagnostics"] = diagnostics
    return report


def _load_yaml_inventory(path: Path) -> dict[str, Any]:
    yaml = _yaml_module()
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"invalid YAML in {path}: {error}") from error
    if not isinstance(content, dict):
        raise ValueError(f"{path} must contain a YAML object at the document root")
    return content


def _yaml_module() -> Any:
    try:
        return importlib.import_module("yaml")
    except ImportError as error:
        raise ValueError(
            "PyYAML is required to read the environment inventory; install `pytest-cuke[env-matrix]`."
        ) from error


def _validate_inventory_records(
    lanes: list[dict[str, Any]],
    cells: list[dict[str, Any]],
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    lane_ids: set[str] = set()
    lanes_by_dimensions: dict[tuple[str, ...], list[tuple[str, str, set[str]]]] = {}
    for lane in lanes:
        lane_id = _lane_id(lane)
        if not lane_id:
            diagnostics.append(
                _diagnostic(
                    "inventory", "lane-id-missing", "a lane has no ID", "Give every lane a unique kebab-case id."
                )
            )
            continue
        if lane_id in lane_ids:
            diagnostics.append(
                _diagnostic(lane_id, "duplicate-lane-id", f"lane ID {lane_id!r} is duplicated", "Keep lane IDs unique.")
            )
        lane_ids.add(lane_id)
        status = _status(lane)
        if status not in _SUPPORTED_STATUSES:
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "invalid-status",
                    f"unsupported lane status {status!r}",
                    "Use required, optional, or unsupported.",
                )
            )
        dimensions = tuple(
            str(lane.get(key) or "").strip().casefold() for key in ("runtime", "python", "platform", "capability")
        )
        pytest_factors = _pytest_factors(lane.get("pytest"))
        if status in _SUPPORTED_STATUSES and all(dimensions) and pytest_factors:
            for other_id, other_status, other_pytest_factors in lanes_by_dimensions.get(dimensions, []):
                overlap = pytest_factors & other_pytest_factors
                if overlap and status != other_status:
                    diagnostics.append(
                        _diagnostic(
                            lane_id,
                            "lane-status-conflict",
                            f"lane {other_id!r} has status {other_status!r} and lane {lane_id!r} has status "
                            f"{status!r} for overlapping {dimensions[0]} Python {dimensions[1]}, pytest "
                            f"{', '.join(sorted(overlap))}, platform {dimensions[2]}, capability {dimensions[3]}",
                            "Align lane statuses, merge the records, or remove the stale entry.",
                        )
                    )
            lanes_by_dimensions.setdefault(dimensions, []).append((lane_id, status, pytest_factors))
        missing = [
            key for key in ("runtime", "python", "pytest", "platform", "capability") if lane.get(key) in (None, "", [])
        ]
        if missing:
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "lane-fields-missing",
                    f"lane is missing runtime dimensions: {', '.join(missing)}",
                    "Declare runtime, python, pytest, platform, and capability.",
                )
            )
        if status == "required":
            missing_required = [
                key
                for key in ("tox_env", "workflow_selector", "command", "prerequisites", "expected_carrier")
                if lane.get(key) in (None, "", [])
            ]
            if missing_required:
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "required-fields-missing",
                        f"required lane is missing: {', '.join(missing_required)}",
                        "Declare a resolvable tox environment, workflow selector, command, prerequisites, and carrier.",
                    )
                )
        if status == "unsupported" and (lane.get("workflow_selector") or lane.get("tox_env")):
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "unsupported-lane-selected",
                    "unsupported lane has an active tox or workflow selector",
                    "Remove active selectors and retain the source-backed exclusion reason.",
                )
            )
        if status == "unsupported" and not lane.get("reason"):
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "unsupported-reason-missing",
                    "unsupported lane has no reason",
                    "Record the package floor, upstream constraint, or other source-backed reason.",
                )
            )
        if status == "unsupported" and not lane.get("source_evidence"):
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "unsupported-source-missing",
                    "unsupported lane has no source evidence",
                    "Add a source URL or repository reference that supports the exclusion.",
                )
            )
        prerequisites = lane.get("prerequisites")
        if status != "unsupported" and not isinstance(prerequisites, list):
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "prerequisites-invalid",
                    "prerequisites must be a list",
                    "List each required package or command and its install remedy.",
                )
            )
        elif isinstance(prerequisites, list):
            for prerequisite in prerequisites:
                if (
                    not isinstance(prerequisite, dict)
                    or not prerequisite.get("type")
                    or not prerequisite.get("name")
                    or not prerequisite.get("remedy")
                ):
                    diagnostics.append(
                        _diagnostic(
                            lane_id,
                            "prerequisite-remedy-missing",
                            "a prerequisite must name its type, package/command, and install remedy",
                            "Add type, name, and remedy to each prerequisite.",
                        )
                    )
                    break
        carrier = lane.get("expected_carrier")
        if status != "unsupported" and not _is_carrier(carrier):
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "carrier-invalid",
                    "required or optional lane has no runnable expected_carrier",
                    "Declare a carrier kind and an existing path or command.",
                )
            )

    cell_ids: set[str] = set()
    for cell in cells:
        cell_id = _cell_id(cell)
        if not cell_id:
            diagnostics.append(
                _diagnostic(
                    "workflow", "cell-id-missing", "a workflow cell has no ID", "Give every workflow cell a unique id."
                )
            )
            continue
        if cell_id in cell_ids:
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "duplicate-cell-id",
                    f"workflow cell ID {cell_id!r} is duplicated",
                    "Keep workflow cell IDs unique.",
                )
            )
        cell_ids.add(cell_id)
        if not isinstance(cell.get("tox_envs"), list) or not cell.get("tox_envs"):
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "cell-tox-envs-missing",
                    "workflow cell has no tox_envs list",
                    "List the exact tox environments selected by this workflow cell.",
                )
            )
    return diagnostics


_RUNTIME_POLICY_EVIDENCE_FIELDS = {
    "python",
    "pytest",
    "platform",
    "architecture",
    "git_sha",
    "command",
    "selected_tests",
    "passed_tests",
    "outcome",
    "job_url",
    "run_url",
}


def _expected_runtime_cell_keys() -> set[tuple[str, str, str, str]]:
    expected = {
        (
            "cpython",
            f"3.{minor}",
            platform_name,
            "x86_64" if minor == 11 and platform_name == "linux" else "runner-native",
        )
        for minor in range(11, 16)
        for platform_name in ("linux", "macos", "windows")
    }
    expected.update({("pypy", "3.12", "linux", "x86_64"), ("graalpy", "3.13.14", "linux", "x86_64")})
    return expected


def _runtime_cell_key(cell: dict[str, Any]) -> tuple[str, str, str, str]:
    return tuple(str(cell.get(key, "")).strip().casefold() for key in ("runtime", "python", "platform", "architecture"))  # type: ignore[return-value]


def _validate_runtime_policy(
    document: dict[str, Any],
    lanes: list[dict[str, Any]],
    cells: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Validate current product runtime policy independently from its history."""
    diagnostics: list[dict[str, str]] = []
    policy = document.get("runtime_policy")
    if not isinstance(policy, dict):
        return (
            {"requiredCellCount": 0, "exclusionCount": 0, "pytestMinimum": None, "latestPytest": None},
            [
                _diagnostic(
                    "runtime-policy",
                    "runtime-policy-missing",
                    "inventory must declare the active runtime_policy separately from historical support data",
                    "Add canonical required runtime cells and source-backed runtime exclusions to the inventory.",
                )
            ],
        )

    pytest_policy = policy.get("pytest")
    if not isinstance(pytest_policy, dict):
        pytest_policy = {}
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-pytest-missing",
                "runtime_policy must declare its pytest minimum and latest required line",
                "Declare pytest minimum >=7.0 and the current latest pytest 9.x line.",
            )
        )
    pytest_minimum = pytest_policy.get("minimum")
    latest_pytest = pytest_policy.get("latest")
    if pytest_minimum != ">=7.0" or latest_pytest != "9.x":
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-pytest-range-invalid",
                f"runtime_policy pytest range is {pytest_minimum!r} through {latest_pytest!r}; expected >=7.0 and 9.x",
                "Keep pytest >=7 support and require the latest pytest 9.x line on each CPython runtime cell.",
            )
        )
    project = document.get("project")
    if isinstance(project, dict) and project.get("python_requirement") != ">=3.11":
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-python-minimum-mismatch",
                f"project Python requirement {project.get('python_requirement')!r} does not match >=3.11",
                "Align the environment inventory's project Python requirement with the active runtime policy.",
            )
        )
    if policy.get("python_requirement") != ">=3.11":
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-python-minimum-invalid",
                f"runtime policy Python requirement is {policy.get('python_requirement')!r}; expected >=3.11",
                "Declare the current supported product minimum as Python >=3.11.",
            )
        )

    required_cells = policy.get("required_cells")
    if not isinstance(required_cells, list) or not required_cells:
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-cells-missing",
                "runtime_policy.required_cells must be a non-empty canonical runtime matrix",
                "Add CPython 3.11-3.15 on all three platforms plus PyPy 3.12 and GraalPy 25.3 on Linux x86_64.",
            )
        )
        required_cells = []

    keyed_cells: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    duplicate_keys: set[tuple[str, str, str, str]] = set()
    cell_ids: set[str] = set()
    workflow_by_id = {_cell_id(cell): cell for cell in cells if _cell_id(cell)}
    for value in required_cells:
        if not isinstance(value, dict):
            diagnostics.append(
                _diagnostic(
                    "runtime-policy",
                    "runtime-policy-cell-invalid",
                    "a required runtime cell is not an object",
                    "Declare each cell with runtime, Python, platform, architecture, CI selector, "
                    "and evidence contract.",
                )
            )
            continue
        cell = value
        cell_id = str(cell.get("id") or "runtime-policy")
        key = _runtime_cell_key(cell)
        if (key[0] == "cpython" and key[1] == "3.10") or (key[0] == "pypy" and key[1] in {"3.10", "3.11"}):
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-obsolete-active-runtime",
                    f"historical runtime cell {key[:3]!r} is still marked as required support",
                    "Retain CPython 3.10 and PyPy 3.10/3.11 in source-backed exclusion history only; active runtime "
                    "cells are CPython 3.11-3.15 and PyPy 3.12.",
                )
            )
        if cell_id in cell_ids:
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-cell-id-duplicate",
                    f"runtime cell ID {cell_id!r} is duplicated",
                    "Keep runtime cell IDs unique.",
                )
            )
        cell_ids.add(cell_id)
        if key in keyed_cells:
            duplicate_keys.add(key)
        keyed_cells[key] = cell

        missing_dimensions = [
            name for name, part in zip(("runtime", "python", "platform", "architecture"), key, strict=True) if not part
        ]
        if missing_dimensions:
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-cell-dimensions-missing",
                    f"required runtime cell is missing: {', '.join(missing_dimensions)}",
                    "Declare the exact runtime, Python version, platform, and architecture for each cell.",
                )
            )

        for field in ("upstream_availability", "installability", "product_support", "required_ci", "measured_evidence"):
            if not isinstance(cell.get(field), dict):
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "runtime-policy-dimension-missing",
                        f"required runtime cell is missing its {field} record",
                        "Keep upstream availability, installability, product support, required CI, "
                        "and measured evidence separate.",
                    )
                )

        availability = cell.get("upstream_availability")
        if isinstance(availability, dict) and (
            availability.get("status") != "available" or not _has_source_evidence(availability.get("source_evidence"))
        ):
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-upstream-evidence-invalid",
                    "a required runtime must have upstream availability status and HTTP(S) source evidence",
                    "Cite the upstream runtime's official supported downloads or release page.",
                )
            )

        installability = cell.get("installability")
        if isinstance(installability, dict):
            acceptance = installability.get("acceptance")
            if (
                installability.get("status") != "required-acceptance"
                or not isinstance(acceptance, list)
                or not {
                    "core-install",
                    "core-tests",
                    "examples",
                }
                <= set(acceptance)
            ):
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "runtime-policy-installability-incomplete",
                        "required runtime cells must install the core package and accept core tests and examples",
                        "Declare core-install, core-tests, and examples in installability.acceptance "
                        "for every required cell.",
                    )
                )

        product_support = cell.get("product_support")
        if isinstance(product_support, dict) and product_support.get("status") != "supported":
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-product-support-invalid",
                    "required runtime cell is not marked as product-supported",
                    "Use product_support.status: supported only for active product runtime cells.",
                )
            )

        required_ci = cell.get("required_ci")
        if isinstance(required_ci, dict):
            selector = required_ci.get("workflow_cell")
            workflow_cell = workflow_by_id.get(str(selector)) if selector else None
            tox_envs = required_ci.get("tox_envs")
            if required_ci.get("status") != "required" or not isinstance(tox_envs, list) or not tox_envs:
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "runtime-policy-required-ci-invalid",
                        "required runtime cell must declare its active workflow selector and tox environments",
                        "Set required_ci.status to required and list its canonical workflow cell and tox environments.",
                    )
                )
            elif workflow_cell is None:
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "runtime-policy-workflow-cell-unresolved",
                        f"required CI selector {selector!r} is not present in workflow_cells",
                        "Add the matching canonical workflow cell or correct required_ci.workflow_cell.",
                    )
                )
            else:
                workflow_key = _runtime_cell_key(workflow_cell)
                if workflow_key != key:
                    diagnostics.append(
                        _diagnostic(
                            cell_id,
                            "runtime-policy-workflow-cell-mismatch",
                            f"workflow cell {selector!r} does not match runtime dimensions {key!r}",
                            "Keep one workflow cell per canonical runtime, Python, platform, and architecture tuple.",
                        )
                    )
                setup = cell.get("setup_python")
                if isinstance(setup, dict) and (
                    workflow_cell.get("setup_python_input") != setup.get("input")
                    or workflow_cell.get("expected_interpreter") != setup.get("expected_interpreter")
                ):
                    diagnostics.append(
                        _diagnostic(
                            cell_id,
                            "runtime-policy-workflow-setup-mismatch",
                            f"workflow cell {selector!r} does not carry the canonical setup-python contract",
                            "Copy setup_python.input and setup_python.expected_interpreter into "
                            "the workflow cell fields.",
                        )
                    )
                if cell.get("runtime_version") is not None and workflow_cell.get("runtime_version") != cell.get(
                    "runtime_version"
                ):
                    diagnostics.append(
                        _diagnostic(
                            cell_id,
                            "runtime-policy-workflow-runtime-version-mismatch",
                            f"workflow cell {selector!r} does not carry runtime version "
                            f"{cell.get('runtime_version')!r}",
                            "Keep runtime_version identical in the canonical policy and workflow cell.",
                        )
                    )
                selected_envs = workflow_cell.get("tox_envs")
                if not isinstance(selected_envs, list) or set(tox_envs) != set(selected_envs):
                    diagnostics.append(
                        _diagnostic(
                            cell_id,
                            "runtime-policy-tox-selection-mismatch",
                            f"workflow cell {selector!r} does not have the canonical runtime cell tox environment set",
                            "Keep required_ci.tox_envs identical to the matching workflow cell tox_envs.",
                        )
                    )
                matching_lanes = [
                    lane
                    for lane in lanes
                    if _status(lane) == "required"
                    and _runtime_cell_key(lane)[:3] == key[:3]
                    and str(lane.get("workflow_selector")) == str(selector)
                    and set(_split_tox_envs(lane.get("tox_env"))) & set(tox_envs)
                ]
                represented_envs = {
                    environment for lane in matching_lanes for environment in _split_tox_envs(lane.get("tox_env"))
                }
                if not set(tox_envs) <= represented_envs:
                    diagnostics.append(
                        _diagnostic(
                            cell_id,
                            "runtime-policy-lane-unresolved",
                            "one or more required runtime tox environments have no matching required lane",
                            "Represent each required runtime acceptance environment in an active required lane.",
                        )
                    )

        setup_python = cell.get("setup_python")
        if (
            not isinstance(setup_python, dict)
            or not setup_python.get("input")
            or not setup_python.get("expected_interpreter")
        ):
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-setup-python-missing",
                    "required runtime cell must declare setup-python input and expected interpreter",
                    "Set setup_python.input and setup_python.expected_interpreter for every required cell.",
                )
            )

        required_pytest_lines = cell.get("required_pytest_lines")
        if key[0] == "cpython" and (not isinstance(required_pytest_lines, list) or "9.x" not in required_pytest_lines):
            diagnostics.append(
                _diagnostic(
                    cell_id,
                    "runtime-policy-latest-pytest-missing",
                    "every required CPython cell must test the latest pytest 9.x line",
                    "Add 9.x to required_pytest_lines for every CPython 3.11-3.15 platform cell.",
                )
            )

        measured_evidence = cell.get("measured_evidence")
        if isinstance(measured_evidence, dict):
            fields = measured_evidence.get("fields")
            missing_fields = (
                _RUNTIME_POLICY_EVIDENCE_FIELDS - set(fields)
                if isinstance(fields, list)
                else _RUNTIME_POLICY_EVIDENCE_FIELDS
            )
            if measured_evidence.get("status") != "per-run" or missing_fields:
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "runtime-policy-evidence-fields-missing",
                        f"measured evidence is missing fields: {', '.join(sorted(missing_fields))}",
                        "Require Python, pytest, platform, architecture, SHA, command, selected/passed counts, "
                        "outcome, and job/run URLs.",
                    )
                )

    expected_keys = _expected_runtime_cell_keys()
    actual_keys = set(keyed_cells)
    if duplicate_keys or actual_keys != expected_keys:
        missing_keys = sorted(expected_keys - actual_keys)
        extra_keys = sorted(actual_keys - expected_keys)
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-canonical-cells-invalid",
                f"required runtime cells do not match the canonical support matrix; missing={missing_keys!r}, "
                f"extra={extra_keys!r}, duplicates={sorted(duplicate_keys)!r}",
                "Require CPython 3.11-3.15 on Linux, macOS, and Windows (with CPython 3.11/Linux on x86_64), "
                "PyPy 3.12 on Linux x86_64, and GraalPy 25.3/Python 3.13.14 on Linux x86_64.",
            )
        )

    expected_floor_lines = {
        ("cpython", "3.11", "linux", "x86_64"): "7.4.x",
        ("cpython", "3.12", "linux", "runner-native"): "8.4.x",
    }
    for key, floor_line in expected_floor_lines.items():
        floor_cell = keyed_cells.get(key)
        if floor_cell is not None and floor_line not in floor_cell.get("required_pytest_lines", []):
            diagnostics.append(
                _diagnostic(
                    str(floor_cell.get("id") or "runtime-policy"),
                    "runtime-policy-pytest-floor-missing",
                    f"required CPython {key[1]} Linux pytest floor {floor_line} is missing",
                    "Include pytest 7.4.x on CPython 3.11 Linux and pytest 8.4.x on CPython 3.12 Linux.",
                )
            )

    special_setup = {
        ("graalpy", "3.13.14", "linux", "x86_64"): ("graalpy-25.3", "3.13.14"),
        **{
            ("cpython", "3.15", platform_name, "runner-native"): ("3.15.0", "3.15.0")
            for platform_name in ("linux", "macos", "windows")
        },
    }
    for key, (setup_input, interpreter) in special_setup.items():
        setup_cell = keyed_cells.get(key)
        setup = setup_cell.get("setup_python") if setup_cell else None
        if setup_cell is not None and (
            not isinstance(setup, dict)
            or setup.get("input") != setup_input
            or setup.get("expected_interpreter") != interpreter
        ):
            diagnostics.append(
                _diagnostic(
                    str(setup_cell.get("id") or "runtime-policy"),
                    "runtime-policy-setup-python-mismatch",
                    f"setup-python must use input {setup_input!r} and expect interpreter {interpreter!r}",
                    "Pin GraalPy 25.3 and CPython 3.15.0 explicitly in the canonical runtime inventory.",
                )
            )
        if key[0] == "graalpy" and setup_cell is not None and setup_cell.get("runtime_version") != "25.3":
            diagnostics.append(
                _diagnostic(
                    str(setup_cell.get("id") or "runtime-policy"),
                    "runtime-policy-graalpy-version-mismatch",
                    f"GraalPy runtime version is {setup_cell.get('runtime_version')!r}; expected 25.3",
                    "Set runtime_version to 25.3 and Python to 3.13.14 for the GraalPy cell.",
                )
            )

    for lane in lanes:
        key = _runtime_cell_key(lane)
        if _status(lane) != "unsupported" and (
            (key[0] == "cpython" and key[1] == "3.10") or (key[0] == "pypy" and key[1] in {"3.10", "3.11"})
        ):
            diagnostics.append(
                _diagnostic(
                    _lane_id(lane) or "runtime-policy",
                    "runtime-policy-obsolete-active-runtime",
                    f"historical runtime lane {key[:3]!r} is still marked active",
                    "Retain CPython 3.10 and PyPy 3.10/3.11 in the historical ledger only; "
                    "keep current lanes at CPython 3.11-3.15 and PyPy 3.12.",
                )
            )

    exclusions = policy.get("exclusions")
    if not isinstance(exclusions, list) or not exclusions:
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-exclusions-missing",
                "runtime_policy.exclusions must retain reasoned runtime exclusions",
                "Record unsupported runtime tuples with a reason and upstream or issue source evidence.",
            )
        )
        exclusions = []
    exclusion_ids: set[str] = set()
    for exclusion in exclusions:
        if not isinstance(exclusion, dict):
            diagnostics.append(
                _diagnostic(
                    "runtime-policy",
                    "runtime-policy-exclusion-invalid",
                    "a runtime policy exclusion is not an object",
                    "Declare ID, runtime, Python, reason, and source evidence for each excluded tuple.",
                )
            )
            continue
        exclusion_id = exclusion.get("id")
        if (
            not isinstance(exclusion_id, str)
            or not exclusion_id
            or exclusion_id in exclusion_ids
            or not exclusion.get("runtime")
            or not exclusion.get("python")
            or not isinstance(exclusion.get("reason"), str)
            or not exclusion["reason"].strip()
            or not _has_source_evidence(exclusion.get("source_evidence"))
        ):
            diagnostics.append(
                _diagnostic(
                    str(exclusion_id or "runtime-policy"),
                    "runtime-policy-exclusion-invalid",
                    "runtime exclusions need a unique ID, runtime tuple, reason, and HTTP(S) source evidence",
                    "Keep every unsupported runtime exclusion reasoned and linked to an upstream or issue source.",
                )
            )
        if isinstance(exclusion_id, str):
            exclusion_ids.add(exclusion_id)
        availability = exclusion.get("upstream_availability")
        installability = exclusion.get("installability")
        support = exclusion.get("product_support")
        required_ci = exclusion.get("required_ci")
        measured_evidence = exclusion.get("measured_evidence")
        if (
            not isinstance(availability, dict)
            or availability.get("status") not in {"available", "unavailable", "unknown"}
            or not _has_source_evidence(availability.get("source_evidence"))
            or not isinstance(installability, dict)
            or installability.get("status") not in {"incompatible", "not-assessed"}
            or not isinstance(installability.get("reason"), str)
            or not installability["reason"].strip()
            or not isinstance(support, dict)
            or support.get("status") != "unsupported"
            or not isinstance(support.get("reason"), str)
            or not support["reason"].strip()
            or not isinstance(required_ci, dict)
            or required_ci.get("status") != "excluded"
            or required_ci.get("workflow_cell") is not None
            or required_ci.get("tox_envs") != []
            or not isinstance(required_ci.get("reason"), str)
            or not required_ci["reason"].strip()
            or not isinstance(measured_evidence, dict)
            or measured_evidence.get("status") != "not-run"
            or not isinstance(measured_evidence.get("fields"), list)
            or not _RUNTIME_POLICY_EVIDENCE_FIELDS <= set(measured_evidence["fields"])
            or not isinstance(measured_evidence.get("reason"), str)
            or not measured_evidence["reason"].strip()
        ):
            diagnostics.append(
                _diagnostic(
                    str(exclusion_id or "runtime-policy"),
                    "runtime-policy-exclusion-dimensions-invalid",
                    "an excluded runtime must distinguish availability, installability, product support, required CI, "
                    "and measured evidence",
                    "Declare source-backed upstream_availability, installability.status and reason, unsupported "
                    "product_support, excluded required_ci, and not-run measured_evidence with the standard fields "
                    "and a reason.",
                )
            )
        exclusion_key = (
            str(exclusion.get("runtime", "")).casefold(),
            str(exclusion.get("python", "")).casefold(),
            str(exclusion.get("platform", "")).casefold(),
            str(exclusion.get("architecture", "")).casefold(),
        )
        if (
            exclusion_key in expected_keys
            and (exclusion_key[0], exclusion_key[1], exclusion_key[2], exclusion_key[3]) in actual_keys
        ):
            diagnostics.append(
                _diagnostic(
                    str(exclusion_id or "runtime-policy"),
                    "runtime-policy-exclusion-conflict",
                    f"excluded runtime tuple {exclusion_key!r} is also an active required cell",
                    "Remove the active runtime cell or correct the exclusion tuple.",
                )
            )

    expected_exclusion_keys = {
        ("cpython", "3.10", "all", "all"),
        ("pypy", "3.10", "all", "all"),
        ("pypy", "3.11", "all", "all"),
        ("pypy", "3.12", "macos", "all"),
        ("pypy", "3.12", "windows", "all"),
    }
    actual_exclusion_keys = {
        (
            str(exclusion.get("runtime", "")).casefold(),
            str(exclusion.get("python", "")).casefold(),
            str(exclusion.get("platform", "")).casefold(),
            str(exclusion.get("architecture", "")).casefold(),
        )
        for exclusion in exclusions
        if isinstance(exclusion, dict)
    }
    if actual_exclusion_keys != expected_exclusion_keys:
        diagnostics.append(
            _diagnostic(
                "runtime-policy",
                "runtime-policy-canonical-exclusions-invalid",
                "runtime exclusions must retain CPython 3.10 below the product floor, retired PyPy 3.10/3.11, "
                "and PyPy 3.12 on macOS/Windows; "
                f"missing={sorted(expected_exclusion_keys - actual_exclusion_keys)!r}, "
                f"extra={sorted(actual_exclusion_keys - expected_exclusion_keys)!r}",
                "Keep CPython 3.10 and PyPy 3.10/3.11 as historical unsupported rows and PyPy 3.12 macOS/Windows "
                "as source-backed platform exclusions while active support uses CPython 3.11-3.15 and PyPy 3.12 "
                "on Linux x86_64.",
            )
        )

    return (
        {
            "requiredCellCount": len(keyed_cells),
            "exclusionCount": len(exclusions),
            "pytestMinimum": pytest_minimum,
            "latestPytest": latest_pytest,
            "evidenceFields": sorted(_RUNTIME_POLICY_EVIDENCE_FIELDS),
        },
        diagnostics,
    )


def _validate_support_ledger(
    document: dict[str, Any],
    lanes: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    tox_environments: set[str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Check that support history, active tox lanes, and exclusions agree."""
    diagnostics: list[dict[str, str]] = []
    ledger = document.get("support_ledger")
    if not isinstance(ledger, dict):
        return (
            {"historicalCellCount": 0, "laneProvenanceCount": 0, "exclusionCount": 0, "originCounts": {}},
            [
                _diagnostic(
                    "support-ledger",
                    "support-ledger-missing",
                    "inventory must contain a structured support_ledger",
                    "Record the pinned historical reference, retained cells, active tox provenance, and exclusions.",
                )
            ],
        )

    reference = ledger.get("historical_reference")
    expected_reference = {
        "repository": "elchupanebrej/pytest-bdd-ng",
        "revision": "fb5f16f11f3f66fce97a5eeb5f5a862ab71949ce",
        "tox_file": "tox.ini",
        "workflow_file": ".github/workflows/main.yml",
    }
    if reference != expected_reference:
        diagnostics.append(
            _diagnostic(
                "support-ledger",
                "historical-reference-invalid",
                "historical_reference must pin the source repository, revision, tox file, and workflow file",
                "Use the exact R reference recorded in the compatibility acceptance baseline.",
            )
        )

    historical_cells = ledger.get("historical_cells")
    historical_cell_count = 0
    historical_cell_keys: set[tuple[str, str, str]] = set()
    if not isinstance(historical_cells, list) or len(historical_cells) != 12:
        diagnostics.append(
            _diagnostic(
                "support-ledger",
                "historical-cell-count-invalid",
                "support_ledger.historical_cells must retain the twelve frozen #149 cells",
                "Record CPython 3.10-3.12 on Linux, CPython 3.13-3.14 on all three platforms, and PyPy 3.11 "
                "on all three platforms.",
            )
        )
        historical_cells = historical_cells if isinstance(historical_cells, list) else []
    for item in historical_cells:
        if not isinstance(item, dict):
            diagnostics.append(
                _diagnostic(
                    "support-ledger",
                    "historical-cell-invalid",
                    "a historical cell record is not an object",
                    "Declare runtime, Python, platform, required disposition, and source evidence.",
                )
            )
            continue
        runtime, python, platform_name = (item.get(key) for key in ("runtime", "python", "platform"))
        key = (str(runtime), str(python), str(platform_name))
        historical_cell_count += 1
        if (
            not all(isinstance(value, str) and value for value in (runtime, python, platform_name))
            or item.get("disposition") != "required"
            or not _has_source_evidence(item.get("source_evidence"))
        ):
            diagnostics.append(
                _diagnostic(
                    str(item.get("id") or "support-ledger"),
                    "historical-cell-invalid",
                    "historical cells require runtime, Python, platform, required disposition, and source evidence",
                    "Keep each frozen cell source-backed and mark it required.",
                )
            )
        if key in historical_cell_keys:
            diagnostics.append(
                _diagnostic(
                    str(item.get("id") or "support-ledger"),
                    "historical-cell-duplicate",
                    f"historical cell {key!r} is duplicated",
                    "Keep exactly one record for each frozen runtime/Python/platform tuple.",
                )
            )
        historical_cell_keys.add(key)

    lane_by_id = {_lane_id(lane): lane for lane in lanes if _lane_id(lane)}
    active_env_lanes: dict[str, list[dict[str, Any]]] = {}
    for lane in lanes:
        if _status(lane) == "unsupported":
            continue
        for environment in _split_tox_envs(lane.get("tox_env")):
            active_env_lanes.setdefault(environment, []).append(lane)

    provenance = ledger.get("lane_provenance")
    provenance_count = 0
    origin_counts: dict[str, int] = {}
    provenance_ids: set[str] = set()
    provenance_envs: set[str] = set()
    if not isinstance(provenance, list) or not provenance:
        diagnostics.append(
            _diagnostic(
                "support-ledger",
                "lane-provenance-missing",
                "support_ledger.lane_provenance must identify each active tox environment",
                "Add a source-backed origin and required/manual disposition for every resolved environment.",
            )
        )
        provenance = provenance if isinstance(provenance, list) else []
    for item in provenance:
        if not isinstance(item, dict):
            diagnostics.append(
                _diagnostic(
                    "support-ledger",
                    "lane-provenance-invalid",
                    "a lane provenance record is not an object",
                    "Declare id, lane_id, tox_env, origin, disposition, and source evidence.",
                )
            )
            continue
        provenance_count += 1
        provenance_id = item.get("id")
        lane_id = item.get("lane_id")
        provenance_environment = item.get("tox_env")
        provenance_origin = item.get("origin")
        provenance_disposition = item.get("disposition")
        if (
            not isinstance(provenance_id, str)
            or not provenance_id
            or not isinstance(lane_id, str)
            or not lane_id
            or not isinstance(provenance_environment, str)
            or not provenance_environment
            or not isinstance(provenance_origin, str)
            or provenance_origin not in {"historical", "added", "preserved-current"}
            or not isinstance(provenance_disposition, str)
            or provenance_disposition not in {"required", "manual"}
            or not _has_source_evidence(item.get("source_evidence"))
        ):
            diagnostics.append(
                _diagnostic(
                    str(provenance_id or "support-ledger"),
                    "lane-provenance-invalid",
                    "lane provenance requires an ID, active lane/tox environment, valid origin/disposition, and "
                    "source evidence",
                    "Use historical, added, or preserved-current origin and required or manual disposition.",
                )
            )
            continue
        if provenance_id in provenance_ids:
            diagnostics.append(
                _diagnostic(
                    provenance_id,
                    "lane-provenance-id-duplicate",
                    f"lane provenance ID {provenance_id!r} is duplicated",
                    "Give every provenance row a unique ID.",
                )
            )
        provenance_ids.add(provenance_id)
        origin_counts[provenance_origin] = origin_counts.get(provenance_origin, 0) + 1
        if provenance_environment in provenance_envs:
            diagnostics.append(
                _diagnostic(
                    provenance_id,
                    "lane-provenance-environment-duplicate",
                    f"tox environment {provenance_environment!r} has more than one provenance record",
                    "Keep one provenance record for each concrete active tox environment.",
                )
            )
        provenance_envs.add(provenance_environment)
        provenance_lane = lane_by_id.get(lane_id)
        if (
            provenance_lane is None
            or _status(provenance_lane) == "unsupported"
            or provenance_environment not in _split_tox_envs(provenance_lane.get("tox_env"))
        ):
            diagnostics.append(
                _diagnostic(
                    provenance_id,
                    "lane-provenance-lane-unresolved",
                    f"provenance references lane {lane_id!r} without active tox environment {provenance_environment!r}",
                    "Point the provenance row at an active inventory lane containing this exact tox environment.",
                )
            )
        if provenance_environment not in tox_environments:
            diagnostics.append(
                _diagnostic(
                    provenance_id,
                    "lane-provenance-tox-unresolved",
                    f"provenance tox environment {provenance_environment!r} is not present in `tox list --no-desc`",
                    "Restore the exact tox environment or remove the stale provenance row.",
                )
            )
        provenance_lane_status = _status(provenance_lane) if provenance_lane is not None else ""
        selected_in_ci = any(
            provenance_environment in cell.get("tox_envs", [])
            for cell in cells
            if isinstance(cell, dict) and isinstance(cell.get("tox_envs"), list)
        )
        if provenance_disposition == "required" and (provenance_lane_status != "required" or not selected_in_ci):
            diagnostics.append(
                _diagnostic(
                    provenance_id,
                    "lane-provenance-required-not-selected",
                    f"required provenance for {provenance_environment!r} is not represented by a required CI lane",
                    "Select the environment from a required workflow cell or mark it manual if it is not in CI.",
                )
            )
        if provenance_disposition == "manual" and selected_in_ci:
            diagnostics.append(
                _diagnostic(
                    provenance_id,
                    "lane-provenance-manual-selected",
                    f"manual provenance for {provenance_environment!r} is selected by a workflow cell",
                    "Mark the lane required or remove it from automatic workflow cells.",
                )
            )

    for environment in sorted(set(active_env_lanes) - provenance_envs):
        lane_id = _lane_id(active_env_lanes[environment][0])
        diagnostics.append(
            _diagnostic(
                lane_id,
                "lane-provenance-environment-missing",
                f"active tox environment {environment!r} has no support provenance",
                "Add a lane_provenance row for every active environment in config/env-matrix.yaml.",
            )
        )
    for environment in sorted(provenance_envs - set(active_env_lanes)):
        diagnostics.append(
            _diagnostic(
                "support-ledger",
                "lane-provenance-environment-orphaned",
                f"provenance tox environment {environment!r} has no active required or optional lane",
                "Remove stale provenance or restore the active lane.",
            )
        )

    exclusions = ledger.get("exclusions")
    exclusion_count = 0
    exclusion_keys: set[tuple[str, str, str, str]] = set()
    if not isinstance(exclusions, list) or len(exclusions) != 15:
        diagnostics.append(
            _diagnostic(
                "support-ledger",
                "historical-exclusion-count-invalid",
                "support_ledger.exclusions must contain the fifteen source-backed historical upstream exclusions",
                "Record pytest 7.0-7.2 on Python 3.12 and pytest 8.0-8.1 on Python 3.13 for all three platforms.",
            )
        )
        exclusions = exclusions if isinstance(exclusions, list) else []
    active_tuples: set[tuple[str, str, str, str]] = set()
    for lane in lanes:
        if _status(lane) == "unsupported":
            continue
        runtime = lane.get("runtime")
        python = lane.get("python")
        platform_name = lane.get("platform")
        for pytest_factor in _pytest_factors(lane.get("pytest")):
            active_tuples.add((str(runtime), str(python), pytest_factor, str(platform_name)))
    for item in exclusions:
        if not isinstance(item, dict):
            diagnostics.append(
                _diagnostic(
                    "support-ledger",
                    "historical-exclusion-invalid",
                    "a historical exclusion record is not an object",
                    "Declare runtime, Python, pytest, platform, basis, reason, and source evidence.",
                )
            )
            continue
        exclusion_count += 1
        excluded_runtime = item.get("runtime")
        excluded_python = item.get("python")
        excluded_pytest = item.get("pytest")
        excluded_platform = item.get("platform")
        exclusion_basis = item.get("basis")
        exclusion_reason = item.get("reason")
        if (
            not isinstance(excluded_runtime, str)
            or not excluded_runtime
            or not isinstance(excluded_python, str)
            or not excluded_python
            or not isinstance(excluded_pytest, str)
            or not excluded_pytest
            or not isinstance(excluded_platform, str)
            or not excluded_platform
            or not isinstance(exclusion_basis, str)
            or not exclusion_basis.strip()
            or not isinstance(exclusion_reason, str)
            or not exclusion_reason.strip()
            or not _has_source_evidence(item.get("source_evidence"))
        ):
            diagnostics.append(
                _diagnostic(
                    str(item.get("id") or "support-ledger"),
                    "historical-exclusion-invalid",
                    "historical exclusions require a complete tuple, basis, reason, and HTTP(S) source evidence",
                    "Add the source policy and the concrete reason the environment is not viable.",
                )
            )
            continue
        excluded_tuple = (excluded_runtime, excluded_python, excluded_pytest, excluded_platform)
        if excluded_tuple in exclusion_keys:
            diagnostics.append(
                _diagnostic(
                    str(item.get("id") or "support-ledger"),
                    "historical-exclusion-duplicate",
                    f"historical exclusion {excluded_tuple!r} is duplicated",
                    "Keep one exclusion record for each exact runtime/Python/pytest/platform tuple.",
                )
            )
        exclusion_keys.add(excluded_tuple)
        if excluded_tuple in active_tuples:
            diagnostics.append(
                _diagnostic(
                    str(item.get("id") or "support-ledger"),
                    "historical-exclusion-conflict",
                    f"excluded historical tuple {excluded_tuple!r} also appears in an active lane",
                    "Remove the active unsupported tuple or revise the source-backed exclusion decision.",
                )
            )

    return (
        {
            "historicalCellCount": historical_cell_count,
            "laneProvenanceCount": provenance_count,
            "exclusionCount": exclusion_count,
            "originCounts": origin_counts,
        },
        diagnostics,
    )


def _validate_capability_exclusions(
    document: dict[str, Any],
    lanes: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Validate source-backed exclusions for optional capabilities on supported runtimes."""
    diagnostics: list[dict[str, str]] = []
    exclusions = document.get("capability_exclusions", [])
    if not isinstance(exclusions, list):
        return (
            {"count": 0, "entries": []},
            [
                _diagnostic(
                    "capability-exclusions",
                    "capability-exclusions-invalid",
                    "capability_exclusions must be a list",
                    "Declare capability-specific unsupported combinations as a list of source-backed records.",
                )
            ],
        )

    seen_ids: set[str] = set()
    seen_dimensions: set[tuple[str, str, str, str]] = set()
    entries: list[dict[str, Any]] = []
    supported_dimensions = {
        (
            str(lane.get("runtime", "")).casefold(),
            str(lane.get("python", "")).casefold(),
            str(lane.get("platform", "")).casefold(),
        )
        for lane in lanes
        if _status(lane) in {"required", "optional"}
    }
    active_capabilities = {
        (
            str(lane.get("runtime", "")).casefold(),
            str(lane.get("python", "")).casefold(),
            str(lane.get("platform", "")).casefold(),
            str(lane.get("capability", "")).casefold(),
        )
        for lane in lanes
        if _status(lane) in {"required", "optional"}
    }

    for item in exclusions:
        if not isinstance(item, dict):
            diagnostics.append(
                _diagnostic(
                    "capability-exclusions",
                    "capability-exclusion-invalid",
                    "a capability exclusion record is not an object",
                    "Declare ID, runtime, Python, platform, capability, unsupported status, basis, reason, and "
                    "source evidence.",
                )
            )
            continue

        exclusion_id = item.get("id")
        runtime = item.get("runtime")
        python = item.get("python")
        platform_name = item.get("platform")
        capability = item.get("capability")
        status = item.get("status")
        basis = item.get("basis")
        reason = item.get("reason")
        dimensions = (
            str(runtime or "").casefold(),
            str(python or "").casefold(),
            str(platform_name or "").casefold(),
        )
        key = (*dimensions, str(capability or "").casefold())
        if (
            not isinstance(exclusion_id, str)
            or not exclusion_id
            or not isinstance(runtime, str)
            or not runtime
            or not isinstance(python, str)
            or not python
            or not isinstance(platform_name, str)
            or not platform_name
            or not isinstance(capability, str)
            or not capability
            or status != "unsupported"
            or not isinstance(basis, str)
            or not basis.strip()
            or not isinstance(reason, str)
            or not reason.strip()
            or not _has_source_evidence(item.get("source_evidence"))
        ):
            diagnostics.append(
                _diagnostic(
                    str(exclusion_id or "capability-exclusions"),
                    "capability-exclusion-invalid",
                    "capability exclusions require ID, runtime, Python, platform, capability, unsupported status, "
                    "basis, reason, and HTTP(S) source evidence",
                    "Add the exact supported-runtime capability pair, explain the upstream constraint, and cite "
                    "its source.",
                )
            )
            continue

        if exclusion_id in seen_ids:
            diagnostics.append(
                _diagnostic(
                    exclusion_id,
                    "capability-exclusion-id-duplicate",
                    f"capability exclusion ID {exclusion_id!r} is duplicated",
                    "Give each capability exclusion a unique ID.",
                )
            )
        seen_ids.add(exclusion_id)
        if key in seen_dimensions:
            diagnostics.append(
                _diagnostic(
                    exclusion_id,
                    "capability-exclusion-duplicate",
                    f"capability exclusion {key!r} is duplicated",
                    "Keep one record for each runtime/Python/platform/capability tuple.",
                )
            )
        seen_dimensions.add(key)

        if dimensions not in supported_dimensions:
            diagnostics.append(
                _diagnostic(
                    exclusion_id,
                    "capability-exclusion-runtime-unavailable",
                    f"capability exclusion {key!r} has no required or optional base runtime lane",
                    "Keep a required or optional base lane when excluding only one capability.",
                )
            )
        if key in active_capabilities:
            diagnostics.append(
                _diagnostic(
                    exclusion_id,
                    "capability-exclusion-conflict",
                    f"unsupported capability {capability!r} is also active for {runtime} Python {python} "
                    f"on {platform_name}",
                    "Remove the active lane for this capability or revise the exclusion record.",
                )
            )
        entries.append(
            {
                "id": exclusion_id,
                "runtime": runtime,
                "python": python,
                "platform": platform_name,
                "capability": capability,
                "status": status,
                "basis": basis,
                "reason": reason,
                "sourceEvidence": item["source_evidence"],
            }
        )

    return {"count": len(entries), "entries": entries}, diagnostics


def _validate_historical_capability_exclusions(
    document: dict[str, Any],
    lanes: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Keep retired-runtime capability exclusions auditable without treating them as active lanes."""
    diagnostics: list[dict[str, str]] = []
    ledger = document.get("support_ledger")
    exclusions = ledger.get("historical_capability_exclusions") if isinstance(ledger, dict) else None
    if not isinstance(exclusions, list):
        return (
            {"count": 0, "entries": []},
            [
                _diagnostic(
                    "support-ledger",
                    "historical-capability-exclusions-missing",
                    "support_ledger.historical_capability_exclusions must preserve retired-runtime capability records",
                    "Move source-backed capability exclusions for retired runtimes out of the active capability list "
                    "and into the historical support ledger.",
                )
            ],
        )

    expected_keys = {
        ("pypy", "3.10", "windows", "debug-mcp"),
        ("pypy", "3.11", "windows", "debug-mcp"),
    }
    active_runtime_dimensions = {
        (
            str(lane.get("runtime", "")).casefold(),
            str(lane.get("python", "")).casefold(),
            str(lane.get("platform", "")).casefold(),
        )
        for lane in lanes
        if _status(lane) in {"required", "optional"}
    }
    seen_ids: set[str] = set()
    actual_keys: set[tuple[str, str, str, str]] = set()
    entries: list[dict[str, Any]] = []
    for item in exclusions:
        if not isinstance(item, dict):
            diagnostics.append(
                _diagnostic(
                    "support-ledger",
                    "historical-capability-exclusion-invalid",
                    "a historical capability exclusion is not an object",
                    "Declare source-backed runtime dimensions, capability, retired-runtime status, and reason.",
                )
            )
            continue
        exclusion_id = item.get("id")
        runtime = item.get("runtime")
        python = item.get("python")
        platform_name = item.get("platform")
        capability = item.get("capability")
        key = (
            str(runtime or "").casefold(),
            str(python or "").casefold(),
            str(platform_name or "").casefold(),
            str(capability or "").casefold(),
        )
        if (
            not isinstance(exclusion_id, str)
            or not exclusion_id
            or exclusion_id in seen_ids
            or item.get("status") != "unsupported"
            or item.get("historical_status") != "retired-runtime"
            or not isinstance(item.get("basis"), str)
            or not item["basis"].strip()
            or not isinstance(item.get("reason"), str)
            or not item["reason"].strip()
            or not _has_source_evidence(item.get("source_evidence"))
            or not all(key_part for key_part in key)
        ):
            diagnostics.append(
                _diagnostic(
                    str(exclusion_id or "support-ledger"),
                    "historical-capability-exclusion-invalid",
                    "historical capability exclusions require a unique ID, retired-runtime status, reason, and "
                    "HTTP(S) source evidence",
                    "Retain the exact old runtime/capability tuple with status: unsupported and "
                    "historical_status: retired-runtime.",
                )
            )
            continue
        seen_ids.add(exclusion_id)
        actual_keys.add(key)
        if key[:3] in active_runtime_dimensions:
            diagnostics.append(
                _diagnostic(
                    exclusion_id,
                    "historical-capability-exclusion-runtime-active",
                    f"historical capability tuple {key!r} still has an active base runtime lane",
                    "Move this record back to the active capability exclusions only if the runtime is still "
                    "supported; otherwise remove the active base lane.",
                )
            )
        entries.append(
            {
                "id": exclusion_id,
                "runtime": runtime,
                "python": python,
                "platform": platform_name,
                "capability": capability,
                "status": "unsupported",
                "historicalStatus": "retired-runtime",
                "basis": item["basis"],
                "reason": item["reason"],
                "sourceEvidence": item["source_evidence"],
            }
        )

    if actual_keys != expected_keys:
        diagnostics.append(
            _diagnostic(
                "support-ledger",
                "historical-capability-exclusions-invalid",
                "historical Debug MCP exclusions must retain PyPy 3.10 and 3.11 on Windows; "
                f"missing={sorted(expected_keys - actual_keys)!r}, extra={sorted(actual_keys - expected_keys)!r}",
                "Preserve the source-backed PyPy 3.10/3.11 Windows Debug MCP constraints as historical rows after "
                "retiring those runtimes.",
            )
        )
    return {"count": len(entries), "entries": entries}, diagnostics


def _validate_optional_integration_inventory(
    document: dict[str, Any],
    lanes: list[dict[str, Any]],
    cells: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Keep optional-package acceptance isolated from the required runtime matrix."""
    diagnostics: list[dict[str, str]] = []
    expected_environments = {
        "py313-pytest84-allure-coverage-lin",
        "py314-debug-mcp",
        "py314-struct-bdd",
        *{
            f"py314-pytestlatest-{gherkin}-xdist-coverage-{platform_suffix}"
            for gherkin in ("gherkin33", "gherkinlatest")
            for platform_suffix in ("lin", "mac", "win")
        },
    }
    project = document.get("project")
    evidence = project.get("evidence") if isinstance(project, dict) else None
    groups = evidence.get("aggregate_groups") if isinstance(evidence, dict) else None
    if not isinstance(groups, list) or "optional" not in groups:
        diagnostics.append(
            _diagnostic(
                "optional-integrations",
                "optional-evidence-group-missing",
                "project.evidence.aggregate_groups must include the separate optional group",
                "Add optional as its own evidence aggregation group for optional integration acceptance.",
            )
        )

    optional_cells = [cell for cell in cells if cell.get("job") == "optional-integrations"]
    environments = [
        environment
        for cell in optional_cells
        for environment in cell.get("tox_envs", [])
        if isinstance(environment, str)
    ]
    if set(environments) != expected_environments or len(environments) != len(set(environments)):
        diagnostics.append(
            _diagnostic(
                "optional-integrations",
                "optional-workflow-environments-invalid",
                "optional-integrations cells must select one isolated Allure lane, Debug MCP lane, StructBDD lane, "
                "and six Gherkin/xdist lanes; "
                f"missing={sorted(expected_environments - set(environments))!r}, "
                f"extra={sorted(set(environments) - expected_environments)!r}, duplicates="
                f"{sorted(environment for environment in environments if environments.count(environment) > 1)!r}",
                "Keep each Allure, Debug MCP, StructBDD, and Gherkin/xdist environment in its isolated "
                "optional-integrations workflow cell.",
            )
        )
    if any(len(cell.get("tox_envs", [])) != 1 for cell in optional_cells):
        diagnostics.append(
            _diagnostic(
                "optional-integrations",
                "optional-workflow-cell-not-isolated",
                "every optional integration workflow cell must contain exactly one tox environment",
                "Split optional integration cells by tox environment so each row has unique evidence identity.",
            )
        )

    required_runtime_environments = {
        environment
        for runtime_cell in document.get("runtime_policy", {}).get("required_cells", [])
        if isinstance(runtime_cell, dict)
        for environment in runtime_cell.get("required_ci", {}).get("tox_envs", [])
        if isinstance(environment, str)
    }
    overlap = sorted(set(environments) & required_runtime_environments)
    if overlap:
        diagnostics.append(
            _diagnostic(
                "optional-integrations",
                "optional-workflow-overlaps-required-runtime",
                "optional integration environments are included in required runtime acceptance: " + ", ".join(overlap),
                "Keep optional extras and Gherkin/xdist variants separate from the required core runtime matrix.",
            )
        )

    cell_by_environment = {
        environment: cell
        for cell in optional_cells
        for environment in cell.get("tox_envs", [])
        if isinstance(environment, str)
    }
    lane_by_environment: dict[str, list[dict[str, Any]]] = {}
    for lane in lanes:
        if _status(lane) == "unsupported":
            continue
        for environment in _split_tox_envs(lane.get("tox_env")):
            lane_by_environment.setdefault(environment, []).append(lane)

    for environment in sorted(expected_environments):
        cell = cell_by_environment.get(environment)
        candidates = lane_by_environment.get(environment, [])
        matching_lanes = [
            lane
            for lane in candidates
            if _status(lane) == "required"
            and cell is not None
            and str(lane.get("workflow_selector")) == str(cell.get("id"))
        ]
        if len(matching_lanes) != 1:
            diagnostics.append(
                _diagnostic(
                    "optional-integrations",
                    "optional-workflow-lane-unresolved",
                    f"optional tox environment {environment!r} must have one required lane selecting its workflow cell",
                    "Add a required acceptance lane linked to the matching optional-integrations cell.",
                )
            )
            continue
        lane = matching_lanes[0]
        extras = lane.get("extras", [])
        prerequisites = lane.get("prerequisites", [])
        package_requirements = (
            {
                re.sub(r"[-_.]+", "-", str(item.get("name", "")).casefold()): item
                for item in prerequisites
                if isinstance(item, dict) and item.get("type") == "python-package"
            }
            if isinstance(prerequisites, list)
            else {}
        )
        command_requirements = (
            {
                str(item.get("name", "")).casefold()
                for item in prerequisites
                if isinstance(item, dict) and item.get("type") == "command"
            }
            if isinstance(prerequisites, list)
            else set()
        )
        if "allure" in environment:
            allure = package_requirements.get("allure-python-commons-test")
            if (
                extras != ["allure"]
                or not isinstance(allure, dict)
                or allure.get("version") != "2.16.0"
                or "uv" not in command_requirements
            ):
                diagnostics.append(
                    _diagnostic(
                        str(lane.get("id") or "optional-integrations"),
                        "optional-allure-prerequisites-invalid",
                        "the Allure acceptance lane must declare the allure extra and "
                        "allure-python-commons-test 2.16.0, plus uv for isolated consumer installs",
                        "Declare extras: [allure], the pinned Allure test dependency, and uv on the isolated lane.",
                    )
                )
        elif "struct-bdd" in environment:
            required_loaders = {"hjson", "json5", "pyhocon", "pyyaml"}
            missing_loaders = sorted(required_loaders - package_requirements.keys())
            if extras != ["struct-bdd"] or missing_loaders or "uv" not in command_requirements:
                diagnostics.append(
                    _diagnostic(
                        str(lane.get("id") or "optional-integrations"),
                        "optional-struct-bdd-prerequisites-invalid",
                        "the StructBDD acceptance lane must declare the struct-bdd extra, all four loader packages, "
                        f"and uv as a command prerequisite; missing loaders={missing_loaders!r}, "
                        f"uv declared={'uv' in command_requirements}",
                        "Declare extras: [struct-bdd], hjson/json5/pyhocon/PyYAML package prerequisites, and uv "
                        "for isolated consumer installs.",
                    )
                )
        elif "debug-mcp" in environment:
            required_packages = {
                "mcp-pdb": ">=0.6,<0.7",
                "mcp": ">=1.24,<2",
                "uvicorn": ">=0.34",
                "pydantic": ">=2.0.3",
            }
            missing_or_mismatched = {
                package: requirement
                for package, requirement in required_packages.items()
                if not isinstance(package_requirements.get(package), dict)
                or package_requirements[package].get("version") != requirement
            }
            if extras != ["debug-mcp"] or missing_or_mismatched or "uv" not in command_requirements:
                diagnostics.append(
                    _diagnostic(
                        str(lane.get("id") or "optional-integrations"),
                        "optional-debug-mcp-prerequisites-invalid",
                        "the Debug MCP acceptance lane must declare the debug-mcp extra, its supported MCP package "
                        f"requirements, and uv as a command prerequisite; invalid packages={missing_or_mismatched!r}, "
                        f"uv declared={'uv' in command_requirements}",
                        "Declare extras: [debug-mcp], mcp-pdb>=0.6,<0.7, mcp>=1.24,<2, uvicorn>=0.34, "
                        "pydantic>=2.0.3, and uv for isolated consumer installs.",
                    )
                )
        else:
            xdist = package_requirements.get("pytest-xdist")
            gherkin = package_requirements.get("gherkin-official")
            expected_gherkin = "gherkin-official>=33,<34" if "gherkin33" in environment else "gherkin-official"
            if (
                extras != []
                or not isinstance(xdist, dict)
                or xdist.get("version") != "<4"
                or not isinstance(gherkin, dict)
                or gherkin.get("requirement") != expected_gherkin
            ):
                diagnostics.append(
                    _diagnostic(
                        str(lane.get("id") or "optional-integrations"),
                        "optional-xdist-prerequisites-invalid",
                        f"the Gherkin/xdist lane {environment!r} must declare pytest-xdist<4 and {expected_gherkin}",
                        "Keep pytest-xdist and the selected Gherkin dependency as explicit "
                        "isolated-lane prerequisites.",
                    )
                )

    return (
        {
            "cellCount": len(optional_cells),
            "environmentCount": len(environments),
            "environments": sorted(environments),
            "aggregateGroup": "optional" if isinstance(groups, list) and "optional" in groups else None,
        },
        diagnostics,
    )


def _has_source_evidence(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, str) and item.startswith(("https://", "http://")) for item in value)


def _pytest_factors(value: Any) -> set[str]:
    """Expand declared pytest minor ranges so overlapping lane statuses are comparable."""
    factors = value if isinstance(value, list) else [value]
    versions: set[str] = set()
    for factor in factors:
        if not isinstance(factor, (str, int, float)) or isinstance(factor, bool):
            continue
        version = str(factor).strip().casefold().replace(" ", "")
        match = re.fullmatch(r"(\d+)\.(\d+)-(\d+)\.(\d+)", version)
        if match is None:
            if version:
                versions.add(version)
            continue

        major, minor, end_major, end_minor = (int(part) for part in match.groups())
        current = (major, minor)
        end = (end_major, end_minor)
        if current > end:
            versions.add(version)
            continue
        while current <= end:
            versions.add(f"{current[0]}.{current[1]}")
            current = (current[0] + 1, 0) if current[1] == 9 else (current[0], current[1] + 1)
    return versions


def _index_cells(cells: list[dict[str, Any]], diagnostics: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for cell in cells:
        cell_id = _cell_id(cell)
        if cell_id:
            index[cell_id] = cell
    for cell_id, cell in index.items():
        for env_name in cell.get("tox_envs", []):
            if not isinstance(env_name, str) or not env_name.strip():
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "cell-tox-env-invalid",
                        "workflow cell contains an empty tox environment",
                        "Use exact names from `tox list --no-desc`.",
                    )
                )
    return index


def _list_tox_environments(project_root: Path) -> tuple[subprocess.CompletedProcess[str] | None, list[str]]:
    executable = shutil.which("tox")
    if executable is None:
        return None, []
    command = [executable, *TOX_LIST_COMMAND[1:]]
    try:
        result = subprocess.run(  # noqa: S603 -- command is the fixed tox list invocation.
            command, cwd=project_root, capture_output=True, text=True, check=False, timeout=120
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        failed = subprocess.CompletedProcess(command, 127, "", str(error))
        return failed, []
    names = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.strip().startswith("All environments:")
    ]
    return result, names


def _classify_tox_listing(
    document: dict[str, Any],
    tox_listing: list[str],
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    """Separate concrete tox environments from bare conditional-factor labels."""
    diagnostics: list[dict[str, str]] = []
    project = document.get("project")
    configured_fragments = project.get("tox_selector_fragments") if isinstance(project, dict) else None
    if not isinstance(configured_fragments, list) or any(
        not isinstance(fragment, str) or not fragment.strip() for fragment in configured_fragments
    ):
        diagnostics.append(
            _diagnostic(
                "tox-inventory",
                "tox-selector-fragments-invalid",
                "project.tox_selector_fragments must list bare tox factor labels separately from environments",
                "Declare conditional labels such as pytest70 and allure as selector fragments, not tox lanes.",
            )
        )
        configured_fragments = []

    selector_fragments = [str(fragment).strip() for fragment in configured_fragments]
    if len(selector_fragments) != len(set(selector_fragments)):
        diagnostics.append(
            _diagnostic(
                "tox-inventory",
                "tox-selector-fragments-duplicate",
                "project.tox_selector_fragments contains duplicate labels",
                "Keep each conditional tox factor label once in the selector fragment list.",
            )
        )

    active_environment_names = {
        environment
        for lane in document.get("lanes", [])
        if isinstance(lane, dict) and _status(lane) != "unsupported"
        for environment in _split_tox_envs(lane.get("tox_env"))
    }
    active_environment_names.update(
        environment
        for cell in document.get("workflow_cells", [])
        if isinstance(cell, dict)
        for environment in cell.get("tox_envs", [])
        if isinstance(environment, str)
    )
    fragments_used_as_environments = sorted(set(selector_fragments) & active_environment_names)
    if fragments_used_as_environments:
        diagnostics.append(
            _diagnostic(
                "tox-inventory",
                "tox-selector-fragment-used-as-environment",
                "bare tox factor labels are declared as active environments: "
                + ", ".join(fragments_used_as_environments),
                "Keep only concrete configured env_list entries or expanded tox environments "
                "in workflow cells and lanes.",
            )
        )

    raw_names = set(tox_listing)
    concrete_names = [name for name in tox_listing if name not in set(selector_fragments)]
    undeclared_names = sorted(raw_names - active_environment_names - set(selector_fragments))
    if undeclared_names:
        diagnostics.append(
            _diagnostic(
                "tox-inventory",
                "tox-listing-entry-unclassified",
                "tox list includes entries that are not declared as concrete environments or selector fragments: "
                + ", ".join(undeclared_names),
                "Add each concrete environment to the inventory, or declare bare conditional factor labels in "
                "project.tox_selector_fragments.",
            )
        )
    return concrete_names, selector_fragments, diagnostics


def _check_workflow_jobs(
    project_root: Path,
    cells: list[dict[str, Any]],
    diagnostics: list[dict[str, str]],
) -> dict[str, tuple[bool, str]]:
    workflow_jobs: dict[str, set[str]] = {}
    for cell in cells:
        workflow_path = _workflow_path(project_root, cell)
        job_id = str(cell.get("job", ""))
        if job_id not in workflow_jobs:
            workflow_jobs[job_id] = _load_workflow_jobs(workflow_path)
        if job_id not in workflow_jobs[job_id]:
            diagnostics.append(
                _diagnostic(
                    _cell_id(cell),
                    "workflow-job-unresolved",
                    f"workflow job {job_id!r} is not defined in {workflow_path.relative_to(project_root)}",
                    f"Add job {job_id!r} to the named workflow or correct the inventory selector.",
                )
            )
    return {
        cell_id: _cell_selected(project_root, _workflow_path(project_root, cell), cell)
        for cell in cells
        if (cell_id := _cell_id(cell))
    }


def _workflow_path(project_root: Path, cell: dict[str, Any]) -> Path:
    configured = cell.get("workflow")
    if isinstance(configured, str) and configured:
        return project_root / configured
    if cell.get("job") == "native-go-parser":
        return project_root / ".github" / "workflows" / "native-go-parser.yml"
    return project_root / ".github" / "workflows" / "main.yml"


def _load_workflow_jobs(path: Path) -> set[str]:
    yaml = _yaml_module()
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError):
        return set()
    jobs = document.get("jobs") if isinstance(document, dict) else None
    return set(jobs) if isinstance(jobs, dict) else set()


def _cell_selected(project_root: Path, workflow_path: Path, cell: dict[str, Any]) -> tuple[bool, str]:
    """Confirm that the configured workflow job consumes this inventory cell."""
    job_id = str(cell.get("job", ""))
    try:
        content = workflow_path.read_text(encoding="utf-8")
    except OSError:
        return False, f"workflow file {workflow_path} cannot be read"
    command = f"scripts/env_matrix.py --job {job_id}"
    if command not in content:
        return False, f"workflow does not generate a matrix with {command!r}"
    yaml = _yaml_module()
    try:
        workflow = yaml.safe_load(content)
    except (ValueError, yaml.YAMLError):
        return False, f"workflow file {workflow_path} is not valid YAML"
    jobs = workflow.get("jobs") if isinstance(workflow, dict) else None
    job = jobs.get(job_id) if isinstance(jobs, dict) else None
    strategy = job.get("strategy") if isinstance(job, dict) else None
    matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
    selected_cells = matrix.get("cell") if isinstance(matrix, dict) else None
    if not isinstance(selected_cells, str) or not isinstance(jobs, dict) or not isinstance(job, dict):
        return False, f"job {job_id!r} has no matrix.cell expression"

    dependencies = job.get("needs")
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    if not isinstance(dependencies, list) or len(dependencies) != 1:
        return False, f"job {job_id!r} must depend on one inventory matrix selector job"
    selector_job_id = dependencies[0]
    selector_job = jobs.get(selector_job_id) if isinstance(selector_job_id, str) else None
    if not isinstance(selector_job, dict):
        return False, f"job {job_id!r} depends on an undefined matrix selector job"

    steps = selector_job.get("steps")
    outputs = selector_job.get("outputs")
    if not isinstance(steps, list) or not isinstance(outputs, dict):
        return False, f"selector job {selector_job_id!r} has no steps or declared outputs"
    matching_steps = [
        step
        for step in steps
        if isinstance(step, dict)
        and isinstance(step.get("id"), str)
        and f"scripts/env_matrix.py --job {job_id}" in str(step.get("run", ""))
    ]
    if len(matching_steps) != 1:
        return False, f"selector job {selector_job_id!r} does not run exactly one {command!r} step"

    selector_step = matching_steps[0]
    step_id = selector_step["id"]
    if "--github-output" not in str(selector_step.get("run", "")):
        return (
            False,
            f"selector step {step_id!r} for job {job_id!r} must pass --github-output to expose its matrix output",
        )
    matching_outputs = [
        name
        for name, value in outputs.items()
        if isinstance(name, str) and value == f"${{{{ steps.{step_id}.outputs.cells }}}}"
    ]
    if len(matching_outputs) != 1:
        return False, f"selector job {selector_job_id!r} does not expose exactly one output for step {step_id!r}"

    expected_selection = f"${{{{ fromJSON(needs.{selector_job_id}.outputs.{matching_outputs[0]}) }}}}"
    normalized_selection = re.sub(r"\s+", "", selected_cells)
    normalized_expected_selection = re.sub(r"\s+", "", expected_selection)
    if normalized_selection == normalized_expected_selection:
        return True, ""

    actual_output_match = re.fullmatch(
        r"\$\{\{\s*fromJSON\(needs\.([^.]+)\.outputs\.([^)]+)\)\s*\}\}",
        selected_cells.strip(),
    )
    if actual_output_match is not None:
        actual_selector_job, actual_output = actual_output_match.groups()
        return (
            False,
            f"job {job_id!r} consumes matrix output {actual_selector_job!r}.{actual_output!r}; expected "
            f"{selector_job_id!r}.{matching_outputs[0]!r} for scripts/env_matrix.py --job {job_id}",
        )
    return False, f"job {job_id!r} matrix.cell must consume {expected_selection}"


def _build_lane_proof(
    lanes: list[dict[str, Any]],
    cells: dict[str, dict[str, Any]],
    workflow_results: dict[str, tuple[bool, str]],
    tox_environments: set[str],
    project_root: Path,
    diagnostics: list[dict[str, str]],
    *,
    probe_lane_id: str | None,
) -> list[dict[str, Any]]:
    proof: list[dict[str, Any]] = []
    if tox_environments:
        for workflow_cell in cells.values():
            cell_id = _cell_id(workflow_cell)
            cell_environments = workflow_cell.get("tox_envs")
            if not cell_id or not isinstance(cell_environments, list):
                continue
            for environment in cell_environments:
                if not isinstance(environment, str) or environment in tox_environments:
                    continue
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "workflow-tox-environment-unresolved",
                        f"workflow cell {cell_id!r} selects tox environment {environment!r}, which is not present "
                        "in the real `tox list --no-desc` output",
                        f"Add {environment!r} to tox.ini or remove it from workflow cell {cell_id!r} in "
                        "config/env-matrix.yaml.",
                    )
                )

    represented_environments = {
        environment
        for lane in lanes
        if _status(lane) != "unsupported"
        for environment in _split_tox_envs(lane.get("tox_env"))
    }
    for environment in sorted(set(tox_environments) - represented_environments):
        command_lanes = [lane for lane in lanes if environment in _command_tox_environments(lane.get("command"))]
        if command_lanes:
            for lane in command_lanes:
                lane_id = _lane_id(lane)
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "tox-environment-unrepresented",
                        f"resolved tox environment {environment!r} is missing from lane {lane_id!r}'s tox_env list",
                        f"Add {environment!r} to lane {lane_id!r}'s tox_env list or remove it from tox.ini.",
                    )
                )
            continue

        workflow_cell_ids = [
            _cell_id(workflow_cell)
            for workflow_cell in cells.values()
            if isinstance(workflow_cell.get("tox_envs"), list)
            and environment in workflow_cell["tox_envs"]
            and _cell_id(workflow_cell)
        ]
        if workflow_cell_ids:
            for cell_id in workflow_cell_ids:
                diagnostics.append(
                    _diagnostic(
                        cell_id,
                        "tox-environment-unrepresented",
                        f"resolved tox environment {environment!r} is selected by workflow cell {cell_id!r} "
                        "but has no required or optional inventory lane",
                        f"Add {environment!r} to a lane in config/env-matrix.yaml or remove it from workflow cell "
                        f"{cell_id!r} in config/env-matrix.yaml.",
                    )
                )
            continue

        diagnostics.append(
            _diagnostic(
                "tox-inventory",
                "tox-environment-unrepresented",
                f"resolved tox environment {environment!r} has no required or optional inventory lane",
                f"Add {environment!r} to a lane in config/env-matrix.yaml or remove it from tox.ini.",
            )
        )

    for lane in lanes:
        lane_id = _lane_id(lane)
        status = _status(lane)
        tox_env = lane.get("tox_env")
        env_names = _split_tox_envs(tox_env)
        unresolved = [env for env in env_names if env not in tox_environments]
        if status != "unsupported" and unresolved:
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "tox-environment-unresolved",
                    f"tox environment(s) {', '.join(unresolved)} are not present in the real "
                    "`tox list --no-desc` output",
                    f"Add the exact tox environment to tox.ini or correct lane {lane_id!r}; "
                    "resolve it with `tox list --no-desc`.",
                )
            )

        selector = lane.get("workflow_selector")
        cell = cells.get(str(selector)) if selector else None
        ci_selected = False
        workflow_name: str | None = None
        if status == "required":
            if cell is None:
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "workflow-selector-unresolved",
                        f"workflow selector {selector!r} does not name an inventory workflow cell",
                        f"Add the selected workflow cell or correct lane {lane_id!r}'s workflow_selector.",
                    )
                )
            else:
                workflow_path = _workflow_path(project_root, cell)
                workflow_name = str(workflow_path.relative_to(project_root)).replace("\\", "/")
                cell_envs = set(cell.get("tox_envs", []))
                if not set(env_names) <= cell_envs:
                    diagnostics.append(
                        _diagnostic(
                            lane_id,
                            "workflow-tox-mismatch",
                            f"workflow cell {selector!r} does not select every lane tox environment",
                            "Add the lane's resolved tox environments to the workflow cell in config/env-matrix.yaml.",
                        )
                    )
                ci_selected, workflow_detail = workflow_results.get(
                    str(selector), (False, "workflow cell has no matrix selection result")
                )
                if not ci_selected:
                    diagnostics.append(
                        _diagnostic(
                            lane_id,
                            "workflow-not-selected",
                            f"workflow cell {selector!r} is not selected by its GitHub Actions job matrix output: "
                            f"{workflow_detail}",
                            "Make the job consume the matrix output generated from config/env-matrix.yaml with "
                            f"`python scripts/env_matrix.py --job {cell.get('job')}`.",
                        )
                    )
        elif cell is not None:
            workflow_path = _workflow_path(project_root, cell)
            workflow_name = str(workflow_path.relative_to(project_root)).replace("\\", "/")
            ci_selected = workflow_results.get(str(selector), (False, ""))[0]

        declared_command = _command_text(lane.get("command"))
        if status == "required" and (not declared_command or any(env not in declared_command for env in env_names)):
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "lane-command-unresolved",
                    f"lane command {declared_command!r} does not invoke every declared tox environment: "
                    f"{', '.join(env_names)}",
                    f"Set command to `tox run -e {','.join(env_names)}` and verify it with `tox list --no-desc`.",
                )
            )

        lane_proof: dict[str, Any] = {
            "id": lane_id,
            "status": status,
            "tox": {
                "environment": tox_env,
                "command": _tox_run_command(env_names) if env_names else [],
                "resolved": status == "unsupported" or not unresolved,
            },
            "ci": {"workflow": workflow_name, "selector": selector, "selected": ci_selected},
            "command": {"declared": lane.get("command"), "resolved": bool(declared_command)},
            "carrier": _carrier_declaration(lane.get("expected_carrier")),
        }
        if lane_id == probe_lane_id:
            _probe_lane(lane, project_root, lane_proof["carrier"], diagnostics)
        proof.append(lane_proof)
    return proof


@dataclass(frozen=True)
class _PackagePrerequisiteConstraint:
    specifier: SpecifierSet | None
    requested: str | None
    error: str | None
    applies_to_environment: bool = True


def _package_prerequisite_constraint(prerequisite: dict[str, Any]) -> _PackagePrerequisiteConstraint:
    """Parse a package prerequisite's version constraint for the current environment."""
    name = str(prerequisite.get("name", ""))
    requirement_value = prerequisite.get("requirement")
    if requirement_value is not None:
        requirement_text = str(requirement_value)
        try:
            requirement = Requirement(requirement_text)
        except InvalidRequirement as error:
            return _PackagePrerequisiteConstraint(None, requirement_text, f"invalid PEP 508 requirement: {error}")
        normalized_requirement_name = re.sub(r"[-_.]+", "-", requirement.name).casefold()
        normalized_declared_name = re.sub(r"[-_.]+", "-", name).casefold()
        if normalized_requirement_name != normalized_declared_name:
            return _PackagePrerequisiteConstraint(
                None,
                requirement_text,
                f"requirement names {requirement.name!r}, not the declared package {name!r}",
            )
        if requirement.marker is not None and not requirement.marker.evaluate():
            return _PackagePrerequisiteConstraint(None, requirement_text, None, applies_to_environment=False)
        return _PackagePrerequisiteConstraint(requirement.specifier, requirement_text, None)

    version_value = prerequisite.get("version")
    if version_value is None or str(version_value).strip().casefold() in {"", "latest"}:
        return _PackagePrerequisiteConstraint(None, None, None)
    version_text = str(version_value).strip()
    specifier_text = version_text
    if not version_text.startswith(("<", ">", "=", "!", "~")):
        specifier_text = f"=={version_text}"
    try:
        specifier = SpecifierSet(specifier_text)
    except InvalidSpecifier as error:
        return _PackagePrerequisiteConstraint(None, version_text, f"invalid version specifier: {error}")
    return _PackagePrerequisiteConstraint(specifier, specifier_text, None)


def _probe_lane(
    lane: dict[str, Any],
    project_root: Path,
    carrier_proof: dict[str, Any],
    diagnostics: list[dict[str, str]],
) -> None:
    lane_id = _lane_id(lane)
    for prerequisite in lane.get("prerequisites", []):
        if not isinstance(prerequisite, dict):
            continue
        prerequisite_type = prerequisite.get("type")
        name = str(prerequisite.get("name", ""))
        if prerequisite_type == "python-package":
            constraint = _package_prerequisite_constraint(prerequisite)
            if not constraint.applies_to_environment:
                continue
            if constraint.error is not None:
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "package-prerequisite-invalid",
                        f"requested constraint {constraint.requested!r} for Python package {name!r} is invalid: "
                        f"{constraint.error}",
                        str(prerequisite.get("remedy", f"Correct the declared requirement for {name!r}.")),
                    )
                )
                continue
            try:
                installed_version = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "package-prerequisite-missing",
                        f"required Python package {name!r} is not installed for lane {lane_id!r}",
                        str(prerequisite.get("remedy", f"Install package {name!r} before running this lane.")),
                    )
                )
                continue

            if constraint.specifier is None or not constraint.specifier:
                continue
            try:
                version = Version(installed_version)
            except InvalidVersion as error:
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "package-prerequisite-version-invalid",
                        f"installed version {installed_version!r} for Python package {name!r} cannot be "
                        f"checked against requested constraint {constraint.requested!r}: {error}",
                        str(prerequisite.get("remedy", f"Install a compatible version of {name!r}.")),
                    )
                )
                continue
            if not constraint.specifier.contains(version):
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "package-prerequisite-version-mismatch",
                        f"required Python package {name!r} has installed version {installed_version!r}, which "
                        f"does not satisfy requested constraint {constraint.requested!r} for lane {lane_id!r}",
                        str(
                            prerequisite.get(
                                "remedy",
                                f"Install a version of {name!r} that satisfies {constraint.requested}.",
                            )
                        ),
                    )
                )
        elif prerequisite_type == "command" and shutil.which(name) is None:
            diagnostics.append(
                _diagnostic(
                    lane_id,
                    "command-prerequisite-missing",
                    f"required command {name!r} is not available for lane {lane_id!r}",
                    str(prerequisite.get("remedy", f"Install command {name!r} before running this lane.")),
                )
            )

    carrier = lane.get("expected_carrier")
    if not _is_carrier(carrier):
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-invalid",
                "requested lane has no runnable carrier",
                "Declare a carrier kind and a path or command.",
            )
        )
        return
    carrier_path = project_root / str(carrier.get("path", "")) if carrier.get("path") else None
    if carrier_path is not None and not carrier_path.exists():
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-not-found",
                f"carrier path {carrier.get('path')!r} is missing for lane {lane_id!r}",
                "Restore the test carrier in the repository or correct expected_carrier.path.",
            )
        )
        return
    command = _command_text(carrier.get("command"))
    if carrier.get("kind") == "tool":
        carrier_proof.update({"selected": True, "selectedCount": 1, "command": command})
        return

    if not command:
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-command-missing",
                "requested test carrier has no collect-only command",
                "Add a pytest collect-only command to expected_carrier.",
            )
        )
        return
    try:
        tokens = shlex.split(command)
    except ValueError as error:
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-command-invalid",
                f"carrier command cannot be parsed: {error}",
                "Use a shell-free pytest command with quoted arguments.",
            )
        )
        return
    if not tokens:
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-command-invalid",
                "carrier command is empty",
                "Declare `pytest --collect-only -q <test-path>` as the carrier command.",
            )
        )
        return
    executable_name = Path(tokens[0]).name.casefold()
    if executable_name in {"pytest", "pytest.exe"}:
        pytest_args = tokens[1:]
    elif (
        executable_name in {"python", "python3", "python.exe"} and len(tokens) >= 3 and tokens[1:3] == ["-m", "pytest"]
    ):
        pytest_args = tokens[3:]
    else:
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-command-invalid",
                f"carrier command must start with pytest or python -m pytest: {command}",
                "Declare `pytest --collect-only -q <test-path>` as the carrier command.",
            )
        )
        return
    if "--collect-only" not in pytest_args:
        pytest_args.insert(0, "--collect-only")
    if "-q" not in pytest_args and "--quiet" not in pytest_args:
        pytest_args.insert(0, "-q")
    probe_command = [sys.executable, "-m", "pytest", *pytest_args]
    try:
        result = subprocess.run(  # noqa: S603 -- pytest arguments come from the checked inventory carrier.
            probe_command, cwd=project_root, capture_output=True, text=True, check=False, timeout=180
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-probe-failed",
                f"carrier collect-only probe could not run: {error}",
                "Install pytest and the lane prerequisites, then rerun the lane probe.",
            )
        )
        return
    selected_count = _collected_count(result.stdout + "\n" + result.stderr)
    carrier_proof.update(
        {
            "selected": result.returncode == 0 and selected_count > 0,
            "selectedCount": selected_count,
            "command": probe_command,
        }
    )
    if result.returncode != 0 or selected_count == 0:
        details = (result.stdout + "\n" + result.stderr).strip()
        diagnostics.append(
            _diagnostic(
                lane_id,
                "carrier-selection-empty",
                f"lane carrier selected no tests or pytest collection failed: {details}",
                "Install the declared lane prerequisites and update the carrier command to select a real test.",
            )
        )


def _collected_count(output: str) -> int:
    selected_matches = re.findall(r"\b(\d+)\s*/\s*\d+\s+(?:items?|tests?)\s+collected\b", output, flags=re.IGNORECASE)
    if selected_matches:
        return int(selected_matches[-1])
    matches = re.findall(r"\b(\d+)\s+(?:items?|tests?)\s+collected\b", output, flags=re.IGNORECASE)
    if matches:
        return int(matches[-1])
    return sum(1 for line in output.splitlines() if "::" in line and not line.lstrip().startswith("<"))


def _carrier_declaration(carrier: Any) -> dict[str, Any]:
    if not isinstance(carrier, dict):
        return {
            "kind": None,
            "path": None,
            "command": None,
            "selected": None,
            "selectedCount": None,
            "passed": None,
            "skipped": None,
        }
    return {
        "kind": carrier.get("kind"),
        "path": carrier.get("path"),
        "command": carrier.get("command"),
        "selected": None,
        "selectedCount": None,
        "passed": None,
        "skipped": None,
    }


def _active_environment() -> dict[str, str | None]:
    try:
        pytest_version = importlib.metadata.version("pytest")
    except importlib.metadata.PackageNotFoundError:
        pytest_version = None
    return {
        "runtime": platform.python_implementation(),
        "python": platform.python_version(),
        "pytest": pytest_version,
        "platform": sys.platform,
    }


def _split_tox_envs(value: Any) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [part.strip() for part in value if isinstance(part, str) and part.strip()]
    return []


def _tox_run_command(env_names: list[str]) -> list[str]:
    if not env_names:
        return []
    return ["tox", "run", "-e", ",".join(env_names)]


def _command_tox_environments(value: Any) -> set[str]:
    command = _command_text(value)
    try:
        tokens = shlex.split(command)
    except ValueError:
        return set()
    environments: set[str] = set()
    for index, argument in enumerate(tokens):
        if argument == "-e" and index + 1 < len(tokens):
            environments.update(name for name in tokens[index + 1].split(",") if name)
        elif argument.startswith("-e") and argument != "-e":
            environments.update(name for name in argument[2:].split(",") if name)
    return environments


def _command_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return " ".join(value)
    return ""


def _is_carrier(value: Any) -> TypeGuard[dict[str, Any]]:
    return isinstance(value, dict) and bool(value.get("kind")) and bool(value.get("path") or value.get("command"))


def _lane_id(lane: dict[str, Any]) -> str:
    value = lane.get("id")
    return value.strip() if isinstance(value, str) else ""


def _cell_id(cell: dict[str, Any]) -> str:
    value = cell.get("id")
    return value.strip() if isinstance(value, str) else ""


def _status(lane: dict[str, Any]) -> str:
    value = lane.get("status")
    return value.strip().casefold() if isinstance(value, str) else ""


def _display_inventory_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _diagnostic(lane_id: str, code: str, message: str, remedy: str) -> dict[str, str]:
    return {"laneId": lane_id, "code": code, "message": message, "remedy": remedy}


def _failure(diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    return {"status": "fail", "diagnostics": diagnostics}


__all__ = ["TOX_LIST_COMMAND", "check_environment_inventory"]
