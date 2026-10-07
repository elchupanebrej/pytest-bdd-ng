"""CLI adapters for Cucumber Messages capability inventory and release governance."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytest_cuke.message_capability_governance import (
    build_capability_report,
    installed_capability_inventory,
    load_capability_ids_file,
    load_decisions_file,
    read_validated_ndjson,
)
from pytest_cuke.message_schema_sync import SchemaSyncError, resolve_upstream_release
from pytest_cuke.model.message_baseline_diff import (
    BaselineDiffRecord,
    baseline_diff_to_dict,
    build_baseline_diff,
)
from pytest_cuke.model.message_capability_inventory import (
    build_capability_inventory,
    capabilities_from_json,
    capability_inventory_to_dict,
)
from pytest_cuke.model.message_governance_checklist import (
    build_governance_checklist,
    checklist_to_dict,
    render_checklist_markdown,
)
from pytest_cuke.model.message_status_governance import CapabilityDecision, decision_to_dict

if TYPE_CHECKING:
    from pytest_cuke.model.message_capability import MessageCapability


def configure_capability_governance_parser(parser: argparse.ArgumentParser) -> None:
    """Add `messages capabilities` operations to the public `cuke` command tree."""
    actions = parser.add_subparsers(dest="capability_command", required=True)

    sync_parser = actions.add_parser("sync", help="build a capability inventory from a schema baseline")
    sync_parser.add_argument("--baseline-release", required=True, help="stable name of the schema baseline")
    sync_parser.add_argument(
        "--schema-dir",
        type=Path,
        help="schema directory for this baseline; defaults to the installed Cucumber Messages schemas",
    )
    sync_parser.add_argument("--output", type=Path, help="write the inventory JSON to this path")

    decision_parser = actions.add_parser("validate-decision", help="validate and normalize decision JSON")
    decision_parser.add_argument("--input", required=True, type=Path, help="decision JSON file")
    decision_parser.add_argument("--output", type=Path, help="write normalized decisions to this path")

    diff_parser = actions.add_parser("diff", help="compare capability baselines and their decisions")
    diff_parser.add_argument("--previous-baseline", required=True)
    diff_parser.add_argument("--current-baseline", required=True)
    diff_parser.add_argument("--previous", required=True, type=Path, help="previous synchronized inventory JSON")
    diff_parser.add_argument("--current", required=True, type=Path, help="current synchronized inventory JSON")
    diff_parser.add_argument("--previous-decisions", type=Path)
    diff_parser.add_argument("--current-decisions", type=Path)
    diff_parser.add_argument("--output", type=Path)

    checklist_parser = actions.add_parser("checklist", help="render a release governance checklist")
    checklist_parser.add_argument("--capabilities", required=True, type=Path, help="synchronized inventory JSON")
    checklist_parser.add_argument("--decisions", type=Path, help="optional decision JSON file")
    checklist_parser.add_argument("--mandatory-capabilities-file", type=Path)
    checklist_parser.add_argument("--baseline-diff", type=Path)
    checklist_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    checklist_parser.add_argument("--output", type=Path)

    report_parser = actions.add_parser("report", help="report field observations from Messages NDJSON")
    report_parser.add_argument("--messages-file", required=True, type=Path, help="Cucumber Messages NDJSON input")
    report_parser.add_argument(
        "--input-kind",
        required=True,
        choices=("runtime", "synthetic"),
        help="provenance of the NDJSON; synthetic data never satisfies runtime coverage",
    )
    report_parser.add_argument("--baseline-release", help="baseline label; defaults to installed schema version")
    report_parser.add_argument("--capabilities", type=Path, help="synchronized capability inventory JSON")
    report_parser.add_argument("--decisions", type=Path, help="optional capability decision JSON")
    report_parser.add_argument("--mandatory-capabilities-file", type=Path)
    report_parser.add_argument("--runtime-required-capabilities-file", type=Path)
    report_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    report_parser.add_argument("--output", type=Path)
    report_parser.add_argument(
        "--require-fully-governed",
        action="store_true",
        help="fail if any mandatory capability lacks an Implemented decision",
    )
    report_parser.add_argument(
        "--require-runtime-required-covered",
        action="store_true",
        help="fail if any runtime-required capability is not present in runtime NDJSON",
    )
    report_parser.add_argument(
        "--require-non-runtime-classified",
        action="store_true",
        help="fail if uncovered relevant non-runtime capabilities lack an explicit classification",
    )


def _read_json(path: Path, *, description: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {description} {path}: {error}") from error


def _inventory(path: Path) -> tuple[str, tuple[MessageCapability, ...]]:
    payload = _read_json(path, description="capability inventory")
    if not isinstance(payload, dict):
        raise ValueError(f"capability inventory must be a JSON object: {path}")
    baseline_release = payload.get("baseline_release")
    if not isinstance(baseline_release, str) or not baseline_release.strip():
        raise ValueError(f"capability inventory is missing baseline_release: {path}")
    return baseline_release, capabilities_from_json(payload)


def _decision_records(path: Path | None) -> tuple[CapabilityDecision, ...]:
    if path is None:
        return ()
    return load_decisions_file(path)


def _scope(path: Path | None) -> tuple[str, ...]:
    return load_capability_ids_file(path) if path is not None else ()


def _json_text(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_text(text: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(text)
        return
    parent = output.parent if output.parent != Path("") else Path(".")
    try:
        parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=parent,
                prefix=f".{output.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temp_path = Path(stream.name)
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, output)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
    except OSError as error:
        raise ValueError(f"cannot write output {output}: {error}") from error


def _reject_output_input_alias(output: Path | None, input_paths: tuple[Path | None, ...]) -> None:
    if output is None:
        return
    for input_path in input_paths:
        if input_path is None:
            continue
        try:
            aliases_input = output.resolve() == input_path.resolve() or (
                output.exists() and input_path.exists() and os.path.samefile(output, input_path)
            )
        except (OSError, RuntimeError) as error:
            raise ValueError(f"cannot compare output path {output} with input path {input_path}: {error}") from error
        if aliases_input:
            raise ValueError(f"output path {output} resolves to input file {input_path} and cannot replace it")


def _load_baseline_diff(path: Path | None) -> object | None:
    if path is None:
        return None
    payload = _read_json(path, description="baseline diff")
    if not isinstance(payload, dict):
        raise ValueError(f"baseline diff must be a JSON object: {path}")
    required = ("previous_baseline", "current_baseline")
    if any(not isinstance(payload.get(field), str) for field in required):
        raise ValueError(f"baseline diff is missing required baseline metadata: {path}")
    fields = (
        "added_capability_ids",
        "changed_capability_ids",
        "removed_capability_ids",
        "added_decision_ids",
        "changed_decision_ids",
        "removed_decision_ids",
    )
    values: dict[str, tuple[str, ...]] = {}
    for field in fields:
        raw = payload.get(field, [])
        if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
            raise ValueError(f"baseline diff field {field!r} must be an array of strings")
        values[field] = tuple(raw)
    return BaselineDiffRecord(
        previous_baseline=cast("str", payload["previous_baseline"]),
        current_baseline=cast("str", payload["current_baseline"]),
        **values,
    )


def _load_installed_or_explicit_inventory(
    path: Path | None,
    baseline_release: str | None,
) -> tuple[str, tuple[MessageCapability, ...]]:
    if path is not None:
        inventory_release, capabilities = _inventory(path)
        if baseline_release is not None and baseline_release != inventory_release:
            raise ValueError(
                f"requested baseline {baseline_release!r} does not match inventory baseline {inventory_release!r}"
            )
        return inventory_release, capabilities
    installed_release, _ = resolve_upstream_release()
    selected_release = baseline_release or installed_release
    if selected_release != installed_release:
        raise ValueError(
            f"baseline {selected_release!r} is not available in the installed schemas; pass --capabilities "
            "with a synchronized inventory for that baseline"
        )
    installed_release, capabilities = installed_capability_inventory()
    return installed_release, capabilities


def _format_report(report: dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return _json_text(report)
    summary = cast("dict[str, object]", report["summary"])
    observations = cast("dict[str, object]", report["observations"])
    scope = cast("dict[str, object]", report["scope"])
    decisions = cast("list[dict[str, object]]", report["decisions"])
    gates = cast("dict[str, object]", report["gates"])
    rows = [
        f"# Cucumber Messages capability report ({report['baseline_release']})",
        "",
        f"Observation source: `{observations['source_kind']}`",
        f"NDJSON records: {observations['record_count']}",
        "",
        "## Summary",
        "",
    ]
    for name, value in sorted(summary.items()):
        rows.append(f"- {name.replace('_', ' ').title()}: {value}")
    rows.extend(["", "## Scope", "", "### Mandatory", ""])
    rows.extend(f"- `{item}`" for item in cast("list[str]", scope["mandatory_capability_ids"]))
    rows.extend(["", "### Runtime required", ""])
    rows.extend(f"- `{item}`" for item in cast("list[str]", scope["runtime_required_capability_ids"]))
    rows.extend(["", "## Observed fields", ""])
    observed_ids = cast("list[str]", observations["capability_ids"])
    rows.extend(f"- `{item}`" for item in observed_ids)
    if not observed_ids:
        rows.append("- None")
    rows.extend(
        [
            "",
            "## Decisions",
            "",
            "| Capability | Release | Status | Comment |",
            "| --- | --- | --- | --- |",
        ]
    )
    for decision in decisions:
        comment = str(decision.get("comment", "")).replace("|", "\\|").replace("\n", " ")
        rows.append(
            f"| `{decision['capability_id']}` | {decision['release_target']} | {decision['status']} | {comment} |"
        )
    if not decisions:
        rows.append("| — | — | — | — |")
    failures = cast("list[str]", gates["failures"])
    rows.extend(["", "## Gate result", "", "Passed" if gates["passed"] else "Failed", ""])
    rows.extend(f"- {failure}" for failure in failures)
    rows.extend(
        [
            "",
            "## Capabilities",
            "",
            "| Capability | Status | Runtime | Synthetic |",
            "| --- | --- | --- | --- |",
        ]
    )
    for capability in cast("list[dict[str, object]]", report["capabilities"]):
        rows.append(
            f"| `{capability['capability_id']}` | {capability['status']} | "
            f"{'yes' if capability['observed_runtime'] else 'no'} | "
            f"{'yes' if capability['observed_sample'] else 'no'} |"
        )
    return "\n".join(rows) + "\n"


def _run_action(arguments: argparse.Namespace) -> tuple[int, str, bool]:
    action = arguments.capability_command
    if action == "sync":
        baseline = arguments.baseline_release
        if arguments.schema_dir is None:
            installed_baseline, _ = resolve_upstream_release()
            if baseline != installed_baseline:
                raise ValueError(
                    f"requested baseline {baseline!r} does not match installed schema baseline "
                    f"{installed_baseline!r}; pass --schema-dir for another schema source"
                )
            schema_dir = Path(__file__).parent / "model" / "message_schemas"
        else:
            schema_dir = arguments.schema_dir
        schema_inputs = tuple(schema_dir.rglob("*.json")) if schema_dir.is_dir() else (schema_dir,)
        _reject_output_input_alias(arguments.output, schema_inputs)
        capabilities = build_capability_inventory(schema_dir, baseline_release=baseline)
        payload = capability_inventory_to_dict(capabilities, baseline_release=baseline)
        return (0, _json_text(payload), False)

    if action == "validate-decision":
        _reject_output_input_alias(arguments.output, (arguments.input,))
        decisions = load_decisions_file(arguments.input)
        return (0, _json_text({"decisions": [decision_to_dict(item) for item in decisions]}), False)

    if action == "diff":
        _reject_output_input_alias(
            arguments.output,
            (
                arguments.previous,
                arguments.current,
                arguments.previous_decisions,
                arguments.current_decisions,
            ),
        )
        previous_baseline, previous_capabilities = _inventory(arguments.previous)
        current_baseline, current_capabilities = _inventory(arguments.current)
        if previous_baseline != arguments.previous_baseline:
            raise ValueError(
                f"previous inventory baseline {previous_baseline!r} does not match requested "
                f"{arguments.previous_baseline!r}"
            )
        if current_baseline != arguments.current_baseline:
            raise ValueError(
                f"current inventory baseline {current_baseline!r} does not match requested "
                f"{arguments.current_baseline!r}"
            )
        diff = build_baseline_diff(
            previous_baseline=previous_baseline,
            current_baseline=current_baseline,
            previous_capabilities=previous_capabilities,
            current_capabilities=current_capabilities,
            previous_decisions=_decision_records(arguments.previous_decisions),
            current_decisions=_decision_records(arguments.current_decisions),
        )
        return (0, _json_text(baseline_diff_to_dict(diff)), False)

    if action == "checklist":
        _reject_output_input_alias(
            arguments.output,
            (
                arguments.capabilities,
                arguments.decisions,
                arguments.mandatory_capabilities_file,
                arguments.baseline_diff,
            ),
        )
        baseline, capabilities = _inventory(arguments.capabilities)
        decisions = _decision_records(arguments.decisions)
        mandatory = _scope(arguments.mandatory_capabilities_file)
        baseline_diff = _load_baseline_diff(arguments.baseline_diff)
        checklist = build_governance_checklist(
            capabilities,
            decisions,
            baseline_release=baseline,
            mandatory_capability_ids=mandatory,
            baseline_diff=cast("BaselineDiffRecord | None", baseline_diff),
        )
        text = (
            _json_text(checklist_to_dict(checklist))
            if arguments.format == "json"
            else render_checklist_markdown(checklist)
        )
        return (0, text, False)

    if action == "report":
        _reject_output_input_alias(
            arguments.output,
            (
                arguments.messages_file,
                arguments.capabilities,
                arguments.decisions,
                arguments.mandatory_capabilities_file,
                arguments.runtime_required_capabilities_file,
            ),
        )
        baseline, capabilities = _load_installed_or_explicit_inventory(
            arguments.capabilities,
            arguments.baseline_release,
        )
        envelopes = read_validated_ndjson(arguments.messages_file)
        report = build_capability_report(
            envelopes,
            capabilities=capabilities,
            decisions=_decision_records(arguments.decisions),
            baseline_release=baseline,
            input_kind=arguments.input_kind,
            mandatory_capability_ids=_scope(arguments.mandatory_capabilities_file),
            runtime_required_capability_ids=_scope(arguments.runtime_required_capabilities_file),
            require_fully_governed=arguments.require_fully_governed,
            require_runtime_required_covered=arguments.require_runtime_required_covered,
            require_non_runtime_classified=arguments.require_non_runtime_classified,
        )
        passed = cast("bool", cast("dict[str, object]", report["gates"])["passed"])
        return (0 if passed else 1, _format_report(report, arguments.format), True)

    raise ValueError(f"unknown capability governance command: {action}")


def run_capability_governance_command(arguments: argparse.Namespace) -> int:
    """Run a parsed command and report actionable errors without false-success output."""
    try:
        exit_code, output, is_report = _run_action(arguments)
        _write_text(output, arguments.output)
        if is_report and exit_code != 0:
            report = json.loads(output) if arguments.format == "json" else None
            if report is not None:
                failures = cast("list[str]", cast("dict[str, object]", report["gates"])["failures"])
                for failure in failures:
                    print(f"cuke messages capabilities report: {failure}", file=sys.stderr)
        return exit_code
    except (OSError, TypeError, ValueError, KeyError, SchemaSyncError) as error:
        print(f"cuke messages capabilities {arguments.capability_command}: error: {error}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    """Standalone dispatcher used by the installed `cuke` command and tests."""
    parser = argparse.ArgumentParser(prog="cuke messages capabilities")
    configure_capability_governance_parser(parser)
    return run_capability_governance_command(parser.parse_args(argv))


__all__ = ["configure_capability_governance_parser", "main", "run_capability_governance_command"]
