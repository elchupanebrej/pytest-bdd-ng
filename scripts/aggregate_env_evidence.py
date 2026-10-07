"""Validate and summarize every environment in the full inventory proof."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from environment_evidence import (
    EVIDENCE_GROUPS,
    EXPECTED_JOBS,
    OPTIONAL_VERSION_KEYS,
    TEST_EVIDENCE_GROUPS,
    evidence_group,
    required_optional_versions,
)


def _version_pair(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"^(\d+)\.(\d+)(?:\.|[-+]|$)", value)
    return (int(match.group(1)), int(match.group(2))) if match else None


def _pytest_factor(tox_environment: str) -> str | None:
    match = re.search(r"(?:^|-)pytest(\d{2}|latest)(?:-|$)", tox_environment)
    return match.group(1) if match else None


def _pytest_factor_pair(tox_environment: str) -> tuple[int, int] | None:
    factor = _pytest_factor(tox_environment)
    if factor is None or factor == "latest":
        return None
    return int(factor[0]), int(factor[1])


def _inventory_environments(inventory_path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    try:
        inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise RuntimeError(f"cannot read environment inventory {inventory_path}: {error}") from error
    if not isinstance(inventory, dict):
        raise RuntimeError(f"environment inventory {inventory_path} must contain a YAML object")
    cells = inventory.get("workflow_cells")
    if not isinstance(cells, list) or any(not isinstance(cell, dict) for cell in cells):
        raise RuntimeError(f"environment inventory {inventory_path} must contain workflow_cells objects")
    cell_jobs = [cell.get("job") for cell in cells]
    if any(not isinstance(job, str) or not job for job in cell_jobs):
        raise RuntimeError(f"environment inventory {inventory_path} has a workflow cell without a job name")
    inventory_jobs = set(cell_jobs)
    if inventory_jobs != set(EXPECTED_JOBS):
        raise RuntimeError(
            f"inventory workflow jobs {sorted(inventory_jobs)!r} do not match the proof job ledger "
            f"{sorted(EXPECTED_JOBS)!r}"
        )
    project_config = inventory.get("project")
    evidence_config = project_config.get("evidence") if isinstance(project_config, dict) else None
    declared_groups = evidence_config.get("aggregate_groups") if isinstance(evidence_config, dict) else None
    expected_groups = set(EVIDENCE_GROUPS)
    if (
        not isinstance(declared_groups, list)
        or any(not isinstance(group, str) for group in declared_groups)
        or set(declared_groups) != expected_groups
    ):
        raise RuntimeError(
            f"inventory evidence.aggregate_groups must declare exactly {sorted(expected_groups)!r}"
        )

    expected: dict[tuple[str, str, str], dict[str, str]] = {}
    for job in EXPECTED_JOBS:
        job_cells = [cell for cell in cells if cell.get("job") == job]
        if not job_cells:
            raise RuntimeError(f"inventory has no workflow cells for job {job!r}")
        for cell in job_cells:
            cell_id = cell.get("id")
            runtime = cell.get("runtime")
            python = cell.get("python")
            platform_name = cell.get("platform")
            tox_environments = cell.get("tox_envs")
            if any(not isinstance(value, str) or not value for value in (cell_id, runtime, python, platform_name)):
                raise RuntimeError(f"inventory cell for job {job!r} must declare id, runtime, python, and platform")
            if not isinstance(tox_environments, list) or not tox_environments:
                raise RuntimeError(f"inventory cell {cell_id!r} must declare tox_envs")
            if any(not isinstance(value, str) or not value for value in tox_environments):
                raise RuntimeError(f"inventory cell {cell_id!r} contains an invalid tox environment")
            for tox_environment in tox_environments:
                name = str(tox_environment)
                key = (job, cell_id, name)
                if key in expected:
                    raise RuntimeError(f"inventory repeats environment {job}/{cell_id}/{name}")
                expected[key] = {
                    "group": evidence_group(job, name),
                    "runtime": runtime,
                    "python": python,
                    "platform": platform_name,
                }
    return expected


def _tox_command_matches(command: Any, tox_environment: str) -> bool:
    if not isinstance(command, list) or any(not isinstance(part, str) for part in command):
        return False
    if len(command) < 5 or command[1] != "run" or "--result-json" not in command:
        return False
    executable_name = command[0].replace("\\", "/").rsplit("/", maxsplit=1)[-1].casefold()
    try:
        environment_index = command.index("-e") + 1
    except ValueError:
        return False
    return (
        executable_name in {"tox", "tox.exe"}
        and command[environment_index : environment_index + 1] == [tox_environment]
    )


def _tox_result_entry(payload: Any, tox_environment: str) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    testenvs = payload.get("testenvs")
    entry = testenvs.get(tox_environment) if isinstance(testenvs, dict) else None
    if not isinstance(entry, dict):
        return None
    result = entry.get("result")
    commands = entry.get("test")
    valid_result = isinstance(result, dict) and result.get("success") is True and result.get("exit_code") == 0
    valid_commands = (
        isinstance(commands, list)
        and bool(commands)
        and all(
            isinstance(command, dict)
            and command.get("retcode") == 0
            and isinstance(command.get("command"), list)
            and bool(command["command"])
            and all(isinstance(part, str) for part in command["command"])
            and bool(command["command"][0])
            for command in commands
        )
    )
    if (
        not valid_result
        or not valid_commands
        or not isinstance(entry.get("python"), dict)
        or not isinstance(entry.get("installed_packages"), list)
    ):
        return None
    return entry


def _tox_installed_versions(entry: dict[str, Any]) -> dict[str, str]:
    installed_packages = entry.get("installed_packages")
    if not isinstance(installed_packages, list):
        return {}
    versions: dict[str, str] = {}
    for package in installed_packages:
        if not isinstance(package, str):
            continue
        name, separator, version = package.partition("==")
        if separator:
            normalized_name = re.sub(r"[-_.]+", "-", name).casefold()
            versions[normalized_name] = version
    return versions


def _platform_matches(expected_platform: str, observed_platform: Any) -> bool:
    expected_value = {"linux": "linux", "macos": "darwin", "windows": "win32"}.get(expected_platform)
    return expected_value is not None and observed_platform == expected_value


def collect_evidence(
    root: Path, expected_sha: str, inventory_path: Path
) -> tuple[dict[str, Any], list[str]]:
    records: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    errors: list[str] = []
    try:
        expected = _inventory_environments(inventory_path)
    except RuntimeError as error:
        return (
            {
                "schema_version": 1,
                "git_sha": expected_sha,
                "outcome": "failed",
                "groups": {},
                "environment_count": 0,
            },
            [f"cannot load expected environment inventory: {error}"],
        )

    evidence_files = sorted(root.rglob("evidence-*.json"))
    if not evidence_files:
        errors.append(f"no evidence-*.json files found under {root}")

    for path in evidence_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"cannot read {path}: {error}")
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("environments"), list):
            errors.append(f"{path} is not an environment evidence document")
            continue
        if payload.get("schema_version") != 1:
            errors.append(f"{path} does not use environment evidence schema version 1")
        if payload.get("git_sha") != expected_sha:
            errors.append(f"{path} records SHA {payload.get('git_sha')!r}; expected exact SHA {expected_sha!r}")
        payload_outcome = payload.get("outcome")
        if payload_outcome != "passed":
            errors.append(f"{path} reports overall outcome {payload_outcome!r}")
        payload_job = payload.get("job")
        payload_cell = payload.get("cell")
        for environment in payload["environments"]:
            if not isinstance(environment, dict):
                errors.append(f"{path} contains a non-object environment record")
                continue
            job = environment.get("job")
            cell = environment.get("cell")
            tox_environment = environment.get("tox_environment")
            key = (str(job), str(cell), str(tox_environment))
            if payload_job != job or payload_cell != cell:
                errors.append(f"{path} environment {tox_environment!r} disagrees with its job/cell header")
            if environment.get("git_sha") != expected_sha:
                errors.append(f"{path} environment {tox_environment!r} has a mismatched SHA")
            if key not in expected:
                errors.append(f"{path} contains unrequested environment {job}/{cell}/{tox_environment}")
            records.setdefault(key, []).append({**environment, "_payload_outcome": payload_outcome})

    group_records: dict[str, list[dict[str, Any]]] = {group: [] for group in EVIDENCE_GROUPS}
    invalid_groups: set[str] = set()
    for key, specification in expected.items():
        job, cell, tox_environment = key
        expected_group = specification["group"]
        observed = records.get(key, [])
        if not observed:
            errors.append(f"missing evidence for expected environment {job}/{cell}/{tox_environment}")
            invalid_groups.add(expected_group)
            continue
        if len(observed) > 1:
            errors.append(f"duplicate evidence for expected environment {job}/{cell}/{tox_environment}")
            invalid_groups.add(expected_group)
        record = observed[0]
        group_records[expected_group].append(record)
        if record.get("_payload_outcome") != "passed":
            invalid_groups.add(expected_group)
        if record.get("group") != expected_group:
            errors.append(
                f"{job}/{cell}/{tox_environment} is labeled {record.get('group')!r}; expected {expected_group!r}"
            )
            invalid_groups.add(expected_group)
        if record.get("outcome") != "passed" or record.get("returncode") != 0:
            errors.append(f"{job}/{cell}/{tox_environment} did not pass")
            invalid_groups.add(expected_group)
        if record.get("runtime") != specification["runtime"]:
            errors.append(
                f"{job}/{cell}/{tox_environment} reports runtime {record.get('runtime')!r}; "
                f"inventory expects {specification['runtime']!r}"
            )
            invalid_groups.add(expected_group)
        if _version_pair(record.get("python")) != _version_pair(specification["python"]):
            errors.append(
                f"{job}/{cell}/{tox_environment} reports Python {record.get('python')!r}; "
                f"inventory expects {specification['python']!r}"
            )
            invalid_groups.add(expected_group)
        if not _platform_matches(specification["platform"], record.get("platform_name")):
            errors.append(
                f"{job}/{cell}/{tox_environment} reports platform {record.get('platform_name')!r}; "
                f"inventory expects {specification['platform']!r}"
            )
            invalid_groups.add(expected_group)
        if not _tox_command_matches(record.get("command"), tox_environment):
            errors.append(f"{job}/{cell}/{tox_environment} is missing a resolved tox command")
            invalid_groups.add(expected_group)
        if not isinstance(record.get("result_json"), str) or not record["result_json"]:
            errors.append(f"{job}/{cell}/{tox_environment} is missing the tox result path")
            invalid_groups.add(expected_group)
        tox_result_entry = _tox_result_entry(record.get("tox_result"), tox_environment)
        if tox_result_entry is None:
            errors.append(
                f"{job}/{cell}/{tox_environment} is missing a successful tox result entry "
                "with interpreter, package, and command evidence"
            )
            invalid_groups.add(expected_group)
        optional_versions = record.get("optional_versions")
        if (
            not isinstance(optional_versions, dict)
            or not set(OPTIONAL_VERSION_KEYS) <= set(optional_versions)
            or any(value is not None and not isinstance(value, str) for value in optional_versions.values())
        ):
            errors.append(f"{job}/{cell}/{tox_environment} is missing actual optional dependency versions")
            invalid_groups.add(expected_group)
        elif isinstance(optional_versions, dict):
            for package in required_optional_versions(tox_environment):
                if not isinstance(optional_versions.get(package), str) or not optional_versions[package]:
                    errors.append(
                        f"{job}/{cell}/{tox_environment} requires installed optional package {package!r}; "
                        "add it to the tox environment dependencies"
                    )
                    invalid_groups.add(expected_group)
        if tox_result_entry is not None:
            tox_python = tox_result_entry.get("python")
            tox_version_info = tox_python.get("version_info") if isinstance(tox_python, dict) else None
            tox_python_pair = None
            if (
                isinstance(tox_version_info, list)
                and len(tox_version_info) >= 2
                and all(isinstance(value, int) and not isinstance(value, bool) for value in tox_version_info[:2])
            ):
                tox_python_pair = (tox_version_info[0], tox_version_info[1])
            if not isinstance(tox_python, dict) or tox_python.get("implementation") != record.get("runtime"):
                errors.append(f"{job}/{cell}/{tox_environment} tox result runtime disagrees with runtime evidence")
                invalid_groups.add(expected_group)
            if tox_python_pair != _version_pair(record.get("python")):
                errors.append(
                    f"{job}/{cell}/{tox_environment} tox result Python version disagrees with runtime evidence"
                )
                invalid_groups.add(expected_group)
            if tox_python.get("sysplatform") != record.get("platform_name"):
                errors.append(f"{job}/{cell}/{tox_environment} tox result platform disagrees with runtime evidence")
                invalid_groups.add(expected_group)
            tox_versions = _tox_installed_versions(tox_result_entry)
            recorded_versions = dict(optional_versions) if isinstance(optional_versions, dict) else {}
            recorded_versions["pytest"] = record.get("pytest")
            for package, recorded_version in recorded_versions.items():
                tox_version = tox_versions.get(re.sub(r"[-_.]+", "-", package).casefold())
                if recorded_version != tox_version:
                    errors.append(
                        f"{job}/{cell}/{tox_environment} records {package}={recorded_version!r}; "
                        f"successful tox result contains {tox_version!r}"
                    )
                    invalid_groups.add(expected_group)
        pytest_version = record.get("pytest")
        actual_pytest_pair = _version_pair(pytest_version)
        declared_pytest_factor = _pytest_factor(tox_environment)
        declared_pytest_pair = _pytest_factor_pair(tox_environment)
        requires_pytest = (
            expected_group in TEST_EVIDENCE_GROUPS
            or declared_pytest_factor is not None
            or tox_environment == "typecheck"
        )
        if requires_pytest and actual_pytest_pair is None:
            errors.append(f"{job}/{cell}/{tox_environment} is missing an actual pytest version")
            invalid_groups.add(expected_group)
        if (
            actual_pytest_pair is not None
            and declared_pytest_pair is not None
            and actual_pytest_pair != declared_pytest_pair
        ):
            errors.append(
                f"{job}/{cell}/{tox_environment} reports pytest {pytest_version!r}; "
                f"tox factor requires {declared_pytest_pair[0]}.{declared_pytest_pair[1]}"
            )
            invalid_groups.add(expected_group)
        if expected_group in TEST_EVIDENCE_GROUPS:
            selected_tests = record.get("selected_tests")
            if isinstance(selected_tests, bool) or not isinstance(selected_tests, int) or selected_tests < 1:
                errors.append(f"{job}/{cell}/{tox_environment} selected no tests")
                invalid_groups.add(expected_group)
            passed_tests = record.get("passed_tests")
            if isinstance(passed_tests, bool) or not isinstance(passed_tests, int) or passed_tests < 1:
                errors.append(f"{job}/{cell}/{tox_environment} selected no tests that passed")
                invalid_groups.add(expected_group)

    groups: dict[str, dict[str, Any]] = {}
    for group, grouped in group_records.items():
        expected_count = sum(1 for value in expected.values() if value["group"] == group)
        observed_count = len(grouped)
        groups[group] = {
            "outcome": (
                "passed"
                if observed_count == expected_count and expected_count > 0 and group not in invalid_groups
                else "failed"
            ),
            "environmentCount": observed_count,
            "expectedEnvironmentCount": expected_count,
            "environments": [record.get("tox_environment") for record in grouped],
        }

    return {
        "schema_version": 1,
        "git_sha": expected_sha,
        "outcome": "failed" if errors else "passed",
        "groups": groups,
        "environments": [
            {
                field: record.get(field)
                for field in (
                    "git_sha",
                    "job",
                    "cell",
                    "group",
                    "tox_environment",
                    "runtime",
                    "python",
                    "pytest",
                    "optional_versions",
                    "platform",
                    "platform_name",
                    "command",
                    "selected_tests",
                    "passed_tests",
                    "outcome",
                    "returncode",
                    "result_json",
                )
            }
            for key in expected
            for record in records.get(key, [])[:1]
        ],
        "environment_count": len(records),
        "expected_environment_count": len(expected),
    }, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--inventory", type=Path, default=Path("config/env-matrix.yaml"))
    parser.add_argument("--sha", required=True, help="expected full Git SHA for all evidence")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", args.sha):
        parser.error("--sha must be a full 40- or 64-character hexadecimal Git commit SHA")

    summary, errors = collect_evidence(args.input_dir, args.sha, args.inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    for error in errors:
        print(f"proof: {error}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
