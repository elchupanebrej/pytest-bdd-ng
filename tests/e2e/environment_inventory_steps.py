"""Installed-consumer acceptance steps for the repository environment inventory."""

from __future__ import annotations

import configparser
import importlib
import io
import json
import os
import platform
import re
import runpy
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import version as distribution_version
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml
from pytest_cuke import given, parsers, then, when
from pytest_cuke.compatibility.environment_matrix import _collected_count, check_environment_inventory
from pytest_cuke.compatibility.runtime_compat import is_pair_compatible


@dataclass
class EnvironmentInventoryContext:
    consumer: Any
    repository_root: Path
    document: dict[str, Any]
    check_result: subprocess.CompletedProcess[str] | None = None
    report: dict[str, Any] | None = None
    tox_result: subprocess.CompletedProcess[str] | None = None
    tox_configurations: dict[str, dict[str, list[str]]] | None = None
    package_constraint_lane: str | None = None
    package_constraint_expectations: list[dict[str, str]] | None = None
    inactive_marker_lane: str | None = None
    inactive_marker_package: str | None = None


@dataclass
class TemporaryEnvironmentInventoryContext:
    project_root: Path
    inventory_path: Path
    document: dict[str, Any]
    report: dict[str, Any] | None = None
    unrepresented_tox_lane: str | None = None
    unrepresented_tox_environment: str | None = None
    unresolved_workflow_cell: str | None = None
    unresolved_workflow_environment: str | None = None
    conflicting_optional_lane_id: str | None = None
    conflicting_unsupported_lane_id: str | None = None
    mismatched_workflow_cell_id: str | None = None
    mismatched_workflow_lane_id: str | None = None
    missing_matrix_export_cell_id: str | None = None
    missing_matrix_export_lane_id: str | None = None


@dataclass(frozen=True)
class CompatibilityAuditDocuments:
    contributor_entry: str
    audit_guide: str


def _context(consumer: Any) -> EnvironmentInventoryContext:
    context = getattr(consumer, "_environment_inventory_context", None)
    assert context is not None, "the installed consumer's environment inventory has not been loaded"
    return context


def _lanes(context: EnvironmentInventoryContext) -> list[dict[str, Any]]:
    lanes = context.document.get("lanes")
    assert isinstance(lanes, list) and lanes, "config/env-matrix.yaml must contain a non-empty lanes list"
    assert all(isinstance(lane, dict) for lane in lanes), lanes
    return lanes


def _runtime_policy(context: EnvironmentInventoryContext) -> dict[str, Any]:
    policy = context.document.get("runtime_policy")
    assert isinstance(policy, dict), "config/env-matrix.yaml must declare runtime_policy"
    return policy


def _required_runtime_cells(context: EnvironmentInventoryContext) -> list[dict[str, Any]]:
    cells = _runtime_policy(context).get("required_cells")
    assert isinstance(cells, list) and cells, "runtime_policy.required_cells must be a non-empty list"
    assert all(isinstance(cell, dict) for cell in cells), cells
    return cells


def _runtime_cell_key(cell: dict[str, Any]) -> tuple[str, str, str, str]:
    return tuple(str(cell.get(key, "")).casefold() for key in ("runtime", "python", "platform", "architecture"))  # type: ignore[return-value]


def _lane_text(lane: dict[str, Any]) -> str:
    return json.dumps(lane, ensure_ascii=False, sort_keys=True, default=str).casefold()


def _inventory_command_environment(
    consumer: Any,
    *,
    include_doc_generation_tools: bool = False,
) -> dict[str, str]:
    environment = consumer.env.copy()
    path_entries = [str(Path(consumer.python).resolve().parent)]
    pandoc_executable = shutil.which("pandoc") if include_doc_generation_tools else None
    if pandoc_executable is not None:
        path_entries.append(str(Path(pandoc_executable).parent))
    path_entries.extend(environment.get("PATH", os.defpath).split(os.pathsep))
    # Keep setup-python interpreters visible to tox even though the consumer PATH is isolated.
    path_entries.extend(os.environ.get("PATH", os.defpath).split(os.pathsep))
    environment["PATH"] = os.pathsep.join(dict.fromkeys(path_entries))
    return environment


def _list_tox_environment_names(
    project_root: Path,
    *,
    environment: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], set[str]]:
    result = subprocess.run(
        ["tox", "list", "--no-desc"],
        cwd=project_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"real tox list failed: {result.stdout}\n{result.stderr}"
    names = {
        line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("All environments:")
    }
    return result, names


def _tox_configured_commands(consumer: Any, environment_name: str) -> list[str]:
    result = subprocess.run(
        ["tox", "config", "-e", environment_name],
        cwd=consumer.path,
        env=_inventory_command_environment(consumer),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"tox config failed for {environment_name}: {result.stdout}\n{result.stderr}"
    commands: list[str] = []
    in_commands = False
    for line in result.stdout.splitlines():
        if line.startswith("commands ="):
            in_commands = True
            command = line.partition("=")[2].strip()
            if command:
                commands.append(command)
            continue
        if in_commands:
            if line.startswith("  "):
                commands.append(line.strip())
            else:
                break
    return commands


def _resolved_tox_configurations(context: EnvironmentInventoryContext) -> dict[str, dict[str, list[str]]]:
    if context.tox_configurations is not None:
        return context.tox_configurations

    consumer = context.consumer
    result = subprocess.run(
        ["tox", "config", "-e", "ALL", "-k", "deps", "extras", "commands"],
        cwd=consumer.path,
        env=_inventory_command_environment(consumer),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"tox config failed for all environments: {result.stdout}\n{result.stderr}"

    configurations: dict[str, dict[str, list[str]]] = {}
    environment_name: str | None = None
    current_field: str | None = None
    for line in result.stdout.splitlines():
        section = re.fullmatch(r"\[testenv:([^]]+)\]", line)
        if section is not None:
            environment_name = section.group(1)
            configurations[environment_name] = {"deps": [], "extras": [], "commands": []}
            current_field = None
            continue
        if environment_name is None:
            continue
        field_match = re.match(r"^(deps|extras|commands)\s*=\s*(.*)$", line)
        if field_match is not None:
            current_field = field_match.group(1)
            inline_value = field_match.group(2).strip()
            if inline_value:
                configurations[environment_name][current_field].append(inline_value)
            continue
        if current_field is not None and line.startswith("  "):
            value = line.strip()
            if value:
                configurations[environment_name][current_field].append(value)
            continue
        current_field = None

    context.tox_configurations = configurations
    return configurations


def _run_environment_check(
    context: EnvironmentInventoryContext,
    *,
    lane_id: str | None = None,
    include_doc_generation_tools: bool = False,
) -> subprocess.CompletedProcess[str]:
    consumer = context.consumer
    command = [
        str(consumer.cuke),
        "compatibility",
        "--check-environments",
        "--inventory",
        "config/env-matrix.yaml",
    ]
    if lane_id is not None:
        command.extend(("--lane", lane_id))
    command.append("--json")
    result = subprocess.run(
        command,
        cwd=consumer.path,
        env=_inventory_command_environment(
            consumer,
            include_doc_generation_tools=include_doc_generation_tools,
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    context.check_result = result
    consumer.command_result = result
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        context.report = None
    else:
        context.report = payload if isinstance(payload, dict) else None
    return result


def _installed_consumer_version(consumer: Any, package_name: str) -> str:
    result = subprocess.run(
        [
            str(consumer.python),
            "-c",
            "from importlib.metadata import version; import sys; print(version(sys.argv[1]))",
            package_name,
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"could not read installed {package_name} version from the isolated consumer:\n{result.stdout}\n{result.stderr}"
    )
    detected_version = result.stdout.strip()
    assert detected_version, f"the isolated consumer returned an empty {package_name} version"
    return detected_version


def _report(context: EnvironmentInventoryContext) -> dict[str, Any]:
    result = context.check_result
    assert result is not None, "the environment inventory check has not run"
    assert context.report is not None, (
        "the environment inventory command must emit JSON on stdout in both success and failure cases; "
        f"exit={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return context.report


def _proof_lanes(context: EnvironmentInventoryContext) -> dict[str, dict[str, Any]]:
    proof_lanes = _report(context).get("proof", {}).get("lanes")
    assert isinstance(proof_lanes, list), proof_lanes
    indexed = {lane.get("id"): lane for lane in proof_lanes if isinstance(lane, dict)}
    assert len(indexed) == len(proof_lanes), proof_lanes
    return indexed


def _lane_id(lane: dict[str, Any]) -> str:
    lane_id = lane.get("id")
    assert isinstance(lane_id, str) and lane_id, lane
    return lane_id


def _status(lane: dict[str, Any]) -> str:
    return str(lane.get("status", "")).casefold()


def _major(value: Any) -> int | None:
    if isinstance(value, list):
        majors = {_major(item) for item in value}
        majors.discard(None)
        return min(majors) if majors else None
    match = re.match(r"\s*(?:pytest\s*)?(\d+)", str(value), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _majors(value: Any) -> set[int]:
    """Return every explicit pytest major represented by one inventory value."""
    if isinstance(value, list):
        return {major for item in value for major in _majors(item)}
    major = _major(value)
    return {major} if major is not None else set()


def _prerequisite_entries(lane: dict[str, Any]) -> list[dict[str, Any]]:
    prerequisites = lane.get("prerequisites")
    assert isinstance(prerequisites, list), f"lane {_lane_id(lane)!r} must declare prerequisites as a list"
    assert all(isinstance(item, dict) for item in prerequisites), prerequisites
    return prerequisites


def _carrier(lane: dict[str, Any]) -> dict[str, Any]:
    carrier = lane.get("expected_carrier")
    assert isinstance(carrier, dict), f"lane {_lane_id(lane)!r} must declare an expected_carrier object"
    assert carrier.get("kind"), carrier
    assert carrier.get("path") or carrier.get("command"), carrier
    return carrier


def _doc_generation_lane(context: EnvironmentInventoryContext) -> dict[str, Any]:
    matches = [lane for lane in _lanes(context) if str(lane.get("capability", "")).casefold() == "doc-generation"]
    assert len(matches) == 1, f"the inventory must declare exactly one doc-generation capability lane; found {matches}"
    lane = matches[0]
    assert _status(lane) == "required", f"the doc-generation lane must be required: {lane}"
    return lane


def _assert_carrier_path_exists(context: EnvironmentInventoryContext, lane: dict[str, Any]) -> None:
    carrier_path = _carrier(lane).get("path")
    if carrier_path:
        path = context.repository_root / str(carrier_path)
        assert path.exists(), f"lane {_lane_id(lane)!r} names missing carrier path {carrier_path!r}"


def _feature_arguments(command: str) -> set[str]:
    feature_arguments: set[str] = set()
    for argument in shlex.split(command, posix=False):
        normalized_argument = argument.strip("\"'").replace("\\", "/")
        if normalized_argument.endswith(".feature"):
            feature_arguments.add(Path(normalized_argument).as_posix())
    return feature_arguments


def _precommit_hook_selects_path(hook: dict[str, Any], path: str) -> bool:
    files_pattern = hook.get("files", "")
    exclude_pattern = hook.get("exclude", "")
    if not isinstance(files_pattern, str) or not isinstance(exclude_pattern, str):
        return False
    return re.search(files_pattern, path) is not None and (
        not exclude_pattern or re.search(exclude_pattern, path) is None
    )


def _write_inventory(context: EnvironmentInventoryContext) -> None:
    path = context.consumer.path / "config" / "env-matrix.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(context.document, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _install_inventory_checker_tools(consumer: Any) -> None:
    """Install the optional checker dependencies into this isolated consumer."""
    uv_executable = shutil.which("uv")
    assert uv_executable, "the environment inventory contract requires uv to install tox and PyYAML"
    result = subprocess.run(
        [
            uv_executable,
            "pip",
            "install",
            "--python",
            str(consumer.python),
            "tox>=4.2",
            "PyYAML",
            "pytest>=7.0",
        ],
        cwd=consumer.path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"could not install environment checker dependencies:\n{result.stdout}\n{result.stderr}"
    )


@given("the repository environment inventory is loaded")
def repository_environment_inventory_is_loaded(request: Any, consumer: Any) -> None:
    repository_root = Path(request.config.rootpath)
    required_files = [
        Path("config/env-matrix.yaml"),
        Path("tox.ini"),
        Path("pyproject.toml"),
    ]
    workflow_directory = Path(".github/workflows")
    workflow_files = sorted((repository_root / workflow_directory).glob("*.yml")) + sorted(
        (repository_root / workflow_directory).glob("*.yaml")
    )
    assert workflow_files, "the repository must contain GitHub Actions workflow files"
    for relative_path in required_files:
        source = repository_root / relative_path
        assert source.is_file(), f"required environment inventory input is missing: {source}"
        destination = consumer.path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    # The installed wheel's sample pytest config enables autoload globally.
    # Even a unit-only carrier collection needs the configured feature root.
    (consumer.path / "features").mkdir(parents=True, exist_ok=True)
    for source in workflow_files:
        relative_path = source.relative_to(repository_root)
        destination = consumer.path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    carrier = repository_root / "tests" / "unit" / "compatibility" / "test_runtime_compat.py"
    assert carrier.is_file(), f"the optional-lane carrier is missing: {carrier}"
    carrier_destination = consumer.path / "tests" / "unit" / "compatibility" / carrier.name
    carrier_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(carrier, carrier_destination)

    doc_generation_carrier = repository_root / "tests" / "unit" / "docs" / "test_doc.py"
    assert doc_generation_carrier.is_file(), f"the doc-generation carrier is missing: {doc_generation_carrier}"
    doc_generation_destination = consumer.path / "tests" / "unit" / "docs" / doc_generation_carrier.name
    doc_generation_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(doc_generation_carrier, doc_generation_destination)

    _install_inventory_checker_tools(consumer)

    inventory_path = consumer.path / "config" / "env-matrix.yaml"
    document = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    assert isinstance(document, dict), document
    context = EnvironmentInventoryContext(consumer, repository_root, document)
    _lanes(context)
    consumer._environment_inventory_context = context


@then("each lane should declare runtime Python pytest platform capability and status")
def each_lane_declares_support_dimensions(consumer: Any) -> None:
    for lane in _lanes(_context(consumer)):
        missing = {
            name
            for name in ("id", "status", "runtime", "python", "pytest", "platform", "capability")
            if name not in lane or lane[name] in (None, "", [])
        }
        assert not missing, f"lane {_lane_id(lane)!r} is missing inventory fields: {sorted(missing)}"
        assert _status(lane) in {"required", "optional", "unsupported"}, lane


@then("required lanes should declare tox environment workflow selector command prerequisites and carrier")
def required_lanes_declare_execution_inputs(consumer: Any) -> None:
    required = [lane for lane in _lanes(_context(consumer)) if _status(lane) == "required"]
    assert required, "the inventory must declare at least one required lane"
    for lane in required:
        missing = {
            name
            for name in ("tox_env", "workflow_selector", "command", "prerequisites", "expected_carrier")
            if name not in lane or lane[name] in (None, "", [])
        }
        assert not missing, f"required lane {_lane_id(lane)!r} is missing: {sorted(missing)}"
        _prerequisite_entries(lane)
        _carrier(lane)
        _assert_carrier_path_exists(_context(consumer), lane)


@then("unsupported lanes should have a source-backed reason and no active selector")
def unsupported_lanes_have_evidence_without_active_selectors(consumer: Any) -> None:
    unsupported = [lane for lane in _lanes(_context(consumer)) if _status(lane) == "unsupported"]
    assert unsupported, "the inventory must state why unsupported cells are excluded"
    for lane in unsupported:
        assert lane.get("reason"), lane
        assert lane.get("source_evidence"), lane
        assert not lane.get("workflow_selector") and not lane.get("tox_env"), lane


@then("CPython 3.12 Windows and macOS lanes should be required full-matrix cells")
def cpython_312_windows_macos_are_required_runtime_cells(consumer: Any) -> None:
    context = _context(consumer)
    lanes = _lanes(context)
    required_lanes = {
        str(lane.get("platform")): lane
        for lane in lanes
        if lane.get("runtime") == "CPython"
        and str(lane.get("python")) == "3.12"
        and lane.get("platform") in {"windows", "macos"}
        and lane.get("capability") == "core-runtime-acceptance"
    }
    assert set(required_lanes) == {"windows", "macos"}, required_lanes
    workflow_cells = {
        str(cell.get("id")): cell
        for cell in context.document.get("workflow_cells", [])
        if isinstance(cell, dict) and cell.get("job") == "full-matrix"
    }
    for platform_name, lane in required_lanes.items():
        assert _status(lane) == "required", lane
        selector = lane.get("workflow_selector")
        assert selector in workflow_cells, (lane, workflow_cells)
        cell = workflow_cells[str(selector)]
        assert cell.get("runtime") == "CPython", cell
        assert str(cell.get("python")) == "3.12", cell
        assert cell.get("platform") == platform_name, cell
        lane_environments = [part.strip() for part in str(lane.get("tox_env", "")).split(",") if part.strip()]
        assert lane_environments == cell.get("tox_envs"), (lane, cell)


@when("I run the project environment inventory check in JSON mode")
def run_project_environment_inventory_json_check(consumer: Any) -> None:
    _run_environment_check(_context(consumer))


@then("the environment inventory check should pass")
def environment_inventory_check_passes(consumer: Any) -> None:
    context = _context(consumer)
    result = context.check_result
    report = _report(context)
    assert result is not None and result.returncode == 0, (result, report)
    assert report.get("status") == "pass", report
    assert report.get("inventory", {}).get("path") == "config/env-matrix.yaml", report
    required_lanes = [lane for lane in _lanes(context) if _status(lane) == "required"]
    assert report.get("inventory", {}).get("requiredLaneCount") == len(required_lanes), report


@given("the doc-generation package prerequisites are installed in the consumer")
def install_doc_generation_package_prerequisites(consumer: Any) -> None:
    context = _context(consumer)
    lane = _doc_generation_lane(context)
    package_names = [
        str(item["name"])
        for item in _prerequisite_entries(lane)
        if item.get("type") == "python-package" and item.get("name")
    ]
    uv_executable = shutil.which("uv")
    assert uv_executable, "the doc-generation carrier probe requires uv to install declared Python packages"
    result = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(consumer.python), *package_names],
        cwd=consumer.path,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"could not install doc-generation package prerequisites {package_names!r}:\n{result.stdout}\n{result.stderr}"
    )


@then("its tox listing proof should match the real tox environment list")
def tox_listing_proof_matches_real_tox(consumer: Any) -> None:
    context = _context(consumer)
    report = _report(context)
    proof = report.get("proof", {}).get("tox", {})
    command = proof.get("command")
    assert command == ["tox", "list", "--no-desc"], proof

    result, actual_names = _list_tox_environment_names(
        consumer.path,
        environment=_inventory_command_environment(consumer),
    )
    context.tox_result = result
    proof_names = proof.get("environments")
    inventory_names = report.get("inventory", {}).get("toxEnvironments")
    assert isinstance(proof_names, list) and proof_names, proof
    assert set(proof_names) == actual_names, (proof_names, actual_names)
    assert isinstance(inventory_names, list) and set(inventory_names) == actual_names, inventory_names
    configured_names = report.get("inventory", {}).get("configuredToxEnvironments")
    selector_fragments = report.get("inventory", {}).get("toxSelectorFragments")
    proof_configured_names = proof.get("configuredEnvironments")
    proof_selector_fragments = proof.get("selectorFragments")
    assert isinstance(configured_names, list) and isinstance(selector_fragments, list), report
    assert isinstance(proof_configured_names, list) and isinstance(proof_selector_fragments, list), proof
    assert set(proof_selector_fragments) == set(selector_fragments), proof
    assert set(configured_names) == set(proof_configured_names), (configured_names, proof_configured_names)
    actual_fragments = actual_names - set(configured_names)
    assert actual_fragments <= set(selector_fragments), (actual_fragments, selector_fragments)
    assert "allure" in selector_fragments, selector_fragments


@then("tox selector fragments should remain separate from configured environments")
def tox_selector_fragments_remain_separate_from_configured_environments(consumer: Any) -> None:
    context = _context(consumer)
    report = _report(context)
    inventory = report.get("inventory", {})
    configured_names = inventory.get("configuredToxEnvironments")
    selector_fragments = inventory.get("toxSelectorFragments")
    resolved_names = inventory.get("toxEnvironments")
    assert isinstance(configured_names, list) and configured_names, inventory
    assert isinstance(selector_fragments, list) and selector_fragments, inventory
    assert isinstance(resolved_names, list) and resolved_names, inventory
    assert set(configured_names).isdisjoint(selector_fragments), (configured_names, selector_fragments)
    assert set(configured_names) <= set(resolved_names), (resolved_names, configured_names)
    assert set(resolved_names) - set(configured_names) <= set(selector_fragments), (
        resolved_names,
        configured_names,
        selector_fragments,
    )
    active_environments = {
        environment
        for lane in _lanes(context)
        if _status(lane) != "unsupported"
        for environment in str(lane.get("tox_env", "")).split(",")
        if environment
    }
    assert not (set(selector_fragments) & active_environments), (selector_fragments, active_environments)


@then("resolved tox base Python selectors should match inventory tox_base_python for PyPy and GraalPy")
def alternative_runtime_tox_base_python_matches_inventory(consumer: Any) -> None:
    context = _context(consumer)
    alternative_cells = {
        str(cell.get("runtime", "")).casefold(): cell
        for cell in _required_runtime_cells(context)
        if str(cell.get("runtime", "")).casefold() in {"pypy", "graalpy"}
    }
    assert set(alternative_cells) == {"pypy", "graalpy"}, alternative_cells

    expected_setup_inputs = {"pypy": "pypy3.12", "graalpy": "graalpy-25.3"}
    problems: list[str] = []
    for runtime, cell in alternative_cells.items():
        setup_python = cell.get("setup_python")
        setup_python_input = setup_python.get("input") if isinstance(setup_python, dict) else None
        expected_setup_input = expected_setup_inputs[runtime]
        if setup_python_input != expected_setup_input:
            problems.append(
                f"{runtime} setup_python.input is {setup_python_input!r}; "
                f"Actions setup input must remain {expected_setup_input!r}"
            )

        expected_base_python = cell.get("tox_base_python")
        if not isinstance(expected_base_python, str) or not expected_base_python:
            problems.append(f"{runtime} cell {cell.get('id')!r} has no tox_base_python: {expected_base_python!r}")
            continue

        required_ci = cell.get("required_ci")
        tox_environments = required_ci.get("tox_envs") if isinstance(required_ci, dict) else None
        if not isinstance(tox_environments, list) or not tox_environments:
            problems.append(f"{runtime} cell {cell.get('id')!r} has no required tox environments: {required_ci!r}")
            continue

        for environment_name in tox_environments:
            result = subprocess.run(
                ["tox", "config", "-e", str(environment_name), "-k", "base_python"],
                cwd=consumer.path,
                env=_inventory_command_environment(consumer),
                check=False,
                capture_output=True,
                text=True,
            )
            match = re.search(r"^base_python\s*=\s*(.*)$", result.stdout, flags=re.MULTILINE)
            actual_base_python = match.group(1).strip() if match is not None else None
            if result.returncode != 0:
                problems.append(
                    f"{environment_name} tox config failed with exit {result.returncode}: "
                    f"{result.stdout.strip()} {result.stderr.strip()}"
                )
            if actual_base_python != expected_base_python:
                problems.append(
                    f"{environment_name} resolved base_python {actual_base_python!r}; "
                    f"inventory {runtime} tox_base_python is {expected_base_python!r}"
                )

    assert not problems, "alternative runtime tox base_python must match canonical inventory selectors: " + "; ".join(
        problems
    )


@when(
    "the matrix runner checks a PyPy cell against a mismatched runtime version and platform",
    target_fixture="matrix_runner_runtime_preflight",
)
def matrix_runner_rejects_mismatched_runtime_before_tox(
    consumer: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> dict[str, Any]:
    context = _context(consumer)
    cell = next(
        candidate
        for candidate in _required_runtime_cells(context)
        if str(candidate.get("runtime", "")).casefold() == "pypy"
    )
    runner_cell = dict(cell)
    setup_python = cell.get("setup_python")
    assert isinstance(setup_python, dict), cell
    expected_interpreter = setup_python.get("expected_interpreter")
    assert isinstance(expected_interpreter, str) and expected_interpreter, setup_python
    runner_cell["expected_interpreter"] = expected_interpreter
    required_ci = cell.get("required_ci")
    assert isinstance(required_ci, dict), cell
    tox_environments = required_ci.get("tox_envs")
    assert isinstance(tox_environments, list) and tox_environments, cell
    runner_cell["tox_envs"] = tox_environments

    scripts_directory = context.repository_root / "scripts"
    monkeypatch.syspath_prepend(str(scripts_directory))
    runner = importlib.import_module("run_env_matrix_cell")

    expected_platform = str(runner_cell["platform"])
    actual_platform = {"linux": "win32", "macos": "linux", "windows": "linux"}[expected_platform]
    actual_python = "0.0.0"
    actual_runtime = "CPython"
    monkeypatch.setattr(
        runner,
        "platform",
        SimpleNamespace(
            python_implementation=lambda: actual_runtime,
            python_version=lambda: actual_python,
            machine=lambda: "x86_64",
        ),
    )
    monkeypatch.setattr(
        runner,
        "sys",
        SimpleNamespace(platform=actual_platform, stdout=sys.stdout, stderr=sys.stderr),
    )
    monkeypatch.setattr(runner, "shutil", SimpleNamespace(which=lambda name: "/fake/bin/tox"))
    monkeypatch.setattr(runner, "load_cells", lambda inventory, job: [runner_cell])

    tox_calls: list[list[str]] = []

    class UnexpectedToxInvocation(RuntimeError):
        pass

    def record_tox_invocation(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        tox_calls.append(command)
        raise UnexpectedToxInvocation(f"tox was invoked before runtime validation: {command!r}")

    monkeypatch.setattr(runner, "subprocess", SimpleNamespace(run=record_tox_invocation))

    output_path = tmp_path / "evidence" / "cell.json"
    inventory_path = tmp_path / "config" / "env-matrix.yaml"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_env_matrix_cell.py",
            "--job",
            "full-matrix",
            "--cell",
            str(runner_cell["id"]),
            "--inventory",
            str(inventory_path),
            "--output",
            str(output_path),
            "--sha",
            "a" * 40,
        ],
    )

    tox_invocation_error = None
    try:
        return_code = runner.main()
    except UnexpectedToxInvocation as error:
        tox_invocation_error = str(error)
        return_code = None
    stderr = capsys.readouterr().err
    return {
        "return_code": return_code,
        "stderr": stderr,
        "tox_calls": tox_calls,
        "tox_invocation_error": tox_invocation_error,
        "output_path": output_path,
        "expected_runtime": str(runner_cell["runtime"]),
        "expected_python": str(runner_cell["expected_interpreter"]),
        "expected_platform": expected_platform,
        "actual_runtime": actual_runtime,
        "actual_python": actual_python,
        "actual_platform": actual_platform,
    }


@then("it should reject the cell before invoking tox or writing evidence")
def matrix_runner_preflight_stops_before_tox(matrix_runner_runtime_preflight: dict[str, Any]) -> None:
    result = matrix_runner_runtime_preflight
    assert result["return_code"] == 1, result
    assert result["tox_calls"] == [], result
    assert result["tox_invocation_error"] is None, result
    assert not result["output_path"].exists(), result
    stderr = result["stderr"]
    assert "selected runtime does not match inventory cell" in stderr, stderr
    assert f"runtime={result['actual_runtime']!r}" in stderr, stderr
    assert f"python={result['actual_python']!r}" in stderr, stderr
    assert f"platform={result['actual_platform']!r}" in stderr, stderr
    for dimension in ("runtime", "python", "platform"):
        assert f"expected {result[f'expected_{dimension}']!r}" in stderr, stderr


@when(
    parsers.parse(
        'I start CPython 3.15 cell "{cell_id}" with platform name "{platform_name}", '
        'platform "{platform}", machine "{machine}", and normalized architecture "{normalized_architecture}"'
    ),
    target_fixture="cpython_315_preflight",
)
def start_cpython_315_cell_with_preflight(
    cell_id: str,
    platform_name: str,
    platform: str,
    machine: str,
    normalized_architecture: str,
    request: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Any]:
    repository_root = Path(request.config.rootpath)
    inventory_path = repository_root / "config" / "env-matrix.yaml"
    scripts_directory = repository_root / "scripts"
    monkeypatch.syspath_prepend(str(scripts_directory))
    runner = importlib.import_module("run_env_matrix_cell")
    cell = next(
        candidate for candidate in runner.load_cells(inventory_path, "full-matrix") if candidate["id"] == cell_id
    )
    assert cell.get("runtime") == "CPython", cell
    assert cell.get("python") == "3.15", cell
    assert cell.get("expected_interpreter") == "3.15.0", cell

    actual_runtime = "CPython"
    actual_python = "3.15.0"
    monkeypatch.setattr(
        runner,
        "platform",
        SimpleNamespace(
            python_implementation=lambda: actual_runtime,
            python_version=lambda: actual_python,
            platform=lambda: platform,
            machine=lambda: machine,
        ),
    )
    monkeypatch.setattr(runner.sys, "platform", platform_name)
    monkeypatch.setattr(runner.shutil, "which", lambda name: "/fake/bin/tox")

    output_path = tmp_path / "evidence" / f"{cell_id}.json"
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "run_env_matrix_cell.py",
            "--job",
            "full-matrix",
            "--cell",
            cell_id,
            "--inventory",
            str(inventory_path),
            "--output",
            str(output_path),
            "--sha",
            "a" * 40,
        ],
    )

    launch_preflight: dict[str, Any] | None = None
    tox_environments = list(cell["tox_envs"])

    def start_tox(command: list[str], **kwargs: Any) -> Any:
        nonlocal launch_preflight
        if output_path.is_file():
            launch_payload = json.loads(output_path.read_text(encoding="utf-8"))
            candidate = launch_payload.get("preflight") if isinstance(launch_payload, dict) else None
            launch_preflight = candidate if isinstance(candidate, dict) else None
        result_json = Path(command[3])
        result_json.write_text("{}\n", encoding="utf-8")
        environment_name = command[-1]
        assert environment_name in tox_environments, command
        stdout = io.StringIO(
            f"{environment_name}> commands[0]> pytest tests/unit\n"
            "1 passed in 0.01s\n"
            f"{environment_name}> commands[1]> pytest examples/tutorial\n"
            "1 passed in 0.01s\n"
        )
        return SimpleNamespace(stdout=stdout, wait=lambda: 0)

    monkeypatch.setattr(runner.subprocess, "Popen", start_tox)
    monkeypatch.setattr(
        runner,
        "_installed_versions",
        lambda python: {"runtime": actual_runtime, "python": actual_python, "packages": {"pytest": "9.0.0"}},
    )
    monkeypatch.setattr(runner, "_system_tool_evidence", lambda *args, **kwargs: ({}, {}))
    monkeypatch.setattr(runner, "_python_in_tox_environment", lambda *args: Path("/fake/python"))
    monkeypatch.setattr(runner, "required_optional_versions", lambda environment: ())
    monkeypatch.setattr(runner, "required_system_tool_versions", lambda environment: ())

    return_code = runner.main()
    assert output_path.is_file(), f"matrix runner did not write evidence for {cell_id}"
    evidence = json.loads(output_path.read_text(encoding="utf-8"))
    return {
        "cell_id": cell_id,
        "expected_interpreter": str(cell["expected_interpreter"]),
        "actual_runtime": actual_runtime,
        "actual_python": actual_python,
        "actual_platform": platform,
        "actual_platform_name": platform_name,
        "actual_machine": machine,
        "expected_architecture": normalized_architecture,
        "return_code": return_code,
        "tox_environments": tox_environments,
        "launch_preflight": launch_preflight,
        "final_preflight": evidence.get("preflight"),
    }


@then("its preflight evidence should record the expected interpreter and actual runner identity before tox starts")
def cpython_315_preflight_is_recorded_before_tox(cpython_315_preflight: dict[str, Any]) -> None:
    result = cpython_315_preflight
    assert result["return_code"] == 0, result
    assert result["tox_environments"], result
    launch_preflight = result["launch_preflight"]
    assert isinstance(launch_preflight, dict), "preflight evidence was not persisted before tox started"
    assert launch_preflight == result["final_preflight"], result
    assert launch_preflight["expected_interpreter"] == "3.15.0", launch_preflight
    assert launch_preflight["runtime"] == result["actual_runtime"] == "CPython", launch_preflight
    assert launch_preflight["python"] == result["actual_python"] == "3.15.0", launch_preflight
    assert launch_preflight["platform"] == result["actual_platform"], launch_preflight
    assert launch_preflight["platform_name"] == result["actual_platform_name"], launch_preflight
    assert launch_preflight["architecture"] == result["expected_architecture"], launch_preflight


def _serialize_runtime_acceptance_evidence(
    request: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    cell_id: str,
    actual_runtime: str,
    implementation_name: str,
    actual_python: str,
    actual_pytest: str,
    sha: str,
    run_url: str,
    job_url: str,
    core_command: str,
    core_summary: str,
    tutorial_command: str,
) -> dict[str, Any]:
    repository_root = Path(request.config.rootpath)
    inventory_path = repository_root / "config" / "env-matrix.yaml"
    scripts_directory = repository_root / "scripts"
    monkeypatch.syspath_prepend(str(scripts_directory))
    runner = importlib.import_module("run_env_matrix_cell")
    selected = next(cell for cell in runner.load_cells(inventory_path, "full-matrix") if cell.get("id") == cell_id)
    tox_executable = shutil.which("tox")
    assert tox_executable is not None, "tox is needed to inspect the measured runtime environment"
    monkeypatch.setattr(
        runner,
        "platform",
        SimpleNamespace(
            python_implementation=lambda: implementation_name,
            python_version=lambda: actual_python,
            platform=lambda: "Linux-test",
            machine=lambda: "x86_64",
        ),
    )
    monkeypatch.setattr(runner.sys, "platform", "linux")
    monkeypatch.setattr(runner.shutil, "which", lambda name: "/fake/bin/tox")
    monkeypatch.setenv("PYTEST_CUKE_JOB_URL", job_url)
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "elchupanebrej/pytest-bdd-ng")
    monkeypatch.setenv("GITHUB_RUN_ID", run_url.rsplit("/", maxsplit=1)[-1])

    output_path = tmp_path / "evidence" / f"{cell_id}.json"
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "run_env_matrix_cell.py",
            "--job",
            "full-matrix",
            "--cell",
            cell_id,
            "--inventory",
            str(inventory_path),
            "--output",
            str(output_path),
            "--sha",
            sha,
        ],
    )

    tox_launch: dict[str, Any] = {}

    def run_tox(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        tox_launch["command"] = command
        launch_payload = json.loads(output_path.read_text(encoding="utf-8"))
        tox_launch["preflight"] = launch_payload.get("preflight")
        Path(command[3]).write_text('{"result": "passed"}\n', encoding="utf-8")
        environment_name = command[-1]
        assert environment_name in selected["tox_envs"], command
        stdout = (
            f"{environment_name}> commands[0]> {core_command}\n"
            f"{core_summary}\n"
            f"{environment_name}> commands[1]> {tutorial_command}\n"
            "1 passed in 0.01s\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "_run_and_stream", run_tox)
    monkeypatch.setattr(
        runner,
        "_installed_versions",
        lambda python: {
            "runtime": actual_runtime,
            "python": actual_python,
            "packages": {"pytest": actual_pytest},
        },
    )
    monkeypatch.setattr(runner, "_system_tool_evidence", lambda *args, **kwargs: ({}, {}))
    monkeypatch.setattr(runner, "_python_in_tox_environment", lambda *args: Path("/fake/python"))
    monkeypatch.setattr(runner, "required_optional_versions", lambda environment: ())
    monkeypatch.setattr(runner, "required_system_tool_versions", lambda environment: ())

    return_code = runner.main()
    evidence = json.loads(output_path.read_text(encoding="utf-8"))
    document = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    policy_cell = next(cell for cell in document["runtime_policy"]["required_cells"] if cell.get("id") == cell_id)
    return {
        "return_code": return_code,
        "evidence": evidence,
        "tox_launch": tox_launch,
        "selected_cell": selected,
        "policy_cell": policy_cell,
        "sha": sha,
        "actual_python": actual_python,
        "actual_pytest": actual_pytest,
        "run_url": run_url,
        "job_url": job_url,
        "tox_executable": tox_executable,
        "repository_root": repository_root,
        "inventory_path": inventory_path,
    }


@when("I run the PyPy 3.12 Linux acceptance cell with measured evidence", target_fixture="pypy_312_acceptance")
def run_pypy_312_linux_acceptance_cell(
    request: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Any]:
    return _serialize_runtime_acceptance_evidence(
        request,
        monkeypatch,
        tmp_path,
        cell_id="pypy-312-linux",
        actual_runtime="PyPy",
        implementation_name="PyPy",
        actual_python="3.12.15",
        actual_pytest="9.1.1",
        sha="b" * 40,
        run_url="https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/12345",
        job_url="https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/12345/job/67890",
        core_command="python -m pytest -m core",
        core_summary="1 passed in 0.01s",
        tutorial_command="python -m pytest features/compatibility/tutorial-example-acceptance.feature",
    )


@then("its measured evidence should record exact PyPy and pytest versions on Linux x86_64")
def pypy_312_measured_versions_are_recorded(pypy_312_acceptance: dict[str, Any]) -> None:
    result = pypy_312_acceptance
    evidence = result["evidence"]
    selected = result["selected_cell"]
    policy_cell = result["policy_cell"]
    assert result["return_code"] == 0, evidence
    assert selected.get("runtime") == "PyPy", selected
    assert selected.get("python") == "3.12", selected
    assert selected.get("platform") == "linux", selected
    assert selected.get("architecture") == "x86_64", selected
    assert selected.get("expected_interpreter") == "3.12.*", selected
    assert policy_cell.get("required_pytest_lines") == ["9.x"], policy_cell
    assert evidence["preflight"] == result["tox_launch"].get("preflight"), result["tox_launch"]
    preflight = evidence["preflight"]
    assert preflight["runtime"] == "PyPy", preflight
    assert preflight["python"] == result["actual_python"] == "3.12.15", preflight
    assert preflight["platform_name"] == "linux", preflight
    assert preflight["platform"] == "Linux-test", preflight
    assert preflight["architecture"] == "x86_64", preflight

    environments = evidence.get("environments")
    assert isinstance(environments, list) and len(environments) == 1, environments
    environment = environments[0]
    assert environment["runtime"] == "PyPy", environment
    assert environment["python"] == result["actual_python"], environment
    assert environment["pytest"] == result["actual_pytest"] == "9.1.1", environment
    assert re.fullmatch(r"3\.12\.\d+", environment["python"]), environment
    assert re.fullmatch(r"9\.\d+\.\d+", environment["pytest"]), environment
    assert environment["platform_name"] == "linux", environment
    assert environment["architecture"] == "x86_64", environment


@then("its acceptance evidence should prove the core and executable example commands with SHA and CI links")
def pypy_312_acceptance_commands_and_ci_links_are_recorded(pypy_312_acceptance: dict[str, Any]) -> None:
    result = pypy_312_acceptance
    evidence = result["evidence"]
    environments = evidence.get("environments")
    assert isinstance(environments, list) and len(environments) == 1, environments
    environment = environments[0]
    expected_run_url = "https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/12345"
    expected_job_url = f"{expected_run_url}/job/67890"
    assert evidence["git_sha"] == result["sha"], evidence
    assert evidence["outcome"] == environment["outcome"] == "passed", evidence
    assert environment["git_sha"] == result["sha"], environment
    assert environment["run_url"] == expected_run_url, environment
    assert environment["job_url"] == expected_job_url, environment
    assert environment["tox_environment"] == "pypy312-pytestlatest-coverage-lin", environment
    assert environment["command"] == result["tox_launch"]["command"], environment
    assert environment["selected_tests"] == environment["passed_tests"] == 2, environment
    acceptance = environment.get("acceptance_commands")
    assert isinstance(acceptance, dict), environment
    assert set(acceptance) == {"core_tests", "tutorial_example"}, acceptance
    for name, expected_index in {"core_tests": 0, "tutorial_example": 1}.items():
        command_result = acceptance[name]
        assert command_result["command_index"] == expected_index, command_result
        assert command_result["selected_tests"] == command_result["passed_tests"] == 1, command_result
        assert command_result["outcome"] == "passed", command_result


@when("I inspect the PyPy 3.12 platform exclusions", target_fixture="pypy_312_platform_exclusions")
def inspect_pypy_312_platform_exclusions(request: Any) -> list[dict[str, Any]]:
    inventory_path = Path(request.config.rootpath) / "config" / "env-matrix.yaml"
    document = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    exclusions = document.get("runtime_policy", {}).get("exclusions")
    assert isinstance(exclusions, list), exclusions
    return [
        exclusion
        for exclusion in exclusions
        if isinstance(exclusion, dict)
        and str(exclusion.get("runtime", "")).casefold() == "pypy"
        and str(exclusion.get("python")) == "3.12"
        and str(exclusion.get("platform", "")).casefold() in {"macos", "windows"}
    ]


@then("macOS and Windows should remain upstream available and carry technical exclusion reasons")
def pypy_312_non_linux_exclusions_are_source_backed(
    pypy_312_platform_exclusions: list[dict[str, Any]],
) -> None:
    exclusions = pypy_312_platform_exclusions
    by_platform = {str(exclusion.get("platform", "")).casefold(): exclusion for exclusion in exclusions}
    assert set(by_platform) == {"macos", "windows"}, by_platform

    for platform_name, exclusion in by_platform.items():
        assert exclusion.get("upstream_availability", {}).get("status") == "available", exclusion
        assert exclusion.get("product_support", {}).get("status") == "unsupported", exclusion
        required_ci = exclusion.get("required_ci")
        assert isinstance(required_ci, dict) and required_ci.get("status") == "excluded", exclusion
        assert required_ci.get("tox_envs") == [], exclusion
        reason = str(exclusion.get("reason", "")).casefold()
        assert reason, exclusion
        assert "pydantic-core" in reason, (platform_name, exclusion)
        assert "wheel" in reason, (platform_name, exclusion)
        assert "source" in reason and any(term in reason for term in ("unverified", "not verified")), (
            platform_name,
            exclusion,
        )
        source_evidence = exclusion.get("source_evidence")
        assert isinstance(source_evidence, list) and source_evidence, exclusion
        assert all(str(source).startswith(("http://", "https://")) for source in source_evidence), exclusion


@when(
    "I serialize a previously measured GraalPy 25.3 Linux acceptance artifact",
    target_fixture="graalpy_253_serialized_evidence",
)
def run_graalpy_253_linux_acceptance(
    request: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Any]:
    acceptance = _serialize_runtime_acceptance_evidence(
        request,
        monkeypatch,
        tmp_path,
        cell_id="graalpy-253-linux",
        actual_runtime="GraalPy",
        implementation_name="GraalVM",
        actual_python="3.13.14",
        actual_pytest="9.1.1",
        sha="f32d1150893bf0227e13940abd83549f4d9dc748",
        run_url="https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/39730654752",
        job_url="https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/39730654752/job/119664736950",
        core_command="coverage run --append -m pytest -m core",
        core_summary="1260 passed, 49 skipped in 30.00s",
        tutorial_command=("python -m pytest features/compatibility/tutorial-example-acceptance.feature -m e2e -q"),
    )
    repository_root = acceptance["repository_root"]
    selected = acceptance["selected_cell"]
    tox_config = subprocess.run(
        [
            acceptance["tox_executable"],
            "config",
            "-e",
            selected["tox_envs"][0],
            "-k",
            "package",
            "skip_install",
            "deps",
            "commands",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert tox_config.returncode == 0, f"GraalPy tox config failed: {tox_config.stdout}\n{tox_config.stderr}"

    workflow_path = repository_root / ".github" / "workflows" / "main.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    artifact_names = [
        step.get("with", {}).get("name")
        for job in workflow["jobs"].values()
        if isinstance(job, dict)
        for step in job.get("steps", [])
        if isinstance(step, dict) and step.get("uses") == "actions/upload-artifact@v4"
    ]
    return {
        **acceptance,
        "tox_config": tox_config.stdout,
        "expected_run_url": acceptance["run_url"],
        "expected_job_url": acceptance["job_url"],
        "expected_artifact_name": f"full-supported-proof-{acceptance['sha']}",
        "artifact_names": artifact_names,
    }


@then("serialized evidence should preserve exact GraalPy and pytest versions on Linux x86_64 and bundled pip")
def graalpy_253_measured_versions_and_bundled_pip_are_recorded(graalpy_253_serialized_evidence: dict[str, Any]) -> None:
    result = graalpy_253_serialized_evidence
    evidence = result["evidence"]
    selected = result["selected_cell"]
    policy_cell = result["policy_cell"]
    assert result["return_code"] == 0, evidence
    assert selected.get("runtime") == "GraalPy", selected
    assert selected.get("runtime_version") == "25.3", selected
    assert selected.get("python") == result["actual_python"] == "3.13.14", selected
    assert selected.get("platform") == "linux", selected
    assert selected.get("architecture") == "x86_64", selected
    assert selected.get("expected_interpreter") == "3.13.14", selected
    assert selected.get("setup_python_input") == "graalpy-25.3", selected
    assert policy_cell.get("required_pytest_lines") == ["9.x"], policy_cell
    assert policy_cell.get("runtime_version") == "25.3", policy_cell
    assert policy_cell.get("python") == "3.13.14", policy_cell
    installability = policy_cell.get("installability")
    assert isinstance(installability, dict), policy_cell
    assert installability.get("acceptance") == ["core-install", "core-tests", "examples"], installability

    assert evidence["preflight"] == result["tox_launch"].get("preflight"), result["tox_launch"]
    preflight = evidence["preflight"]
    assert preflight["runtime"] == "GraalPy", preflight
    assert preflight["python"] == result["actual_python"], preflight
    assert preflight["platform_name"] == "linux", preflight
    assert preflight["platform"] == "Linux-test", preflight
    assert preflight["architecture"] == "x86_64", preflight

    environments = evidence.get("environments")
    assert isinstance(environments, list) and len(environments) == 1, environments
    environment = environments[0]
    assert environment["runtime"] == "GraalPy", environment
    assert environment["python"] == result["actual_python"], environment
    assert environment["pytest"] == result["actual_pytest"] == "9.1.1", environment
    assert environment["platform_name"] == "linux", environment
    assert environment["architecture"] == "x86_64", environment
    assert re.fullmatch(r"9\.\d+\.\d+", environment["pytest"]), environment

    tox_config = result["tox_config"]
    assert "package = sdist" in tox_config, tox_config
    assert "skip_install = False" in tox_config, tox_config
    assert not re.search(r"(?im)^\s*pip(?:\b|[<>=!~])", tox_config), tox_config
    assert not re.search(r"(?i)(?:python\s+-m\s+)?pip\s+install\b", tox_config), tox_config


@then("serialized acceptance evidence should preserve sdist installation core and tutorial results with exact CI links")
def graalpy_253_acceptance_commands_and_ci_links_are_recorded(
    graalpy_253_serialized_evidence: dict[str, Any],
) -> None:
    result = graalpy_253_serialized_evidence
    evidence = result["evidence"]
    environments = evidence.get("environments")
    assert isinstance(environments, list) and len(environments) == 1, environments
    environment = environments[0]
    assert evidence["git_sha"] == result["sha"] == "f32d1150893bf0227e13940abd83549f4d9dc748", evidence
    assert evidence["outcome"] == environment["outcome"] == "passed", evidence
    assert environment["git_sha"] == result["sha"], environment
    assert environment["run_url"] == result["expected_run_url"], environment
    assert environment["job_url"] == result["expected_job_url"], environment
    assert environment["tox_environment"] == "graalpy-253-pytestlatest-coverage-lin", environment
    assert environment["command"] == result["tox_launch"]["command"], environment
    assert environment["command"][1:2] == ["run"], environment
    assert "--result-json" in environment["command"], environment
    assert environment["command"][-2:] == ["-e", "graalpy-253-pytestlatest-coverage-lin"], environment
    assert environment["selected_tests"] == 1310, environment
    assert environment["passed_tests"] == 1261, environment

    acceptance = environment.get("acceptance_commands")
    assert isinstance(acceptance, dict), environment
    core = acceptance.get("core_tests")
    tutorial = acceptance.get("tutorial_example")
    assert isinstance(core, dict) and isinstance(tutorial, dict), acceptance
    assert core["command_index"] == 0, core
    assert core["selected_tests"] == 1309 and core["passed_tests"] == 1260, core
    assert core["outcome"] == "passed" and core["failed_tests"] == core["error_tests"] == 0, core
    assert tutorial["command_index"] == 1, tutorial
    assert tutorial["selected_tests"] == tutorial["passed_tests"] == 1, tutorial
    assert tutorial["outcome"] == "passed", tutorial
    artifact_template = "full-supported-proof-${{ github.sha }}"
    assert result["artifact_names"].count(artifact_template) == 1, result["artifact_names"]
    assert result["expected_artifact_name"] == artifact_template.replace("${{ github.sha }}", result["sha"]), result


@when("I inspect the GraalPy 25.3 platform exclusions", target_fixture="graalpy_253_platform_exclusions")
def inspect_graalpy_253_platform_exclusions(request: Any) -> list[dict[str, Any]]:
    inventory_path = Path(request.config.rootpath) / "config" / "env-matrix.yaml"
    document = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    exclusions = document.get("runtime_policy", {}).get("exclusions")
    assert isinstance(exclusions, list), exclusions
    return [
        exclusion
        for exclusion in exclusions
        if isinstance(exclusion, dict)
        and str(exclusion.get("runtime", "")).casefold() == "graalpy"
        and str(exclusion.get("runtime_version")) == "25.3"
        and str(exclusion.get("platform", "")).casefold() in {"macos", "windows"}
    ]


@then("macOS and Windows should remain upstream available and carry GraalPy-specific technical reasons")
def graalpy_253_non_linux_exclusions_are_source_backed(
    graalpy_253_platform_exclusions: list[dict[str, Any]],
) -> None:
    exclusions = graalpy_253_platform_exclusions
    by_platform = {str(exclusion.get("platform", "")).casefold(): exclusion for exclusion in exclusions}
    assert set(by_platform) == {"macos", "windows"}, by_platform
    for platform_name, exclusion in by_platform.items():
        assert exclusion.get("python") == "3.13.14", exclusion
        assert exclusion.get("upstream_availability", {}).get("status") == "available", exclusion
        assert exclusion.get("product_support", {}).get("status") == "unsupported", exclusion
        required_ci = exclusion.get("required_ci")
        assert isinstance(required_ci, dict) and required_ci.get("status") == "excluded", exclusion
        assert required_ci.get("tox_envs") == [], exclusion
        reason = str(exclusion.get("reason", "")).casefold()
        assert reason, exclusion
        assert "source/native" in reason and any(term in reason for term in ("not verified", "unverified")), (
            platform_name,
            exclusion,
        )
        assert "graalpy-compatible wheels" in reason and "source builds" in reason, (platform_name, exclusion)
        upstream_reason = str(exclusion.get("installability", {}).get("reason", "")).casefold()
        if platform_name == "macos":
            assert "less comprehensively tested" in upstream_reason, exclusion
        else:
            assert "additional windows limitations" in upstream_reason, exclusion
        source_evidence = exclusion.get("source_evidence")
        assert isinstance(source_evidence, list) and source_evidence, exclusion
        assert "https://www.graalvm.org/latest/python/docs/" in source_evidence, exclusion


@then("the CPython 3.14 macOS tox config should include uv>=0.8")
def cpython_314_macos_runtime_tox_config_installs_uv(consumer: Any) -> None:
    context = _context(consumer)
    cell = next(
        (
            candidate
            for candidate in _required_runtime_cells(context)
            if str(candidate.get("runtime", "")).casefold() == "cpython"
            and str(candidate.get("python")) == "3.14"
            and str(candidate.get("platform", "")).casefold() == "macos"
        ),
        None,
    )
    assert cell is not None, "the runtime inventory must declare CPython 3.14 macOS acceptance"
    required_ci = cell.get("required_ci")
    tox_environments = required_ci.get("tox_envs") if isinstance(required_ci, dict) else None
    assert isinstance(tox_environments, list) and tox_environments, cell

    for environment_name in tox_environments:
        result = subprocess.run(
            ["tox", "config", "-e", str(environment_name), "-k", "deps", "--format=json"],
            cwd=consumer.path,
            env=_inventory_command_environment(consumer),
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"tox config failed for {environment_name}: {result.stdout}\n{result.stderr}"
        payload = json.loads(result.stdout)
        environment_config = payload.get("env", {}).get(str(environment_name), {})
        dependencies = environment_config.get("deps")
        normalized_dependencies = (
            {re.sub(r"\s+", "", str(dependency)).casefold() for dependency in dependencies}
            if isinstance(dependencies, list)
            else set()
        )
        assert "uv>=0.8" in normalized_dependencies, (
            f"{environment_name} must resolve uv>=0.8 for the isolated consumer acceptance tests; "
            f"resolved dependencies were {dependencies!r}"
        )


@then("every required lane should have resolved command and CI selection proof")
def every_required_lane_has_tox_and_ci_proof(consumer: Any) -> None:
    context = _context(consumer)
    proof_lanes = _proof_lanes(context)
    workflow_cells = _report(context).get("inventory", {}).get("workflowCells")
    assert isinstance(workflow_cells, list) and workflow_cells, workflow_cells
    workflow_evidence = json.dumps(workflow_cells, ensure_ascii=False, sort_keys=True, default=str)
    for lane in _lanes(context):
        if _status(lane) != "required":
            continue
        lane_id = _lane_id(lane)
        proof = proof_lanes.get(lane_id)
        assert proof is not None, f"required lane {lane_id!r} has no proof record"
        tox_proof = proof.get("tox", {})
        ci_proof = proof.get("ci", {})
        assert tox_proof.get("environment") == lane["tox_env"], (lane, tox_proof)
        assert tox_proof.get("resolved") is True, (lane, tox_proof)
        assert tox_proof.get("command"), (lane, tox_proof)
        assert ci_proof.get("workflow") and ci_proof.get("selector"), (lane, ci_proof)
        assert ci_proof.get("selected") is True, (lane, ci_proof)
        selector_json = json.dumps(lane["workflow_selector"], ensure_ascii=False, sort_keys=True, default=str)
        assert selector_json.strip('"') in workflow_evidence, (lane, workflow_cells)
        command_proof = proof.get("command", {})
        assert command_proof.get("declared") == lane["command"], (lane, command_proof)
        assert command_proof.get("resolved") is True, (lane, command_proof)


@then("the active lane proof should record actual runtime Python pytest and platform versions")
def active_lane_proof_records_actual_versions(consumer: Any) -> None:
    active = _report(_context(consumer)).get("proof", {}).get("activeEnvironment")
    assert isinstance(active, dict), active
    assert str(active.get("runtime", "")).casefold() == platform.python_implementation().casefold(), active
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert str(active.get("python", "")).startswith(python_version), active
    assert str(active.get("pytest", "")) == pytest.__version__, active
    actual_platforms = {sys.platform.casefold(), platform.system().casefold()}
    assert str(active.get("platform", "")).casefold() in actual_platforms, active


@then("active runtime policy should require CPython 3.11 through 3.15 on Linux macOS and Windows")
def active_runtime_policy_requires_current_cpython_cells(consumer: Any) -> None:
    context = _context(consumer)
    cells = _required_runtime_cells(context)
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
    actual = {_runtime_cell_key(cell) for cell in cells if str(cell.get("runtime", "")).casefold() == "cpython"}
    assert actual == expected, (sorted(expected - actual), sorted(actual - expected))


@then("active runtime policy should require PyPy 3.12 and GraalPy 25.3 on Linux x86_64")
def active_runtime_policy_requires_alternative_runtimes(consumer: Any) -> None:
    actual = {_runtime_cell_key(cell) for cell in _required_runtime_cells(_context(consumer))}
    expected = {
        ("pypy", "3.12", "linux", "x86_64"),
        ("graalpy", "3.13.14", "linux", "x86_64"),
    }
    assert expected <= actual, (sorted(expected - actual), sorted(actual - expected))
    graalpy = next(
        cell
        for cell in _required_runtime_cells(_context(consumer))
        if str(cell.get("runtime", "")).casefold() == "graalpy"
    )
    assert graalpy.get("runtime_version") == "25.3", graalpy


@then("GraalPy and CPython 3.15 cells should pin their setup-python inputs and expected interpreters")
def special_runtimes_pin_setup_python_inputs(consumer: Any) -> None:
    context = _context(consumer)
    cells = _required_runtime_cells(context)
    workflow_cells = context.document.get("workflow_cells")
    assert isinstance(workflow_cells, list), workflow_cells
    workflow_by_id = {str(cell.get("id")): cell for cell in workflow_cells if isinstance(cell, dict)}
    graalpy = next(cell for cell in cells if str(cell.get("runtime", "")).casefold() == "graalpy")
    assert graalpy.get("setup_python") == {"input": "graalpy-25.3", "expected_interpreter": "3.13.14"}, graalpy
    graalpy_workflow = workflow_by_id.get(str(graalpy.get("id")))
    assert isinstance(graalpy_workflow, dict), graalpy_workflow
    assert graalpy_workflow.get("setup_python_input") == "graalpy-25.3", graalpy_workflow
    assert graalpy_workflow.get("expected_interpreter") == "3.13.14", graalpy_workflow
    cpython_315 = [
        cell
        for cell in cells
        if str(cell.get("runtime", "")).casefold() == "cpython" and str(cell.get("python")) == "3.15"
    ]
    assert len(cpython_315) == 3, cpython_315
    for cell in cpython_315:
        assert cell.get("setup_python") == {"input": "3.15.0", "expected_interpreter": "3.15.0"}, cell
        workflow_cell = workflow_by_id.get(str(cell.get("id")))
        assert isinstance(workflow_cell, dict), workflow_cell
        assert workflow_cell.get("setup_python_input") == "3.15.0", workflow_cell
        assert workflow_cell.get("expected_interpreter") == "3.15.0", workflow_cell


@then("the CPython 3.11 Linux required cell should require x86_64 in runtime policy and CI")
def cpython_311_linux_cell_requires_x86_64(consumer: Any) -> None:
    context = _context(consumer)
    policy_cell = next(
        (cell for cell in _required_runtime_cells(context) if cell.get("id") == "cpython-311-linux"),
        None,
    )
    assert isinstance(policy_cell, dict), "runtime policy must contain the required cpython-311-linux cell"

    workflow_cells = context.document.get("workflow_cells")
    assert isinstance(workflow_cells, list), workflow_cells
    workflow_cell = next(
        (
            cell
            for cell in workflow_cells
            if isinstance(cell, dict) and cell.get("id") == "cpython-311-linux" and cell.get("job") == "full-matrix"
        ),
        None,
    )
    assert isinstance(workflow_cell, dict), "full-matrix workflow must contain cpython-311-linux"

    actual_architectures = {
        "runtime_policy": policy_cell.get("architecture"),
        "workflow_cell": workflow_cell.get("architecture"),
    }
    assert actual_architectures == {"runtime_policy": "x86_64", "workflow_cell": "x86_64"}, actual_architectures


@then("required CPython cells should use latest pytest 9 with the specified pytest 7 and 8 floor cells")
def required_cpython_cells_use_latest_and_compatible_floor_pytest(consumer: Any) -> None:
    context = _context(consumer)
    policy = _runtime_policy(context)
    pytest_policy = policy.get("pytest")
    assert isinstance(pytest_policy, dict), pytest_policy
    assert pytest_policy.get("minimum") == ">=7.0", pytest_policy
    assert pytest_policy.get("latest") == "9.x", pytest_policy
    cells = _required_runtime_cells(context)
    for cell in cells:
        if str(cell.get("runtime", "")).casefold() != "cpython":
            continue
        required_lines = cell.get("required_pytest_lines")
        assert isinstance(required_lines, list) and "9.x" in required_lines, cell
    by_key = {_runtime_cell_key(cell): cell for cell in cells}
    expected_floor_lines = {
        ("cpython", "3.11", "linux", "x86_64"): "7.4.x",
        ("cpython", "3.12", "linux", "runner-native"): "8.4.x",
    }
    for key, floor in expected_floor_lines.items():
        cell = by_key.get(key)
        assert cell is not None, key
        assert floor in cell.get("required_pytest_lines", []), (key, cell)


@then("every required runtime cell should include core install and example acceptance")
def every_required_runtime_cell_accepts_core_install_and_examples(consumer: Any) -> None:
    context = _context(consumer)
    workflow_cells = context.document.get("workflow_cells")
    assert isinstance(workflow_cells, list), workflow_cells
    workflow_by_id = {str(cell.get("id")): cell for cell in workflow_cells if isinstance(cell, dict)}
    for cell in _required_runtime_cells(context):
        cell_id = str(cell.get("id", ""))
        installability = cell.get("installability")
        assert isinstance(installability, dict) and installability.get("status") == "required-acceptance", (
            cell_id,
            cell,
        )
        acceptance = installability.get("acceptance")
        assert isinstance(acceptance, list) and {"core-install", "core-tests", "examples"} <= set(acceptance), cell
        required_ci = cell.get("required_ci")
        assert isinstance(required_ci, dict) and required_ci.get("status") == "required", cell
        selector = required_ci.get("workflow_cell")
        assert selector == cell_id and selector in workflow_by_id, (cell, workflow_by_id.keys())


@then("optional extras should remain separate from required runtime acceptance")
def optional_extras_remain_separate_from_runtime_acceptance(consumer: Any) -> None:
    optional_extra_markers = ("allure", "playwright", "native", "remote", "formatter", "browser", "struct-bdd")
    for cell in _required_runtime_cells(_context(consumer)):
        installability = cell.get("installability")
        assert isinstance(installability, dict), cell
        acceptance = installability.get("acceptance")
        assert acceptance == ["core-install", "core-tests", "examples"], (cell.get("id"), acceptance)
        required_ci = cell.get("required_ci")
        assert isinstance(required_ci, dict), cell
        tox_envs = required_ci.get("tox_envs")
        assert isinstance(tox_envs, list) and tox_envs, cell
        assert not any(
            marker in str(environment).casefold() for environment in tox_envs for marker in optional_extra_markers
        ), (cell.get("id"), tox_envs)


@then(
    "every required runtime cell should declare upstream availability installability product support required CI and measured evidence separately"
)
def every_required_runtime_cell_separates_policy_dimensions(consumer: Any) -> None:
    required_keys = {
        "upstream_availability",
        "installability",
        "product_support",
        "required_ci",
        "measured_evidence",
    }
    for cell in _required_runtime_cells(_context(consumer)):
        missing = required_keys - cell.keys()
        assert not missing, (cell.get("id"), sorted(missing))
        availability = cell["upstream_availability"]
        support = cell["product_support"]
        measured = cell["measured_evidence"]
        assert isinstance(availability, dict) and availability.get("status") == "available", cell
        assert _has_http_sources(availability.get("source_evidence")), cell
        assert isinstance(support, dict) and support.get("status") == "supported", cell
        assert isinstance(measured, dict) and measured.get("status") == "per-run", cell


@then(
    "every required cell should require measured Python pytest platform architecture SHA command selected and passed tests outcome and workflow URLs"
)
def every_required_cell_requires_complete_measured_evidence(consumer: Any) -> None:
    fields = {
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
    for cell in _required_runtime_cells(_context(consumer)):
        measured = cell.get("measured_evidence")
        assert isinstance(measured, dict), cell
        declared_fields = measured.get("fields")
        assert isinstance(declared_fields, list) and fields <= set(declared_fields), (cell.get("id"), declared_fields)


@then("historical support rows should remain history and must not be active support")
def historical_rows_remain_outside_active_support(consumer: Any) -> None:
    context = _context(consumer)
    historical = context.document.get("support_ledger", {}).get("historical_cells")
    assert isinstance(historical, list) and len(historical) == 12, historical
    current_cells = {_runtime_cell_key(cell) for cell in _required_runtime_cells(context)}
    assert all(key[0] != "pypy" or key[1] != "3.11" for key in current_cells), current_cells
    assert all(key[0] != "cpython" or key[1] != "3.10" for key in current_cells), current_cells
    active_lanes = [lane for lane in _lanes(context) if _status(lane) != "unsupported"]
    assert all(
        not (str(lane.get("runtime", "")).casefold() == "pypy" and str(lane.get("python")) == "3.11")
        and not (str(lane.get("runtime", "")).casefold() == "cpython" and str(lane.get("python")) == "3.10")
        for lane in active_lanes
    ), active_lanes


@then("PyPy 3.10 and 3.11 exclusions should remain source-backed historical runtime records")
def retired_pypy_runtime_and_capability_exclusions_remain_historical(consumer: Any) -> None:
    context = _context(consumer)
    policy_exclusions = _runtime_policy(context).get("exclusions")
    assert isinstance(policy_exclusions, list), policy_exclusions
    pypy_runtime_exclusions = {
        str(item.get("python")): item
        for item in policy_exclusions
        if isinstance(item, dict)
        and str(item.get("runtime", "")).casefold() == "pypy"
        and str(item.get("python")) in {"3.10", "3.11"}
    }
    assert set(pypy_runtime_exclusions) == {"3.10", "3.11"}, pypy_runtime_exclusions
    for version, exclusion in pypy_runtime_exclusions.items():
        assert exclusion.get("reason") and exclusion.get("source_evidence"), (version, exclusion)

    assert context.document.get("capability_exclusions") == []
    historical_exclusions = context.document.get("support_ledger", {}).get("historical_capability_exclusions")
    assert isinstance(historical_exclusions, list), historical_exclusions
    historical_pypy = {
        str(item.get("python")): item
        for item in historical_exclusions
        if isinstance(item, dict)
        and str(item.get("runtime", "")).casefold() == "pypy"
        and item.get("capability") == "debug-mcp"
        and item.get("platform") == "windows"
    }
    assert set(historical_pypy) == {"3.10", "3.11"}, historical_pypy
    assert all(item.get("historical_status") == "retired-runtime" for item in historical_pypy.values())
    assert all(item.get("reason") and item.get("source_evidence") for item in historical_pypy.values())


@then("pytest 7 support should cover every Python pairing allowed by upstream constraints")
def every_upstream_compatible_pairing_retains_pytest_7_support(consumer: Any) -> None:
    from pytest_cuke.compatibility.runtime_compat import PYTEST_COMPATIBILITY_BOUNDS

    python_versions = {
        str(cell["python"])
        for cell in _required_runtime_cells(_context(consumer))
        if str(cell.get("runtime", "")).casefold() == "cpython"
    }
    for python_version in python_versions:
        python_tuple = tuple(int(part) for part in python_version.split("."))
        python_factor = python_version.replace(".", "")
        for pytest_factor, (minimum_python, maximum_python) in PYTEST_COMPATIBILITY_BOUNDS.items():
            upstream_allows_pair = python_tuple >= minimum_python and (
                maximum_python is None or python_tuple <= maximum_python
            )
            if not upstream_allows_pair:
                continue
            compatible, reason = is_pair_compatible(python_factor, pytest_factor)
            assert compatible, (
                f"Python {python_version} and pytest {pytest_factor} are permitted upstream, "
                f"but product compatibility reports {reason}"
            )


@then("each unsupported runtime or pytest pairing should have upstream evidence and a reason")
def unsupported_pairs_have_upstream_evidence_and_reason(consumer: Any) -> None:
    context = _context(consumer)
    exclusions = _runtime_policy(context).get("exclusions")
    assert isinstance(exclusions, list) and exclusions, exclusions
    for exclusion in exclusions:
        assert isinstance(exclusion, dict), exclusion
        assert exclusion.get("reason"), exclusion
        assert _has_http_sources(exclusion.get("source_evidence")), exclusion
        availability = exclusion.get("upstream_availability")
        product_support = exclusion.get("product_support")
        assert isinstance(availability, dict) and availability.get("status") in {
            "available",
            "unavailable",
            "unknown",
        }, exclusion
        assert _has_http_sources(availability.get("source_evidence")), exclusion
        assert isinstance(product_support, dict) and product_support.get("status") == "unsupported", exclusion
        assert product_support.get("reason"), exclusion
    historical_pairings = context.document.get("support_ledger", {}).get("exclusions")
    assert isinstance(historical_pairings, list) and historical_pairings, historical_pairings
    for exclusion in historical_pairings:
        assert isinstance(exclusion, dict), exclusion
        assert exclusion.get("reason") and exclusion.get("basis"), exclusion
        assert _has_http_sources(exclusion.get("source_evidence")), exclusion


@then(
    "every runtime exclusion should record upstream availability installability product support required CI "
    "measured evidence and a named reason"
)
def runtime_exclusions_record_separate_policy_dimensions(consumer: Any) -> None:
    exclusions = _runtime_policy(_context(consumer)).get("exclusions")
    assert isinstance(exclusions, list) and exclusions, exclusions
    dimensions = (
        "upstream_availability",
        "installability",
        "product_support",
        "required_ci",
        "measured_evidence",
    )
    for exclusion in exclusions:
        assert isinstance(exclusion, dict), exclusion
        assert str(exclusion.get("id", "")).strip(), exclusion
        assert str(exclusion.get("reason", "")).strip(), exclusion
        for dimension in dimensions:
            record = exclusion.get(dimension)
            assert isinstance(record, dict), (exclusion.get("id"), dimension, exclusion)
            assert str(record.get("status", "")).strip(), (exclusion.get("id"), dimension, record)
        availability = exclusion["upstream_availability"]
        assert availability.get("status") in {"available", "unavailable", "unknown"}, exclusion
        assert _has_http_sources(availability.get("source_evidence")), exclusion
        support = exclusion["product_support"]
        assert support.get("status") == "unsupported", exclusion
        assert str(support.get("reason", "")).strip(), exclusion


def _has_http_sources(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(source, str) and source.startswith(("https://", "http://")) for source in value)
    )


@then("the pre-commit lane should resolve to a tox command that runs pre-commit")
def precommit_lane_resolves_to_lint_command(consumer: Any) -> None:
    context = _context(consumer)
    lane_matches = [
        lane for lane in _lanes(context) if "pre-commit" in _lane_text(lane) or "precommit" in _lane_text(lane)
    ]
    assert lane_matches, "the inventory must declare the pre-commit lane"
    proof_lanes = _proof_lanes(context)
    for lane in lane_matches:
        lane_id = _lane_id(lane)
        proof = proof_lanes.get(lane_id)
        assert proof is not None, lane
        tox_proof = proof.get("tox", {})
        assert tox_proof.get("environment") == lane.get("tox_env"), (lane, tox_proof)
        command = " ".join(_tox_configured_commands(consumer, str(lane["tox_env"]))).casefold()
        assert "pre-commit" in command, (lane, tox_proof)


@then("configured hook Python should match the pre-commit lane interpreter")
def configured_precommit_python_matches_lane_interpreter(consumer: Any) -> None:
    context = _context(consumer)
    lane = next((candidate for candidate in _lanes(context) if _lane_id(candidate) == "pre-commit"), None)
    assert lane is not None, "the inventory must declare the required pre-commit lane"
    assert str(lane.get("runtime", "")).casefold() == "cpython", lane
    expected_python = f"python{lane.get('python')}"
    config_path = context.repository_root / ".pre-commit-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert isinstance(config, dict), f"pre-commit config must be a YAML mapping: {config_path}"

    default_versions = config.get("default_language_version")
    assert isinstance(default_versions, dict), f"pre-commit config must declare default_language_version: {config}"
    default_python = default_versions.get("python")
    assert default_python == expected_python, (
        f"pre-commit's default Python {default_python!r} must match the selected lane interpreter {expected_python!r}"
    )

    repositories = config.get("repos")
    assert isinstance(repositories, list), f"pre-commit config must declare repos: {config}"
    hook_overrides = [
        (hook.get("id", "<unnamed>"), hook["language_version"])
        for repository in repositories
        if isinstance(repository, dict)
        for hook in repository.get("hooks", [])
        if isinstance(hook, dict) and "language_version" in hook
    ]
    mismatches = [(hook_id, version) for hook_id, version in hook_overrides if version != expected_python]
    assert not mismatches, (
        f"Python hook overrides must match the selected lane interpreter {expected_python!r}: {mismatches!r}"
    )


@then("the pre-commit tox environment should install the testtypes and debug-mcp extras")
def precommit_tox_environment_installs_typing_extras(consumer: Any) -> None:
    context = _context(consumer)
    lane = next((candidate for candidate in _lanes(context) if _lane_id(candidate) == "pre-commit"), None)
    assert lane is not None, "the inventory must declare the required pre-commit lane"
    environment_name = lane.get("tox_env")
    assert environment_name == "py314-pre-commit-lin", lane
    result = subprocess.run(
        ["tox", "config", "-e", str(environment_name), "-k", "extras", "--format=json"],
        cwd=consumer.path,
        env=_inventory_command_environment(consumer),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"tox config failed for {environment_name}: {result.stdout}\n{result.stderr}"
    payload = json.loads(result.stdout)
    environment_config = payload.get("env", {}).get(environment_name, {})
    extras = environment_config.get("extras")
    expected_extras = {"testtypes", "debug-mcp"}
    assert isinstance(extras, list) and expected_extras <= set(extras), (
        f"{environment_name} must install {sorted(expected_extras)!r}; resolved extras were {extras!r}"
    )


@then("Ruff pre-commit hooks should match the py314-ruff tox scope and pinned version")
def ruff_precommit_hooks_match_tox_scope(consumer: Any) -> None:
    context = _context(consumer)
    commands = _tox_configured_commands(consumer, "py314-ruff")
    command_tokens = [token for command in commands for token in shlex.split(command)]
    assert len(command_tokens) >= 3 and command_tokens[:2] == [
        "ruff",
        "check",
    ], f"py314-ruff must resolve to an explicit Ruff check command, got {commands!r}"
    carrier_paths = command_tokens[2:]
    assert carrier_paths and all(not path.startswith("-") for path in carrier_paths), (
        f"py314-ruff must list its carrier paths explicitly, got {commands!r}"
    )
    normalized_carriers = [Path(path).as_posix() for path in carrier_paths]

    legacy_path = "tests/e2e/steps.py"
    assert (context.repository_root / legacy_path).is_file(), f"expected legacy file is missing: {legacy_path}"
    assert legacy_path not in normalized_carriers, (
        f"the legacy file used to guard the approved scope must remain outside py314-ruff: {legacy_path}"
    )

    config_path = context.repository_root / ".pre-commit-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert isinstance(config, dict), f"pre-commit config must be a YAML mapping: {config_path}"
    repositories = config.get("repos")
    assert isinstance(repositories, list), f"pre-commit config must declare repos: {config}"
    hooks = {
        str(hook.get("id")): hook
        for repository in repositories
        if isinstance(repository, dict)
        for hook in repository.get("hooks", [])
        if isinstance(hook, dict) and hook.get("id")
    }

    ruff_repository = next(
        (
            repository
            for repository in repositories
            if isinstance(repository, dict) and repository.get("repo") == "https://github.com/astral-sh/ruff-pre-commit"
        ),
        None,
    )
    assert ruff_repository is not None, "pre-commit config must declare the official Ruff hooks repository"
    expected_revision = "v0.17.0"
    revision = ruff_repository.get("rev")
    assert revision == expected_revision, (
        f"the Ruff pre-commit repository must be pinned to {expected_revision!r}, got {revision!r}"
    )

    tox_config = configparser.ConfigParser(interpolation=None)
    tox_config_path = context.repository_root / "tox.ini"
    assert tox_config.read(tox_config_path, encoding="utf-8"), f"could not read {tox_config_path}"
    tox_section = "testenv:py314-ruff"
    assert tox_config.has_section(tox_section), f"tox.ini must declare [{tox_section}]"
    tox_ruff_dependencies = [
        dependency.strip()
        for dependency in tox_config[tox_section].get("deps", "").splitlines()
        if dependency.strip().casefold().startswith("ruff")
    ]
    expected_dependency = f"ruff=={expected_revision.removeprefix('v')}"
    assert tox_ruff_dependencies == [expected_dependency], (
        f"[{tox_section}] must pin {expected_dependency!r} to match the Ruff hook revision; "
        f"resolved Ruff dependencies were {tox_ruff_dependencies!r}"
    )

    missing_hooks = [hook_id for hook_id in ("ruff-check", "ruff-format") if hook_id not in hooks]
    assert not missing_hooks, f"pre-commit config is missing scoped Ruff hooks: {missing_hooks!r}"
    uncovered: dict[str, list[str]] = {}
    selected_legacy: list[str] = []
    for hook_id in ("ruff-check", "ruff-format"):
        hook = hooks[hook_id]
        files_pattern = hook.get("files", "")
        exclude_pattern = hook.get("exclude", "")
        if not isinstance(files_pattern, str) or not isinstance(exclude_pattern, str):
            uncovered[hook_id] = normalized_carriers
            continue

        uncovered[hook_id] = [path for path in normalized_carriers if not _precommit_hook_selects_path(hook, path)]
        if _precommit_hook_selects_path(hook, legacy_path):
            selected_legacy.append(hook_id)

    assert not any(uncovered.values()), (
        "both Ruff pre-commit hooks must include every carrier path selected by py314-ruff; "
        f"uncovered paths: {uncovered!r}"
    )
    assert not selected_legacy, (
        f"the legacy file outside the approved py314-ruff scope must not be selected by Ruff hooks: {selected_legacy!r}"
    )


@then("pre-commit text fixers should exclude upstream schemas and generated docs")
def precommit_text_fixers_exclude_schemas_and_generated_docs(consumer: Any) -> None:
    context = _context(consumer)
    config_path = context.repository_root / ".pre-commit-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert isinstance(config, dict), f"pre-commit config must be a YAML mapping: {config_path}"
    repositories = config.get("repos")
    assert isinstance(repositories, list), f"pre-commit config must declare repos: {config}"
    hooks = {
        str(hook.get("id")): hook
        for repository in repositories
        if isinstance(repository, dict)
        for hook in repository.get("hooks", [])
        if isinstance(hook, dict) and hook.get("id")
    }
    fixer_ids = ("trailing-whitespace", "end-of-file-fixer")
    schema_paths = sorted(
        path.relative_to(context.repository_root).as_posix()
        for path in (
            *context.repository_root.glob("src/pytest_cuke/model/message_schemas/*.schema.json"),
            *context.repository_root.glob("tests/fixtures/message-schemas-v*/jsonschema/*.json"),
        )
    )
    assert schema_paths, "the repository should contain upstream message schema files"
    generated_doc_paths = sorted(
        path.relative_to(context.repository_root).as_posix()
        for path in context.repository_root.glob("docs/features/*.rst")
    )
    assert generated_doc_paths, "the repository should contain generated docs/features/*.rst files"
    missing_hooks = [hook_id for hook_id in fixer_ids if hook_id not in hooks]
    assert not missing_hooks, f"pre-commit config is missing schema-mutating text fixers: {missing_hooks!r}"

    uncovered: dict[str, list[str]] = {}
    for hook_id in fixer_ids:
        exclusion = hooks[hook_id].get("exclude")
        if not isinstance(exclusion, str) or not exclusion:
            uncovered[hook_id] = schema_paths
            continue
        unmatched = [path for path in schema_paths if re.search(exclusion, path) is None]
        if unmatched:
            uncovered[hook_id] = unmatched
    assert not uncovered, (
        "pre-commit text fixers must exclude every upstream schema path so their bytes remain unchanged; "
        f"uncovered paths: {uncovered!r}"
    )

    trailing_whitespace_exclusion = hooks["trailing-whitespace"].get("exclude")
    unmatched_generated_docs = (
        [path for path in generated_doc_paths if re.search(trailing_whitespace_exclusion, path) is None]
        if isinstance(trailing_whitespace_exclusion, str)
        else generated_doc_paths
    )
    assert not unmatched_generated_docs, (
        "the trailing-whitespace hook must exclude generated documentation under docs/features; "
        f"uncovered paths: {unmatched_generated_docs!r}"
    )


@then("Ruff and typecheck lanes should resolve to their real tools")
def ruff_and_typecheck_lanes_resolve_to_real_tools(consumer: Any) -> None:
    lanes = {_lane_id(lane): lane for lane in _lanes(_context(consumer))}
    expected_commands = {
        "ruff": ("ruff",),
        "typecheck": (
            "scripts/check_types.py",
            "mypy",
            "mypy-runtime-gate.feature",
            "installed-consumer-typing.feature",
        ),
    }
    for lane_id, expected_fragments in expected_commands.items():
        lane = lanes.get(lane_id)
        assert lane is not None, f"the inventory must declare the {lane_id!r} lane"
        tox_environments = [part.strip() for part in str(lane.get("tox_env", "")).split(",") if part.strip()]
        assert tox_environments, lane
        configured = " ".join(
            command
            for environment_name in tox_environments
            for command in _tox_configured_commands(consumer, environment_name)
        ).casefold()
        assert all(fragment.casefold() in configured for fragment in expected_fragments), (lane, configured)


@then("optional capability lanes should declare carriers without claiming runtime outcomes")
def optional_capability_carriers_are_declared(consumer: Any) -> None:
    context = _context(consumer)
    optional = [
        lane
        for lane in _lanes(context)
        if _status(lane) == "optional" or "optional" in str(lane.get("capability", "")).casefold()
    ]
    assert optional, "the inventory must declare optional capability lanes"
    proof_lanes = _proof_lanes(context)
    for lane in optional:
        lane_id = _lane_id(lane)
        carrier = _carrier(lane)
        _prerequisite_entries(lane)
        _assert_carrier_path_exists(context, lane)
        proof = proof_lanes.get(lane_id)
        if proof is not None:
            carrier_proof = proof.get("carrier", {})
            assert carrier_proof.get("passed") is None, (lane, carrier_proof)
            assert carrier_proof.get("skipped") is None, (lane, carrier_proof)
            assert carrier_proof.get("kind") in (None, carrier.get("kind")), (lane, carrier_proof)


@then("optional integration cells should provide isolated optional acceptance")
def optional_integration_cells_are_isolated_from_core_runtime_acceptance(consumer: Any) -> None:
    context = _context(consumer)
    cells = [
        cell
        for cell in context.document.get("workflow_cells", [])
        if isinstance(cell, dict) and cell.get("job") == "optional-integrations"
    ]
    expected_environments = {"py313-pytest84-allure-coverage-lin", "py314-debug-mcp", "py314-struct-bdd"} | {
        f"py314-pytestlatest-{gherkin}-xdist-coverage-{platform_suffix}"
        for gherkin in ("gherkin33", "gherkinlatest")
        for platform_suffix in ("lin", "mac", "win")
    }
    actual_environments = [environment for cell in cells for environment in cell.get("tox_envs", [])]
    assert set(actual_environments) == expected_environments, actual_environments
    assert len(actual_environments) == len(set(actual_environments)) == 9, actual_environments
    assert all(len(cell.get("tox_envs", [])) == 1 for cell in cells), cells
    assert all(cell.get("architecture") == "runner-native" for cell in cells), cells

    required_runtime_environments = {
        environment
        for cell in _required_runtime_cells(context)
        for environment in cell.get("required_ci", {}).get("tox_envs", [])
    }
    assert not (expected_environments & required_runtime_environments), required_runtime_environments
    evidence = context.document.get("project", {}).get("evidence", {})
    aggregate_groups = evidence.get("aggregate_groups") if isinstance(evidence, dict) else None
    assert isinstance(aggregate_groups, list) and "optional" in aggregate_groups, aggregate_groups


@then("optional integration cells should declare their extra markers and package requirements")
def optional_integration_lanes_declare_extras_and_package_constraints(consumer: Any) -> None:
    context = _context(consumer)
    cells = [
        cell
        for cell in context.document.get("workflow_cells", [])
        if isinstance(cell, dict) and cell.get("job") == "optional-integrations"
    ]
    lanes_by_environment = {
        environment: lane
        for lane in _lanes(context)
        if _status(lane) != "unsupported"
        for environment in str(lane.get("tox_env", "")).split(",")
        if environment
    }
    assert len(cells) == 9, cells
    for cell in cells:
        environment = cell["tox_envs"][0]
        lane = lanes_by_environment.get(environment)
        assert lane is not None, (cell, lanes_by_environment)
        assert _status(lane) == "required", lane
        assert lane.get("workflow_selector") == cell.get("id"), (lane, cell)
        prerequisites = _prerequisite_entries(lane)
        packages = {
            re.sub(r"[-_.]+", "-", str(item.get("name", "")).casefold()): item
            for item in prerequisites
            if item.get("type") == "python-package"
        }

        if "allure" in environment:
            assert lane.get("extras") == ["allure"], lane
            assert packages.get("allure-python-commons-test", {}).get("version") == "2.16.0", packages
            assert any(item.get("type") == "command" and item.get("name") == "uv" for item in prerequisites), (
                prerequisites
            )
            commands = _resolved_tox_configurations(context).get(environment, {}).get("commands", [])
            assert any("features/compatibility/optional-struct-bdd-extra.feature" in command for command in commands), (
                environment,
                commands,
            )
            continue

        if "struct-bdd" in environment:
            assert lane.get("extras") == ["struct-bdd"], lane
            assert {"hjson", "json5", "pyhocon", "pyyaml"} <= packages.keys(), packages
            assert any(item.get("type") == "command" and item.get("name") == "uv" for item in prerequisites), (
                prerequisites
            )
            commands = _resolved_tox_configurations(context).get(environment, {}).get("commands", [])
            assert any("features/compatibility/optional-struct-bdd-extra.feature" in command for command in commands), (
                environment,
                commands,
            )
            continue

        if "debug-mcp" in environment:
            assert lane.get("extras") == ["debug-mcp"], lane
            expected_packages = {
                "mcp-pdb": ">=0.6,<0.7",
                "mcp": ">=1.24,<2",
                "uvicorn": ">=0.34",
                "pydantic": ">=2.0.3",
            }
            assert all(
                packages.get(name, {}).get("version") == version for name, version in expected_packages.items()
            ), (
                packages,
                expected_packages,
            )
            assert any(item.get("type") == "command" and item.get("name") == "uv" for item in prerequisites), (
                prerequisites
            )
            commands = _resolved_tox_configurations(context).get(environment, {}).get("commands", [])
            assert any(
                "features/debug-mcp-failure-inspection.feature" in command and "-m e2e" in command
                for command in commands
            ), (environment, commands)
            assert any(
                "features/debug-mcp-xdist-worker-discovery.feature" in command and "-m e2e" in command
                for command in commands
            ), (environment, commands)
            continue

        assert lane.get("extras") == [], lane
        assert packages.get("pytest-xdist", {}).get("version") == "<4", packages
        gherkin = packages.get("gherkin-official")
        assert gherkin is not None, packages
        if "gherkin33" in environment:
            assert gherkin.get("requirement") == "gherkin-official>=33,<34", gherkin
        else:
            assert gherkin.get("requirement") == "gherkin-official", gherkin


@then("optional integration evidence should use its own aggregate group")
def optional_integration_evidence_has_separate_aggregate_group(consumer: Any) -> None:
    context = _context(consumer)
    groups = context.document.get("project", {}).get("evidence", {}).get("aggregate_groups")
    assert isinstance(groups, list) and "optional" in groups, groups
    workflow_cells = context.document.get("workflow_cells", [])
    assert any(isinstance(cell, dict) and cell.get("job") == "optional-integrations" for cell in workflow_cells), (
        workflow_cells
    )
    inventory_summary = _report(context).get("inventory", {}).get("optionalIntegrations")
    assert isinstance(inventory_summary, dict), inventory_summary
    assert inventory_summary.get("cellCount") == 9, inventory_summary
    assert inventory_summary.get("environmentCount") == 9, inventory_summary


@then("optional integration evidence should include the StructBDD environment")
def optional_integration_evidence_includes_struct_bdd(consumer: Any) -> None:
    environments = _report(_context(consumer)).get("inventory", {}).get("optionalIntegrations", {}).get("environments")
    assert isinstance(environments, list), environments
    assert "py314-struct-bdd" in environments, environments


@then("optional integration evidence should include the Debug MCP environment")
def optional_integration_evidence_includes_debug_mcp(consumer: Any) -> None:
    environments = _report(_context(consumer)).get("inventory", {}).get("optionalIntegrations", {}).get("environments")
    assert isinstance(environments, list), environments
    assert "py314-debug-mcp" in environments, environments


@then("required runtime tox environments should not install the StructBDD extra")
def required_runtime_tox_environments_omit_struct_bdd_extra(consumer: Any) -> None:
    context = _context(consumer)
    tox_configurations = _resolved_tox_configurations(context)
    required_environments = {
        str(environment)
        for cell in _required_runtime_cells(context)
        for environment in cell.get("required_ci", {}).get("tox_envs", [])
    }
    assert required_environments, "the inventory must declare required core runtime tox environments"

    violations = {
        environment: configuration
        for environment in sorted(required_environments)
        if (configuration := tox_configurations.get(environment)) is None
        or any("struct-bdd" in value.casefold() for field in ("deps", "extras") for value in configuration[field])
    }
    assert not violations, (
        "required core runtime tox environments must keep the optional StructBDD extra out of their install set; "
        f"resolved violations={violations!r}"
    )


@then("the optional StructBDD integration cell should install and run its acceptance feature")
def optional_struct_bdd_cell_installs_and_runs_acceptance_feature(consumer: Any) -> None:
    context = _context(consumer)
    cell_id = "struct-bdd-py314-linux"
    environment_name = "py314-struct-bdd"
    feature_path = "features/struct-bdd-discovery/struct-bdd-autoload-discovery.feature"
    isolated_extra_feature_path = "features/compatibility/optional-struct-bdd-extra.feature"
    cells = [
        cell
        for cell in context.document.get("workflow_cells", [])
        if isinstance(cell, dict) and cell.get("id") == cell_id
    ]
    assert len(cells) == 1, f"the workflow inventory must declare exactly one {cell_id!r} cell: {cells!r}"
    cell = cells[0]
    assert cell.get("job") == "optional-integrations", cell
    assert cell.get("platform") == "linux" and cell.get("python") == "3.14", cell
    assert cell.get("tox_envs") == [environment_name], cell

    lanes = [lane for lane in _lanes(context) if _lane_id(lane) == cell_id]
    assert len(lanes) == 1, f"the environment inventory must declare exactly one {cell_id!r} lane: {lanes!r}"
    lane = lanes[0]
    assert _status(lane) == "required", lane
    assert lane.get("tox_env") == environment_name, lane
    assert lane.get("workflow_selector") == cell_id, lane
    assert lane.get("extras") == ["struct-bdd"], lane

    prerequisites = _prerequisite_entries(lane)
    package_names = {
        re.sub(r"[-_.]+", "-", str(item.get("name", "")).casefold())
        for item in prerequisites
        if item.get("type") == "python-package"
    }
    assert {"hjson", "json5", "pyhocon", "pyyaml"} <= package_names, prerequisites
    assert any(item.get("type") == "command" and item.get("name") == "uv" for item in prerequisites), prerequisites

    carrier = _carrier(lane)
    assert carrier.get("kind") == "pytest" and carrier.get("path") == feature_path, carrier
    assert "-m e2e" in str(carrier.get("command", "")), carrier

    configurations = _resolved_tox_configurations(context)
    configuration = configurations.get(environment_name)
    assert configuration is not None, f"tox does not resolve the optional StructBDD environment {environment_name!r}"
    resolved_install_inputs = [*configuration["deps"], *configuration["extras"]]
    assert any("struct-bdd" in value.casefold() for value in resolved_install_inputs), configuration
    assert any(value.casefold().startswith("uv>=0.8") for value in configuration["deps"]), configuration
    resolved_commands = "\n".join(configuration["commands"])
    assert feature_path in resolved_commands and "-m e2e" in resolved_commands, configuration
    assert isolated_extra_feature_path in resolved_commands, configuration


@then("the optional Debug MCP integration cell should install and run its acceptance feature")
def optional_debug_mcp_cell_installs_and_runs_acceptance_feature(consumer: Any) -> None:
    context = _context(consumer)
    cell_id = "debug-mcp-py314-linux"
    environment_name = "py314-debug-mcp"
    feature_path = "features/debug-mcp-failure-inspection.feature"
    worker_feature_path = "features/debug-mcp-xdist-worker-discovery.feature"
    cells = [
        cell
        for cell in context.document.get("workflow_cells", [])
        if isinstance(cell, dict) and cell.get("id") == cell_id
    ]
    assert len(cells) == 1, f"the workflow inventory must declare exactly one {cell_id!r} cell: {cells!r}"
    cell = cells[0]
    assert cell.get("job") == "optional-integrations", cell
    assert cell.get("platform") == "linux" and cell.get("python") == "3.14", cell
    assert cell.get("tox_envs") == [environment_name], cell

    lanes = [lane for lane in _lanes(context) if _lane_id(lane) == cell_id]
    assert len(lanes) == 1, f"the environment inventory must declare exactly one {cell_id!r} lane: {lanes!r}"
    lane = lanes[0]
    assert _status(lane) == "required", lane
    assert lane.get("tox_env") == environment_name, lane
    assert lane.get("workflow_selector") == cell_id, lane
    assert lane.get("extras") == ["debug-mcp"], lane

    prerequisites = _prerequisite_entries(lane)
    package_requirements = {
        re.sub(r"[-_.]+", "-", str(item.get("name", "")).casefold()): item.get("version")
        for item in prerequisites
        if item.get("type") == "python-package"
    }
    assert package_requirements == {
        "mcp-pdb": ">=0.6,<0.7",
        "mcp": ">=1.24,<2",
        "uvicorn": ">=0.34",
        "pydantic": ">=2.0.3",
    }, prerequisites
    assert any(item.get("type") == "command" and item.get("name") == "uv" for item in prerequisites), prerequisites

    carrier = _carrier(lane)
    assert carrier.get("kind") == "pytest" and carrier.get("path") == feature_path, carrier
    carrier_command = str(carrier.get("command", ""))
    assert "-m e2e" in carrier_command and worker_feature_path in carrier_command, carrier

    configurations = _resolved_tox_configurations(context)
    configuration = configurations.get(environment_name)
    assert configuration is not None, f"tox does not resolve the optional Debug MCP environment {environment_name!r}"
    resolved_install_inputs = [*configuration["deps"], *configuration["extras"]]
    assert any("debug-mcp" in value.casefold() for value in resolved_install_inputs), configuration
    assert any(value.casefold().startswith("uv>=0.8") for value in configuration["deps"]), configuration
    resolved_commands = "\n".join(configuration["commands"])
    assert (
        feature_path in resolved_commands and worker_feature_path in resolved_commands and "-m e2e" in resolved_commands
    ), configuration


@when("I probe a declared optional capability lane")
def probe_declared_optional_capability_lane(consumer: Any) -> None:
    context = _context(consumer)
    lane = next(
        (candidate for candidate in _lanes(context) if _lane_id(candidate) == "optional-dependency-probe"), None
    )
    assert lane is not None, "the inventory must declare an optional capability lane"
    context.probed_optional_lane = _lane_id(lane)
    _run_environment_check(context, lane_id=context.probed_optional_lane)


@then("its collect-only carrier probe should select tests without claiming runtime outcomes")
def optional_carrier_probe_selects_tests_without_test_outcomes(consumer: Any) -> None:
    context = _context(consumer)
    report = _report(context)
    result = context.check_result
    assert result is not None and result.returncode == 0, (result, report)
    assert report.get("status") == "pass", report
    proof = _proof_lanes(context).get(context.probed_optional_lane)
    assert proof is not None, report
    carrier = proof.get("carrier", {})
    assert carrier.get("selected") is True, (context.probed_optional_lane, carrier)
    assert carrier.get("selectedCount", 0) > 0, (context.probed_optional_lane, carrier)
    assert carrier.get("command"), (context.probed_optional_lane, carrier)
    assert carrier.get("passed") is None, carrier
    assert carrier.get("skipped") is None, carrier


@when("I parse a partially deselected pytest collection summary")
def parse_partially_deselected_collection_summary(request: pytest.FixtureRequest) -> None:
    request.node._environment_inventory_selected_count = _collected_count("2/1341 tests collected (1339 deselected)")


@then("the selected count should be 2")
def partially_deselected_collection_has_two_selected_tests(request: pytest.FixtureRequest) -> None:
    assert request.node._environment_inventory_selected_count == 2


@when("I parse a fully deselected pytest collection summary")
def parse_fully_deselected_collection_summary(request: pytest.FixtureRequest) -> None:
    request.node._environment_inventory_selected_count = _collected_count("0/1341 tests collected (1341 deselected)")


@then("the selected count should be 0")
def fully_deselected_collection_has_no_selected_tests(request: pytest.FixtureRequest) -> None:
    assert request.node._environment_inventory_selected_count == 0


@when("I probe a temporary optional lane with a missing package prerequisite")
def probe_temporary_optional_lane_with_missing_package(consumer: Any) -> None:
    context = _context(consumer)
    lane = next(
        (candidate for candidate in _lanes(context) if _lane_id(candidate) == "optional-dependency-probe"), None
    )
    assert lane is not None, "cannot test missing prerequisites without the optional dependency probe lane"
    package = "pytest-cuke-acceptance-missing-extra-000000"
    prerequisites = _prerequisite_entries(lane)
    prerequisites.append(
        {
            "type": "python-package",
            "name": package,
            "remedy": f"python -m pip install {package}",
        }
    )
    _write_inventory(context)
    context.missing_prerequisite_lane = _lane_id(lane)
    context.missing_prerequisite_package = package
    _run_environment_check(context, lane_id=context.missing_prerequisite_lane)


@when("I probe an optional lane with installed packages outside declared version and PEP 508 requirements")
def probe_optional_lane_with_incompatible_package_requirements(consumer: Any) -> None:
    context = _context(consumer)
    lane = next(
        (candidate for candidate in _lanes(context) if _lane_id(candidate) == "optional-dependency-probe"), None
    )
    assert lane is not None, "cannot test package constraints without the optional dependency probe lane"

    expectations: list[dict[str, str]] = []
    for package, field in (("pytest", "version"), ("packaging", "requirement")):
        detected_version = _installed_consumer_version(consumer, package)
        requested_constraint = f">{detected_version}"
        display_constraint = requested_constraint if field == "version" else f"{package}{requested_constraint}"
        remedy = f"python -m pip install '{package}{requested_constraint}'"
        prerequisite: dict[str, str] = {
            "type": "python-package",
            "name": package,
            field: display_constraint,
            "remedy": remedy,
        }
        _prerequisite_entries(lane).append(prerequisite)
        expectations.append(
            {
                "package": package,
                "requested": display_constraint,
                "detected": detected_version,
                "remedy": remedy,
            }
        )

    context.package_constraint_lane = _lane_id(lane)
    context.package_constraint_expectations = expectations
    _write_inventory(context)
    _run_environment_check(context, lane_id=context.package_constraint_lane)


@when("I probe an optional lane with an absent package behind an inactive PEP 508 marker")
def probe_optional_lane_with_inactive_package_marker(consumer: Any) -> None:
    context = _context(consumer)
    lane = next(
        (candidate for candidate in _lanes(context) if _lane_id(candidate) == "optional-dependency-probe"), None
    )
    assert lane is not None, "cannot test PEP 508 markers without the optional dependency probe lane"
    package = "pytest-cuke-acceptance-inactive-marker-000000"
    _prerequisite_entries(lane).append(
        {
            "type": "python-package",
            "name": package,
            "requirement": f"{package}; python_version < '0'",
            "remedy": f"python -m pip install {package}",
        }
    )
    context.inactive_marker_lane = _lane_id(lane)
    context.inactive_marker_package = package
    _write_inventory(context)
    _run_environment_check(context, lane_id=context.inactive_marker_lane)


@then("the inventory check should fail with the lane package and install remedy")
def missing_optional_package_fails_with_remedy(consumer: Any) -> None:
    context = _context(consumer)
    result = context.check_result
    report = _report(context)
    assert result is not None and result.returncode != 0, (result, report)
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    lane_id = context.missing_prerequisite_lane
    package = context.missing_prerequisite_package
    matching = [item for item in diagnostics if isinstance(item, dict) and item.get("laneId") == lane_id]
    assert any(
        package.casefold() in str(item.get("message", "")).casefold()
        and f"python -m pip install {package}".casefold() in str(item.get("remedy", "")).casefold()
        for item in matching
    ), diagnostics


@then("the inventory check should report each requested package constraint installed version and install remedy")
def incompatible_optional_package_constraints_fail_with_remedies(consumer: Any) -> None:
    context = _context(consumer)
    result = context.check_result
    report = _report(context)
    assert result is not None and result.returncode != 0, (result, report)
    assert report.get("status") == "fail", report
    expectations = context.package_constraint_expectations
    assert expectations, "the package constraint probe should retain its requested and installed versions"
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    lane_id = context.package_constraint_lane
    matching = [item for item in diagnostics if isinstance(item, dict) and item.get("laneId") == lane_id]
    for expected in expectations:
        package_diagnostics = [
            item for item in matching if expected["package"].casefold() in str(item.get("message", "")).casefold()
        ]
        assert any(
            expected["requested"].casefold() in str(item.get("message", "")).casefold()
            and expected["detected"] in str(item.get("message", ""))
            and expected["remedy"].casefold() in str(item.get("remedy", "")).casefold()
            for item in package_diagnostics
        ), {"expected": expected, "diagnostics": package_diagnostics}


@then("the inventory check should pass without a missing-package diagnostic for that package")
def inactive_marker_skips_missing_package_check(consumer: Any) -> None:
    context = _context(consumer)
    result = context.check_result
    report = _report(context)
    assert result is not None and result.returncode == 0, (result, report)
    assert report.get("status") == "pass", report
    lane_id = context.inactive_marker_lane
    package = context.inactive_marker_package
    diagnostics = report.get("diagnostics", [])
    assert isinstance(diagnostics, list), report
    missing_package_diagnostics = [
        item
        for item in diagnostics
        if isinstance(item, dict)
        and item.get("laneId") == lane_id
        and item.get("code") == "package-prerequisite-missing"
        and package.casefold() in str(item.get("message", "")).casefold()
    ]
    assert not missing_package_diagnostics, missing_package_diagnostics


@then("the missing prerequisite should not be reported as a skip")
def missing_prerequisite_is_not_a_skip(consumer: Any) -> None:
    diagnostics = _report(_context(consumer)).get("diagnostics", [])
    assert "skip" not in json.dumps(diagnostics, ensure_ascii=False).casefold(), diagnostics


@then("the inventory should include a Playwright browser lane with an HTML report carrier")
def inventory_includes_playwright_html_carrier(consumer: Any) -> None:
    lanes = _lanes(_context(consumer))
    matches = [lane for lane in lanes if "playwright" in _lane_text(lane) or "browser" in _lane_text(lane)]
    assert matches, "the inventory must declare a Playwright/browser capability lane"
    lane = matches[0]
    carrier = _carrier(lane)
    assert _prerequisite_entries(lane), lane
    _assert_carrier_path_exists(_context(consumer), lane)
    carrier_text = json.dumps(carrier, ensure_ascii=False).casefold()
    assert "html" in carrier_text or "html" in _lane_text(lane), (lane, carrier)
    assert "playwright" in _lane_text(lane), lane


@then("the required doc-generation lane should select its pytest carrier")
def required_doc_generation_lane_selects_pytest_carrier(consumer: Any) -> None:
    context = _context(consumer)
    lane = _doc_generation_lane(context)
    carrier = _carrier(lane)
    expected_path = "tests/unit/docs/test_doc.py"
    assert carrier.get("kind") == "pytest", carrier
    assert carrier.get("path") == expected_path, carrier
    assert expected_path in str(carrier.get("command", "")), carrier
    _assert_carrier_path_exists(context, lane)

    lane_proof = _proof_lanes(context).get(_lane_id(lane))
    assert lane_proof is not None, f"the doc-generation lane has no inventory proof: {lane}"
    carrier_proof = lane_proof.get("carrier")
    assert isinstance(carrier_proof, dict), lane_proof
    assert carrier_proof.get("selected") is True, carrier_proof
    assert carrier_proof.get("selectedCount", 0) > 0, carrier_proof


@when("I probe the required doc-generation lane")
def probe_required_doc_generation_lane(consumer: Any) -> None:
    context = _context(consumer)
    lane = _doc_generation_lane(context)
    result = _run_environment_check(
        context,
        lane_id=_lane_id(lane),
        include_doc_generation_tools=True,
    )
    assert result.returncode == 0, f"doc-generation lane probe failed:\n{result.stdout}\n{result.stderr}"


@then("it should declare the doc-gen extra and Pandoc prerequisite")
def doc_generation_lane_declares_extra_and_pandoc(consumer: Any) -> None:
    lane = _doc_generation_lane(_context(consumer))
    extras = lane.get("extras")
    assert isinstance(extras, list) and any(str(extra).casefold() == "doc-gen" for extra in extras), lane

    prerequisites = _prerequisite_entries(lane)
    package_names = {
        re.sub(r"[-_.]+", "-", str(item.get("name", "")).casefold())
        for item in prerequisites
        if item.get("type") == "python-package"
    }
    expected_packages = {"pandoc", "panflute", "pycmarkgfm", "pypandoc"}
    assert expected_packages <= package_names, (expected_packages, package_names)
    pandoc = [
        item
        for item in prerequisites
        if item.get("type") == "command" and str(item.get("name", "")).casefold() == "pandoc"
    ]
    assert pandoc, f"the doc-generation lane must declare Pandoc as a command prerequisite: {prerequisites}"


@then("its tox environment and workflow selector should be active")
def doc_generation_lane_has_active_tox_and_workflow_selectors(consumer: Any) -> None:
    context = _context(consumer)
    lane = _doc_generation_lane(context)
    report = _report(context)
    result = context.check_result
    assert result is not None and result.returncode == 0, (result, report)
    assert report.get("status") == "pass", report

    proof_lanes = _proof_lanes(context)
    lane_proof = proof_lanes.get(_lane_id(lane))
    assert lane_proof is not None, f"the doc-generation lane has no inventory proof: {lane}"
    tox_proof = lane_proof.get("tox", {})
    assert tox_proof.get("environment") == lane.get("tox_env"), (lane, tox_proof)
    assert tox_proof.get("resolved") is True, (lane, tox_proof)
    assert tox_proof.get("command"), (lane, tox_proof)
    ci_proof = lane_proof.get("ci", {})
    assert ci_proof.get("workflow") and ci_proof.get("selector"), (lane, ci_proof)
    assert ci_proof.get("selected") is True, (lane, ci_proof)


@then("the inventory should include socket via and SSH lanes with real report carriers")
def inventory_includes_remote_execution_carriers(consumer: Any) -> None:
    lanes = _lanes(_context(consumer))
    for capability in ("socket", "via", "ssh"):
        matches = [lane for lane in lanes if capability in _lane_text(lane)]
        assert matches, f"the inventory must declare a {capability} capability lane"
        for lane in matches:
            carrier = _carrier(lane)
            assert _prerequisite_entries(lane), lane
            _assert_carrier_path_exists(_context(consumer), lane)
            carrier_text = json.dumps(carrier, ensure_ascii=False).casefold()
            assert not any(marker in carrier_text for marker in ("mock", "fake", "placeholder")), (lane, carrier)


@then("native and formatter lanes should name their test carriers and prerequisites")
def native_and_formatter_lanes_name_carriers(consumer: Any) -> None:
    lanes = _lanes(_context(consumer))
    for capability in ("native", "formatter"):
        matches = [lane for lane in lanes if capability in _lane_text(lane)]
        assert matches, f"the inventory must declare a {capability} capability lane"
        for lane in matches:
            _carrier(lane)
            assert _prerequisite_entries(lane), lane
            _assert_carrier_path_exists(_context(consumer), lane)


@then("the native parser tox environment should install uv")
def native_parser_tox_environment_installs_uv(consumer: Any) -> None:
    result = subprocess.run(
        ["tox", "config", "-e", "native-go-parser", "-k", "deps", "--format=json"],
        cwd=consumer.path,
        env=_inventory_command_environment(consumer),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"tox config failed for native-go-parser: {result.stdout}\n{result.stderr}"
    payload = json.loads(result.stdout)
    environment_config = payload.get("env", {}).get("native-go-parser", {})
    dependencies = environment_config.get("deps")
    assert isinstance(dependencies, list), environment_config
    dependency_names = {
        re.split(r"[<>=!~;\s\[]", str(dependency).strip(), maxsplit=1)[0].casefold() for dependency in dependencies
    }
    assert "uv" in dependency_names, (
        "the native-go-parser tox environment must install uv because its acceptance tests build and install "
        f"isolated consumers; resolved dependencies were {dependencies!r}"
    )


@then("local uv evidence should match the tox acceptance environments that install uv")
def local_uv_evidence_matches_tox_acceptance_environments(
    request: pytest.FixtureRequest,
    consumer: Any,
) -> None:
    repository_root = Path(request.config.rootpath)
    evidence_rules = runpy.run_path(str(repository_root / "scripts" / "environment_evidence.py"))
    required_system_tool_versions = evidence_rules["required_system_tool_versions"]
    tox_environments = _list_tox_environment_names(
        consumer.path,
        environment=_inventory_command_environment(consumer),
    )[1]
    expected_uv_environments = {environment for environment in tox_environments if "-coverage-" in environment}
    expected_uv_environments.update(
        {
            "py314-pytestlatest-playwright-report",
            "py314-debug-mcp",
            "py314-struct-bdd",
            "py313-live-formatters-acceptance-lin",
            "py313-live-formatters-acceptance-mac",
            "py313-live-formatters-acceptance-win",
            "native-go-parser",
            "py314-pytestlatest-mypy",
        }
    )
    actual_uv_environments = {
        environment for environment in tox_environments if "uv" in required_system_tool_versions(environment)
    }
    assert actual_uv_environments == expected_uv_environments, (
        "local uv evidence should be required for every runtime coverage lane and each other tox environment "
        "that installs uv; pytest90-mypy, mypy-messages, doc-gen, pre-commit, and remote xdist environments "
        "must not require it; "
        f"missing={sorted(expected_uv_environments - actual_uv_environments)}, "
        f"unexpected={sorted(actual_uv_environments - expected_uv_environments)}"
    )

    expected_system_tools = {environment: {"tox"} for environment in tox_environments}
    for environment in expected_uv_environments:
        expected_system_tools[environment].add("uv")
    expected_system_tools["py313-pytest84-allure-coverage-lin"].update({"node", "npm", "npx", "allure-cli"})
    expected_system_tools["py314-pytestlatest-playwright-report"].update({"node", "npm", "npx", "allure-cli"})
    expected_system_tools["py314-doc-gen"].add("pandoc")
    expected_system_tools["native-go-parser"].update({"go", "native-compiler"})
    for environment in (
        "py313-live-formatters-acceptance-lin",
        "py313-live-formatters-acceptance-mac",
        "py313-live-formatters-acceptance-win",
    ):
        expected_system_tools[environment].update({"node", "npm", "npx", "allure-cli"})
    actual_system_tools = {
        environment: set(required_system_tool_versions(environment))
        for environment in tox_environments
        if required_system_tool_versions(environment)
    }
    assert actual_system_tools == expected_system_tools, (
        "the evidence collector should record only the system tools used by each acceptance lane, including "
        "tox-local uv for runtime coverage and Node/npm/npx/Allure CLI where used; "
        f"missing={expected_system_tools.keys() - actual_system_tools.keys()}, "
        f"unexpected={actual_system_tools.keys() - expected_system_tools.keys()}, "
        f"mismatched={{{', '.join(f'{name}: expected {sorted(expected_system_tools[name])}, got {sorted(actual_system_tools[name])}' for name in expected_system_tools.keys() & actual_system_tools.keys() if expected_system_tools[name] != actual_system_tools[name])}}}"
    )

    config_result = subprocess.run(
        ["tox", "config", "-e", "ALL", "-k", "deps"],
        cwd=consumer.path,
        env=_inventory_command_environment(consumer),
        check=False,
        capture_output=True,
        text=True,
    )
    assert config_result.returncode == 0, (
        f"tox config failed while checking local uv dependencies: {config_result.stdout}\n{config_result.stderr}"
    )
    dependencies_by_environment: dict[str, set[str]] = {}
    active_environment: str | None = None
    collecting_dependencies = False
    for line in config_result.stdout.splitlines():
        section = re.fullmatch(r"\[testenv:([^]]+)\]", line)
        if section:
            active_environment = section.group(1)
            dependencies_by_environment[active_environment] = set()
            collecting_dependencies = False
            continue
        if active_environment is None:
            continue
        if line.startswith("deps ="):
            collecting_dependencies = True
            inline_dependency = line.partition("=")[2].strip()
            if inline_dependency:
                dependencies_by_environment[active_environment].add(
                    re.split(r"[<>=!~;\s\[]", inline_dependency, maxsplit=1)[0].casefold()
                )
            continue
        if collecting_dependencies and line.startswith("  "):
            dependency = line.strip()
            if dependency:
                dependencies_by_environment[active_environment].add(
                    re.split(r"[<>=!~;\s\[]", dependency, maxsplit=1)[0].casefold()
                )
            continue
        collecting_dependencies = False

    missing_dependencies = sorted(
        environment
        for environment in tox_environments
        if ("uv" in required_system_tool_versions(environment))
        != ("uv" in dependencies_by_environment.get(environment, set()))
    )
    assert not missing_dependencies, (
        "the environment evidence collector must require tox-local uv exactly where resolved tox dependencies "
        f"install uv; mismatched environments={missing_dependencies}, "
        f"resolved dependencies={{{', '.join(f'{name}: {sorted(dependencies_by_environment.get(name, set()))}' for name in missing_dependencies)}}}"
    )


@then("the messages schema tox command should use the fixture for the installed Cucumber Messages release")
def messages_schema_tox_command_uses_installed_schema_fixture(request: pytest.FixtureRequest) -> None:
    repository_root = Path(request.config.rootpath)
    release = distribution_version("cucumber-messages")
    source_directory = f"tests/fixtures/message-schemas-v{release.replace('.', '-')}"
    result = subprocess.run(
        ["tox", "config", "-e", "messages-schema"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"tox config failed for messages-schema: {result.stdout}\n{result.stderr}"

    commands: list[str] = []
    in_commands = False
    for line in result.stdout.splitlines():
        if line.startswith("commands ="):
            in_commands = True
            command = line.partition("=")[2].strip()
            if command:
                commands.append(command)
            continue
        if in_commands:
            if line.startswith("  "):
                commands.append(line.strip())
            else:
                break

    schema_commands = [
        shlex.split(command)
        for command in commands
        if shlex.split(command)[:4] == ["cuke", "sync", "messages", "schemas"]
    ]
    assert schema_commands, f"messages-schema must run cuke sync messages schemas: {result.stdout}"

    configured_source_directories: list[str] = []
    for arguments in schema_commands:
        for index, argument in enumerate(arguments):
            if argument == "--source-dir" and index + 1 < len(arguments):
                configured_source_directories.append(arguments[index + 1])
            elif argument.startswith("--source-dir="):
                configured_source_directories.append(argument.partition("=")[2])
    assert configured_source_directories == [source_directory], (
        f"messages-schema must use --source-dir {source_directory!r} for cucumber-messages {release}; "
        f"configured={configured_source_directories!r}"
    )

    envelope_schema = repository_root / source_directory / "jsonschema" / "Envelope.json"
    assert envelope_schema.is_file(), (
        f"messages-schema fixture for cucumber-messages {release} is missing {envelope_schema}"
    )


@then("the messages schema inventory carrier should use the fixture for the installed Cucumber Messages release")
def messages_schema_inventory_uses_installed_schema_fixture(request: pytest.FixtureRequest) -> None:
    repository_root = Path(request.config.rootpath)
    release = distribution_version("cucumber-messages")
    source_directory = f"tests/fixtures/message-schemas-v{release.replace('.', '-')}"
    inventory_path = repository_root / "config" / "env-matrix.yaml"
    inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    assert isinstance(inventory, dict), inventory
    lanes = inventory.get("lanes")
    assert isinstance(lanes, list), inventory
    matching_lanes = [lane for lane in lanes if isinstance(lane, dict) and lane.get("id") == "messages-schema"]
    assert len(matching_lanes) == 1, f"expected one messages-schema lane in {inventory_path}, got {matching_lanes!r}"
    carrier = matching_lanes[0].get("expected_carrier")
    assert isinstance(carrier, dict), matching_lanes[0]
    command = carrier.get("command")
    assert isinstance(command, str), carrier
    arguments = shlex.split(command)
    configured_source_directories = [
        argument.partition("=")[2] for argument in arguments if argument.startswith("--source-dir=")
    ]
    configured_source_directories.extend(
        arguments[index + 1] for index, argument in enumerate(arguments[:-1]) if argument == "--source-dir"
    )
    assert configured_source_directories == [source_directory], (
        f"messages-schema inventory must use --source-dir {source_directory!r} for cucumber-messages {release}; "
        f"configured={configured_source_directories!r}"
    )


@given(
    "the contributor entry point and compatibility audit guide are loaded",
    target_fixture="compatibility_audit_documents",
)
def compatibility_audit_documents_are_loaded(request: Any) -> CompatibilityAuditDocuments:
    repository_root = Path(request.config.rootpath)
    contributor_entry_path = repository_root / "README.rst"
    audit_guide_path = repository_root / "docs" / "compatibility-and-migration-audit.md"
    assert contributor_entry_path.is_file(), f"contributor entry point is missing: {contributor_entry_path}"
    assert audit_guide_path.is_file(), f"compatibility and migration audit guide is missing: {audit_guide_path}"
    return CompatibilityAuditDocuments(
        contributor_entry=contributor_entry_path.read_text(encoding="utf-8"),
        audit_guide=audit_guide_path.read_text(encoding="utf-8"),
    )


@then("the guide should expose the full-proof command artifact and prerequisites")
def compatibility_audit_guide_documents_full_proof(compatibility_audit_documents: CompatibilityAuditDocuments) -> None:
    guide = compatibility_audit_documents.audit_guide
    normalized_guide = guide.casefold()
    assert "`tox run` executes the complete declared tox environment list." in guide, (
        "the guide should identify tox run as the command for all declared environments"
    )
    assert "workflow dispatch" in normalized_guide, "the guide should explain how to trigger full acceptance proof"
    assert "full-supported-proof-<sha>" in guide, "the guide should name the aggregate proof artifact"

    prerequisites = (
        ".[test,struct-bdd,env-matrix]",
        "uv>=0.8",
        "node.js 22",
        "docker engine and compose",
        "ssh-keygen",
        "chromium",
        "go and a c compiler",
        "pandoc",
    )
    missing_prerequisites = [item for item in prerequisites if item.casefold() not in normalized_guide]
    assert not missing_prerequisites, f"the guide omits full-proof prerequisites: {missing_prerequisites!r}"


@then("the guide should distinguish the broad pytest support promise from measured CI coverage")
def compatibility_audit_guide_distinguishes_support_from_measured_coverage(
    compatibility_audit_documents: CompatibilityAuditDocuments,
) -> None:
    paragraphs = [
        " ".join(paragraph.casefold().split()) for paragraph in compatibility_audit_documents.audit_guide.split("\n\n")
    ]
    support_promise = [
        paragraph
        for paragraph in paragraphs
        if re.search(r"pytest\s*>=\s*7\.0", paragraph)
        and "floor" in paragraph
        and "upstream" in paragraph
        and "pair" in paragraph
    ]
    assert support_promise, "the guide should state that pytest >=7.0 is a support floor for upstream-compatible pairs"

    measured_matrix = [
        paragraph
        for paragraph in paragraphs
        if "measured ci coverage" in paragraph
        and "latest pytest 9.x" in paragraph
        and re.search(r"cpython\s+3\.11\s*[–-]\s*3\.15", paragraph)
        and all(os_name in paragraph for os_name in ("linux", "macos", "windows"))
    ]
    assert measured_matrix, (
        "the guide should identify latest pytest 9.x across CPython 3.11–3.15 Linux, macOS, "
        "and Windows as measured CI coverage"
    )

    anchor_claims = {
        "CPython 3.11/Linux pytest 7.4.x": any(
            "7.4.x" in paragraph and re.search(r"3\.11\s*/\s*linux", paragraph) for paragraph in paragraphs
        ),
        "CPython 3.12/Linux pytest 8.4.x": any(
            "8.4.x" in paragraph and re.search(r"3\.12\s*/\s*linux", paragraph) for paragraph in paragraphs
        ),
    }
    missing_anchors = [claim for claim, present in anchor_claims.items() if not present]
    assert not missing_anchors, f"the guide omits measured pytest anchor cells: {missing_anchors!r}"


@then("the contributor entry point should link to the compatibility audit guide")
def contributor_entry_links_to_compatibility_audit(compatibility_audit_documents: CompatibilityAuditDocuments) -> None:
    contribution_section = compatibility_audit_documents.contributor_entry.partition("How to Contribute")[2]
    link_pattern = r"`[^`<>]*<docs/compatibility-and-migration-audit\.md>`_"
    assert re.search(link_pattern, contribution_section), (
        "README.rst's How to Contribute section should link to docs/compatibility-and-migration-audit.md"
    )


@then("live formatter acceptance should have resolved required lanes for Linux macOS and Windows")
def live_formatter_acceptance_has_required_platform_lanes(consumer: Any) -> None:
    context = _context(consumer)
    lanes = [lane for lane in _lanes(context) if lane.get("capability") == "live-formatters-acceptance"]
    assert len(lanes) == 3, f"expected one live formatter acceptance lane per platform, found {lanes!r}"
    assert {_status(lane) for lane in lanes} == {"required"}, lanes
    assert {str(lane.get("platform", "")).casefold() for lane in lanes} == {"linux", "macos", "windows"}, lanes
    assert all(_lane_id(lane) in _proof_lanes(context) for lane in lanes), lanes


@then("each live formatter acceptance lane should resolve to its selected CI cell and test carrier")
def live_formatter_acceptance_lanes_resolve_to_ci_and_carriers(consumer: Any) -> None:
    context = _context(consumer)
    report = _report(context)
    cells = report.get("inventory", {}).get("workflowCells")
    assert isinstance(cells, list), cells
    cells_by_id = {cell.get("id"): cell for cell in cells if isinstance(cell, dict)}
    proof_lanes = _proof_lanes(context)

    for lane in _lanes(context):
        if lane.get("capability") != "live-formatters-acceptance":
            continue
        lane_id = _lane_id(lane)
        selector = lane.get("workflow_selector")
        cell = cells_by_id.get(selector)
        assert isinstance(cell, dict), (lane_id, selector, cells)
        assert cell.get("job") == "live-formatters-acceptance", (lane, cell)
        assert lane.get("tox_env") in cell.get("tox_envs", []), (lane, cell)

        proof = proof_lanes.get(lane_id)
        assert proof is not None, lane
        assert proof.get("tox", {}).get("resolved") is True, proof
        assert proof.get("ci", {}).get("selected") is True, proof
        carrier = _carrier(lane)
        assert carrier.get("kind") == "pytest", carrier
        assert "--collect-only" in str(carrier.get("command", "")), carrier
        _assert_carrier_path_exists(context, lane)


@then("every live formatter acceptance carrier should select exactly the feature files selected by tox")
def live_formatter_acceptance_carriers_match_tox_features(consumer: Any) -> None:
    windows_feature = r"C:\workspace with spaces\extra.feature"
    synthetic_command = f'python -m pytest "{windows_feature}"'
    assert _feature_arguments(synthetic_command) == {"C:/workspace with spaces/extra.feature"}, synthetic_command

    context = _context(consumer)
    tox_config = configparser.ConfigParser(interpolation=None)
    tox_path = context.repository_root / "tox.ini"
    assert tox_config.read(tox_path, encoding="utf-8"), f"could not read tox configuration: {tox_path}"
    tox_section = "testenv:py313-live-formatters-acceptance-{lin,mac,win}"
    assert tox_config.has_option(tox_section, "commands"), f"tox section {tox_section!r} has no command"
    tox_feature_paths = _feature_arguments(tox_config.get(tox_section, "commands"))
    assert tox_feature_paths, f"tox section {tox_section!r} selects no feature files"

    lanes = [lane for lane in _lanes(context) if lane.get("capability") == "live-formatters-acceptance"]
    expected_lane_ids = {
        "live-formatters-acceptance-linux",
        "live-formatters-acceptance-macos",
        "live-formatters-acceptance-windows",
    }
    assert {_lane_id(lane) for lane in lanes} == expected_lane_ids, lanes
    assert len(lanes) == len(expected_lane_ids), lanes
    lanes_by_platform = {str(lane.get("platform", "")).casefold(): lane for lane in lanes}
    assert set(lanes_by_platform) == {"linux", "macos", "windows"}, lanes

    for platform_name, lane in lanes_by_platform.items():
        carrier = _carrier(lane)
        carrier_command = carrier.get("command")
        assert isinstance(carrier_command, str) and carrier_command, (platform_name, carrier)
        carrier_feature_paths = _feature_arguments(carrier_command)
        missing = tox_feature_paths - carrier_feature_paths
        extra = carrier_feature_paths - tox_feature_paths
        assert not missing and not extra, (
            f"live formatter acceptance carrier for {platform_name} does not match tox feature selection: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )


@then("live formatter acceptance should emit per-scenario progress to workflow logs")
def live_formatter_acceptance_emits_per_scenario_progress(consumer: Any) -> None:
    context = _context(consumer)
    tox_config = configparser.ConfigParser(interpolation=None)
    tox_path = context.repository_root / "tox.ini"
    assert tox_config.read(tox_path, encoding="utf-8"), f"could not read tox configuration: {tox_path}"
    tox_section = "testenv:py313-live-formatters-acceptance-{lin,mac,win}"
    command = tox_config.get(tox_section, "commands")
    command_tokens = shlex.split(command)
    assert "-vv" in command_tokens, command
    assert "--durations=20" in command_tokens, command


@then("the aggregate proof job should require and download live formatter acceptance evidence")
def aggregate_proof_requires_live_formatter_acceptance_evidence(consumer: Any) -> None:
    context = _context(consumer)
    workflow_path = context.repository_root / str(context.document["project"]["workflow"])
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), workflow_path
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), workflow_path

    formatter_job = jobs.get("live-formatters-acceptance")
    assert isinstance(formatter_job, dict), "workflow must define the live formatter acceptance job"
    formatter_steps = formatter_job.get("steps")
    assert isinstance(formatter_steps, list), formatter_job
    upload_steps = [
        step for step in formatter_steps if isinstance(step, dict) and step.get("uses") == "actions/upload-artifact@v4"
    ]
    assert any(
        isinstance(step.get("with"), dict)
        and str(step["with"].get("name", "")).startswith("env-evidence-live-formatters-")
        and "artifacts/evidence-live-formatters-" in str(step["with"].get("path", ""))
        for step in upload_steps
    ), "live formatter acceptance must upload its environment evidence artifact"

    aggregate_job = jobs.get("aggregate-proof")
    assert isinstance(aggregate_job, dict), "workflow must define the aggregate proof job"
    needs = aggregate_job.get("needs")
    assert isinstance(needs, list) and "live-formatters-acceptance" in needs, needs
    aggregate_steps = aggregate_job.get("steps")
    assert isinstance(aggregate_steps, list), aggregate_job
    download_steps = [
        step
        for step in aggregate_steps
        if isinstance(step, dict) and step.get("uses") == "actions/download-artifact@v4"
    ]
    assert any(
        isinstance(step.get("with"), dict) and step["with"].get("pattern") == "env-evidence-*"
        for step in download_steps
    ), "aggregate proof must download environment evidence artifacts"
    proof_runs = [
        str(step.get("run", ""))
        for step in aggregate_steps
        if isinstance(step, dict) and "aggregate_env_evidence.py" in str(step.get("run", ""))
    ]
    assert any("--inventory config/env-matrix.yaml" in run and "--sha" in run for run in proof_runs), (
        "aggregate proof must validate downloaded outcomes against the inventory and commit SHA"
    )


@when("I check a temporary inventory with an unresolved tox workflow selector and command")
def check_inventory_with_unresolved_selectors(consumer: Any) -> None:
    context = _context(consumer)
    lane = next((lane for lane in _lanes(context) if _status(lane) == "required"), None)
    assert lane is not None, "cannot check unresolved selectors without a required lane"
    lane_id = _lane_id(lane)
    lane["tox_env"] = "pytest-cuke-missing-tox-environment"
    lane["workflow_selector"] = "pytest-cuke-missing-workflow-selector"
    lane["command"] = ["pytest-cuke-missing-command-000"]
    _write_inventory(context)
    context.unresolved_selector_lane = lane_id
    _run_environment_check(context)


@then("the inventory check should fail with a lane-specific tox workflow and command diagnostic")
def unresolved_selectors_fail_actionably(consumer: Any) -> None:
    context = _context(consumer)
    result = context.check_result
    report = _report(context)
    assert result is not None and result.returncode != 0, (result, report)
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    diagnostic_text = json.dumps(diagnostics, ensure_ascii=False, sort_keys=True).casefold()
    assert context.unresolved_selector_lane.casefold() in diagnostic_text, diagnostics
    assert "pytest-cuke-missing-tox-environment" in diagnostic_text, diagnostics
    assert "pytest-cuke-missing-workflow-selector" in diagnostic_text, diagnostics
    assert "pytest-cuke-missing-command-000" in diagnostic_text, diagnostics
    assert "tox" in diagnostic_text and "workflow" in diagnostic_text and "command" in diagnostic_text, diagnostics
    assert any(item.get("remedy") for item in diagnostics if isinstance(item, dict)), diagnostics


@given(
    "the repository environment inventory is copied to a temporary project",
    target_fixture="temporary_environment_inventory",
)
def repository_inventory_is_copied_to_temporary_project(
    request: Any, tmp_path: Path
) -> TemporaryEnvironmentInventoryContext:
    repository_root = Path(request.config.rootpath)
    project_root = tmp_path / "environment-inventory-project"
    inventory_path = project_root / "config" / "env-matrix.yaml"
    inventory_path.parent.mkdir(parents=True)
    source_inventory = repository_root / "config" / "env-matrix.yaml"
    document = yaml.safe_load(source_inventory.read_text(encoding="utf-8"))
    assert isinstance(document, dict), document
    inventory_path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")

    for filename in ("tox.ini", "pyproject.toml"):
        shutil.copy2(repository_root / filename, project_root / filename)
    workflow_directory = project_root / ".github" / "workflows"
    workflow_directory.mkdir(parents=True)
    for source in sorted((repository_root / ".github" / "workflows").glob("*.yml")):
        shutil.copy2(source, workflow_directory / source.name)
    for source in sorted((repository_root / ".github" / "workflows").glob("*.yaml")):
        shutil.copy2(source, workflow_directory / source.name)
    return TemporaryEnvironmentInventoryContext(project_root, inventory_path, document)


@when("I check a temporary inventory omitting one resolved tox environment")
def check_inventory_omitting_resolved_tox_environment(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    _, tox_names = _list_tox_environment_names(context.project_root)
    lane_and_names = next(
        (
            (candidate, names)
            for candidate in context.document["lanes"]
            if isinstance(candidate, dict) and _status(candidate) == "required"
            for names in ([part.strip() for part in str(candidate.get("tox_env", "")).split(",") if part.strip()],)
            if len([name for name in names if name in tox_names]) > 1
        ),
        None,
    )
    assert lane_and_names is not None, (
        f"expected a required lane with multiple resolved tox environments: {tox_names!r}"
    )
    lane, environment_names = lane_and_names
    environment_name = next(name for name in environment_names if name in tox_names)
    environment_names.remove(environment_name)
    lane["tox_env"] = ",".join(environment_names)
    lane_id = _lane_id(lane)
    context.inventory_path.write_text(
        yaml.safe_dump(context.document, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    context.unrepresented_tox_lane = lane_id
    context.unrepresented_tox_environment = environment_name
    context.report = check_environment_inventory(context.inventory_path)


@then("the inventory check should fail with a workflow lane and environment diagnostic")
def omitted_tox_environment_fails_with_scoped_diagnostic(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    report = context.report
    assert report is not None, "the direct environment inventory check has not run"
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    lane_id = context.unrepresented_tox_lane
    environment_name = context.unrepresented_tox_environment
    assert lane_id is not None, "the temporary inventory has no lane ID to check"
    assert environment_name is not None, "the temporary inventory has no tox environment to check"
    matching = [
        item
        for item in diagnostics
        if isinstance(item, dict) and item.get("laneId") == lane_id and environment_name in str(item.get("message", ""))
    ]
    assert matching, diagnostics


@when("I add a nonexistent tox environment to a workflow cell")
def add_nonexistent_tox_environment_to_workflow_cell(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    _, tox_names = _list_tox_environment_names(context.project_root)
    environment_name = "pytest-cuke-acceptance-unresolved-tox-environment-000000"
    assert environment_name not in tox_names, f"the test tox environment unexpectedly resolves: {tox_names!r}"

    cell = next(
        candidate for candidate in context.document["workflow_cells"] if candidate.get("id") == "cpython-312-linux"
    )
    cell["tox_envs"].append(environment_name)
    cell_id = str(cell["id"])
    context.inventory_path.write_text(
        yaml.safe_dump(context.document, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    context.unresolved_workflow_cell = cell_id
    context.unresolved_workflow_environment = environment_name
    context.report = check_environment_inventory(context.inventory_path)


@then("the inventory check should fail with a workflow cell and environment diagnostic")
def unresolved_workflow_environment_fails_with_scoped_diagnostic(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    report = context.report
    assert report is not None, "the direct environment inventory check has not run"
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    cell_id = context.unresolved_workflow_cell
    environment_name = context.unresolved_workflow_environment
    assert cell_id is not None, "the temporary inventory has no workflow cell ID to check"
    assert environment_name is not None, "the temporary inventory has no tox environment to check"
    matching = [
        item
        for item in diagnostics
        if isinstance(item, dict)
        and item.get("laneId") == cell_id
        and item.get("code") == "workflow-tox-environment-unresolved"
        and environment_name in str(item.get("message", ""))
    ]
    assert matching, diagnostics


def _full_matrix_workflow_context(
    context: TemporaryEnvironmentInventoryContext,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    cell = next(
        candidate for candidate in context.document["workflow_cells"] if candidate.get("id") == "cpython-311-linux"
    )
    assert cell.get("job") == "full-matrix", cell
    lane = next(
        candidate
        for candidate in context.document["lanes"]
        if candidate.get("workflow_selector") == cell["id"] and _status(candidate) == "required"
    )
    workflow_path = context.project_root / str(context.document["project"]["workflow"])
    return cell, lane, workflow_path


@when("I wire a workflow job to a different matrix selection output")
def wire_workflow_job_to_different_matrix_output(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    cell, lane, workflow_path = _full_matrix_workflow_context(context)
    content = workflow_path.read_text(encoding="utf-8")
    expected_expression = "fromJSON(needs.matrix-select.outputs.full_matrix)"
    wrong_expression = "fromJSON(needs.matrix-select.outputs.remote)"
    assert content.count(expected_expression) == 1, (
        f"expected exactly one full-matrix selector in {workflow_path}, found {content.count(expected_expression)}"
    )
    content = content.replace(expected_expression, wrong_expression, 1)
    assert "fromJSON(needs." in content and wrong_expression in content, content
    workflow_path.write_text(content, encoding="utf-8")
    context.mismatched_workflow_cell_id = str(cell["id"])
    context.mismatched_workflow_lane_id = _lane_id(lane)
    context.report = check_environment_inventory(context.inventory_path)


@then("the inventory check should fail with a scoped matrix output diagnostic")
def mismatched_workflow_matrix_output_fails_actionably(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    report = context.report
    assert report is not None, "the direct environment inventory check has not run"
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    cell_id = context.mismatched_workflow_cell_id
    lane_id = context.mismatched_workflow_lane_id
    assert cell_id is not None, "the temporary inventory has no mismatched workflow cell ID"
    assert lane_id is not None, "the temporary inventory has no required lane for the workflow cell"
    matching = [
        item
        for item in diagnostics
        if isinstance(item, dict)
        and item.get("laneId") == lane_id
        and cell_id in str(item.get("message", ""))
        and "full-matrix" in str(item.get("message", ""))
        and "full_matrix" in str(item.get("message", ""))
        and "remote" in str(item.get("message", ""))
    ]
    assert matching, diagnostics
    diagnostic = matching[0]
    remedy = str(diagnostic.get("remedy", "")).casefold()
    assert remedy and any(action in remedy for action in ("output", "matrix", "selector")), diagnostic


@when("I remove the GitHub output flag from a selector step")
def remove_github_output_flag_from_selector_step(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    cell, lane, workflow_path = _full_matrix_workflow_context(context)
    content = workflow_path.read_text(encoding="utf-8")
    selected_command = "scripts/env_matrix.py --job full-matrix --split-tox-envs --github-output"
    command_without_export = selected_command.removesuffix(" --github-output")
    assert content.count(selected_command) == 1, (
        f"expected exactly one full-matrix output-producing step in {workflow_path}, "
        f"found {content.count(selected_command)}"
    )
    content = content.replace(selected_command, command_without_export, 1)
    changed_step = next(line for line in content.splitlines() if "scripts/env_matrix.py --job full-matrix" in line)
    assert changed_step.strip() == f"run: python {command_without_export}", changed_step
    assert "--github-output" not in changed_step, changed_step
    workflow_path.write_text(content, encoding="utf-8")
    context.missing_matrix_export_cell_id = str(cell["id"])
    context.missing_matrix_export_lane_id = _lane_id(lane)
    context.report = check_environment_inventory(context.inventory_path)


@then("the inventory check should fail with a scoped matrix export diagnostic")
def missing_matrix_export_fails_actionably(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    report = context.report
    assert report is not None, "the direct environment inventory check has not run"
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    cell_id = context.missing_matrix_export_cell_id
    lane_id = context.missing_matrix_export_lane_id
    assert cell_id is not None, "the temporary inventory has no matrix export cell ID"
    assert lane_id is not None, "the temporary inventory has no required lane for the matrix export cell"
    matching = [
        item
        for item in diagnostics
        if isinstance(item, dict)
        and item.get("laneId") == lane_id
        and cell_id in str(item.get("message", ""))
        and "full-matrix" in str(item.get("message", ""))
        and any(word in str(item.get("message", "")).casefold() for word in ("output", "export"))
    ]
    assert matching, diagnostics
    diagnostic = matching[0]
    remedy = str(diagnostic.get("remedy", "")).casefold()
    assert remedy and any(action in remedy for action in ("github-output", "output", "export")), diagnostic


@when(
    "I expand every full-matrix cell into tox environment rows",
    target_fixture="expanded_full_matrix_rows",
)
def expand_selected_full_matrix_cells(
    request: Any,
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> dict[str, Any]:
    return _expand_workflow_job_tox_envs(request, temporary_environment_inventory, "full-matrix")


@when(
    "I expand every optional integration cell into tox environment rows",
    target_fixture="expanded_optional_integration_rows",
)
def expand_optional_integration_cells(
    request: Any,
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> dict[str, Any]:
    return _expand_workflow_job_tox_envs(request, temporary_environment_inventory, "optional-integrations")


def _expand_workflow_job_tox_envs(
    request: Any,
    context: TemporaryEnvironmentInventoryContext,
    job_id: str,
) -> dict[str, Any]:
    repository_root = Path(request.config.rootpath)
    inventory = context.document
    workflow_relative_path = inventory.get("project", {}).get("workflow")
    assert isinstance(workflow_relative_path, str), workflow_relative_path
    workflow = yaml.safe_load((context.project_root / workflow_relative_path).read_text(encoding="utf-8"))
    selector_steps = workflow["jobs"]["matrix-select"]["steps"]
    selector_commands = [
        step.get("run", "")
        for step in selector_steps
        if isinstance(step, dict) and f"scripts/env_matrix.py --job {job_id}" in str(step.get("run", ""))
    ]
    assert len(selector_commands) == 1, selector_commands
    selector_tokens = shlex.split(selector_commands[0])
    assert "--split-tox-envs" in selector_tokens and "--github-output" in selector_tokens, selector_tokens
    selector_path = context.project_root / "scripts" / "env_matrix.py"
    selector_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repository_root / "scripts" / "env_matrix.py", selector_path)
    command = [
        sys.executable,
        str(selector_path),
        "--job",
        job_id,
        "--split-tox-envs",
        "--inventory",
        str(context.inventory_path),
    ]
    result = subprocess.run(
        command,
        cwd=context.project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"full-matrix expansion failed:\n{result.stdout}\n{result.stderr}"
    rows = json.loads(result.stdout)
    assert isinstance(rows, list) and all(isinstance(row, dict) for row in rows), rows
    return {"rows": rows, "inventory": inventory, "job_id": job_id}


@then("every full-matrix tox environment should appear exactly once with canonical cell metadata")
def expanded_full_matrix_rows_cover_every_environment_once(
    expanded_full_matrix_rows: dict[str, Any],
) -> None:
    _assert_expanded_workflow_rows_match_cells(expanded_full_matrix_rows, "full-matrix")


@then("every optional integration tox environment should appear exactly once with canonical cell metadata")
def expanded_optional_integration_rows_cover_every_environment_once(
    expanded_optional_integration_rows: dict[str, Any],
) -> None:
    _assert_expanded_workflow_rows_match_cells(expanded_optional_integration_rows, "optional-integrations")


def _assert_expanded_workflow_rows_match_cells(expansion: dict[str, Any], job_id: str) -> None:
    inventory = expansion["inventory"]
    rows = expansion["rows"]
    assert expansion["job_id"] == job_id, expansion
    inventory_cells = inventory.get("workflow_cells")
    assert isinstance(inventory_cells, list), inventory_cells
    job_cells = [cell for cell in inventory_cells if isinstance(cell, dict) and cell.get("job") == job_id]
    assert job_cells, f"the canonical inventory has no {job_id!r} cells"
    expected_cells = {str(cell["id"]): cell for cell in job_cells}
    expected_environments: list[str] = []
    for cell in expected_cells.values():
        tox_envs = cell.get("tox_envs")
        assert isinstance(tox_envs, list) and tox_envs, cell
        expected_environments.extend(str(tox_env) for tox_env in tox_envs)

    actual_environments = [row.get("tox_environment") for row in rows]
    assert sorted(actual_environments) == sorted(expected_environments), actual_environments
    assert len(actual_environments) == len(set(actual_environments)), actual_environments
    assert len(rows) == len(expected_environments), rows

    for cell in job_cells:
        cell_id = str(cell["id"])
        matching_rows = [row for row in rows if row.get("id") == cell_id]
        assert len(matching_rows) == len(cell["tox_envs"]), (cell_id, matching_rows)
        assert len({row.get("tox_environment") for row in matching_rows}) == len(matching_rows), matching_rows
        for row in matching_rows:
            assert row.get("tox_environment") in cell["tox_envs"], row
            for key, value in cell.items():
                if key != "tox_envs":
                    assert row.get(key) == value, (key, cell, row)


@when("I add an unsupported Windows lane overlapping the optional Windows lane")
def add_overlapping_unsupported_windows_lane(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    optional_lane = next(
        (
            lane
            for lane in context.document["lanes"]
            if _lane_id(lane) == "remote-socket-windows-manual" and _status(lane) == "optional"
        ),
        None,
    )
    assert optional_lane is not None, "the temporary inventory has no optional Windows remote-socket lane"
    optional_lane_id = _lane_id(optional_lane)
    unsupported_lane_id = "remote-socket-windows-unsupported-conflict"
    existing_lane_ids = {_lane_id(lane) for lane in context.document["lanes"]}
    assert unsupported_lane_id not in existing_lane_ids, existing_lane_ids

    unsupported_lane = optional_lane.copy()
    unsupported_lane.update(
        {
            "id": unsupported_lane_id,
            "status": "unsupported",
            "tox_env": None,
            "workflow_selector": None,
            "reason": "The acceptance fixture intentionally overlaps an optional capability lane.",
            "source_evidence": ["tests/e2e/environment_inventory_steps.py"],
        }
    )
    context.document["lanes"].append(unsupported_lane)
    context.inventory_path.write_text(
        yaml.safe_dump(context.document, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    context.conflicting_optional_lane_id = optional_lane_id
    context.conflicting_unsupported_lane_id = unsupported_lane_id
    context.report = check_environment_inventory(context.inventory_path)


@then("the inventory check should fail with an actionable runtime lane conflict diagnostic")
def conflicting_lane_statuses_fail_actionably(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    report = context.report
    assert report is not None, "the direct environment inventory check has not run"
    assert report.get("status") == "fail", report
    diagnostics = report.get("diagnostics")
    assert isinstance(diagnostics, list) and diagnostics, report
    optional_lane_id = context.conflicting_optional_lane_id
    unsupported_lane_id = context.conflicting_unsupported_lane_id
    assert optional_lane_id is not None, "the temporary inventory has no optional conflict lane"
    assert unsupported_lane_id is not None, "the temporary inventory has no unsupported conflict lane"

    matching = [
        item
        for item in diagnostics
        if isinstance(item, dict)
        and item.get("code") == "lane-status-conflict"
        and optional_lane_id in str(item.get("message", ""))
        and unsupported_lane_id in str(item.get("message", ""))
    ]
    assert matching, diagnostics
    diagnostic = matching[0]
    message = str(diagnostic.get("message", "")).casefold()
    remedy = str(diagnostic.get("remedy", "")).casefold()
    assert all(dimension in message for dimension in ("cpython", "3.14", "windows", "xdist-remote-socket")), diagnostic
    assert "latest" in message, diagnostic
    assert "optional" in message and "unsupported" in message, diagnostic
    assert remedy and any(action in remedy for action in ("align", "merge", "change", "remove")), diagnostic
