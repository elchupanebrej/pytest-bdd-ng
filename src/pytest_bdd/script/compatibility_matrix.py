"""
CLI for compatibility matrix inspection and validation.

Responsibility:
    CLI for compatibility matrix inspection and validation. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.compatibility_matrix` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - parse_args: owns nested behavior below this boundary
    - _entry_payload: owns nested behavior below this boundary
    - _emit: owns nested behavior below this boundary
    - main: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates parser, args, summary, payload, python_factors; depends on __future__.annotations, argparse, json, sys,
    pathlib.Path.

Invariants:
    - `pytest_bdd.script.compatibility_matrix` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises SystemExit; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pytest_bdd.compatibility.runtime_compat import (
    REASON_COMPATIBLE,
    CompatibilityMatrixEntry,
    is_pair_compatible,
)
from pytest_bdd.util.matrix import (
    build_matrix,
    build_migration_coverage_summary,
    discover_feature_scenario_ids,
    discover_user_facing_test_scenario_ids,
    expand_tox_env_names,
    extract_factors_from_tox_ini,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Command-line arguments (defaults to sys.argv).

    Returns:
        Parsed arguments namespace.

    Responsibility:
        Parse command-line arguments. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.compatibility_matrix.parse_args` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.add_argument: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - argparse.ArgumentParser: collaborator call used by this boundary
        - parser.parse_args: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `parse_args`
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `parse_args`
        - src/pytest_bdd/scenario.py: imports or references `parse_args`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `parse_args`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `parse_args`

    State and side effects:
        mutates parser.

    Invariants:
        - `pytest_bdd.script.compatibility_matrix.parse_args` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    parser = argparse.ArgumentParser(description="Inspect Python/pytest compatibility matrix")
    parser.add_argument("--tox-ini", type=Path, default=Path("tox.ini"), help="Path to tox.ini")
    parser.add_argument("--python", dest="python_factor", help="Python factor without prefix, e.g. 314")
    parser.add_argument("--pytest", dest="pytest_factor", help="pytest factor, e.g. 90 or latest")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--list", action="store_true", help="List all matrix entries")
    parser.add_argument("--compatible-only", action="store_true", help="List only compatible entries")
    parser.add_argument(
        "--report-e2e-migration-threshold",
        action="store_true",
        help="Report user-facing E2E migration coverage from tests/feature to features/",
    )
    parser.add_argument("--tests-root", type=Path, default=Path("tests"), help="Path to tests root")
    parser.add_argument("--features-root", type=Path, default=Path("features"), help="Path to features root")
    parser.add_argument("--threshold-percent", type=int, default=80, help="Required migration coverage percent")
    return parser.parse_args(argv)


def _entry_payload(entry: CompatibilityMatrixEntry) -> dict[str, object]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.compatibility_matrix._entry_payload` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.compatibility_matrix._entry_payload` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """
    return {
        "pythonVersion": entry.python_version,
        "pytestVersion": entry.pytest_version,
        "isCompatible": entry.is_compatible,
        "isSupported": entry.is_supported,
        "reasonCode": entry.reason_code,
        "toxEnvName": entry.tox_env_name,
    }


def _emit(payload: str) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.compatibility_matrix._emit` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.compatibility_matrix._emit` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sys.stdout.write: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    sys.stdout.write(payload)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    """
    Run the compatibility matrix CLI.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code.

    Responsibility:
        Run the compatibility matrix CLI. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.compatibility_matrix.main` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _emit: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - parse_args: collaborator call used by this boundary
        - build_migration_coverage_summary: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `main`
        - src/pytest_bdd/script/__init__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__main__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/cli/facade.py: imports or references `main`

    State and side effects:
        mutates args, summary, payload, python_factors, pytest_factors.

    Invariants:
        - `pytest_bdd.script.compatibility_matrix.main` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    args = parse_args(argv)

    if args.report_e2e_migration_threshold:
        summary = build_migration_coverage_summary(
            tests_root=args.tests_root,
            features_root=args.features_root,
            threshold_percent=args.threshold_percent,
        )
        payload = {
            "totalUserFacingScenarios": summary.total_user_facing_scenarios,
            "userFacingInFeatures": summary.user_facing_in_features,
            "coveragePercent": summary.coverage_percent,
            "thresholdPercent": summary.threshold_percent,
            "thresholdMet": summary.threshold_met,
            "duplicatesInTests": summary.duplicates_in_tests,
            "featureScenarioIds": sorted(discover_feature_scenario_ids(args.features_root)),
            "userFacingTestScenarioIds": sorted(discover_user_facing_test_scenario_ids(args.tests_root)),
        }
        if args.json:
            _emit(json.dumps(payload, sort_keys=True))
        else:
            _emit(
                " ".join(
                    [
                        f"coverage={payload['coveragePercent']}%",
                        f"threshold={payload['thresholdPercent']}%",
                        f"duplicates={payload['duplicatesInTests']}",
                        f"status={'pass' if payload['thresholdMet'] else 'fail'}",
                    ],
                ),
            )
        return 0 if summary.threshold_met else 1

    python_factors, pytest_factors = extract_factors_from_tox_ini(args.tox_ini)
    entries = build_matrix(python_factors, pytest_factors)

    if args.python_factor and args.pytest_factor:
        compatible, reason = is_pair_compatible(args.python_factor, args.pytest_factor)
        pair_payload: dict[str, object] = {
            "pythonVersion": f"{args.python_factor[0]}.{args.python_factor[1:]}"
            if args.python_factor.isdigit() and len(args.python_factor) == 3  # noqa: PLR2004
            else args.python_factor,
            "pytestVersion": args.pytest_factor,
            "isCompatible": compatible,
            "isSupported": compatible,
            "reasonCode": reason,
            "message": "compatible pair" if reason == REASON_COMPATIBLE else f"unsupported pair: {reason}",
        }
        if args.json:
            _emit(json.dumps(pair_payload, sort_keys=True))
        else:
            _emit(str(pair_payload["message"]))
        return 0 if compatible else 1

    if args.list:
        result = entries if not args.compatible_only else [entry for entry in entries if entry.is_compatible]
        list_payload: list[dict[str, object]] = [_entry_payload(entry) for entry in result]
        if args.json:
            _emit(json.dumps({"entries": list_payload}, sort_keys=True))
        else:
            for item in list_payload:
                _emit(
                    f"{item['pythonVersion']}\t{item['pytestVersion']}\t{item['isCompatible']}\t"
                    f"{item['reasonCode']}\t{item['toxEnvName']}",
                )
        return 0

    tox_env_names = expand_tox_env_names(entries)
    if args.json:
        _emit(json.dumps({"toxEnvNames": tox_env_names}, sort_keys=True))
    else:
        _emit("\n".join(tox_env_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
