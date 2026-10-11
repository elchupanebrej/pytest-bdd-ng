"""Installed-consumer acceptance steps for the repository environment inventory."""

from __future__ import annotations

import configparser
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from pytest_cuke import given, then, when
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
    assert (
        result.returncode == 0
    ), f"could not install environment checker dependencies:\n{result.stdout}\n{result.stderr}"


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


@then("CPython 3.12 Windows and macOS lanes should remain optional manual entries")
def cpython_312_windows_macos_are_manual_optional_lanes(consumer: Any) -> None:
    context = _context(consumer)
    lanes = _lanes(context)
    manual_lanes = {
        str(lane.get("platform")): lane
        for lane in lanes
        if _lane_id(lane) in {"py312-windows-manual", "py312-macos-manual"}
    }
    assert set(manual_lanes) == {"windows", "macos"}, manual_lanes
    for platform_name, lane in manual_lanes.items():
        assert _status(lane) == "optional", lane
        assert "#149" in str(lane.get("reason", "")), lane
        assert any("issues/149" in str(source) for source in lane.get("source_evidence", [])), lane
        assert lane.get("workflow_selector") is None, lane
        assert "py312-pytest73-coverage" in str(lane.get("tox_env", "")), lane
        assert not any(
            cell.get("runtime") == "CPython"
            and str(cell.get("python")) == "3.12"
            and cell.get("platform") == platform_name
            for cell in context.document.get("workflow_cells", [])
            if isinstance(cell, dict)
        ), lane

    excluded = [
        lane
        for lane in lanes
        if _status(lane) == "unsupported"
        and lane.get("runtime") == "CPython"
        and str(lane.get("python")) == "3.12"
        and lane.get("platform") in {"windows", "macos"}
    ]
    assert not excluded, excluded


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
        f"could not install doc-generation package prerequisites {package_names!r}:\n"
        f"{result.stdout}\n{result.stderr}"
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


@then("required lanes should include CPython 3.14 and PyPy 3.11")
def required_lanes_include_current_python_targets(consumer: Any) -> None:
    required = [lane for lane in _lanes(_context(consumer)) if _status(lane) == "required"]
    assert any(
        "cpython" in str(lane["runtime"]).casefold() and str(lane["python"]).startswith("3.14") for lane in required
    )
    assert any(
        "pypy" in str(lane["runtime"]).casefold() and str(lane["python"]).startswith("3.11") for lane in required
    )


@then("required lanes should exercise compatible pytest 7 8 and 9 versions")
def required_lanes_exercise_supported_pytest_majors(consumer: Any) -> None:
    required = [lane for lane in _lanes(_context(consumer)) if _status(lane) == "required"]
    majors = {major for lane in required for major in _majors(lane["pytest"])}
    assert {7, 8, 9} <= majors, majors


@then("the older viable pytest minors should use compatible Python lanes")
def older_pytest_minors_use_compatible_python_lanes(consumer: Any) -> None:
    required = [lane for lane in _lanes(_context(consumer)) if _status(lane) == "required"]
    pair_pattern = re.compile(r"^py(?P<python>\d+)-pytest(?P<pytest>\d+)")
    pairs: set[tuple[str, str]] = set()
    for lane in required:
        tox_environments = str(lane.get("tox_env", "")).split(",")
        for environment in tox_environments:
            match = pair_pattern.match(environment.strip())
            if match is None:
                continue
            python_factor = match.group("python")
            pytest_factor = match.group("pytest")
            compatible, reason = is_pair_compatible(python_factor, pytest_factor)
            assert compatible, f"{environment!r} is not a supported pair: {reason}"
            pairs.add((python_factor, pytest_factor))

    expected = {("310", "70"), ("310", "71"), ("311", "72"), ("312", "80"), ("312", "81")}
    assert expected <= pairs, f"older viable pytest tox pairings are missing: {sorted(expected - pairs)!r}"


@then("Python 3.9 and pytest versions below 7 should be explicitly unsupported and unselected")
def obsolete_runtime_and_pytest_pairs_are_excluded(consumer: Any) -> None:
    unsupported = [lane for lane in _lanes(_context(consumer)) if _status(lane) == "unsupported"]
    assert any(str(lane["python"]).startswith("3.9") for lane in unsupported), unsupported
    assert any(any(major < 7 for major in _majors(lane["pytest"])) for lane in unsupported), unsupported
    active = [lane for lane in _lanes(_context(consumer)) if _status(lane) != "unsupported"]
    assert all(not str(lane["python"]).startswith("3.9") for lane in active), active
    assert all(all(major >= 7 for major in _majors(lane["pytest"])) for lane in active), active


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


@then("Ruff and typecheck lanes should resolve to their real tools")
def ruff_and_typecheck_lanes_resolve_to_real_tools(consumer: Any) -> None:
    lanes = {_lane_id(lane): lane for lane in _lanes(_context(consumer))}
    expected_commands = {
        "ruff": ("ruff",),
        "typecheck": ("scripts/check_types.py", "mypy", "mypy-runtime-gate.feature"),
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
        '.[test,struct-bdd,env-matrix]',
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


@then("the contributor entry point should link to the compatibility audit guide")
def contributor_entry_links_to_compatibility_audit(compatibility_audit_documents: CompatibilityAuditDocuments) -> None:
    contribution_section = compatibility_audit_documents.contributor_entry.partition("How to Contribute")[2]
    link_pattern = r"`[^`<>]*<docs/compatibility-and-migration-audit\.md>`_"
    assert re.search(link_pattern, contribution_section), (
        "README.rst's How to Contribute section should link to "
        "docs/compatibility-and-migration-audit.md"
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
    assert _feature_arguments(synthetic_command) == {
        "C:/workspace with spaces/extra.feature"
    }, synthetic_command

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
    assert any(
        "--inventory config/env-matrix.yaml" in run and "--sha" in run for run in proof_runs
    ), "aggregate proof must validate downloaded outcomes against the inventory and commit SHA"


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
    environment_name = "py312-pytest73-coverage-lin"
    _, tox_names = _list_tox_environment_names(context.project_root)
    assert environment_name in tox_names, f"expected a real resolved tox environment, got {tox_names!r}"

    lane = next(
        candidate for candidate in context.document["lanes"] if _lane_id(candidate) == "cpython-312-linux-pytest7"
    )
    environment_names = [part.strip() for part in str(lane["tox_env"]).split(",") if part.strip()]
    assert environment_name in environment_names, lane
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
        candidate for candidate in context.document["workflow_cells"] if candidate.get("id") == "cpython-310-linux"
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
    assert (
        content.count(expected_expression) == 1
    ), f"expected exactly one full-matrix selector in {workflow_path}, found {content.count(expected_expression)}"
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
    selected_command = "scripts/env_matrix.py --job full-matrix --github-output"
    command_without_export = "scripts/env_matrix.py --job full-matrix"
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


@when("I add an unsupported Windows lane overlapping the optional Windows lane")
def add_overlapping_unsupported_windows_lane(
    temporary_environment_inventory: TemporaryEnvironmentInventoryContext,
) -> None:
    context = temporary_environment_inventory
    optional_lane = next(
        (
            lane
            for lane in context.document["lanes"]
            if _lane_id(lane) == "py312-windows-manual" and _status(lane) == "optional"
        ),
        None,
    )
    assert optional_lane is not None, "the temporary inventory has no optional CPython 3.12 Windows lane"
    optional_lane_id = _lane_id(optional_lane)
    unsupported_lane_id = "py312-windows-pytest73-74-unsupported-conflict"
    existing_lane_ids = {_lane_id(lane) for lane in context.document["lanes"]}
    assert unsupported_lane_id not in existing_lane_ids, existing_lane_ids

    unsupported_lane = optional_lane.copy()
    unsupported_lane.update(
        {
            "id": unsupported_lane_id,
            "status": "unsupported",
            "pytest": "7.3-7.4",
            "tox_env": None,
            "workflow_selector": None,
            "reason": "The acceptance fixture intentionally overlaps an optional runtime lane.",
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
    assert all(dimension in message for dimension in ("cpython", "3.12", "windows", "manual-tox-coverage")), diagnostic
    assert "7.3" in message and "7.4" in message, diagnostic
    assert "optional" in message and "unsupported" in message, diagnostic
    assert remedy and any(action in remedy for action in ("align", "merge", "change", "remove")), diagnostic
