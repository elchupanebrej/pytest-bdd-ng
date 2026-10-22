from __future__ import annotations

from typing import Any

import pytest

from pytest_cuke.compatibility.environment_matrix import (
    _validate_historical_capability_exclusions,
    _validate_optional_integration_inventory,
    _validate_runtime_policy,
)

pytestmark = pytest.mark.unit


_EVIDENCE_FIELDS = [
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
]


def _runtime_cell_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    required_cells: list[dict[str, Any]] = []
    workflow_cells: list[dict[str, Any]] = []
    lanes: list[dict[str, Any]] = []

    targets = [
        (
            "CPython",
            f"3.{minor}",
            platform_name,
            "x86_64" if minor == 11 and platform_name == "linux" else "runner-native",
        )
        for minor in range(11, 16)
        for platform_name in ("linux", "macos", "windows")
    ]
    targets.extend(
        [
            ("PyPy", "3.12", "linux", "x86_64"),
            ("GraalPy", "3.13.14", "linux", "x86_64"),
        ]
    )
    for runtime, python_version, platform_name, architecture in targets:
        if runtime == "CPython":
            cell_id = f"cpython-{python_version.replace('.', '')}-{platform_name}"
            tox_env = f"py{python_version.replace('.', '')}-pytestlatest-coverage-{_tox_platform(platform_name)}"
            pytest_lines = ["9.x"]
            if python_version == "3.11" and platform_name == "linux":
                tox_env = f"{tox_env},py311-pytest74-coverage-lin"
                pytest_lines.append("7.4.x")
            if python_version == "3.12" and platform_name == "linux":
                tox_env = f"{tox_env},py312-pytest84-coverage-lin"
                pytest_lines.append("8.4.x")
            setup_input = "3.15.0" if python_version == "3.15" else python_version
            expected_interpreter = "3.15.0" if python_version == "3.15" else f"{python_version}.*"
        elif runtime == "PyPy":
            cell_id = "pypy-312-linux"
            tox_env = "pypy312-pytestlatest-coverage-lin"
            pytest_lines = ["9.x"]
            setup_input = "pypy3.12"
            tox_base_python = "pypy3.12"
            expected_interpreter = "3.12.*"
        else:
            cell_id = "graalpy-253-linux"
            tox_env = "graalpy-253-pytestlatest-coverage-lin"
            pytest_lines = ["9.x"]
            setup_input = "graalpy-25.3"
            tox_base_python = "graalpy"
            expected_interpreter = "3.13.14"

        environment_names = tox_env.split(",")
        upstream_url = {
            "CPython": "https://www.python.org/downloads/",
            "PyPy": "https://www.pypy.org/download.html",
            "GraalPy": "https://www.graalvm.org/python/",
        }[runtime]
        required_cells.append(
            {
                "id": cell_id,
                "runtime": runtime,
                "python": python_version,
                "platform": platform_name,
                "architecture": architecture,
                "setup_python": {"input": setup_input, "expected_interpreter": expected_interpreter},
                **({"tox_base_python": tox_base_python} if runtime in {"PyPy", "GraalPy"} else {}),
                "upstream_availability": {"status": "available", "source_evidence": [upstream_url]},
                "installability": {
                    "status": "required-acceptance",
                    "acceptance": ["core-install", "core-tests", "examples"],
                },
                "product_support": {"status": "supported"},
                "required_ci": {
                    "status": "required",
                    "workflow_cell": cell_id,
                    "tox_envs": environment_names,
                },
                "required_pytest_lines": pytest_lines,
                "measured_evidence": {"status": "per-run", "fields": list(_EVIDENCE_FIELDS)},
                **({"runtime_version": "25.3"} if runtime == "GraalPy" else {}),
            }
        )
        workflow_cells.append(
            {
                "id": cell_id,
                "job": "full-matrix",
                "runtime": runtime,
                "python": python_version,
                "platform": platform_name,
                "architecture": architecture,
                "runner": {"linux": "ubuntu-latest", "macos": "macos-latest", "windows": "windows-latest"}[
                    platform_name
                ],
                "setup_python_input": setup_input,
                "expected_interpreter": expected_interpreter,
                "tox_envs": environment_names,
                **({"runtime_version": "25.3"} if runtime == "GraalPy" else {}),
            }
        )
        lanes.append(
            {
                "id": cell_id,
                "runtime": runtime,
                "python": python_version,
                "platform": platform_name,
                "capability": "core-runtime-acceptance",
                "status": "required",
                "tox_env": tox_env,
                "workflow_selector": cell_id,
            }
        )

    return required_cells, workflow_cells, lanes


def _tox_platform(platform_name: str) -> str:
    return {"linux": "lin", "macos": "mac", "windows": "win"}[platform_name]


def _runtime_policy_exclusion(
    *,
    cell_id: str,
    runtime: str,
    python_version: str,
    upstream_url: str,
    installability_status: str,
    installability_reason: str,
    support_reason: str,
    reason: str,
    platform_name: str = "all",
    architecture: str = "all",
    source_evidence: list[str] | None = None,
    runtime_version: str | None = None,
) -> dict[str, Any]:
    return {
        "id": cell_id,
        "runtime": runtime,
        "python": python_version,
        "platform": platform_name,
        "architecture": architecture,
        "upstream_availability": {"status": "available", "source_evidence": [upstream_url]},
        "installability": {"status": installability_status, "reason": installability_reason},
        "product_support": {"status": "unsupported", "reason": support_reason},
        "required_ci": {
            "status": "excluded",
            "workflow_cell": None,
            "tox_envs": [],
            "reason": reason,
        },
        "measured_evidence": {
            "status": "not-run",
            "fields": list(_EVIDENCE_FIELDS),
            "reason": reason,
        },
        "reason": reason,
        "source_evidence": source_evidence or ["https://github.com/elchupanebrej/pytest-bdd-ng/issues/300"],
        **({"runtime_version": runtime_version} if runtime_version is not None else {}),
    }


def _policy_document() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    required_cells, workflow_cells, lanes = _runtime_cell_records()
    document = {
        "runtime_policy": {
            "python_requirement": ">=3.11",
            "pytest": {"minimum": ">=7.0", "latest": "9.x"},
            "required_cells": required_cells,
            "exclusions": [
                _runtime_policy_exclusion(
                    cell_id="cpython-310-product-excluded",
                    runtime="CPython",
                    python_version="3.10",
                    upstream_url="https://www.python.org/downloads/",
                    installability_status="incompatible",
                    installability_reason="The package metadata requires Python >=3.11.",
                    support_reason="The product minimum is Python 3.11.",
                    reason="The current runtime support policy starts at CPython 3.11.",
                ),
                _runtime_policy_exclusion(
                    cell_id="pypy-310-product-excluded",
                    runtime="PyPy",
                    python_version="3.10",
                    upstream_url="https://www.pypy.org/download.html",
                    installability_status="incompatible",
                    installability_reason="The package metadata requires Python >=3.11.",
                    support_reason="The product minimum is Python 3.11.",
                    reason="PyPy 3.10 is below the product minimum of Python 3.11.",
                ),
                _runtime_policy_exclusion(
                    cell_id="pypy-311-product-excluded",
                    runtime="PyPy",
                    python_version="3.11",
                    upstream_url="https://www.pypy.org/download.html",
                    installability_status="not-assessed",
                    installability_reason=(
                        "PyPy 3.11 is outside the resolved acceptance matrix, so installation compatibility is not claimed."
                    ),
                    support_reason="The runtime policy selects PyPy 3.12 on Linux x86_64.",
                    reason="The current runtime support policy selects PyPy 3.12.",
                ),
                _runtime_policy_exclusion(
                    cell_id="pypy-312-macos-product-excluded",
                    runtime="PyPy",
                    python_version="3.12",
                    upstream_url="https://www.pypy.org/download.html",
                    installability_status="not-assessed",
                    installability_reason=(
                        "The pytest-cuke PyPy 3.12 macOS source/native install path has not been verified; "
                        "the optional pydantic-core integration has no PyPy 3.12 wheel."
                    ),
                    support_reason="Product acceptance currently covers PyPy 3.12 only on Linux x86_64.",
                    reason=(
                        "PyPy 3.12 product acceptance is limited to Linux x86_64; macOS source/native install and "
                        "installed-consumer acceptance are unverified, and optional pydantic-core has no PyPy 3.12 wheel."
                    ),
                    platform_name="macos",
                    source_evidence=[
                        "https://www.pypy.org/download.html",
                        "https://pypi.org/project/pydantic_core/",
                        "https://github.com/elchupanebrej/pytest-bdd-ng/issues/322",
                    ],
                ),
                _runtime_policy_exclusion(
                    cell_id="pypy-312-windows-product-excluded",
                    runtime="PyPy",
                    python_version="3.12",
                    upstream_url="https://www.pypy.org/download.html",
                    installability_status="not-assessed",
                    installability_reason=(
                        "The pytest-cuke PyPy 3.12 Windows source/native install path has not been verified; "
                        "the optional pydantic-core integration has no PyPy 3.12 wheel."
                    ),
                    support_reason="Product acceptance currently covers PyPy 3.12 only on Linux x86_64.",
                    reason=(
                        "PyPy 3.12 product acceptance is limited to Linux x86_64; Windows source/native install and "
                        "installed-consumer acceptance are unverified, and optional pydantic-core has no PyPy 3.12 wheel."
                    ),
                    platform_name="windows",
                    source_evidence=[
                        "https://www.pypy.org/download.html",
                        "https://pypi.org/project/pydantic_core/",
                        "https://github.com/elchupanebrej/pytest-bdd-ng/issues/322",
                    ],
                ),
                _runtime_policy_exclusion(
                    cell_id="graalpy-253-macos-product-excluded",
                    runtime="GraalPy",
                    runtime_version="25.3",
                    python_version="3.13.14",
                    platform_name="macos",
                    upstream_url="https://www.graalvm.org/latest/python/docs/",
                    installability_status="not-assessed",
                    installability_reason=(
                        "The pytest-cuke GraalPy 25.3 macOS source/native installation and installed-consumer path "
                        "has not been verified; GraalPy documents macOS as less comprehensively tested and native "
                        "packages require GraalPy-compatible wheels or source builds."
                    ),
                    support_reason="Product acceptance currently covers GraalPy 25.3 only on Linux x86_64.",
                    reason=(
                        "GraalPy documents macOS as less comprehensively tested; pytest-cuke has not verified its "
                        "source/native install and installed-consumer path, and native packages need "
                        "GraalPy-compatible wheels or source builds."
                    ),
                    source_evidence=[
                        "https://www.graalvm.org/latest/python/docs/",
                        "https://github.com/elchupanebrej/pytest-bdd-ng/issues/323",
                    ],
                ),
                _runtime_policy_exclusion(
                    cell_id="graalpy-253-windows-product-excluded",
                    runtime="GraalPy",
                    runtime_version="25.3",
                    python_version="3.13.14",
                    platform_name="windows",
                    upstream_url="https://www.graalvm.org/latest/python/docs/",
                    installability_status="not-assessed",
                    installability_reason=(
                        "The pytest-cuke GraalPy 25.3 Windows source/native installation and installed-consumer path "
                        "has not been verified; GraalPy documents additional Windows limitations and native packages "
                        "require GraalPy-compatible wheels or source builds."
                    ),
                    support_reason="Product acceptance currently covers GraalPy 25.3 only on Linux x86_64.",
                    reason=(
                        "GraalPy documents additional Windows limitations; pytest-cuke has not verified its "
                        "source/native install and installed-consumer path, and native packages need "
                        "GraalPy-compatible wheels or source builds."
                    ),
                    source_evidence=[
                        "https://www.graalvm.org/latest/python/docs/",
                        "https://github.com/elchupanebrej/pytest-bdd-ng/issues/323",
                    ],
                ),
            ],
        },
        "project": {"python_requirement": ">=3.11"},
    }
    return document, lanes, workflow_cells


def test_runtime_policy_accepts_the_canonical_required_cells() -> None:
    document, lanes, workflow_cells = _policy_document()

    summary, diagnostics = _validate_runtime_policy(document, lanes, workflow_cells)

    assert diagnostics == []
    assert summary["requiredCellCount"] == 17
    assert summary["exclusionCount"] == 7
    assert summary["pytestMinimum"] == ">=7.0"


def test_runtime_policy_graalpy_version_check_is_independent_of_inventory_order() -> None:
    document, lanes, workflow_cells = _policy_document()
    runtime_policy = document["runtime_policy"]
    graalpy = next(cell for cell in runtime_policy["required_cells"] if cell["runtime"] == "GraalPy")
    graalpy["runtime_version"] = "25.4"
    runtime_policy["required_cells"].reverse()

    _, diagnostics = _validate_runtime_policy(document, lanes, workflow_cells)

    graalpy_diagnostics = [item for item in diagnostics if item["code"] == "runtime-policy-graalpy-version-mismatch"]
    assert len(graalpy_diagnostics) == 1
    assert graalpy_diagnostics[0]["laneId"] == "graalpy-253-linux"


@pytest.mark.parametrize("field", ("installability", "product_support", "required_ci", "measured_evidence"))
def test_runtime_policy_rejects_an_exclusion_missing_a_distinct_dimension(field: str) -> None:
    document, lanes, workflow_cells = _policy_document()
    document["runtime_policy"]["exclusions"][0].pop(field)

    _, diagnostics = _validate_runtime_policy(document, lanes, workflow_cells)

    assert any(item["code"] == "runtime-policy-exclusion-dimensions-invalid" for item in diagnostics)


def test_runtime_policy_rejects_historical_runtime_rows_as_active_support() -> None:
    document, lanes, workflow_cells = _policy_document()
    stale_cell = document["runtime_policy"]["required_cells"][0].copy()
    stale_cell.update(
        {
            "id": "cpython-310-linux",
            "python": "3.10",
            "required_ci": {"status": "required", "workflow_cell": "cpython-310-linux", "tox_envs": []},
        }
    )
    document["runtime_policy"]["required_cells"].append(stale_cell)

    _, diagnostics = _validate_runtime_policy(document, lanes, workflow_cells)

    assert any(item["code"] == "runtime-policy-canonical-cells-invalid" for item in diagnostics)
    assert any(item["code"] == "runtime-policy-obsolete-active-runtime" for item in diagnostics)


def test_runtime_policy_rejects_a_missing_retired_pypy_exclusion() -> None:
    document, lanes, workflow_cells = _policy_document()
    document["runtime_policy"]["exclusions"] = [
        item
        for item in document["runtime_policy"]["exclusions"]
        if item["runtime"] != "PyPy" or item["python"] != "3.11"
    ]

    _, diagnostics = _validate_runtime_policy(document, lanes, workflow_cells)

    assert any(item["code"] == "runtime-policy-canonical-exclusions-invalid" for item in diagnostics)


def test_historical_capability_exclusions_are_source_backed_and_outside_active_policy() -> None:
    document = {
        "support_ledger": {
            "historical_capability_exclusions": [
                {
                    "id": f"pypy-{python}-windows-debug-mcp",
                    "runtime": "PyPy",
                    "python": python,
                    "platform": "windows",
                    "capability": "debug-mcp",
                    "status": "unsupported",
                    "historical_status": "retired-runtime",
                    "basis": "upstream-dependency-wheel-availability",
                    "reason": "pywin32 wheels only target CPython.",
                    "source_evidence": ["https://pypi.org/project/pywin32/310/"],
                }
                for python in ("3.10", "3.11")
            ]
        },
        "lanes": [],
    }

    summary, diagnostics = _validate_historical_capability_exclusions(document, [])

    assert diagnostics == []
    assert summary["count"] == 2
    assert {item["python"] for item in summary["entries"]} == {"3.10", "3.11"}


def test_historical_capability_exclusion_cannot_claim_an_active_runtime() -> None:
    document = {
        "support_ledger": {
            "historical_capability_exclusions": [
                {
                    "id": f"pypy-{python}-windows-debug-mcp",
                    "runtime": "PyPy",
                    "python": python,
                    "platform": "windows",
                    "capability": "debug-mcp",
                    "status": "unsupported",
                    "historical_status": "retired-runtime",
                    "basis": "upstream-dependency-wheel-availability",
                    "reason": "pywin32 wheels only target CPython.",
                    "source_evidence": ["https://pypi.org/project/pywin32/310/"],
                }
                for python in ("3.10", "3.11")
            ]
        },
        "lanes": [
            {"id": "pypy-311-windows", "runtime": "PyPy", "python": "3.11", "platform": "windows", "status": "required"}
        ],
    }

    _, diagnostics = _validate_historical_capability_exclusions(document, document["lanes"])

    assert any(item["code"] == "historical-capability-exclusion-runtime-active" for item in diagnostics)


def test_runtime_policy_rejects_missing_measured_evidence_fields() -> None:
    document, lanes, workflow_cells = _policy_document()
    document["runtime_policy"]["required_cells"][0]["measured_evidence"]["fields"].remove("architecture")

    _, diagnostics = _validate_runtime_policy(document, lanes, workflow_cells)

    assert any(item["code"] == "runtime-policy-evidence-fields-missing" for item in diagnostics)


def _optional_integration_records() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    environments = [
        "py313-pytest84-allure-coverage-lin",
        *(
            f"py314-pytestlatest-{gherkin}-xdist-coverage-{platform_suffix}"
            for gherkin in ("gherkin33", "gherkinlatest")
            for platform_suffix in ("lin", "mac", "win")
        ),
        "py314-debug-mcp",
        "py314-struct-bdd",
    ]
    workflow_cells = [
        {
            "id": environment,
            "job": "optional-integrations",
            "tox_envs": [environment],
        }
        for environment in environments
    ]
    lanes: list[dict[str, Any]] = []
    for cell in workflow_cells:
        environment = cell["tox_envs"][0]
        lane: dict[str, Any] = {
            "id": environment,
            "status": "required",
            "workflow_selector": environment,
            "tox_env": environment,
            "extras": [],
            "prerequisites": [],
        }
        if "allure" in environment:
            lane["extras"] = ["allure"]
            lane["prerequisites"] = [
                {"type": "python-package", "name": "allure-python-commons-test", "version": "2.16.0"}
            ] + [{"type": "command", "name": "uv"}]
        elif "debug-mcp" in environment:
            lane["extras"] = ["debug-mcp"]
            lane["prerequisites"] = [
                {"type": "python-package", "name": package, "version": requirement}
                for package, requirement in (
                    ("mcp-pdb", ">=0.6,<0.7"),
                    ("mcp", ">=1.24,<2"),
                    ("uvicorn", ">=0.34"),
                    ("pydantic", ">=2.0.3"),
                )
            ] + [{"type": "command", "name": "uv"}]
        elif "struct-bdd" in environment:
            lane["extras"] = ["struct-bdd"]
            lane["prerequisites"] = [
                {"type": "python-package", "name": package, "version": "latest"}
                for package in ("hjson", "json5", "pyhocon", "PyYAML")
            ] + [{"type": "command", "name": "uv"}]
        else:
            gherkin = "gherkin-official>=33,<34" if "gherkin33" in environment else "gherkin-official"
            lane["prerequisites"] = [
                {"type": "python-package", "name": "pytest-xdist", "version": "<4"},
                {"type": "python-package", "name": "gherkin-official", "requirement": gherkin},
            ]
        lanes.append(lane)

    document = {"project": {"evidence": {"aggregate_groups": ["optional"]}}, "runtime_policy": {"required_cells": []}}
    return document, lanes, workflow_cells


def test_optional_integration_policy_accepts_an_isolated_struct_bdd_lane() -> None:
    document, lanes, workflow_cells = _optional_integration_records()

    summary, diagnostics = _validate_optional_integration_inventory(document, lanes, workflow_cells)

    assert diagnostics == []
    assert summary["cellCount"] == 9
    assert summary["environmentCount"] == 9
    assert "py314-debug-mcp" in summary["environments"]
    assert "py314-struct-bdd" in summary["environments"]


def test_optional_integration_policy_requires_struct_bdd_packages_and_uv() -> None:
    document, lanes, workflow_cells = _optional_integration_records()
    struct_bdd_lane = next(lane for lane in lanes if lane["id"] == "py314-struct-bdd")
    struct_bdd_lane["prerequisites"] = [
        item for item in struct_bdd_lane["prerequisites"] if item.get("name") not in {"json5", "uv"}
    ]

    _, diagnostics = _validate_optional_integration_inventory(document, lanes, workflow_cells)

    assert any(item["code"] == "optional-struct-bdd-prerequisites-invalid" for item in diagnostics)


def test_optional_integration_policy_requires_debug_mcp_packages_and_uv() -> None:
    document, lanes, workflow_cells = _optional_integration_records()
    debug_mcp_lane = next(lane for lane in lanes if lane["id"] == "py314-debug-mcp")
    debug_mcp_lane["prerequisites"] = [
        item for item in debug_mcp_lane["prerequisites"] if item.get("name") not in {"mcp", "uv"}
    ]

    _, diagnostics = _validate_optional_integration_inventory(document, lanes, workflow_cells)

    assert any(item["code"] == "optional-debug-mcp-prerequisites-invalid" for item in diagnostics)
