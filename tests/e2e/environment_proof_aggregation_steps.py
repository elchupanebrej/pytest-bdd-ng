"""BDD acceptance steps for the inventory-driven full proof aggregator."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pytest_cuke import given, then, when


_EXPECTED_GROUPS = ("serial", "parallel", "e2e", "external", "quality")
_TEST_GROUPS = frozenset(("serial", "parallel", "e2e", "external"))
_OPTIONAL_VERSION_KEYS = ("allure-pytest", "gherkin-official", "playwright", "pytest-xdist", "PyYAML")
_PLAYWRIGHT_REPORT_ENV = "py314-pytestlatest-playwright-report"
_PLAYWRIGHT_REPORT_PACKAGES = ("allure-pytest", "pytest-xdist", "gherkin-official", "playwright")
_PLATFORM_NAMES = {"linux": "linux", "macos": "darwin", "windows": "win32"}
_PROOF_SHA = "a" * 40
_OTHER_SHA = "b" * 40


@dataclass
class EvidenceArtifact:
    path: Path
    job: str
    cell: str
    tox_environment: str
    group: str


@dataclass
class ProofAggregationContext:
    project_root: Path
    inventory_path: Path
    input_directory: Path
    output_path: Path
    git_sha: str
    artifacts: list[EvidenceArtifact] = field(default_factory=list)
    summary: dict[str, Any] | None = None


def _load_cells(inventory_path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{inventory_path} must contain a YAML object"
    cells = payload.get("workflow_cells")
    assert isinstance(cells, list) and cells, "config/env-matrix.yaml must contain workflow_cells"
    selected = [cell for cell in cells if isinstance(cell, dict)]
    assert len(selected) == len(cells), "every workflow cell in config/env-matrix.yaml must be an object"
    return selected


def _group_for(job: str, tox_environment: str) -> str:
    if job == "full-matrix":
        return "parallel" if "xdist" in tox_environment else "serial"
    if job in {"browser-report", "native-go-parser"}:
        return "e2e"
    if job == "remote":
        return "external"
    return "quality"


def _pytest_version(tox_environment: str, group: str) -> str | None:
    match = re.search(r"(?:^|-)pytest(?P<factor>\d{2}|latest)(?:-|$)", tox_environment)
    if match and match.group("factor") == "latest":
        return "9.0.1"
    if match:
        factor = match.group("factor")
        return f"{factor[0]}.{factor[1]}.0"
    if tox_environment == "typecheck":
        return "9.0.1"
    return "9.0.1" if group in _TEST_GROUPS else None


def _optional_versions(tox_environment: str) -> dict[str, str | None]:
    is_playwright_report = tox_environment == _PLAYWRIGHT_REPORT_ENV
    has_gherkin_factor = "gherkin33" in tox_environment or "gherkinlatest" in tox_environment
    return {
        "allure-pytest": "2.16.2" if "allure" in tox_environment or is_playwright_report else None,
        "gherkin-official": "33.0.0" if has_gherkin_factor or is_playwright_report else "29.0.0",
        "playwright": "1.63.0" if "playwright" in tox_environment else None,
        "pytest-xdist": "3.8.0" if "xdist" in tox_environment or is_playwright_report else None,
        "PyYAML": "6.0.3",
    }


def _tox_result(
    tox_environment: str,
    runtime: str,
    python_version: str,
    platform_name: str,
    pytest_version: str | None,
    optional_versions: dict[str, str | None],
) -> dict[str, Any]:
    version_parts = [int(part) for part in python_version.split(".")]
    version_info: list[int | str] = [*version_parts, 0, "final", 0][:5]
    installed_packages = [
        f"{package}=={version}"
        for package, version in (("pytest", pytest_version), *optional_versions.items())
        if version is not None
    ]
    return {
        "testenvs": {
            tox_environment: {
                "python": {
                    "implementation": runtime,
                    "version_info": version_info,
                    "sysplatform": platform_name,
                },
                "installed_packages": installed_packages,
                "result": {"success": True, "exit_code": 0},
                "test": [{"command": ["python", "-m", "pytest", "-q"], "retcode": 0}],
            }
        }
    }


def _synthesize_context(project_root: Path, tmp_path: Path) -> ProofAggregationContext:
    inventory_path = project_root / "config" / "env-matrix.yaml"
    input_directory = tmp_path / "evidence"
    input_directory.mkdir(parents=True)
    context = ProofAggregationContext(
        project_root=project_root,
        inventory_path=inventory_path,
        input_directory=input_directory,
        output_path=tmp_path / "full-proof-summary.json",
        git_sha=_PROOF_SHA,
    )

    artifact_index = 0
    for cell_record in _load_cells(inventory_path):
        job = cell_record.get("job")
        cell_id = cell_record.get("id")
        tox_environments = cell_record.get("tox_envs")
        assert isinstance(job, str) and job, cell_record
        assert isinstance(cell_id, str) and cell_id, cell_record
        assert isinstance(tox_environments, list) and tox_environments, cell_record

        for tox_environment in tox_environments:
            assert isinstance(tox_environment, str) and tox_environment, (cell_record, tox_environment)
            group = _group_for(job, tox_environment)
            python_version = cell_record.get("python")
            runtime = cell_record.get("runtime")
            expected_platform = cell_record.get("platform")
            pytest_version = _pytest_version(tox_environment, group)
            optional_versions = _optional_versions(tox_environment)
            assert isinstance(python_version, str) and python_version, cell_record
            assert isinstance(runtime, str) and runtime, cell_record
            assert isinstance(expected_platform, str) and expected_platform in _PLATFORM_NAMES, cell_record
            platform_name = _PLATFORM_NAMES[expected_platform]
            environment: dict[str, Any] = {
                "git_sha": context.git_sha,
                "job": job,
                "cell": cell_id,
                "group": group,
                "tox_environment": tox_environment,
                "command": ["tox", "run", "--result-json", "tox-result.json", "-e", tox_environment],
                "outcome": "passed",
                "returncode": 0,
                "runtime": runtime,
                "python": f"{python_version}.0",
                "pytest": pytest_version,
                "selected_tests": 1 if group in _TEST_GROUPS else None,
                "passed_tests": 1 if group in _TEST_GROUPS else None,
                "optional_versions": optional_versions,
                "platform": f"synthetic-{expected_platform}",
                "platform_name": platform_name,
                "result_json": f"tox-results/{tox_environment}.json",
                "tox_result": _tox_result(
                    tox_environment,
                    runtime,
                    python_version,
                    platform_name,
                    pytest_version,
                    optional_versions,
                ),
            }
            artifact_path = input_directory / f"evidence-{artifact_index:04d}.json"
            artifact_index += 1
            document = {
                "schema_version": 1,
                "git_sha": context.git_sha,
                "job": job,
                "cell": cell_id,
                "outcome": "passed",
                "environments": [environment],
            }
            artifact_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            context.artifacts.append(
                EvidenceArtifact(
                    path=artifact_path,
                    job=job,
                    cell=cell_id,
                    tox_environment=tox_environment,
                    group=group,
                )
            )
    assert context.artifacts, "the inventory must produce evidence artifacts"
    return context


def _first_test_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    artifact = next((item for item in context.artifacts if item.group in _TEST_GROUPS), None)
    assert artifact is not None, "the inventory must contain a serial, parallel, e2e, or external test environment"
    return artifact


def _mutate_environment(artifact: EvidenceArtifact, mutation: Any) -> None:
    document = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert isinstance(document, dict), document
    environments = document.get("environments")
    assert isinstance(environments, list) and len(environments) == 1, document
    environment = environments[0]
    assert isinstance(environment, dict), environment
    mutation(environment)
    artifact.path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _summary(context: ProofAggregationContext) -> dict[str, Any]:
    summary = context.summary
    assert isinstance(summary, dict), "the aggregator must write its JSON summary"
    return summary


def _group_records(context: ProofAggregationContext) -> dict[str, dict[str, Any]]:
    groups = _summary(context).get("groups")
    assert isinstance(groups, dict), groups
    return groups


@given(
    "evidence artifacts are synthesized from every job cell and tox environment in the inventory",
    target_fixture="proof_aggregation",
)
def synthesize_inventory_proof_artifacts(request: Any, tmp_path: Path) -> ProofAggregationContext:
    return _synthesize_context(Path(request.config.rootpath), tmp_path)


@given("one expected environment is missing from the artifacts")
def omit_expected_environment_from_proof(proof_aggregation: ProofAggregationContext) -> None:
    artifact = proof_aggregation.artifacts.pop()
    artifact.path.unlink()


@given("one test-group environment records zero selected tests")
def zero_selected_tests_for_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.__setitem__("selected_tests", 0))


@given("one test-group environment has selected tests but none passed")
def zero_passed_tests_for_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.__setitem__("passed_tests", 0))


@given("one test-group environment omits its selected test count")
def omit_selected_tests_for_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("selected_tests", None))


@given("one expected environment artifact is duplicated")
def duplicate_expected_environment_artifact(proof_aggregation: ProofAggregationContext) -> None:
    artifact = proof_aggregation.artifacts[0]
    duplicate_path = proof_aggregation.input_directory / "evidence-duplicate.json"
    duplicate_path.write_text(artifact.path.read_text(encoding="utf-8"), encoding="utf-8")


@given("one environment is assigned to the wrong proof group")
def assign_environment_to_wrong_group(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.__setitem__("group", "wrong-group"))


@given("one environment records a different commit SHA")
def assign_wrong_sha_to_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.__setitem__("git_sha", _OTHER_SHA))


@given("one environment omits its resolved tox command")
def omit_resolved_tox_command(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("command", None))


@given("one test-group environment omits its actual pytest version")
def omit_actual_pytest_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("pytest", None))


@given("the quality environment py314-pytestlatest-mypy omits its actual pytest version")
def omit_latest_pytest_version_from_quality_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (
            item
            for item in proof_aggregation.artifacts
            if item.tox_environment == "py314-pytestlatest-mypy"
        ),
        None,
    )
    assert artifact is not None, "the inventory must include quality tox environment py314-pytestlatest-mypy"
    assert artifact.group == "quality", artifact
    _mutate_environment(artifact, lambda environment: environment.pop("pytest", None))


@given("one environment records a pytest version that disagrees with its tox factor")
def assign_pytest_version_mismatching_tox_factor(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (
            item
            for item in proof_aggregation.artifacts
            if re.search(r"(?:^|-)pytest\d{2}(?:-|$)", item.tox_environment)
        ),
        None,
    )
    assert artifact is not None, "the inventory must contain an explicit numeric pytest tox factor"
    _mutate_environment(artifact, lambda environment: environment.__setitem__("pytest", "0.0.0"))


@given("one environment records runtime Python and platform that disagree with inventory")
def assign_runtime_python_and_platform_mismatches(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        environment["runtime"] = "Jython"
        environment["python"] = "0.0.0"
        environment["platform_name"] = "other-platform"

    _mutate_environment(artifact, mutate)


@given("one parallel environment is missing its required pytest-xdist package")
def remove_required_pytest_xdist_from_parallel_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next((item for item in proof_aggregation.artifacts if item.group == "parallel"), None)
    assert artifact is not None, "the inventory must contain a parallel environment"

    def mutate(environment: dict[str, Any]) -> None:
        optional_versions = environment["optional_versions"]
        optional_versions["pytest-xdist"] = None
        tox_result = environment["tox_result"]
        tox_entry = tox_result["testenvs"][artifact.tox_environment]
        tox_entry["installed_packages"] = [
            package
            for package in tox_entry["installed_packages"]
            if package.partition("==")[0].casefold() != "pytest-xdist"
        ]

    _mutate_environment(artifact, mutate)


@given("one environment has no matching successful tox result entry")
def remove_matching_tox_result_entry(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        tox_result = environment["tox_result"]
        testenvs = tox_result["testenvs"]
        testenvs.pop(artifact.tox_environment, None)

    _mutate_environment(artifact, mutate)


@given("the Playwright report environment is missing requested tox-installed extras")
def remove_playwright_report_tox_extras(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.tox_environment == _PLAYWRIGHT_REPORT_ENV),
        None,
    )
    assert artifact is not None, f"the inventory must contain {_PLAYWRIGHT_REPORT_ENV}"
    assert artifact.group == "e2e", artifact

    def mutate(environment: dict[str, Any]) -> None:
        for package in _PLAYWRIGHT_REPORT_PACKAGES:
            environment["optional_versions"][package] = None
        result_entry = environment["tox_result"]["testenvs"][artifact.tox_environment]
        result_entry["installed_packages"] = [
            package
            for package in result_entry["installed_packages"]
            if package.partition("==")[0].casefold() not in _PLAYWRIGHT_REPORT_PACKAGES
        ]

    _mutate_environment(artifact, mutate)


@given("one tox test result has a zero return code but no command")
def remove_command_from_successful_tox_test_result(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        result_entry = environment["tox_result"]["testenvs"][artifact.tox_environment]
        test_result = result_entry["test"][0]
        test_result.pop("command", None)

    _mutate_environment(artifact, mutate)


@given("one successful tox test command contains an empty string argument")
def add_empty_argument_to_successful_tox_test_command(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        result_entry = environment["tox_result"]["testenvs"][artifact.tox_environment]
        command = result_entry["test"][0]["command"]
        command.insert(1, "")

    _mutate_environment(artifact, mutate)


@when("I run the full environment proof aggregator", target_fixture="proof_aggregation_result")
def run_full_environment_proof_aggregator(
    proof_aggregation: ProofAggregationContext,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "scripts/aggregate_env_evidence.py",
        "--input-dir",
        str(proof_aggregation.input_directory),
        "--inventory",
        str(proof_aggregation.inventory_path),
        "--sha",
        proof_aggregation.git_sha,
        "--output",
        str(proof_aggregation.output_path),
    ]
    result = subprocess.run(
        command,
        cwd=proof_aggregation.project_root,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proof_aggregation.output_path.is_file(), (
        f"the aggregator did not write its summary; command={command!r}; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    payload = json.loads(proof_aggregation.output_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), payload
    proof_aggregation.summary = payload
    return result


@then("the proof summary should pass and include every inventory environment")
def proof_summary_passes_with_every_inventory_environment(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    summary = _summary(proof_aggregation)
    expected_count = len(proof_aggregation.artifacts)
    assert proof_aggregation_result.returncode == 0, (
        f"full inventory proof should pass:\n{proof_aggregation_result.stdout}\n{proof_aggregation_result.stderr}"
    )
    assert summary.get("outcome") == "passed", summary
    assert summary.get("git_sha") == proof_aggregation.git_sha, summary
    assert summary.get("environment_count") == expected_count, summary
    assert summary.get("expected_environment_count") == expected_count, summary


@then("the proof summary should report serial parallel e2e external and quality groups")
def proof_summary_reports_all_inventory_groups(proof_aggregation: ProofAggregationContext) -> None:
    groups = _group_records(proof_aggregation)
    assert set(groups) == set(_EXPECTED_GROUPS), groups
    for group in _EXPECTED_GROUPS:
        report = groups[group]
        assert report.get("outcome") == "passed", (group, report)
        assert report.get("expectedEnvironmentCount", 0) > 0, (group, report)
        assert report.get("environmentCount") == report.get("expectedEnvironmentCount"), (group, report)


@then("the proof summary should preserve actual evidence for every environment")
def proof_summary_preserves_actual_environment_evidence(proof_aggregation: ProofAggregationContext) -> None:
    summary_environments = _summary(proof_aggregation).get("environments")
    assert isinstance(summary_environments, list), summary_environments
    expected_records: dict[tuple[str, str, str], dict[str, Any]] = {}
    for artifact in proof_aggregation.artifacts:
        document = json.loads(artifact.path.read_text(encoding="utf-8"))
        environment = document["environments"][0]
        expected_records[(artifact.job, artifact.cell, artifact.tox_environment)] = environment

    summarized_records: dict[tuple[str, str, str], dict[str, Any]] = {}
    for environment in summary_environments:
        assert isinstance(environment, dict), environment
        key = (environment.get("job"), environment.get("cell"), environment.get("tox_environment"))
        summarized_records[key] = environment

    assert set(summarized_records) == set(expected_records), set(summarized_records) ^ set(expected_records)
    preserved_fields = (
        "runtime",
        "python",
        "pytest",
        "optional_versions",
        "command",
        "selected_tests",
        "passed_tests",
        "platform_name",
    )
    for key, expected in expected_records.items():
        actual = summarized_records[key]
        for field_name in preserved_fields:
            assert actual.get(field_name) == expected.get(field_name), (key, field_name, actual, expected)
        optional_versions = actual.get("optional_versions")
        assert isinstance(optional_versions, dict), (key, actual)
        assert set(optional_versions) == set(_OPTIONAL_VERSION_KEYS), (key, optional_versions)
        if expected["group"] in _TEST_GROUPS:
            assert isinstance(actual.get("pytest"), str), (key, actual)
            assert actual.get("selected_tests", 0) > 0, (key, actual)
            assert actual.get("passed_tests", 0) > 0, (key, actual)


@then("the proof summary should fail with a missing environment diagnostic")
def proof_summary_fails_for_missing_environment(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "missing evidence for expected environment" in proof_aggregation_result.stderr


@then("the proof summary should fail with a selected no tests diagnostic")
def proof_summary_fails_for_empty_test_selection(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "selected no tests" in proof_aggregation_result.stderr


@then("the proof summary should fail with a duplicate evidence diagnostic")
def proof_summary_fails_for_duplicate_evidence(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "duplicate evidence for expected environment" in proof_aggregation_result.stderr


@then("the proof summary should fail with a group mismatch diagnostic")
def proof_summary_fails_for_wrong_group(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "is labeled 'wrong-group'" in proof_aggregation_result.stderr


@then("the proof summary should fail with a SHA mismatch diagnostic")
def proof_summary_fails_for_wrong_sha(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "has a mismatched SHA" in proof_aggregation_result.stderr


@then("the proof summary should fail with a missing resolved command diagnostic")
def proof_summary_fails_for_missing_resolved_command(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "is missing a resolved tox command" in proof_aggregation_result.stderr


@then("the proof summary should fail with a missing actual pytest version diagnostic")
def proof_summary_fails_for_missing_actual_pytest_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "is missing an actual pytest version" in proof_aggregation_result.stderr


@then("the proof summary should fail with a pytest tox factor mismatch diagnostic")
def proof_summary_fails_for_pytest_tox_factor_mismatch(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "tox factor requires" in proof_aggregation_result.stderr


@then("the proof summary should fail with runtime Python and platform mismatch diagnostics")
def proof_summary_fails_for_runtime_python_and_platform_mismatches(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    for diagnostic in (
        "reports runtime 'Jython'",
        "reports Python '0.0.0'",
        "reports platform 'other-platform'",
    ):
        assert diagnostic in proof_aggregation_result.stderr


@then("the proof summary should fail with a no tests passed diagnostic")
def proof_summary_fails_when_no_selected_tests_passed(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "selected no tests that passed" in proof_aggregation_result.stderr


@then("the proof summary should fail with a missing pytest-xdist diagnostic")
def proof_summary_fails_for_missing_required_pytest_xdist(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires installed optional package 'pytest-xdist'" in proof_aggregation_result.stderr


@then("the proof summary should fail with a successful tox result entry diagnostic")
def proof_summary_fails_for_missing_successful_tox_result_entry(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "successful tox result entry" in proof_aggregation_result.stderr


@then("the proof summary should fail for missing Playwright report extras")
def proof_summary_fails_for_missing_playwright_report_extras(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    for package in _PLAYWRIGHT_REPORT_PACKAGES:
        assert f"requires installed optional package '{package}'" in proof_aggregation_result.stderr


@then("the proof summary should fail for a missing tox result command")
def proof_summary_fails_for_missing_tox_result_command(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "command evidence" in proof_aggregation_result.stderr
