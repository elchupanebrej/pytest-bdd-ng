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
from pathlib import Path
from typing import Any, TypeGuard

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

    tox_result, tox_environments = _list_tox_environments(project_root)
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
        tox_environments = []
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
            "toxEnvironments": tox_environments,
            "workflowCells": valid_cells,
        },
        "proof": {
            "tox": {"command": list(TOX_LIST_COMMAND), "environments": tox_environments},
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
            str(lane.get(key) or "").strip().casefold()
            for key in ("runtime", "python", "platform", "capability")
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
            try:
                importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                diagnostics.append(
                    _diagnostic(
                        lane_id,
                        "package-prerequisite-missing",
                        f"required Python package {name!r} is not installed for lane {lane_id!r}",
                        str(prerequisite.get("remedy", f"Install package {name!r} before running this lane.")),
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
