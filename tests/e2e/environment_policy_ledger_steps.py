"""Independent historical baseline acceptance for the environment support ledger."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pytest_cuke import given, then, when


_HISTORICAL_BASELINE_PATH = Path("tests/fixtures/compatibility/historical-environment-baseline.yaml")
_MUTATION_TOX_ENV = "py314-pytestlatest-mypy-messages"


@dataclass
class HistoricalEnvironmentBaselineContext:
    consumer: Any
    baseline: dict[str, Any]
    baseline_path: Path
    mutation_row: dict[str, Any] | None = None
    mutation_gaps: list[str] | None = None


def _inventory_context(consumer: Any) -> Any:
    context = getattr(consumer, "_environment_inventory_context", None)
    assert context is not None, "the repository environment inventory has not been loaded"
    return context


def _live_inventory(context: HistoricalEnvironmentBaselineContext) -> dict[str, Any]:
    document = _inventory_context(context.consumer).document
    assert isinstance(document, dict), document
    return document


def _support_ledger(document: dict[str, Any]) -> dict[str, Any]:
    ledger = document.get("support_ledger")
    assert isinstance(ledger, dict), "config/env-matrix.yaml must contain support_ledger"
    return ledger


def _historical_rows(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    families = baseline.get("historical_tox_families")
    assert isinstance(families, list) and families, "the frozen baseline must contain tox selector families"
    rows: dict[str, dict[str, Any]] = {}
    for family in families:
        assert isinstance(family, dict), family
        family_id = family.get("id")
        source_evidence = family.get("source_evidence")
        environments = family.get("environments")
        assert isinstance(family_id, str) and family_id, family
        assert isinstance(source_evidence, list) and source_evidence, family
        assert isinstance(environments, list), family
        for environment in environments:
            assert isinstance(environment, dict), environment
            tox_env = environment.get("tox_env")
            disposition = environment.get("disposition")
            assert isinstance(tox_env, str) and tox_env, environment
            assert disposition in {"required", "manual", "excluded"}, environment
            row = {
                "id": f"r-tox-{tox_env}",
                "tox_env": tox_env,
                "disposition": disposition,
                "family_id": family_id,
                "source_evidence": list(source_evidence),
            }
            previous = rows.get(tox_env)
            if previous is not None:
                assert previous["disposition"] == disposition, (previous, row)
                previous["family_ids"].append(family_id)
                previous["source_evidence"].extend(source_evidence)
            else:
                row["family_ids"] = [family_id]
                rows[tox_env] = row
    result = list(rows.values())
    assert len(result) == 68, f"the pinned R tox selectors should resolve to 68 unique environments, got {len(result)}"
    assert sum(row["disposition"] == "required" for row in result) == 46, result
    assert sum(row["disposition"] == "manual" for row in result) == 7, result
    assert sum(row["disposition"] == "excluded" for row in result) == 15, result
    exclusions = baseline.get("historical_exclusions")
    assert isinstance(exclusions, list) and len(exclusions) == 15, exclusions
    excluded_names = {row["tox_env"] for row in result if row["disposition"] == "excluded"}
    exclusion_names = {entry.get("tox_env") for entry in exclusions if isinstance(entry, dict)}
    assert excluded_names == exclusion_names, (excluded_names, exclusion_names)
    return result


def _tuple_key(entry: dict[str, Any], fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(entry.get(field, "")) for field in fields)


def _evidence_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _contains_url(value: Any) -> bool:
    return bool(re.search(r"https?://\S+", _evidence_text(value)))


def _cell_source(cell: dict[str, Any]) -> Any:
    return cell.get("source_evidence", cell.get("source"))


def _historical_tox_coordinates(tox_env: str) -> tuple[str, str, str] | None:
    parts = tox_env.split("-")
    if len(parts) < 2:
        return None
    factor = parts[0]
    if factor.startswith("pypy"):
        runtime = "PyPy"
        version_digits = factor.removeprefix("pypy")
    elif factor.startswith("py"):
        runtime = "CPython"
        version_digits = factor.removeprefix("py")
    else:
        return None
    if len(version_digits) < 2 or not version_digits.isdigit():
        return None
    platform = {"lin": "linux", "mac": "macos", "win": "windows"}.get(parts[-1])
    if platform is None:
        return None
    python = f"{version_digits[0]}.{version_digits[1:]}"
    return runtime, python, platform


def _current_policy_exclusion(
    document: dict[str, Any],
    runtime: str,
    python: str,
    platform: str,
    subject: str,
    gaps: list[str],
) -> dict[str, Any] | None:
    runtime_inventory = document.get("runtime_inventory")
    exclusions = runtime_inventory.get("exclusions") if isinstance(runtime_inventory, dict) else None
    if not isinstance(exclusions, list):
        gaps.append("runtime_inventory.exclusions is missing or is not a list")
        return None
    matches = [
        row
        for row in exclusions
        if isinstance(row, dict)
        and row.get("runtime") == runtime
        and str(row.get("python")) == python
        and row.get("platform") in {platform, "all", "any"}
    ]
    if len(matches) > 1:
        gaps.append(f"multiple current runtime exclusions cover {subject}: {[row.get('id') for row in matches]!r}")
        return None
    if not matches:
        return None
    exclusion = matches[0]
    evidence = exclusion.get("evidence")
    source = evidence.get("source") if isinstance(evidence, dict) else None
    if not str(exclusion.get("exclusion_reason", "")).strip() or not _contains_url(source):
        gaps.append(f"current runtime exclusion lacks a source-backed reason for {subject}: {exclusion.get('id')!r}")
    return exclusion


def _tox_environment_names(consumer: Any) -> set[str]:
    environment = consumer.env.copy()
    python_directory = str(Path(consumer.python).resolve().parent)
    path_entries = [python_directory, *environment.get("PATH", os.defpath).split(os.pathsep)]
    environment["PATH"] = os.pathsep.join(dict.fromkeys(path_entries))
    result = subprocess.run(
        ["tox", "list", "--no-desc"],
        cwd=consumer.path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"real tox list failed: {result.stdout}\n{result.stderr}"
    return {
        line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("All environments:")
    }


def _lane_tox_environments(lane: dict[str, Any]) -> set[str]:
    value = lane.get("tox_env", [])
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _workflow_tox_environments(document: dict[str, Any]) -> set[str]:
    cells = document.get("workflow_cells")
    assert isinstance(cells, list), "config/env-matrix.yaml must contain workflow_cells"
    result: set[str] = set()
    for cell in cells:
        assert isinstance(cell, dict), cell
        value = cell.get("tox_envs", [])
        if isinstance(value, str):
            result.update(part.strip() for part in value.split(",") if part.strip())
        elif isinstance(value, list):
            result.update(str(item).strip() for item in value if str(item).strip())
    return result


def _baseline_gaps(
    baseline: dict[str, Any],
    document: dict[str, Any],
    tox_names: set[str],
) -> list[str]:
    gaps: list[str] = []
    ledger = document.get("support_ledger")
    if not isinstance(ledger, dict):
        return ["support_ledger is missing"]

    expected_reference = baseline.get("historical_reference")
    actual_reference = ledger.get("historical_reference")
    if actual_reference != expected_reference:
        gaps.append(f"historical_reference differs: expected {expected_reference!r}, got {actual_reference!r}")

    expected_cells = baseline.get("historical_cells")
    actual_cells = ledger.get("historical_cells")
    if not isinstance(expected_cells, list) or not isinstance(actual_cells, list):
        gaps.append("historical_cells is missing or is not a list")
        expected_cells = expected_cells if isinstance(expected_cells, list) else []
        actual_cells = actual_cells if isinstance(actual_cells, list) else []
    cell_fields = ("runtime", "python", "platform")
    expected_cell_map = {_tuple_key(cell, cell_fields): cell for cell in expected_cells if isinstance(cell, dict)}
    actual_cell_map: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for cell in actual_cells:
        if isinstance(cell, dict):
            actual_cell_map.setdefault(_tuple_key(cell, cell_fields), []).append(cell)
    for key, expected in expected_cell_map.items():
        matches = actual_cell_map.get(key, [])
        source = _evidence_text(expected.get("source_evidence", []))
        if len(matches) != 1:
            gaps.append(
                f"historical workflow cell {expected.get('id', key)!r} is missing or duplicated; source={source}"
            )
            continue
        actual = matches[0]
        if actual.get("disposition") != expected.get("disposition"):
            gaps.append(f"historical workflow cell {key!r} has wrong disposition; source={source}")
        if not _contains_url(_cell_source(actual)):
            gaps.append(f"historical workflow cell {key!r} has no source URL; source={source}")
    if set(actual_cell_map) != set(expected_cell_map):
        gaps.append(
            "historical workflow cell tuples differ: "
            f"missing={sorted(set(expected_cell_map) - set(actual_cell_map))}, "
            f"unexpected={sorted(set(actual_cell_map) - set(expected_cell_map))}"
        )

    workflow_cells = document.get("workflow_cells")
    workflow_cell_map: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    if isinstance(workflow_cells, list):
        for cell in workflow_cells:
            if isinstance(cell, dict) and cell.get("job") == "full-matrix":
                workflow_cell_map.setdefault(_tuple_key(cell, cell_fields), []).append(cell)
    else:
        gaps.append("workflow_cells is missing or is not a list")
    for key, expected in expected_cell_map.items():
        runtime, python, platform = key
        exclusion = _current_policy_exclusion(
            document,
            runtime,
            python,
            platform,
            f"historical workflow cell {expected.get('id', key)!r}",
            gaps,
        )
        current_workflow_cells = workflow_cell_map.get(key, [])
        if exclusion is not None:
            if current_workflow_cells:
                gaps.append(
                    f"retired historical workflow cell remains selected by current policy: {key!r}; "
                    f"exclusion={exclusion.get('id')!r}"
                )
            continue
        if len(current_workflow_cells) != 1:
            gaps.append(
                f"workflow selector inventory does not preserve historical cell {key!r}; source={_evidence_text(expected.get('source_evidence', []))}"
            )

    lanes = document.get("lanes")
    if not isinstance(lanes, list):
        gaps.append("lanes is missing or is not a list")
        lanes = []
    lane_ids = {str(lane.get("id")) for lane in lanes if isinstance(lane, dict) and lane.get("id")}
    lane_environment_pairs = {
        (str(lane.get("id")), tox_env)
        for lane in lanes
        if isinstance(lane, dict) and lane.get("id")
        for tox_env in _lane_tox_environments(lane)
    }
    workflow_tox_names = (
        _workflow_tox_environments(document) if isinstance(document.get("workflow_cells"), list) else set()
    )
    provenance = ledger.get("lane_provenance")
    if not isinstance(provenance, list):
        gaps.append("support_ledger.lane_provenance is missing or is not a list")
        provenance = []
    provenance_by_tox: dict[str, list[dict[str, Any]]] = {}
    for entry in provenance:
        if isinstance(entry, dict) and isinstance(entry.get("tox_env"), str):
            provenance_by_tox.setdefault(entry["tox_env"], []).append(entry)

    expected_rows = _historical_rows(baseline)
    for expected in expected_rows:
        tox_env = expected["tox_env"]
        row_id = expected["id"]
        source = _evidence_text(expected["source_evidence"])
        disposition = expected["disposition"]
        matches = provenance_by_tox.get(tox_env, [])
        coordinates = _historical_tox_coordinates(tox_env)
        exclusion = (
            _current_policy_exclusion(
                document,
                *coordinates,
                f"historical tox environment {row_id} ({tox_env})",
                gaps,
            )
            if coordinates is not None
            else None
        )
        if disposition == "required" and exclusion is not None:
            if tox_env in tox_names or matches or tox_env in workflow_tox_names:
                gaps.append(
                    f"retired historical tox environment remains active: {row_id} ({tox_env}); "
                    f"exclusion={exclusion.get('id')!r}; source={source}"
                )
            continue
        if disposition == "excluded":
            if tox_env in tox_names:
                gaps.append(f"excluded historical tox environment is active: {row_id} ({tox_env}); source={source}")
            if matches:
                gaps.append(
                    f"excluded historical tox environment has lane provenance: {row_id} ({tox_env}); source={source}"
                )
            if tox_env in workflow_tox_names:
                gaps.append(
                    f"excluded historical tox environment is selected by workflow: {row_id} ({tox_env}); source={source}"
                )
            continue
        if tox_env not in tox_names:
            gaps.append(
                f"historical tox environment is missing from resolved tox: {row_id} ({tox_env}); source={source}"
            )
        if len(matches) != 1:
            gaps.append(f"historical lane provenance is missing or duplicated: {row_id} ({tox_env}); source={source}")
            continue
        actual = matches[0]
        if actual.get("id") != row_id:
            gaps.append(
                f"historical lane provenance ID differs for {tox_env}: expected {row_id}, got {actual.get('id')!r}; source={source}"
            )
        if actual.get("disposition") != disposition:
            gaps.append(f"historical lane provenance disposition differs for {row_id} ({tox_env}); source={source}")
        if actual.get("origin") not in {"historical", "restored"}:
            gaps.append(f"historical lane provenance has invalid origin for {row_id} ({tox_env}); source={source}")
        lane_id = actual.get("lane_id")
        if lane_id not in lane_ids or (str(lane_id), tox_env) not in lane_environment_pairs:
            gaps.append(f"historical lane inventory entry is missing for {row_id} ({tox_env}); source={source}")
        if not _contains_url(actual.get("source_evidence")):
            gaps.append(f"historical lane provenance has no source URL for {row_id} ({tox_env}); source={source}")
        if disposition == "required" and tox_env not in workflow_tox_names:
            gaps.append(
                f"required historical tox environment has no workflow selector: {row_id} ({tox_env}); source={source}"
            )
        if disposition == "manual" and tox_env in workflow_tox_names:
            gaps.append(
                f"manual historical tox environment is selected by workflow: {row_id} ({tox_env}); source={source}"
            )

    expected_exclusions = baseline.get("historical_exclusions")
    actual_exclusions = ledger.get("exclusions")
    if not isinstance(expected_exclusions, list) or not isinstance(actual_exclusions, list):
        gaps.append("support_ledger.exclusions is missing or is not a list")
        expected_exclusions = expected_exclusions if isinstance(expected_exclusions, list) else []
        actual_exclusions = actual_exclusions if isinstance(actual_exclusions, list) else []
    exclusion_fields = ("runtime", "python", "pytest", "platform")
    expected_exclusion_map = {
        _tuple_key(entry, exclusion_fields): entry for entry in expected_exclusions if isinstance(entry, dict)
    }
    actual_exclusion_map: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for entry in actual_exclusions:
        if isinstance(entry, dict):
            actual_exclusion_map.setdefault(_tuple_key(entry, exclusion_fields), []).append(entry)
    for key, expected in expected_exclusion_map.items():
        source = _evidence_text(expected.get("source_evidence", []))
        matches = actual_exclusion_map.get(key, [])
        if len(matches) != 1:
            gaps.append(f"historical exclusion is missing or duplicated: {expected.get('id', key)!r}; source={source}")
            continue
        actual = matches[0]
        if not actual.get("basis") or not actual.get("reason") or not _contains_url(actual.get("source_evidence")):
            gaps.append(f"historical exclusion is not source-backed: {expected.get('id', key)!r}; source={source}")
    if set(actual_exclusion_map) != set(expected_exclusion_map):
        gaps.append(
            "historical exclusion tuples differ: "
            f"missing={sorted(set(expected_exclusion_map) - set(actual_exclusion_map))}, "
            f"unexpected={sorted(set(actual_exclusion_map) - set(expected_exclusion_map))}"
        )
    return gaps


def _remove_tox_environment(tox_path: Path, tox_env: str) -> None:
    lines = tox_path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_tox_section = False
    env_list_line_found = False
    retained: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_tox_section = stripped == "[tox]"
        if in_tox_section and stripped == tox_env:
            env_list_line_found = True
            continue
        retained.append(line)
    assert env_list_line_found, f"tox.ini does not contain the exact historical selector {tox_env!r}"

    section_header = f"[testenv:{tox_env}]"
    section_index = next((index for index, line in enumerate(retained) if line.strip() == section_header), None)
    assert section_index is not None, f"tox.ini does not contain the dedicated environment section {section_header!r}"
    section_end = next(
        (index for index in range(section_index + 1, len(retained)) if retained[index].strip().startswith("[")),
        len(retained),
    )
    del retained[section_index:section_end]
    tox_path.write_text("".join(retained), encoding="utf-8")


def _remove_tox_name_from_command(command: str, tox_env: str) -> str:
    parts = command.split()
    for index, part in enumerate(parts):
        names = part.split(",")
        if tox_env not in names:
            continue
        remaining = [name for name in names if name != tox_env]
        if remaining:
            parts[index] = ",".join(remaining)
        else:
            del parts[index]
            if index and parts[index - 1] in {"-e", "--env"}:
                del parts[index - 1]
        break
    return " ".join(parts)


@given("the pinned R support baseline is loaded", target_fixture="historical_environment_baseline")
def pinned_r_support_baseline_is_loaded(request: Any, consumer: Any) -> HistoricalEnvironmentBaselineContext:
    baseline_path = Path(request.config.rootpath) / _HISTORICAL_BASELINE_PATH
    baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    assert isinstance(baseline, dict), baseline
    assert len(_historical_rows(baseline)) == 68
    _inventory_context(consumer)
    return HistoricalEnvironmentBaselineContext(consumer, baseline, baseline_path)


@then(
    "the live support ledger should retain the pinned cells and classify retired cells with source-backed policy exclusions"
)
def live_support_ledger_retains_historical_cells_and_current_exclusions(
    historical_environment_baseline: HistoricalEnvironmentBaselineContext,
) -> None:
    context = historical_environment_baseline
    tox_names = _tox_environment_names(context.consumer)
    gaps = _baseline_gaps(context.baseline, _live_inventory(context), tox_names)
    assert not gaps, "historical environment baseline gaps:\n- " + "\n- ".join(gaps)


@then("historical incompatible tox environments should remain source-backed exclusions")
def historical_incompatible_tox_environments_are_excluded(
    historical_environment_baseline: HistoricalEnvironmentBaselineContext,
) -> None:
    context = historical_environment_baseline
    excluded = [row for row in _historical_rows(context.baseline) if row["disposition"] == "excluded"]
    tox_names = _tox_environment_names(context.consumer)
    active = [row for row in excluded if row["tox_env"] in tox_names]
    assert not active, [
        f"{row['id']} ({row['tox_env']}) remains active; source={_evidence_text(row['source_evidence'])}"
        for row in active
    ]
    ledger = _support_ledger(_live_inventory(context))
    actual = ledger.get("exclusions")
    assert isinstance(actual, list), actual
    source_backed = [
        row
        for row in actual
        if isinstance(row, dict)
        and row.get("basis")
        and row.get("reason")
        and _contains_url(row.get("source_evidence"))
    ]
    expected = context.baseline.get("historical_exclusions", [])
    expected_keys = {_tuple_key(row, ("runtime", "python", "pytest", "platform")) for row in expected}
    actual_keys = {_tuple_key(row, ("runtime", "python", "pytest", "platform")) for row in source_backed}
    assert expected_keys <= actual_keys, (
        f"historical exclusions lack source-backed live entries: {sorted(expected_keys - actual_keys)}"
    )


@when("I remove one viable historical lane from the isolated ledger inventory and tox config")
def remove_viable_historical_lane_from_isolated_inputs(
    historical_environment_baseline: HistoricalEnvironmentBaselineContext,
) -> None:
    context = historical_environment_baseline
    expected = next(row for row in _historical_rows(context.baseline) if row["tox_env"] == _MUTATION_TOX_ENV)
    assert expected["disposition"] == "required", expected
    document = _live_inventory(context)
    ledger = _support_ledger(document)
    provenance = ledger.get("lane_provenance")
    assert isinstance(provenance, list), provenance
    matching = [row for row in provenance if isinstance(row, dict) and row.get("tox_env") == _MUTATION_TOX_ENV]
    assert len(matching) == 1 and matching[0].get("id") == expected["id"], matching
    provenance.remove(matching[0])

    lanes = document.get("lanes")
    assert isinstance(lanes, list), lanes
    inventory_hits = 0
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        names = _lane_tox_environments(lane)
        if _MUTATION_TOX_ENV not in names:
            continue
        inventory_hits += 1
        remaining = sorted(names - {_MUTATION_TOX_ENV})
        lane["tox_env"] = ",".join(remaining)
        command = lane.get("command")
        if isinstance(command, str):
            lane["command"] = _remove_tox_name_from_command(command, _MUTATION_TOX_ENV)
    assert inventory_hits == 1, f"expected one inventory lane containing {_MUTATION_TOX_ENV}, found {inventory_hits}"

    cells = document.get("workflow_cells")
    assert isinstance(cells, list), cells
    workflow_hits = 0
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        value = cell.get("tox_envs", [])
        if isinstance(value, str):
            names = [part.strip() for part in value.split(",") if part.strip()]
            if _MUTATION_TOX_ENV in names:
                workflow_hits += 1
                cell["tox_envs"] = [name for name in names if name != _MUTATION_TOX_ENV]
        elif isinstance(value, list) and _MUTATION_TOX_ENV in value:
            workflow_hits += 1
            cell["tox_envs"] = [name for name in value if name != _MUTATION_TOX_ENV]
    assert workflow_hits >= 1, f"expected a workflow inventory reference to {_MUTATION_TOX_ENV}"

    inventory_path = context.consumer.path / "config" / "env-matrix.yaml"
    inventory_path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tox_path = context.consumer.path / "tox.ini"
    _remove_tox_environment(tox_path, _MUTATION_TOX_ENV)
    tox_names = _tox_environment_names(context.consumer)
    assert _MUTATION_TOX_ENV not in tox_names, f"the selected tox environment still resolves: {tox_names!r}"

    context.mutation_row = expected
    context.mutation_gaps = _baseline_gaps(context.baseline, document, tox_names)


@then("the independent historical baseline should report the missing lane ID and pinned source")
def independent_baseline_reports_missing_historical_lane(
    historical_environment_baseline: HistoricalEnvironmentBaselineContext,
) -> None:
    context = historical_environment_baseline
    row = context.mutation_row
    gaps = context.mutation_gaps
    assert row is not None and gaps is not None, "the historical lane mutation has not run"
    source = _evidence_text(row["source_evidence"])
    matching = [gap for gap in gaps if row["id"] in gap and row["tox_env"] in gap]
    assert matching, f"the independent baseline did not detect removed lane {row['id']} ({row['tox_env']}): {gaps!r}"
    assert any(source_part in "\n".join(matching) for source_part in source.split(", ")), (
        f"the missing-lane diagnostic omitted pinned source evidence {source!r}: {matching!r}"
    )
