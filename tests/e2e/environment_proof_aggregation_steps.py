"""BDD acceptance steps for the inventory-driven full proof aggregator."""

from __future__ import annotations

import importlib
import io
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pytest_cuke import given, parsers, then, when


_EXPECTED_GROUPS = ("serial", "parallel", "e2e", "external", "quality", "optional")
_TEST_GROUPS = frozenset(("serial", "parallel", "e2e", "external", "optional"))
_OPTIONAL_VERSION_KEYS = (
    "allure-pytest",
    "gherkin-official",
    "hjson",
    "json5",
    "mcp",
    "mcp-pdb",
    "pandoc",
    "panflute",
    "playwright",
    "pycmarkgfm",
    "pydantic",
    "pypandoc",
    "pyhocon",
    "pytest-xdist",
    "PyYAML",
    "uvicorn",
)
_DEBUG_MCP_ENV = "py314-debug-mcp"
_DEBUG_MCP_PACKAGES = ("mcp", "mcp-pdb", "pydantic", "uvicorn")
_STRUCT_BDD_ENV = "py314-struct-bdd"
_STRUCT_BDD_PACKAGES = ("hjson", "json5", "pyhocon", "PyYAML")
_PLAYWRIGHT_REPORT_ENV = "py314-pytestlatest-playwright-report"
_PLAYWRIGHT_REPORT_PACKAGES = ("allure-pytest", "pytest-xdist", "gherkin-official", "playwright")
_DOC_GENERATION_PACKAGES = ("pandoc", "panflute", "pycmarkgfm", "pypandoc")
_FORMATTER_SYSTEM_TOOL_VERSION_KEYS = ("node", "npm", "npx", "allure-cli", "uv")
_NATIVE_SYSTEM_TOOL_VERSION_KEYS = ("go", "native-compiler")
_SYSTEM_TOOL_VERSION_KEYS = ("tox", *_FORMATTER_SYSTEM_TOOL_VERSION_KEYS, "pandoc", *_NATIVE_SYSTEM_TOOL_VERSION_KEYS)
_PLATFORM_NAMES = {"linux": "linux", "macos": "darwin", "windows": "win32"}
_REMOTE_MODES = {"remote-socket": "socket", "remote-via": "via", "remote-ssh": "ssh"}
_PROOF_SHA = "a" * 40
_OTHER_SHA = "b" * 40
_PRODUCT_ROOT = Path(__file__).resolve().parents[2]
_required_system_tool_versions = runpy.run_path(str(_PRODUCT_ROOT / "scripts" / "environment_evidence.py"))[
    "required_system_tool_versions"
]


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
    if job == "optional-integrations":
        return "optional"
    if "doc-gen" in tox_environment:
        return "serial"
    if job == "full-matrix":
        return "parallel" if "xdist" in tox_environment else "serial"
    if job in {"browser-report", "live-formatters-acceptance", "native-go-parser"}:
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
    is_doc_generation = "doc-gen" in tox_environment
    has_gherkin_factor = "gherkin33" in tox_environment or "gherkinlatest" in tox_environment
    is_debug_mcp = tox_environment == _DEBUG_MCP_ENV
    is_struct_bdd = tox_environment == _STRUCT_BDD_ENV
    return {
        "allure-pytest": "2.16.2" if "allure" in tox_environment or is_playwright_report else None,
        "gherkin-official": "33.0.0" if has_gherkin_factor or is_playwright_report else "29.0.0",
        "hjson": "3.1.0" if is_struct_bdd else None,
        "json5": "0.15.0" if is_struct_bdd else None,
        "mcp": "1.24.2" if is_debug_mcp else None,
        "mcp-pdb": "0.6.2" if is_debug_mcp else None,
        "pandoc": "2.4.1" if is_doc_generation else None,
        "panflute": "2.3.0" if is_doc_generation else None,
        "playwright": "1.63.0" if "playwright" in tox_environment else None,
        "pycmarkgfm": "1.2.0" if is_doc_generation else None,
        "pydantic": "2.12.5" if is_debug_mcp else None,
        "pypandoc": "1.15" if is_doc_generation else None,
        "pyhocon": "0.3.63" if is_struct_bdd else None,
        "pytest-xdist": "3.8.0" if "xdist" in tox_environment or is_playwright_report else None,
        "PyYAML": "6.0.3" if is_struct_bdd else None,
        "uvicorn": "0.34.0" if is_debug_mcp else None,
    }


def _actual_python_version(inventory_version: str) -> str:
    return inventory_version if re.fullmatch(r"\d+\.\d+\.\d+", inventory_version) else f"{inventory_version}.0"


def _system_tool_versions(tox_environment: str, platform_name: str | None = None) -> dict[str, str | None]:
    versions: dict[str, str | None] = dict.fromkeys(_SYSTEM_TOOL_VERSION_KEYS, None)
    versions["tox"] = "4.25.0"
    if "doc-gen" in tox_environment:
        versions["pandoc"] = "3.6.4"
    if "uv" in _required_system_tool_versions(tox_environment):
        versions["uv"] = "0.8.22"
    if (
        "live-formatters-acceptance" in tox_environment
        or "allure" in tox_environment
        or "playwright-report" in tox_environment
    ):
        versions.update(
            {
                "node": "v22.20.0",
                "npm": "10.9.3",
                "npx": "10.9.3",
                "allure-cli": "3.20.0",
            }
        )
    if "native-go-parser" in tox_environment:
        versions.update(
            {
                "go": "go1.24.2",
                "native-compiler": "17.0.0" if platform_name == "macos" else "14.2.0",
            }
        )
    return versions


def _system_tool_commands(tox_environment: str, platform_name: str) -> dict[str, dict[str, Any] | None]:
    commands: dict[str, dict[str, Any] | None] = dict.fromkeys(_SYSTEM_TOOL_VERSION_KEYS, None)

    def record(tool: str, executable: str, arguments: list[str]) -> None:
        commands[tool] = {"executable": executable, "argv": [executable, *arguments]}

    tox_executable = _host_tox_executable(platform_name)
    record("tox", tox_executable, ["--version"])

    if "doc-gen" in tox_environment:
        pandoc = (
            r"C:\Program Files\Pandoc\pandoc.exe"
            if platform_name == "windows"
            else ("/opt/homebrew/bin/pandoc" if platform_name == "macos" else "/usr/bin/pandoc")
        )
        record("pandoc", pandoc, ["--version"])
    if (
        "live-formatters-acceptance" in tox_environment
        or "allure" in tox_environment
        or "playwright-report" in tox_environment
    ):
        for tool, executable, arguments in (
            ("node", "node", ["--version"]),
            ("npm", "npm", ["--version"]),
            ("npx", "npx", ["--version"]),
            ("allure-cli", "npx", ["--yes", "allure@3.20.0", "--version"]),
        ):
            if platform_name == "windows":
                suffix = ".exe" if executable == "node" else ".cmd"
                resolved = rf"C:\Program Files\nodejs\{executable}{suffix}"
            elif platform_name == "macos":
                resolved = f"/opt/homebrew/bin/{executable}"
            else:
                resolved = f"/usr/bin/{executable}"
            record(tool, resolved, arguments)
    if "uv" in _required_system_tool_versions(tox_environment):
        if platform_name == "windows":
            uv_executable = rf"C:\synthetic\project\.tox\{tox_environment}\Scripts\uv.exe"
        else:
            uv_executable = f"/synthetic/project/.tox/{tox_environment}/bin/uv"
        record("uv", uv_executable, ["--version"])
    if "native-go-parser" in tox_environment:
        if platform_name == "windows":
            record("go", r"C:\Go\bin\go.exe", ["version"])
            record("native-compiler", r"C:\msys64\mingw64\bin\gcc.exe", ["--version"])
        else:
            record("go", "/usr/local/go/bin/go", ["version"])
            compiler = "/usr/bin/cc"
            record("native-compiler", compiler, ["--version"])
    return commands


def _host_tox_executable(platform_name: str) -> str:
    if platform_name == "windows":
        return r"C:\host\Python\Scripts\tox.exe"
    if platform_name == "macos":
        return "/host/python/bin/tox"
    return "/usr/local/bin/tox"


def _remote_worker_runs(
    cell_id: str,
    runtime: str,
    python_version: str,
    pytest_version: str | None,
    xdist_version: str | None,
) -> list[dict[str, Any]]:
    mode = _REMOTE_MODES.get(cell_id)
    assert mode is not None, f"unknown remote transport cell {cell_id!r}"
    assert isinstance(pytest_version, str) and pytest_version, "remote worker evidence needs pytest"
    assert isinstance(xdist_version, str) and xdist_version, "remote worker evidence needs pytest-xdist"
    worker = {
        "runtime": runtime,
        "python": f"{python_version}.0",
        "pytest": pytest_version,
        "pytest-xdist": xdist_version,
    }
    return [
        {
            "mode": mode,
            "partial": partial,
            "workers": [{"worker_id": worker_id, **worker} for worker_id in ("gw0", "gw1")],
        }
        for partial in (False, True)
    ]


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
                "command": [
                    _host_tox_executable(expected_platform),
                    "run",
                    "--result-json",
                    "tox-result.json",
                    "-e",
                    tox_environment,
                ],
                "outcome": "passed",
                "returncode": 0,
                "runtime": runtime,
                "python": _actual_python_version(python_version),
                "pytest": pytest_version,
                "architecture": "x86_64",
                "job_url": f"https://github.com/example/project/actions/runs/123456/job/{2000 + artifact_index}",
                "run_url": "https://github.com/example/project/actions/runs/123456",
                "selected_tests": 1 if group in _TEST_GROUPS else None,
                "passed_tests": 1 if group in _TEST_GROUPS else None,
                "optional_versions": optional_versions,
                "system_tool_versions": _system_tool_versions(tox_environment, expected_platform),
                "system_tool_commands": _system_tool_commands(tox_environment, expected_platform),
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
            if job == "remote":
                environment["remote_worker_runs"] = _remote_worker_runs(
                    cell_id,
                    runtime,
                    python_version,
                    pytest_version,
                    optional_versions.get("pytest-xdist"),
                )
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


def _first_required_runtime_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    artifact = next((item for item in context.artifacts if item.job == "full-matrix"), None)
    assert artifact is not None, "the inventory must contain a required runtime environment"
    return artifact


def _optional_allure_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    artifact = next(
        (
            item
            for item in context.artifacts
            if item.job == "optional-integrations" and "allure" in item.tox_environment
        ),
        None,
    )
    assert artifact is not None, "the inventory must contain the optional Allure integration environment"
    return artifact


def _exact_interpreter_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    cells = _load_cells(context.inventory_path)
    exact_cell_ids = {
        cell.get("id")
        for cell in cells
        if cell.get("job") == "full-matrix" and cell.get("expected_interpreter") == "3.15.0"
    }
    assert exact_cell_ids, "the inventory must declare exact CPython 3.15.0 runtime cells"
    artifact = next((item for item in context.artifacts if item.cell in exact_cell_ids), None)
    assert artifact is not None, "the exact CPython 3.15.0 runtime cell must have an evidence artifact"
    return artifact


def _graalpy_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    artifact = next(
        (item for item in context.artifacts if item.job == "full-matrix" and item.cell.startswith("graalpy-")),
        None,
    )
    assert artifact is not None, "the inventory must contain the required GraalPy runtime"
    return artifact


def _first_remote_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    artifact = next((item for item in context.artifacts if item.job == "remote"), None)
    assert artifact is not None, "the inventory must contain a remote transport environment"
    return artifact


def _first_native_parser_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    artifact = next((item for item in context.artifacts if item.job == "native-go-parser"), None)
    assert artifact is not None, "the inventory must contain a native Go parser environment"
    return artifact


def _tox_environment_artifact(context: ProofAggregationContext, tox_environment: str) -> EvidenceArtifact:
    artifact = next((item for item in context.artifacts if item.tox_environment == tox_environment), None)
    assert artifact is not None, f"the inventory must contain tox environment {tox_environment!r}"
    return artifact


def _doc_generation_artifact(context: ProofAggregationContext) -> EvidenceArtifact:
    inventory = yaml.safe_load(context.inventory_path.read_text(encoding="utf-8"))
    assert isinstance(inventory, dict), inventory
    lanes = inventory.get("lanes")
    assert isinstance(lanes, list), lanes
    matches = [lane for lane in lanes if isinstance(lane, dict) and lane.get("capability") == "doc-generation"]
    assert len(matches) == 1, f"expected one doc-generation lane, found {matches}"
    tox_environment = matches[0].get("tox_env")
    assert isinstance(tox_environment, str) and tox_environment, matches[0]
    artifact = next((item for item in context.artifacts if item.tox_environment == tox_environment), None)
    assert artifact is not None, (
        f"the inventory has no proof artifact for doc-generation environment {tox_environment!r}"
    )
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


def _mutate_first_remote_worker(artifact: EvidenceArtifact, mutation: Any) -> None:
    def mutate(environment: dict[str, Any]) -> None:
        runs = environment.get("remote_worker_runs")
        assert isinstance(runs, list) and runs, environment
        complete_run = next((run for run in runs if isinstance(run, dict) and run.get("partial") is False), None)
        assert isinstance(complete_run, dict), runs
        workers = complete_run.get("workers")
        assert isinstance(workers, list) and workers, complete_run
        worker = workers[0]
        assert isinstance(worker, dict), worker
        mutation(worker)

    _mutate_environment(artifact, mutate)


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


@given("one remote environment omits actual worker runtime evidence")
def omit_remote_worker_runtime_evidence(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_remote_artifact(proof_aggregation)
    _mutate_environment(
        artifact,
        lambda environment: environment.pop("remote_worker_runs", None),
    )


@given("one remote worker omits its runtime and Python versions")
def omit_remote_worker_runtime_versions(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_remote_artifact(proof_aggregation)

    def mutate(worker: dict[str, Any]) -> None:
        worker.pop("runtime", None)
        worker.pop("python", None)

    _mutate_first_remote_worker(artifact, mutate)


@given("one remote worker reports runtime and Python versions that disagree with the inventory")
def mismatch_remote_worker_runtime_versions(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_remote_artifact(proof_aggregation)

    def mutate(worker: dict[str, Any]) -> None:
        worker["runtime"] = "Jython"
        worker["python"] = "0.0.0"

    _mutate_first_remote_worker(artifact, mutate)


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


@given("one required runtime environment omits its architecture")
def omit_required_runtime_architecture(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_required_runtime_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("architecture", None))


@given("one required runtime environment reports an invalid architecture")
def report_invalid_required_runtime_architecture(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_required_runtime_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.__setitem__("architecture", "../unknown"))


@given("one required runtime environment omits its workflow job link")
def omit_required_runtime_job_link(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_required_runtime_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("job_url", None))


@given("CPython 3.15.0 reports a different patch version")
def mismatch_exact_interpreter_patch_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _exact_interpreter_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        environment["python"] = "3.15.1"
        tox_result = environment.get("tox_result")
        assert isinstance(tox_result, dict), environment
        testenvs = tox_result.get("testenvs")
        assert isinstance(testenvs, dict), tox_result
        entry = testenvs.get(artifact.tox_environment)
        assert isinstance(entry, dict), testenvs
        python = entry.get("python")
        assert isinstance(python, dict), entry
        python["version_info"] = [3, 15, 1, "final", 0]

    _mutate_environment(artifact, mutate)


@given("one environment records a job link from another workflow run")
def mismatch_environment_workflow_run_link(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_required_runtime_artifact(proof_aggregation)
    _mutate_environment(
        artifact,
        lambda environment: environment.__setitem__(
            "job_url", "https://github.com/example/project/actions/runs/999999/job/2999"
        ),
    )


@given("GraalPy tox results identify their implementation as GraalVM")
def graalpy_tox_implementation_uses_graalvm_identity(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _graalpy_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        tox_result = environment.get("tox_result")
        assert isinstance(tox_result, dict), environment
        testenvs = tox_result.get("testenvs")
        assert isinstance(testenvs, dict), tox_result
        entry = testenvs.get(artifact.tox_environment)
        assert isinstance(entry, dict), testenvs
        python = entry.get("python")
        assert isinstance(python, dict), entry
        python["implementation"] = "GraalVM"

    _mutate_environment(artifact, mutate)


@given("one environment omits its resolved tox command")
def omit_resolved_tox_command(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("command", None))


@given("one environment omits its host tox version and resolved command")
def omit_host_tox_system_tool_evidence(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        commands = environment.get("system_tool_commands")
        assert isinstance(versions, dict) and isinstance(commands, dict), environment
        versions["tox"] = None
        commands["tox"] = None

    _mutate_environment(artifact, mutate)


@given("one test-group environment omits its actual pytest version")
def omit_actual_pytest_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)
    _mutate_environment(artifact, lambda environment: environment.pop("pytest", None))


@given("the quality environment py314-pytestlatest-mypy omits its actual pytest version")
def omit_latest_pytest_version_from_quality_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.tox_environment == "py314-pytestlatest-mypy"),
        None,
    )
    assert artifact is not None, "the inventory must include quality tox environment py314-pytestlatest-mypy"
    assert artifact.group == "quality", artifact
    _mutate_environment(artifact, lambda environment: environment.pop("pytest", None))


@given("one environment records a pytest version that disagrees with its tox factor")
def assign_pytest_version_mismatching_tox_factor(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if re.search(r"(?:^|-)pytest\d{2}(?:-|$)", item.tox_environment)),
        None,
    )
    assert artifact is not None, "the inventory must contain an explicit numeric pytest tox factor"
    _mutate_environment(artifact, lambda environment: environment.__setitem__("pytest", "0.0.0"))


@given("the latest pytest environment py314-pytestlatest-coverage-lin records pytest 8 consistently")
def assign_consistent_pytest_8_to_latest_tox_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _tox_environment_artifact(proof_aggregation, "py314-pytestlatest-coverage-lin")

    def mutate(environment: dict[str, Any]) -> None:
        pytest_version = "8.4.2"
        environment["pytest"] = pytest_version
        tox_result = environment.get("tox_result")
        assert isinstance(tox_result, dict), environment
        testenvs = tox_result.get("testenvs")
        assert isinstance(testenvs, dict), tox_result
        result = testenvs.get(artifact.tox_environment)
        assert isinstance(result, dict), testenvs
        installed_packages = result.get("installed_packages")
        assert isinstance(installed_packages, list), result
        pytest_packages = [
            index
            for index, package in enumerate(installed_packages)
            if isinstance(package, str) and package.partition("==")[0].casefold() == "pytest"
        ]
        assert len(pytest_packages) == 1, installed_packages
        installed_packages[pytest_packages[0]] = f"pytest=={pytest_version}"

    _mutate_environment(artifact, mutate)


@given("one environment records runtime Python and platform that disagree with inventory")
def assign_runtime_python_and_platform_mismatches(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_test_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        environment["runtime"] = "Jython"
        environment["python"] = "0.0.0"
        environment["platform_name"] = "other-platform"

    _mutate_environment(artifact, mutate)


@given("one optional xdist environment is missing its pytest-xdist package")
def remove_pytest_xdist_from_optional_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.group == "optional" and "xdist" in item.tox_environment),
        None,
    )
    assert artifact is not None, "the inventory must contain an optional xdist environment"

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


@given("the optional StructBDD environment is missing its JSON5 loader")
def remove_json5_from_optional_struct_bdd_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.tox_environment == _STRUCT_BDD_ENV),
        None,
    )
    assert artifact is not None, f"the inventory must contain {_STRUCT_BDD_ENV}"

    def mutate(environment: dict[str, Any]) -> None:
        optional_versions = environment["optional_versions"]
        assert isinstance(optional_versions.get("json5"), str) and optional_versions["json5"], optional_versions
        optional_versions["json5"] = None
        tox_result = environment["tox_result"]
        tox_entry = tox_result["testenvs"][artifact.tox_environment]
        tox_entry["installed_packages"] = [
            package
            for package in tox_entry["installed_packages"]
            if re.sub(r"[-_.]+", "-", package.partition("==")[0]).casefold() != "json5"
        ]

    _mutate_environment(artifact, mutate)


@given("the optional StructBDD environment omits its required tox-local uv version")
def remove_uv_from_optional_struct_bdd_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.tox_environment == _STRUCT_BDD_ENV),
        None,
    )
    assert artifact is not None, f"the inventory must contain {_STRUCT_BDD_ENV}"

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment["system_tool_versions"]
        assert isinstance(versions.get("uv"), str) and versions["uv"], versions
        versions["uv"] = None

    _mutate_environment(artifact, mutate)


@given("the optional Debug MCP environment is missing its MCP package")
def remove_mcp_from_optional_debug_mcp_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.tox_environment == _DEBUG_MCP_ENV),
        None,
    )
    assert artifact is not None, f"the inventory must contain {_DEBUG_MCP_ENV}"

    def mutate(environment: dict[str, Any]) -> None:
        optional_versions = environment["optional_versions"]
        assert isinstance(optional_versions.get("mcp"), str) and optional_versions["mcp"], optional_versions
        optional_versions["mcp"] = None
        tox_result = environment["tox_result"]
        tox_entry = tox_result["testenvs"][artifact.tox_environment]
        tox_entry["installed_packages"] = [
            package
            for package in tox_entry["installed_packages"]
            if re.sub(r"[-_.]+", "-", package.partition("==")[0]).casefold() != "mcp"
        ]

    _mutate_environment(artifact, mutate)


@given("the optional Debug MCP environment omits its required tox-local uv version")
def remove_uv_from_optional_debug_mcp_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.tox_environment == _DEBUG_MCP_ENV),
        None,
    )
    assert artifact is not None, f"the inventory must contain {_DEBUG_MCP_ENV}"

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment["system_tool_versions"]
        assert isinstance(versions.get("uv"), str) and versions["uv"], versions
        versions["uv"] = None

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


@given("the doc-generation environment is missing its recorded optional package versions")
def remove_doc_generation_tox_extras(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _doc_generation_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        optional_versions = environment["optional_versions"]
        result_entry = environment["tox_result"]["testenvs"][artifact.tox_environment]
        for package in _DOC_GENERATION_PACKAGES:
            assert isinstance(optional_versions.get(package), str) and optional_versions[package], optional_versions
            optional_versions[package] = None
        result_entry["installed_packages"] = [
            package
            for package in result_entry["installed_packages"]
            if re.sub(r"[-_.]+", "-", package.partition("==")[0]).casefold() not in _DOC_GENERATION_PACKAGES
        ]

    _mutate_environment(artifact, mutate)


@given("the doc-generation environment omits its required Pandoc CLI version")
def remove_doc_generation_pandoc_cli_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _doc_generation_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        optional_versions = environment["optional_versions"]
        for package in _DOC_GENERATION_PACKAGES:
            assert isinstance(optional_versions.get(package), str) and optional_versions[package], optional_versions
        system_tool_versions = environment.get("system_tool_versions")
        assert isinstance(system_tool_versions, dict), environment
        assert isinstance(system_tool_versions.get("pandoc"), str) and system_tool_versions["pandoc"], (
            system_tool_versions
        )
        system_tool_versions.pop("pandoc")

    _mutate_environment(artifact, mutate)


@given("one live formatter environment omits its required Node.js version")
def omit_live_formatter_node_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.job == "live-formatters-acceptance"),
        None,
    )
    assert artifact is not None, "the inventory must contain a live formatter acceptance environment"

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and isinstance(versions.get("node"), str), environment
        versions.pop("node")

    _mutate_environment(artifact, mutate)


@given("the optional Allure environment omits its Allure CLI version")
def omit_optional_allure_cli_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _optional_allure_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and isinstance(versions.get("allure-cli"), str), environment
        versions["allure-cli"] = None

    _mutate_environment(artifact, mutate)


@given("one live formatter environment omits its required uv version")
def omit_live_formatter_uv_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.job == "live-formatters-acceptance"),
        None,
    )
    assert artifact is not None, "the inventory must contain a live formatter acceptance environment"

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and isinstance(versions.get("uv"), str), environment
        versions["uv"] = None

    _mutate_environment(artifact, mutate)


@given("one live formatter environment records uv outside its tox environment")
def record_live_formatter_uv_outside_tox_environment(proof_aggregation: ProofAggregationContext) -> None:
    artifact = next(
        (item for item in proof_aggregation.artifacts if item.job == "live-formatters-acceptance"),
        None,
    )
    assert artifact is not None, "the inventory must contain a live formatter acceptance environment"

    def mutate(environment: dict[str, Any]) -> None:
        commands = environment.get("system_tool_commands")
        assert isinstance(commands, dict) and isinstance(commands.get("uv"), dict), environment
        commands["uv"] = {"executable": "/usr/bin/uv", "argv": ["/usr/bin/uv", "--version"]}

    _mutate_environment(artifact, mutate)


@given("PyPy acceptance omits its tox-local uv version and xdist omits its uv command")
def omit_acceptance_coverage_uv_evidence(proof_aggregation: ProofAggregationContext) -> None:
    version_artifact = _tox_environment_artifact(proof_aggregation, "pypy312-pytestlatest-coverage-lin")
    command_artifact = _tox_environment_artifact(
        proof_aggregation,
        "py314-pytestlatest-gherkin33-xdist-coverage-lin",
    )
    assert version_artifact != command_artifact

    def omit_version(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and isinstance(versions.get("uv"), str), environment
        versions["uv"] = None

    def omit_command(environment: dict[str, Any]) -> None:
        commands = environment.get("system_tool_commands")
        assert isinstance(commands, dict) and isinstance(commands.get("uv"), dict), environment
        commands["uv"] = None

    _mutate_environment(version_artifact, omit_version)
    _mutate_environment(command_artifact, omit_command)


@given("one native parser environment omits its required Go version")
def omit_native_parser_go_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_native_parser_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and isinstance(versions.get("go"), str), environment
        versions["go"] = None

    _mutate_environment(artifact, mutate)


@given("one native parser environment omits its required compiler version")
def omit_native_parser_compiler_version(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_native_parser_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and isinstance(versions.get("native-compiler"), str), environment
        versions["native-compiler"] = None

    _mutate_environment(artifact, mutate)


@given("one native parser environment omits its resolved Go version command")
def omit_native_parser_go_version_command(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_native_parser_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        commands = environment.get("system_tool_commands")
        assert isinstance(commands, dict) and isinstance(commands.get("go"), dict), environment
        commands.pop("go")

    _mutate_environment(artifact, mutate)


@given("one native parser environment omits its resolved compiler version command")
def omit_native_parser_compiler_version_command(proof_aggregation: ProofAggregationContext) -> None:
    artifact = _first_native_parser_artifact(proof_aggregation)

    def mutate(environment: dict[str, Any]) -> None:
        commands = environment.get("system_tool_commands")
        assert isinstance(commands, dict) and isinstance(commands.get("native-compiler"), dict), environment
        commands.pop("native-compiler")

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


@then("the proof summary should report serial parallel e2e external quality and optional groups")
def proof_summary_reports_all_inventory_groups(proof_aggregation: ProofAggregationContext) -> None:
    groups = _group_records(proof_aggregation)
    assert set(groups) == set(_EXPECTED_GROUPS), groups
    for group in _EXPECTED_GROUPS:
        report = groups[group]
        assert report.get("outcome") == "passed", (group, report)
        if group != "parallel":
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
        "system_tool_versions",
        "system_tool_commands",
        "command",
        "selected_tests",
        "passed_tests",
        "platform_name",
        "architecture",
        "job_url",
        "run_url",
    )
    for key, expected in expected_records.items():
        actual = summarized_records[key]
        for field_name in preserved_fields:
            assert actual.get(field_name) == expected.get(field_name), (key, field_name, actual, expected)
        optional_versions = actual.get("optional_versions")
        assert isinstance(optional_versions, dict), (key, actual)
        assert set(optional_versions) == set(_OPTIONAL_VERSION_KEYS), (key, optional_versions)
        system_tool_versions = actual.get("system_tool_versions")
        assert isinstance(system_tool_versions, dict), (key, actual)
        assert set(system_tool_versions) == set(_SYSTEM_TOOL_VERSION_KEYS), (key, system_tool_versions)
        system_tool_commands = actual.get("system_tool_commands")
        assert isinstance(system_tool_commands, dict), (key, actual)
        assert set(system_tool_commands) == set(_SYSTEM_TOOL_VERSION_KEYS), (key, system_tool_commands)
        if expected["group"] in _TEST_GROUPS:
            assert isinstance(actual.get("pytest"), str), (key, actual)
            assert actual.get("selected_tests", 0) > 0, (key, actual)
            assert actual.get("passed_tests", 0) > 0, (key, actual)


@then("the proof summary should preserve architecture and actual job and run links")
def proof_summary_preserves_architecture_and_workflow_links(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    assert environments, "the proof summary must contain environment evidence"
    for environment in environments:
        assert isinstance(environment, dict), environment
        architecture = environment.get("architecture")
        assert isinstance(architecture, str) and architecture, environment
        job_url = environment.get("job_url")
        run_url = environment.get("run_url")
        assert isinstance(job_url, str) and "/actions/runs/" in job_url and "/job/" in job_url, environment
        assert isinstance(run_url, str) and "/actions/runs/" in run_url, environment


@then("host tox evidence should match each environment's resolved tox run command")
def host_tox_evidence_matches_each_tox_run_command(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    assert len(environments) == len(proof_aggregation.artifacts), (len(environments), proof_aggregation.artifacts)
    for environment in environments:
        assert isinstance(environment, dict), environment
        versions = environment.get("system_tool_versions")
        commands = environment.get("system_tool_commands")
        run_command = environment.get("command")
        assert isinstance(versions, dict) and isinstance(versions.get("tox"), str) and versions.get("tox"), environment
        tox_command = commands.get("tox") if isinstance(commands, dict) else None
        assert isinstance(tox_command, dict), environment
        executable = tox_command.get("executable")
        assert isinstance(executable, str) and executable, tox_command
        assert tox_command.get("argv") == [executable, "--version"], tox_command
        assert isinstance(run_command, list) and run_command[0] == executable, (tox_command, run_command)
        assert "/.tox/" not in executable.replace("\\", "/").casefold(), executable


@then("the proof summary should retain the canonical GraalPy runtime evidence")
def proof_summary_retains_canonical_graalpy_runtime(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    graalpy = [environment for environment in environments if environment.get("runtime") == "GraalPy"]
    assert graalpy, environments
    assert all(environment.get("runtime") == "GraalPy" for environment in graalpy), graalpy


@then("optional integration proof should be separated from core support groups")
def optional_proof_is_separate_from_core_groups(proof_aggregation: ProofAggregationContext) -> None:
    optional = [item for item in proof_aggregation.artifacts if item.job == "optional-integrations"]
    assert optional, "the inventory must declare optional integration proof cells"
    optional_environments = {item.tox_environment for item in optional}
    groups = _group_records(proof_aggregation)
    optional_group = groups.get("optional")
    assert isinstance(optional_group, dict), groups
    assert optional_group.get("outcome") == "passed", optional_group
    assert optional_group.get("expectedEnvironmentCount") == len(optional), optional_group
    assert optional_group.get("environmentCount") == len(optional), optional_group
    assert set(optional_group.get("environments", [])) == optional_environments, optional_group
    for group_name in set(groups) - {"optional"}:
        report = groups[group_name]
        assert not optional_environments.intersection(report.get("environments", [])), (group_name, report)


@then("the proof summary should preserve installed StructBDD loader versions")
def proof_summary_preserves_struct_bdd_loader_versions(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [item for item in environments if item.get("tox_environment") == _STRUCT_BDD_ENV]
    assert len(records) == 1, records
    optional_versions = records[0].get("optional_versions")
    assert isinstance(optional_versions, dict), records[0]
    for package in _STRUCT_BDD_PACKAGES:
        assert isinstance(optional_versions.get(package), str) and optional_versions[package], optional_versions


@then("it should preserve the tox-local uv version for StructBDD")
def proof_summary_preserves_struct_bdd_uv_version(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [item for item in environments if item.get("tox_environment") == _STRUCT_BDD_ENV]
    assert len(records) == 1, records
    record = records[0]
    versions = record.get("system_tool_versions")
    assert isinstance(versions, dict) and isinstance(versions.get("uv"), str) and versions["uv"], record
    commands = record.get("system_tool_commands")
    assert isinstance(commands, dict), record
    uv_command = commands.get("uv")
    assert isinstance(uv_command, dict), record
    uv_executable = uv_command.get("executable")
    assert isinstance(uv_executable, str) and uv_executable, uv_command
    expected_suffix = f"/.tox/{_STRUCT_BDD_ENV}/bin/uv"
    assert uv_executable.replace("\\", "/").casefold().endswith(expected_suffix.casefold()), (
        uv_executable,
        expected_suffix,
    )
    assert uv_command.get("argv") == [uv_executable, "--version"], uv_command


@then("the proof summary should preserve installed Debug MCP package versions")
def proof_summary_preserves_debug_mcp_package_versions(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [item for item in environments if item.get("tox_environment") == _DEBUG_MCP_ENV]
    assert len(records) == 1, records
    optional_versions = records[0].get("optional_versions")
    assert isinstance(optional_versions, dict), records[0]
    for package in _DEBUG_MCP_PACKAGES:
        assert isinstance(optional_versions.get(package), str) and optional_versions[package], optional_versions


@then("it should preserve the tox-local uv version for Debug MCP")
def proof_summary_preserves_debug_mcp_uv_version(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [item for item in environments if item.get("tox_environment") == _DEBUG_MCP_ENV]
    assert len(records) == 1, records
    record = records[0]
    versions = record.get("system_tool_versions")
    assert isinstance(versions, dict) and isinstance(versions.get("uv"), str) and versions["uv"], record
    commands = record.get("system_tool_commands")
    assert isinstance(commands, dict), record
    uv_command = commands.get("uv")
    assert isinstance(uv_command, dict), record
    uv_executable = uv_command.get("executable")
    assert isinstance(uv_executable, str) and uv_executable, uv_command
    expected_suffix = f"/.tox/{_DEBUG_MCP_ENV}/bin/uv"
    assert uv_executable.replace("\\", "/").casefold().endswith(expected_suffix.casefold()), (
        uv_executable,
        expected_suffix,
    )
    assert uv_command.get("argv") == [uv_executable, "--version"], uv_command


@then("the proof summary should fail with a missing StructBDD loader diagnostic")
def proof_summary_fails_for_missing_struct_bdd_loader(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    artifact = next(item for item in proof_aggregation.artifacts if item.tox_environment == _STRUCT_BDD_ENV)
    document = json.loads(artifact.path.read_text(encoding="utf-8"))
    environment = document["environments"][0]
    assert environment["optional_versions"]["json5"] is None, environment
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires installed optional package 'json5'" in proof_aggregation_result.stderr


@then("the proof summary should fail for missing StructBDD uv version evidence")
def proof_summary_fails_for_missing_struct_bdd_uv_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'uv' with an actual version" in proof_aggregation_result.stderr


@then("the proof summary should fail with a missing Debug MCP package diagnostic")
def proof_summary_fails_for_missing_debug_mcp_package(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    artifact = next(item for item in proof_aggregation.artifacts if item.tox_environment == _DEBUG_MCP_ENV)
    document = json.loads(artifact.path.read_text(encoding="utf-8"))
    environment = document["environments"][0]
    assert environment["optional_versions"]["mcp"] is None, environment
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires installed optional package 'mcp'" in proof_aggregation_result.stderr


@then("the proof summary should fail for missing Debug MCP uv version evidence")
def proof_summary_fails_for_missing_debug_mcp_uv_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'uv' with an actual version" in proof_aggregation_result.stderr


@then("the proof summary should preserve Linux Windows and macOS runner evidence")
def proof_summary_preserves_supported_platform_runner_evidence(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    platform_names = {environment.get("platform_name") for environment in environments if isinstance(environment, dict)}
    expected_platforms = {"linux", "win32", "darwin"}
    assert expected_platforms <= platform_names, (expected_platforms, platform_names)


@then("it should preserve passed live formatter acceptance outcomes for Linux macOS and Windows")
def proof_summary_preserves_live_formatter_acceptance_outcomes(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [
        environment
        for environment in environments
        if isinstance(environment, dict) and environment.get("job") == "live-formatters-acceptance"
    ]
    expected = {
        ("live-formatters-linux", "py313-live-formatters-acceptance-lin", "linux"),
        ("live-formatters-macos", "py313-live-formatters-acceptance-mac", "darwin"),
        ("live-formatters-windows", "py313-live-formatters-acceptance-win", "win32"),
    }
    observed = {
        (environment.get("cell"), environment.get("tox_environment"), environment.get("platform_name"))
        for environment in records
    }
    assert observed == expected, (observed, expected)
    assert all(environment.get("group") == "e2e" for environment in records), records
    assert all(environment.get("outcome") == "passed" for environment in records), records
    assert all(environment.get("selected_tests", 0) > 0 for environment in records), records
    assert all(environment.get("passed_tests", 0) > 0 for environment in records), records


@then("it should preserve actual Node npm npx Allure CLI and tox-local uv evidence for live formatters")
def proof_summary_preserves_live_formatter_system_tool_versions(
    proof_aggregation: ProofAggregationContext,
) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [
        environment
        for environment in environments
        if isinstance(environment, dict) and environment.get("job") == "live-formatters-acceptance"
    ]
    assert len(records) == 3, records
    for environment in records:
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict), environment
        for tool in _FORMATTER_SYSTEM_TOOL_VERSION_KEYS:
            assert isinstance(versions.get(tool), str) and versions[tool], (tool, environment)
        commands = environment.get("system_tool_commands")
        assert isinstance(commands, dict), environment
        uv_command = commands.get("uv")
        assert isinstance(uv_command, dict), environment
        uv_executable = uv_command.get("executable")
        assert isinstance(uv_executable, str), environment
        expected_suffix = (
            f"/.tox/{environment['tox_environment']}/scripts/uv.exe"
            if environment.get("platform_name") == "win32"
            else f"/.tox/{environment['tox_environment']}/bin/uv"
        )
        assert uv_executable.replace("\\", "/").casefold().endswith(expected_suffix.casefold()), (
            uv_executable,
            expected_suffix,
        )
        assert uv_command.get("argv") == [uv_executable, "--version"], uv_command


@then("it should preserve Node npm npx Allure CLI and tox-local uv evidence for browser reports")
def proof_summary_preserves_browser_report_system_tool_evidence(
    proof_aggregation: ProofAggregationContext,
) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [
        environment
        for environment in environments
        if isinstance(environment, dict)
        and environment.get("job") == "browser-report"
        and environment.get("tox_environment") == "py314-pytestlatest-playwright-report"
    ]
    assert len(records) == 1, records
    record = records[0]
    versions = record.get("system_tool_versions")
    assert isinstance(versions, dict), record
    for tool in _FORMATTER_SYSTEM_TOOL_VERSION_KEYS:
        assert isinstance(versions.get(tool), str) and versions[tool], (tool, record)
    commands = record.get("system_tool_commands")
    assert isinstance(commands, dict), record
    assert commands["allure-cli"] == {
        "executable": commands["npx"]["executable"],
        "argv": [commands["npx"]["executable"], "--yes", "allure@3.20.0", "--version"],
    }, commands
    uv_command = commands.get("uv")
    assert isinstance(uv_command, dict), record
    uv_executable = uv_command.get("executable")
    assert isinstance(uv_executable, str), record
    expected_suffix = f"/.tox/{record['tox_environment']}/bin/uv"
    assert uv_executable.replace("\\", "/").casefold().endswith(expected_suffix.casefold()), (
        uv_executable,
        expected_suffix,
    )
    assert uv_command.get("argv") == [uv_executable, "--version"], uv_command


@then("core CPython and GraalPy coverage evidence should include tox-local uv")
def proof_summary_core_coverage_includes_tox_local_uv(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    expected_environments = {
        "py314-pytestlatest-coverage-lin",
        "graalpy-253-pytestlatest-coverage-lin",
    }
    records = {
        environment.get("tox_environment"): environment
        for environment in environments
        if isinstance(environment, dict) and environment.get("tox_environment") in expected_environments
    }
    assert set(records) == expected_environments, records
    for name, environment in records.items():
        versions = environment.get("system_tool_versions")
        commands = environment.get("system_tool_commands")
        assert isinstance(versions, dict) and isinstance(versions.get("uv"), str) and versions["uv"], (name, versions)
        assert isinstance(commands, dict), (name, commands)
        uv_command = commands.get("uv")
        assert isinstance(uv_command, dict), (name, commands)
        executable = uv_command.get("executable")
        assert isinstance(executable, str) and executable.replace("\\", "/").endswith(f"/.tox/{name}/bin/uv"), (
            name,
            uv_command,
        )
        assert uv_command.get("argv") == [executable, "--version"], (name, uv_command)


@then("the proof summary should preserve Node npm npx and Allure CLI evidence for optional Allure")
def proof_summary_preserves_optional_allure_system_tool_evidence(
    proof_aggregation: ProofAggregationContext,
) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = [
        environment
        for environment in environments
        if isinstance(environment, dict)
        and environment.get("job") == "optional-integrations"
        and "allure" in environment.get("tox_environment", "")
    ]
    assert len(records) == 1, records
    versions = records[0].get("system_tool_versions")
    assert isinstance(versions, dict), records[0]
    for tool in ("node", "npm", "npx", "allure-cli"):
        assert isinstance(versions.get(tool), str) and versions[tool], (tool, records[0])
    commands = records[0].get("system_tool_commands")
    assert isinstance(commands, dict), records[0]
    assert commands["allure-cli"] == {
        "executable": commands["npx"]["executable"],
        "argv": [commands["npx"]["executable"], "--yes", "allure@3.20.0", "--version"],
    }, commands


@then("the proof summary should fail for missing optional Allure CLI evidence")
def proof_summary_fails_for_missing_optional_allure_cli_evidence(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "optional-integrations" in proof_aggregation_result.stderr
    assert "system tool 'allure-cli'" in proof_aggregation_result.stderr


@then("the proof summary should fail for missing live formatter system tool versions")
def proof_summary_fails_for_missing_live_formatter_system_tool_versions(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'node' with an actual version" in proof_aggregation_result.stderr


@then("the proof summary should fail for missing host tox evidence")
def proof_summary_fails_for_missing_host_tox_evidence(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'tox' with an actual version" in proof_aggregation_result.stderr
    assert "requires system tool 'tox' with its resolved version command" in proof_aggregation_result.stderr


@then("the proof summary should fail for a missing live formatter uv version diagnostic")
def proof_summary_fails_for_missing_live_formatter_uv_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'uv' with an actual version" in proof_aggregation_result.stderr


@then("the proof summary should fail for a uv command outside its tox environment diagnostic")
def proof_summary_fails_for_live_formatter_uv_outside_tox_environment(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'uv' with its resolved version command" in proof_aggregation_result.stderr


@then("the proof summary should fail with actionable acceptance uv diagnostics")
def proof_summary_fails_for_missing_acceptance_uv_evidence(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    version_artifact = _tox_environment_artifact(proof_aggregation, "pypy312-pytestlatest-coverage-lin")
    command_artifact = _tox_environment_artifact(
        proof_aggregation,
        "py314-pytestlatest-gherkin33-xdist-coverage-lin",
    )
    stderr = proof_aggregation_result.stderr
    version_prefix = (
        f"{version_artifact.job}/{version_artifact.cell}/{version_artifact.tox_environment} "
        "requires system tool 'uv' with an actual version; ensure the tox environment installs uv>=0.8"
    )
    command_prefix = (
        f"{command_artifact.job}/{command_artifact.cell}/{command_artifact.tox_environment} "
        "requires system tool 'uv' with its resolved version command; "
        f"record the resolved executable from .tox/{command_artifact.tox_environment}/"
    )
    assert version_prefix in stderr, stderr
    assert command_prefix in stderr, stderr


@then("the proof summary should fail for a missing Go version diagnostic")
def proof_summary_fails_for_missing_native_go_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'go' with an actual version" in proof_aggregation_result.stderr


@then("the proof summary should fail for a missing native compiler version diagnostic")
def proof_summary_fails_for_missing_native_compiler_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'native-compiler' with an actual version" in proof_aggregation_result.stderr


@then("the proof summary should fail for a missing Go version command diagnostic")
def proof_summary_fails_for_missing_native_go_version_command(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'go' with its resolved version command" in proof_aggregation_result.stderr


@then("the proof summary should fail for a missing native compiler version command diagnostic")
def proof_summary_fails_for_missing_native_compiler_version_command(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "requires system tool 'native-compiler' with its resolved version command" in proof_aggregation_result.stderr


@then("it should preserve Go and native compiler versions and commands for Linux macOS and Windows")
def proof_summary_preserves_native_parser_toolchain_evidence(
    proof_aggregation: ProofAggregationContext,
) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    records = {
        (environment.get("cell"), environment.get("platform_name")): environment
        for environment in environments
        if isinstance(environment, dict) and environment.get("job") == "native-go-parser"
    }
    expected_platforms = {
        ("native-linux", "linux"),
        ("native-macos", "darwin"),
        ("native-windows", "win32"),
    }
    assert set(records) == expected_platforms, set(records)
    for key, environment in records.items():
        versions = environment.get("system_tool_versions")
        commands = environment.get("system_tool_commands")
        assert isinstance(versions, dict) and isinstance(commands, dict), (key, environment)
        for tool in _NATIVE_SYSTEM_TOOL_VERSION_KEYS:
            assert isinstance(versions.get(tool), str) and versions[tool], (key, tool, versions)
            command = commands.get(tool)
            assert isinstance(command, dict), (key, tool, commands)
            executable = command.get("executable")
            argv = command.get("argv")
            assert isinstance(executable, str) and executable, (key, tool, command)
            assert isinstance(argv, list) and all(isinstance(part, str) and part for part in argv), (
                key,
                tool,
                command,
            )
            assert argv[0] == executable, (key, tool, command)
            assert argv[-1] == ("version" if tool == "go" else "--version"), (key, tool, command)
        compiler = commands["native-compiler"]["executable"].replace("\\", "/").rsplit("/", maxsplit=1)[-1].casefold()
        if key[1] == "win32":
            assert compiler.removesuffix(".exe") == "gcc", (key, compiler)
        else:
            assert compiler == "cc", (key, compiler)


@when("the live formatter runner captures required system tool versions", target_fixture="formatter_tool_capture")
def capture_live_formatter_system_tool_versions(request: Any, tmp_path: Path, monkeypatch: Any) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(Path(request.config.rootpath) / "scripts"))
    runner = importlib.import_module("run_env_matrix_cell")
    executable_paths = {
        "tox": r"C:\host\Python\Scripts\tox.exe",
        "node": r"C:\Program Files\nodejs\node.exe",
        "npm": r"C:\Program Files\nodejs\npm.cmd",
        "npx": r"C:\Program Files\nodejs\npx.cmd",
    }
    monkeypatch.setattr(runner.shutil, "which", executable_paths.get)
    calls: list[tuple[list[str], dict[str, Any]]] = []
    outputs = {
        ("tox", ("--version",)): "4.25.0 from C:\\host\\Python\\Lib\\site-packages\\tox\\__init__.py\n",
        ("node", ("--version",)): "v22.20.0\n",
        ("npm", ("--version",)): "10.9.3\n",
        ("npx", ("--version",)): "10.9.3\n",
        ("npx", ("--yes", "allure@3.20.0", "--version")): "3.20.0\n",
        ("uv", ("--version",)): "uv 0.8.22 (x86_64-pc-windows-msvc)\n",
    }

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        executable = command[0].replace("\\", "/").rsplit("/", maxsplit=1)[-1].casefold()
        executable = executable.removesuffix(".cmd").removesuffix(".exe")
        output = outputs[(executable, tuple(command[1:]))]
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    tox_environment = "py313-live-formatters-acceptance-win"
    tox_uv = tmp_path / ".tox" / tox_environment / "Scripts" / "uv.exe"
    tox_uv.parent.mkdir(parents=True)
    tox_uv.write_text("synthetic uv executable", encoding="utf-8")
    versions, commands = runner._system_tool_evidence(tox_environment, "win32", project_root=tmp_path)
    return {"versions": versions, "commands": commands, "calls": calls, "tox_uv": tox_uv}


@then("it should record host tox Node npm npx Allure CLI and tox-local uv versions using resolved argv commands")
def formatter_runner_records_required_versions_with_argv(formatter_tool_capture: dict[str, Any]) -> None:
    versions = formatter_tool_capture["versions"]
    assert versions == {
        "tox": "4.25.0",
        "node": "v22.20.0",
        "npm": "10.9.3",
        "npx": "10.9.3",
        "allure-cli": "3.20.0",
        "uv": "0.8.22",
        "pandoc": None,
        "go": None,
        "native-compiler": None,
    }
    commands = formatter_tool_capture["commands"]
    for tool, expected_executable in (
        ("tox", r"C:\host\Python\Scripts\tox.exe"),
        ("node", r"C:\Program Files\nodejs\node.exe"),
        ("npm", r"C:\Program Files\nodejs\npm.cmd"),
        ("npx", r"C:\Program Files\nodejs\npx.cmd"),
        ("allure-cli", r"C:\Program Files\nodejs\npx.cmd"),
        ("uv", str(formatter_tool_capture["tox_uv"])),
    ):
        assert commands[tool] == {
            "executable": expected_executable,
            "argv": [
                expected_executable,
                *(["--yes", "allure@3.20.0", "--version"] if tool == "allure-cli" else ["--version"]),
            ],
        }, (tool, commands)
    calls = formatter_tool_capture["calls"]
    invoked_commands = {
        (
            command[0].replace("\\", "/").rsplit("/", maxsplit=1)[-1].casefold(),
            tuple(command[1:]),
        )
        for command, _kwargs in calls
    }
    assert ("node.exe", ("--version",)) in invoked_commands, invoked_commands
    assert ("tox.exe", ("--version",)) in invoked_commands, invoked_commands
    assert ("npm.cmd", ("--version",)) in invoked_commands, invoked_commands
    assert ("npx.cmd", ("--version",)) in invoked_commands, invoked_commands
    assert ("npx.cmd", ("--yes", "allure@3.20.0", "--version")) in invoked_commands, invoked_commands
    assert (formatter_tool_capture["tox_uv"].name, ("--version",)) in invoked_commands, invoked_commands
    assert commands["uv"]["executable"] == str(formatter_tool_capture["tox_uv"]), commands
    assert all(kwargs.get("shell", False) is False for _command, kwargs in calls), calls


@when(
    "the native parser runner captures toolchain evidence for Linux macOS and Windows",
    target_fixture="native_toolchain_capture",
)
def capture_native_parser_toolchain_evidence(request: Any, monkeypatch: Any) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(Path(request.config.rootpath) / "scripts"))
    runner = importlib.import_module("run_env_matrix_cell")
    tool_paths = {
        "linux": {"tox": "/usr/local/bin/tox", "go": "/usr/local/go/bin/go", "cc": "/usr/bin/cc"},
        "darwin": {"tox": "/opt/homebrew/bin/tox", "go": "/usr/local/go/bin/go", "cc": "/usr/bin/cc"},
        "win32": {
            "tox": r"C:\host\Python\Scripts\tox.exe",
            "go": r"C:\Go\bin\go.exe",
            "gcc": r"C:\msys64\mingw64\bin\gcc.exe",
        },
    }
    outputs = {
        ("tox", ("--version",)): "4.25.0 from /host/python/lib/site-packages/tox/__init__.py\n",
        ("go", ("version",)): "go version go1.24.2 linux/amd64\n",
        ("cc", ("--version",)): "cc (GCC) 14.2.0\n",
        ("gcc", ("--version",)): "x86_64-w64-mingw32-gcc.exe (GCC) 14.2.0\n",
    }
    results: dict[str, Any] = {}

    for platform_name, executables in tool_paths.items():
        monkeypatch.setattr(runner.shutil, "which", executables.get)
        calls: list[tuple[list[str], dict[str, Any]]] = []

        def fake_run(
            command: list[str], _calls: list[tuple[list[str], dict[str, Any]]] = calls, **kwargs: Any
        ) -> subprocess.CompletedProcess[str]:
            _calls.append((command, kwargs))
            executable = command[0].replace("\\", "/").rsplit("/", maxsplit=1)[-1].casefold()
            executable = executable.removesuffix(".exe")
            output = outputs[(executable, tuple(command[1:]))]
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

        monkeypatch.setattr(runner.subprocess, "run", fake_run)
        versions, commands = runner._system_tool_evidence("native-go-parser", platform_name)
        results[platform_name] = {"versions": versions, "commands": commands, "calls": calls}

    return results


@then("it should record Go and native compiler versions and invocation commands")
def native_runner_records_toolchain_versions_and_commands(native_toolchain_capture: dict[str, Any]) -> None:
    for platform_name, evidence in native_toolchain_capture.items():
        versions = evidence["versions"]
        commands = evidence["commands"]
        assert versions["tox"] == "4.25.0", (platform_name, versions)
        assert commands["tox"]["argv"][1:] == ["--version"], (platform_name, commands)
        assert versions["go"] == "go1.24.2", (platform_name, versions)
        assert versions["native-compiler"] == "14.2.0", (platform_name, versions)
        assert commands["go"]["argv"][1:] == ["version"], (platform_name, commands)
        assert commands["native-compiler"]["argv"][1:] == ["--version"], (platform_name, commands)
        compiler_name = commands["native-compiler"]["executable"].replace("\\", "/").rsplit("/", maxsplit=1)[-1]
        if platform_name == "win32":
            assert compiler_name.casefold().removesuffix(".exe") == "gcc", commands
        else:
            assert compiler_name == "cc", commands
        assert all(kwargs.get("shell", False) is False for _command, kwargs in evidence["calls"]), evidence


@given("PYTHONUTF8 is unset in the runner environment")
def unset_utf8_mode_for_matrix_runner(monkeypatch: Any) -> None:
    monkeypatch.delenv("PYTHONUTF8", raising=False)


def _capture_matrix_runner_with_non_ascii_evidence_path(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
    *,
    tox_returncode: int,
    tox_stdout: str,
) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(Path(request.config.rootpath) / "scripts"))
    runner = importlib.import_module("run_env_matrix_cell")
    project_root = tmp_path / "project"
    inventory_path = project_root / "config" / "env-matrix.yaml"
    inventory_path.parent.mkdir(parents=True)
    inventory_path.write_text("{}\n", encoding="utf-8")
    output_path = tmp_path / "environment-evidence-доказательства.json"

    monkeypatch.setattr(runner.shutil, "which", lambda _executable: "tox")
    monkeypatch.setattr(
        runner,
        "load_cells",
        lambda _inventory, _job: [
            {
                "id": "utf8-test-cell",
                "tox_envs": ["py313-utf8-evidence"],
            }
        ],
    )
    monkeypatch.setattr(
        runner,
        "_installed_versions",
        lambda _python: {
            "python": "3.13.0",
            "runtime": "CPython",
            "packages": {"pytest": "9.0.1"},
        },
    )
    monkeypatch.setattr(runner, "_python_in_tox_environment", lambda *_args: tmp_path / "python")
    monkeypatch.setattr(runner.platform, "platform", lambda: "synthetic-platform")
    parent_stdout_bytes = io.BytesIO()
    parent_stdout = io.TextIOWrapper(parent_stdout_bytes, encoding="cp1252", errors="strict")
    monkeypatch.setattr(runner.sys, "stdout", parent_stdout)
    tox_calls: list[dict[str, Any]] = []
    tox_version_calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command[1:] == ["--version"]:
            tox_version_calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="4.25.0 from synthetic tox\n", stderr="")
        raise AssertionError(f"tox execution should use the streaming process runner: {command!r}")

    def fake_popen(command: list[str], **kwargs: Any) -> Any:
        tox_calls.append({"command": command, "returncode": tox_returncode, **kwargs})
        result_json = Path(command[command.index("--result-json") + 1])
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text('{"testenvs": {}}\n', encoding="utf-8")

        class FakeProcess:
            stdout = io.StringIO(tox_stdout)

            @staticmethod
            def wait() -> int:
                return tox_returncode

        return FakeProcess()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_env_matrix_cell.py",
            "--job",
            "full-matrix",
            "--cell",
            "utf8-test-cell",
            "--inventory",
            str(inventory_path),
            "--output",
            str(output_path),
            "--sha",
            _PROOF_SHA,
        ],
    )

    result = runner.main()
    parent_stdout.flush()
    return {
        "returncode": result,
        "tox_calls": tox_calls,
        "tox_version_calls": tox_version_calls,
        "output_path": output_path,
        "stdout": parent_stdout_bytes.getvalue().decode("cp1252"),
    }


@when(
    "I run the environment matrix runner with a non-ASCII evidence path and cp1252 parent stdout",
    target_fixture="matrix_runner_cp1252_capture",
)
def run_matrix_runner_with_non_ascii_evidence_path(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
) -> dict[str, Any]:
    return _capture_matrix_runner_with_non_ascii_evidence_path(
        request,
        tmp_path,
        monkeypatch,
        tox_returncode=0,
        tox_stdout="1 passed in 0.01s\nUnicode smoke: café, Ж\n",
    )


@when(
    "I run the environment matrix runner with a non-ASCII evidence path and cp1252 parent stdout when tox exits 23",
    target_fixture="matrix_runner_cp1252_capture",
)
def run_matrix_runner_with_nonzero_tox_status(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
) -> dict[str, Any]:
    return _capture_matrix_runner_with_non_ascii_evidence_path(
        request,
        tmp_path,
        monkeypatch,
        tox_returncode=23,
        tox_stdout="1 failed in 0.01s\nUnicode smoke: café, Ж\n",
    )


@then("it should return tox status write evidence and escape unrepresentable log characters")
def matrix_runner_preserves_evidence_when_parent_stdout_is_cp1252(
    matrix_runner_cp1252_capture: dict[str, Any],
) -> None:
    assert matrix_runner_cp1252_capture["returncode"] == 0
    output_path = matrix_runner_cp1252_capture["output_path"]
    assert "доказательства" in str(output_path)
    assert output_path.is_file()
    evidence = json.loads(output_path.read_text(encoding="utf-8"))
    assert evidence["outcome"] == "passed", evidence
    assert evidence["environments"][0]["returncode"] == 0, evidence
    assert evidence["environments"][0]["system_tool_versions"]["tox"] == "4.25.0", evidence
    assert evidence["environments"][0]["system_tool_commands"]["tox"] == {
        "executable": "tox",
        "argv": ["tox", "--version"],
    }, evidence
    assert matrix_runner_cp1252_capture["tox_version_calls"] == [["tox", "--version"]]
    assert "Unicode smoke: café, \\u0416" in matrix_runner_cp1252_capture["stdout"]
    assert "доказательства" not in matrix_runner_cp1252_capture["stdout"]
    assert (
        "\\u0434\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b\\u044c\\u0441\\u0442\\u0432\\u0430"
        in (matrix_runner_cp1252_capture["stdout"])
    )
    tox_calls = matrix_runner_cp1252_capture["tox_calls"]
    assert len(tox_calls) == 1, tox_calls
    tox_call = tox_calls[0]
    assert tox_call["command"][:2] == ["tox", "run"], tox_call
    assert tox_call["env"].get("PYTHONUTF8") == "1", tox_call["env"]
    assert tox_call.get("encoding") == "utf-8", tox_call
    assert tox_call.get("errors") == "replace", tox_call
    assert tox_call.get("stderr") == subprocess.STDOUT, tox_call
    assert tox_call.get("stdout") == subprocess.PIPE, tox_call


@then("it should return failure and record tox exit 23 in evidence")
def matrix_runner_records_failed_tox_status_under_cp1252_stdout(
    matrix_runner_cp1252_capture: dict[str, Any],
) -> None:
    assert matrix_runner_cp1252_capture["returncode"] == 1
    output_path = matrix_runner_cp1252_capture["output_path"]
    assert "доказательства" in str(output_path)
    assert output_path.is_file()
    evidence = json.loads(output_path.read_text(encoding="utf-8"))
    assert evidence["outcome"] == "failed", evidence
    record = evidence["environments"][0]
    assert record["outcome"] == "failed", record
    tox_calls = matrix_runner_cp1252_capture["tox_calls"]
    assert len(tox_calls) == 1, tox_calls
    assert tox_calls[0]["returncode"] == 23, tox_calls
    assert record["returncode"] == tox_calls[0]["returncode"], record
    assert "Unicode smoke: café, \\u0416" in matrix_runner_cp1252_capture["stdout"]


@then("the proof summary should preserve two-worker socket via and ssh runtime evidence")
def proof_summary_preserves_remote_worker_runtime_evidence(proof_aggregation: ProofAggregationContext) -> None:
    environments = _summary(proof_aggregation).get("environments")
    assert isinstance(environments, list), environments
    remote_records = {
        environment.get("cell"): environment
        for environment in environments
        if isinstance(environment, dict) and environment.get("job") == "remote"
    }
    assert set(remote_records) == set(_REMOTE_MODES), remote_records

    for cell_id, mode in _REMOTE_MODES.items():
        record = remote_records[cell_id]
        runs = record.get("remote_worker_runs")
        assert isinstance(runs, list) and len(runs) == 2, (cell_id, record)
        assert {run.get("mode") for run in runs} == {mode}, (cell_id, runs)
        assert {run.get("partial") for run in runs} == {False, True}, (cell_id, runs)
        for run in runs:
            workers = run.get("workers")
            assert isinstance(workers, list) and len(workers) == 2, (cell_id, run)
            worker_ids = {worker.get("worker_id") for worker in workers}
            assert len(worker_ids) == 2 and None not in worker_ids, (cell_id, workers)
            for worker in workers:
                assert worker.get("runtime") == record.get("runtime"), (cell_id, worker, record)
                assert worker.get("python", "").startswith(record.get("python", "")), (cell_id, worker, record)
                assert worker.get("pytest") == record.get("pytest"), (cell_id, worker, record)
                assert worker.get("pytest-xdist") == record.get("optional_versions", {}).get("pytest-xdist"), (
                    cell_id,
                    worker,
                    record,
                )


@then("the proof summary should fail with a missing environment diagnostic")
def proof_summary_fails_for_missing_environment(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "missing evidence for expected environment" in proof_aggregation_result.stderr


@then("the proof summary should fail with a missing remote worker runtime diagnostic")
def proof_summary_fails_for_missing_remote_worker_runtime_evidence(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "is missing actual remote worker runtime evidence" in proof_aggregation_result.stderr


@then("the proof summary should fail with missing remote worker version diagnostics")
def proof_summary_fails_for_missing_remote_worker_versions(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "worker gw0 reports runtime None" in proof_aggregation_result.stderr
    assert "worker gw0 reports Python None" in proof_aggregation_result.stderr


@then("the proof summary should fail with mismatched remote worker version diagnostics")
def proof_summary_fails_for_mismatched_remote_worker_versions(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "worker gw0 reports runtime 'Jython'" in proof_aggregation_result.stderr
    assert "worker gw0 reports Python '0.0.0'" in proof_aggregation_result.stderr


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


@then("the proof summary should reject pytest 8 for a latest pytest tox factor")
def proof_summary_rejects_pytest_8_for_latest_tox_factor(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "py314-pytestlatest-coverage-lin" in proof_aggregation_result.stderr
    assert "pytestlatest tox factor requires pytest 9.x" in proof_aggregation_result.stderr


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


@then("pytest output should show the duplicate step warning without an xdist internal error")
def duplicate_step_warning_deserializes_without_xdist_error(consumer: Any) -> None:
    result = consumer.pytest_result
    assert result is not None, "the duplicate step warning consumer run has not completed"
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, f"xdist failed while serializing the duplicate step warning:\n{output}"
    assert re.search(r"\b1 passed\b", output), f"the xdist scenario did not pass:\n{output}"
    assert "Alternative step definitions are found" in output, f"the duplicate step warning was not reported:\n{output}"
    assert "INTERNALERROR" not in output, f"xdist reported an internal error:\n{output}"
    assert "PytestBDDStepDefinitionWarning'" not in output, f"xdist could not deserialize the warning class:\n{output}"


@given("the installed consumer requires pytest-xdist")
def install_required_consumer_pytest_xdist(consumer: Any) -> None:
    probe = subprocess.run(
        [str(consumer.python), "-c", "import xdist"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        return

    uv_executable = shutil.which("uv")
    assert uv_executable is not None, "the xdist warning acceptance requires uv to install pytest-xdist"
    install = subprocess.run(
        [
            uv_executable,
            "pip",
            "install",
            "--python",
            str(consumer.python),
            "pytest-xdist==3.8.0",
        ],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert install.returncode == 0, f"could not install required pytest-xdist:\n{install.stdout}\n{install.stderr}"
    probe = subprocess.run(
        [str(consumer.python), "-c", "import xdist"],
        cwd=consumer.path,
        env=consumer.env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert probe.returncode == 0, f"pytest-xdist remains unavailable in the consumer:\n{probe.stdout}\n{probe.stderr}"


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


@then("the proof summary should fail for missing doc-generation packages")
def proof_summary_fails_for_missing_doc_generation_packages(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    for package in _DOC_GENERATION_PACKAGES:
        assert f"requires installed optional package '{package}'" in proof_aggregation_result.stderr
    assert "add it to the tox environment dependencies" in proof_aggregation_result.stderr


@then("the proof summary should fail for missing Pandoc CLI version evidence")
def proof_summary_fails_for_missing_pandoc_cli_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    artifact = _doc_generation_artifact(proof_aggregation)
    document = json.loads(artifact.path.read_text(encoding="utf-8"))
    environment = document["environments"][0]
    for package in _DOC_GENERATION_PACKAGES:
        version = environment["optional_versions"].get(package)
        assert isinstance(version, str) and version, (package, environment)
        versions = environment.get("system_tool_versions")
        assert isinstance(versions, dict) and versions.get("pandoc") is None, environment

    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    diagnostic = proof_aggregation_result.stderr.casefold()
    assert "system tool 'pandoc'" in diagnostic, proof_aggregation_result.stderr
    assert "version" in diagnostic, proof_aggregation_result.stderr
    assert "install pandoc before running the documentation tox environment" in diagnostic, (
        proof_aggregation_result.stderr
    )


@then("the proof summary should fail for a missing tox result command")
def proof_summary_fails_for_missing_tox_result_command(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "command evidence" in proof_aggregation_result.stderr


@then("the proof summary should fail with a missing architecture diagnostic")
def proof_summary_fails_without_architecture(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "reports architecture None" in proof_aggregation_result.stderr, proof_aggregation_result.stderr


@then("the proof summary should fail with an invalid architecture diagnostic")
def proof_summary_fails_with_invalid_architecture(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "reports architecture '../unknown'" in proof_aggregation_result.stderr, proof_aggregation_result.stderr


@then("the proof summary should fail with a missing workflow job link diagnostic")
def proof_summary_fails_without_job_link(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "missing a valid workflow job link" in proof_aggregation_result.stderr


@then("the proof summary should fail with an exact interpreter version diagnostic")
def proof_summary_fails_for_wrong_exact_interpreter_version(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "inventory expects '3.15.0'" in proof_aggregation_result.stderr


@then("the proof summary should fail with a mismatched workflow run link diagnostic")
def proof_summary_fails_with_mismatched_workflow_links(
    proof_aggregation: ProofAggregationContext,
    proof_aggregation_result: subprocess.CompletedProcess[str],
) -> None:
    assert proof_aggregation_result.returncode != 0, proof_aggregation_result.stdout
    assert _summary(proof_aggregation).get("outcome") == "failed", _summary(proof_aggregation)
    assert "job and run links do not identify the same workflow run" in proof_aggregation_result.stderr


def _run_selected_matrix_environment(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
    *,
    requested_environment: str,
    tox_stdout: str | None = None,
    tox_returncode: int = 0,
    machine_value: str | None = None,
    selected_cell: dict[str, Any] | None = None,
    installed_runtime: dict[str, Any] | None = None,
    host_runtime: dict[str, str] | None = None,
    system_tool_evidence: tuple[dict[str, str | None], dict[str, dict[str, Any] | None]] | None = None,
) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(Path(request.config.rootpath) / "scripts"))
    runner = importlib.import_module("run_env_matrix_cell")
    project_root = tmp_path / "project"
    inventory_path = project_root / "config" / "env-matrix.yaml"
    inventory_path.parent.mkdir(parents=True)
    inventory_path.write_text("{}\n", encoding="utf-8")
    output_path = tmp_path / "artifacts" / "canonical-cell-evidence.json"
    cell = selected_cell or {
        "id": "cpython-313-linux",
        "runtime": "CPython",
        "python": "3.13",
        "platform": "linux",
        "runner": "ubuntu-latest",
        "tox_envs": [
            "py313-pytestlatest-runner-selected",
            "py313-pytest90-runner-other",
        ],
    }
    if tox_stdout is None:
        tox_stdout = (
            f"{requested_environment}: commands[0]> python -m pytest\n"
            "1 passed in 0.01s\n"
            f"{requested_environment}: commands[1]> python -m pytest tutorial-example-acceptance.feature\n"
            "1 passed in 0.01s\n"
        )
    monkeypatch.setattr(runner.shutil, "which", lambda _executable: "tox")
    monkeypatch.setattr(runner, "load_cells", lambda _inventory, _job: [cell])
    monkeypatch.setattr(
        runner,
        "_installed_versions",
        lambda _python: (
            installed_runtime
            or {
                "python": "3.13.0",
                "runtime": "CPython",
                "packages": {"pytest": "9.0.1"},
            }
        ),
    )
    monkeypatch.setattr(runner, "_python_in_tox_environment", lambda *_args: tmp_path / "python")
    monkeypatch.setattr(runner.platform, "platform", lambda: "synthetic-platform")
    if machine_value is not None:
        monkeypatch.setattr(runner.platform, "machine", lambda: machine_value)
    if host_runtime is not None:
        monkeypatch.setattr(runner.platform, "python_implementation", lambda: host_runtime["runtime"])
        monkeypatch.setattr(runner.platform, "python_version", lambda: host_runtime["python"])
        monkeypatch.setattr(runner.sys, "platform", host_runtime["platform"])
        monkeypatch.setattr(runner.platform, "machine", lambda: host_runtime["architecture"])
    if system_tool_evidence is not None:
        monkeypatch.setattr(runner, "_system_tool_evidence", lambda *_args, **_kwargs: system_tool_evidence)
    tox_calls: list[dict[str, Any]] = []
    tox_version_calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command[1:] == ["--version"]:
            tox_version_calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="4.25.0 from synthetic tox\n", stderr="")
        raise AssertionError(f"tox execution should use the streaming process runner: {command!r}")

    def fake_popen(command: list[str], **kwargs: Any) -> Any:
        tox_calls.append({"command": command, "returncode": tox_returncode, **kwargs})
        result_json = Path(command[command.index("--result-json") + 1])
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text('{"testenvs": {}}\n', encoding="utf-8")

        class FakeProcess:
            stdout = io.StringIO(tox_stdout)

            @staticmethod
            def wait() -> int:
                return tox_returncode

        return FakeProcess()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_env_matrix_cell.py",
            "--job",
            "full-matrix",
            "--cell",
            str(cell["id"]),
            "--tox-env",
            requested_environment,
            "--inventory",
            str(inventory_path),
            "--output",
            str(output_path),
            "--sha",
            _PROOF_SHA,
        ],
    )
    returncode = runner.main()
    return {
        "returncode": returncode,
        "tox_calls": tox_calls,
        "tox_version_calls": tox_version_calls,
        "output_path": output_path,
        "cell": cell,
        "requested_environment": requested_environment,
    }


@when(
    "I run the matrix runner for one tox environment selected from its cell",
    target_fixture="selected_matrix_environment_run",
)
def run_matrix_runner_for_one_selected_environment(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
) -> dict[str, Any]:
    return _run_selected_matrix_environment(
        request,
        tmp_path,
        monkeypatch,
        requested_environment="py313-pytestlatest-runner-selected",
    )


@then("it should execute only that environment and record the canonical proof key and SHA")
def selected_matrix_environment_has_canonical_evidence(selected_matrix_environment_run: dict[str, Any]) -> None:
    capture = selected_matrix_environment_run
    assert capture["returncode"] == 0, capture
    assert capture["tox_version_calls"] == [["tox", "--version"]], capture
    calls = capture["tox_calls"]
    assert len(calls) == 1, calls
    command = calls[0]["command"]
    assert command[command.index("-e") + 1] == capture["requested_environment"], command

    evidence = json.loads(capture["output_path"].read_text(encoding="utf-8"))
    record = evidence["environments"][0]
    assert evidence["job"] == record["job"] == "full-matrix", evidence
    assert evidence["cell"] == record["cell"] == capture["cell"]["id"], evidence
    assert record["tox_environment"] == capture["requested_environment"], record
    assert evidence["git_sha"] == record["git_sha"] == _PROOF_SHA, evidence
    assert record["acceptance_commands"] == {
        "core_tests": {
            "command_index": 0,
            "selected_tests": 1,
            "passed_tests": 1,
            "failed_tests": 0,
            "error_tests": 0,
            "outcome": "passed",
        },
        "tutorial_example": {
            "command_index": 1,
            "selected_tests": 1,
            "passed_tests": 1,
            "failed_tests": 0,
            "error_tests": 0,
            "outcome": "passed",
        },
    }, record
    assert len(evidence["environments"]) == 1, evidence


@when(
    "I run the matrix runner on a host reporting the AMD64 architecture",
    target_fixture="amd64_matrix_environment_run",
)
def run_matrix_runner_with_amd64_architecture(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
) -> dict[str, Any]:
    return _run_selected_matrix_environment(
        request,
        tmp_path,
        monkeypatch,
        requested_environment="py313-pytestlatest-runner-selected",
        machine_value="AMD64",
    )


@then("the matrix runner should record the normalized x86_64 architecture")
def matrix_runner_records_normalized_amd64_architecture(amd64_matrix_environment_run: dict[str, Any]) -> None:
    capture = amd64_matrix_environment_run
    assert capture["returncode"] == 0, capture
    evidence = json.loads(capture["output_path"].read_text(encoding="utf-8"))
    assert evidence["environments"][0]["architecture"] == "x86_64", evidence


@when(
    "I run the matrix runner for a tox environment outside its cell",
    target_fixture="rejected_matrix_environment_run",
)
def run_matrix_runner_for_environment_outside_cell(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
) -> dict[str, Any]:
    return _run_selected_matrix_environment(
        request,
        tmp_path,
        monkeypatch,
        requested_environment="py313-pytestlatest-not-in-cell",
    )


@then("it should reject the environment before invoking tox or writing evidence")
def matrix_runner_rejects_environment_outside_cell(rejected_matrix_environment_run: dict[str, Any]) -> None:
    capture = rejected_matrix_environment_run
    assert capture["returncode"] == 2, capture
    assert capture["tox_calls"] == [], capture
    assert not capture["output_path"].exists(), capture


@when(
    "I run the matrix runner for a tox environment whose tests all skip",
    target_fixture="skipped_only_matrix_environment_run",
)
def run_matrix_runner_for_skipped_only_environment(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
) -> dict[str, Any]:
    return _run_selected_matrix_environment(
        request,
        tmp_path,
        monkeypatch,
        requested_environment="py313-pytestlatest-runner-selected",
        tox_stdout="2 skipped in 0.01s\n",
    )


@then("it should reject the skipped-only tox result and record a failed environment outcome")
def skipped_only_matrix_environment_is_failed(
    skipped_only_matrix_environment_run: dict[str, Any],
) -> None:
    capture = skipped_only_matrix_environment_run
    assert capture["returncode"] == 1, capture
    assert len(capture["tox_calls"]) == 1, capture

    evidence = json.loads(capture["output_path"].read_text(encoding="utf-8"))
    assert evidence["outcome"] == "failed", evidence
    assert len(evidence["environments"]) == 1, evidence
    assert evidence["environments"][0]["selected_tests"] == 2, evidence
    assert evidence["environments"][0]["passed_tests"] == 0, evidence
    assert evidence["environments"][0]["outcome"] == "failed", evidence


@when(
    parsers.parse(
        'I run the CPython 3.11 Linux latest pytest lane with core summary "{core_summary}" '
        "and a passing tutorial example"
    ),
    target_fixture="cpython_311_linux_skipped_core_matrix_run",
)
def run_cpython_311_linux_lane_with_skipped_core_and_passing_tutorial(
    request: Any,
    tmp_path: Path,
    monkeypatch: Any,
    core_summary: str,
) -> dict[str, Any]:
    cell = {
        "id": "cpython-311-linux",
        "runtime": "CPython",
        "python": "3.11",
        "platform": "linux",
        "architecture": "x86_64",
        "expected_interpreter": "3.11.*",
        "runner": "ubuntu-latest",
        "tox_envs": ["py311-pytestlatest-coverage-lin", "py311-pytest74-coverage-lin"],
    }
    capture = _run_selected_matrix_environment(
        request,
        tmp_path,
        monkeypatch,
        requested_environment="py311-pytestlatest-coverage-lin",
        tox_stdout=(
            "py311-pytestlatest-coverage-lin: commands[0]> coverage run --append -m pytest "
            "-m 'not e2e and not external and not typecheck and not doc_gen' -q\n"
            f"{core_summary}\n"
            "py311-pytestlatest-coverage-lin: commands[1]> python -m pytest --cuke-autoload "
            "--cuke-features-dir=features features/compatibility/tutorial-example-acceptance.feature -m e2e -q\n"
            "1 passed in 0.01s\n"
        ),
        selected_cell=cell,
        installed_runtime={
            "python": "3.11.9",
            "runtime": "CPython",
            "packages": {"pytest": "9.0.1"},
        },
        host_runtime={
            "runtime": "CPython",
            "python": "3.11.9",
            "platform": "linux",
            "architecture": "x86_64",
        },
        system_tool_evidence=(
            {"tox": "4.25.0", "uv": "0.8.22"},
            {
                "tox": {"executable": "tox", "argv": ["tox", "--version"]},
                "uv": {
                    "executable": "/project/.tox/py311-pytestlatest-coverage-lin/bin/uv",
                    "argv": ["uv", "--version"],
                },
            },
        ),
    )
    capture["core_summary"] = core_summary
    return capture


@then(
    parsers.parse(
        "it should record a failed CPython 3.11 Linux core acceptance result with {core_passed:d} passed "
        "and {core_failed:d} failed"
    )
)
def cpython_311_linux_skipped_core_acceptance_is_failed(
    cpython_311_linux_skipped_core_matrix_run: dict[str, Any],
    core_passed: int,
    core_failed: int,
) -> None:
    capture = cpython_311_linux_skipped_core_matrix_run
    assert capture["returncode"] == 1, capture
    assert len(capture["tox_calls"]) == 1, capture
    command = capture["tox_calls"][0]["command"]
    assert command[command.index("-e") + 1] == "py311-pytestlatest-coverage-lin", command

    evidence = json.loads(capture["output_path"].read_text(encoding="utf-8"))
    assert evidence["outcome"] == "failed", evidence
    assert evidence["cell"] == "cpython-311-linux", evidence
    assert evidence["git_sha"] == _PROOF_SHA, evidence
    assert len(evidence["environments"]) == 1, evidence
    record = evidence["environments"][0]
    assert record["tox_environment"] == "py311-pytestlatest-coverage-lin", record
    assert record["python"] == "3.11.9", record
    assert record["pytest"] == "9.0.1", record
    assert record["platform_name"] == "linux", record
    assert record["architecture"] == "x86_64", record
    assert record["outcome"] == "failed", record
    assert record["acceptance_commands"]["core_tests"] == {
        "command_index": 0,
        "selected_tests": 20,
        "passed_tests": core_passed,
        "failed_tests": core_failed,
        "error_tests": 0,
        "outcome": "failed",
    }, record
    assert record["acceptance_commands"]["tutorial_example"] == {
        "command_index": 1,
        "selected_tests": 1,
        "passed_tests": 1,
        "failed_tests": 0,
        "error_tests": 0,
        "outcome": "passed",
    }, record


@when("I watch a matrix command that waits after writing its first progress line", target_fixture="streamed_matrix_run")
def run_matrix_command_and_observe_live_progress(monkeypatch: Any, tmp_path: Path) -> dict[str, Any]:
    runner = importlib.import_module("run_env_matrix_cell")
    output = io.StringIO()
    monkeypatch.setattr(runner.sys, "stdout", output)
    release_path = tmp_path / "release-matrix-command.txt"
    command_script = "\n".join(
        (
            "import pathlib, sys, time",
            "release = pathlib.Path(sys.argv[1])",
            "print('matrix progress marker', flush=True)",
            "deadline = time.monotonic() + 8",
            "while not release.exists() and time.monotonic() < deadline:",
            "    time.sleep(0.01)",
            "print('1 passed in 0.01s', flush=True)",
        )
    )
    results: list[subprocess.CompletedProcess[str]] = []
    errors: list[BaseException] = []

    def run_command() -> None:
        try:
            results.append(
                runner._run_and_stream(
                    [sys.executable, "-u", "-c", command_script, str(release_path)],
                    cwd=tmp_path,
                    env=os.environ.copy(),
                )
            )
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=run_command, daemon=True)
    thread.start()
    observed_while_running = False
    deadline = time.monotonic() + 3
    try:
        while thread.is_alive() and time.monotonic() < deadline:
            if "matrix progress marker" in output.getvalue():
                observed_while_running = thread.is_alive()
                break
            time.sleep(0.01)
    finally:
        release_path.touch()
        thread.join(timeout=10)

    return {
        "observed_while_running": observed_while_running,
        "thread_stopped": not thread.is_alive(),
        "output": output.getvalue(),
        "results": results,
        "errors": errors,
    }


@then("the runner should expose progress while the command is still running and retain its final output")
def matrix_runner_streams_progress_before_exit(streamed_matrix_run: dict[str, Any]) -> None:
    assert streamed_matrix_run["observed_while_running"], streamed_matrix_run
    assert streamed_matrix_run["thread_stopped"], streamed_matrix_run
    assert not streamed_matrix_run["errors"], streamed_matrix_run
    result = streamed_matrix_run["results"][0]
    assert result.returncode == 0, result
    assert "matrix progress marker" in streamed_matrix_run["output"], streamed_matrix_run
    assert "matrix progress marker" in result.stdout, result
    assert "1 passed in 0.01s" in result.stdout, result
