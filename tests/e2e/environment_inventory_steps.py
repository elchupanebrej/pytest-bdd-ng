"""Installed-consumer acceptance steps for the repository environment inventory."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from pytest_cuke.compatibility.runtime_compat import is_pair_compatible
from pytest_cuke import given, then, when


@dataclass
class EnvironmentInventoryContext:
    consumer: Any
    repository_root: Path
    document: dict[str, Any]
    check_result: subprocess.CompletedProcess[str] | None = None
    report: dict[str, Any] | None = None
    tox_result: subprocess.CompletedProcess[str] | None = None


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


def _inventory_command_environment(consumer: Any) -> dict[str, str]:
    environment = consumer.env.copy()
    consumer_binary_directory = str(Path(consumer.python).resolve().parent)
    environment["PATH"] = os.pathsep.join((consumer_binary_directory, environment.get("PATH", os.defpath)))
    return environment


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
        env=_inventory_command_environment(consumer),
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


def _assert_carrier_path_exists(context: EnvironmentInventoryContext, lane: dict[str, Any]) -> None:
    carrier_path = _carrier(lane).get("path")
    if carrier_path:
        path = context.repository_root / str(carrier_path)
        assert path.exists(), f"lane {_lane_id(lane)!r} names missing carrier path {carrier_path!r}"


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


@then("its tox listing proof should match the real tox environment list")
def tox_listing_proof_matches_real_tox(consumer: Any) -> None:
    context = _context(consumer)
    report = _report(context)
    proof = report.get("proof", {}).get("tox", {})
    command = proof.get("command")
    assert command == ["tox", "list", "--no-desc"], proof

    result = subprocess.run(
        command,
        cwd=consumer.path,
        env=_inventory_command_environment(consumer),
        check=False,
        capture_output=True,
        text=True,
    )
    context.tox_result = result
    assert result.returncode == 0, f"real tox list failed: {result.stdout}\n{result.stderr}"
    actual_names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    actual_names = [line for line in actual_names if not line.startswith("All environments:")]
    proof_names = proof.get("environments")
    inventory_names = report.get("inventory", {}).get("toxEnvironments")
    assert isinstance(proof_names, list) and proof_names, proof
    assert set(proof_names) == set(actual_names), (proof_names, actual_names)
    assert isinstance(inventory_names, list) and set(inventory_names) == set(actual_names), inventory_names


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
