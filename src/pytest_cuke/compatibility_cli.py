"""Command-line adapter for compatibility inspection and migration auditing."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pytest_cuke.compatibility.matrix import (
    CompatibilityConfig,
    CompatibilityConfigurationError,
    build_matrix,
    entry_payload,
    expanded_tox_env_names,
    load_compatibility_config,
    pair_entry,
)
from pytest_cuke.compatibility.migration_audit import MigrationAuditError, build_migration_audit

if TYPE_CHECKING:
    import argparse


_REASON_MESSAGES = {
    "compatible": "supported by the project and the selected pytest compatibility policy",
    "python_not_supported_by_pytest": "the selected pytest release does not support this Python version",
    "pytest_unavailable": "no pinned compatibility policy is available for this pytest factor",
    "python_unavailable": "the Python factor is not a recognized version",
    "eol_python": "the Python version is outside the project's supported range",
    "eol_pytest": "the pytest version is outside the project's supported range",
}


def configure_compatibility_parser(parser: argparse.ArgumentParser) -> None:
    """Add matrix, pair-check, tox-expansion and migration-audit options."""
    parser.add_argument("--config", type=Path, help="use an explicit TOML or legacy tox INI configuration")
    parser.add_argument("--list", action="store_true", help="list the configured Python/pytest matrix")
    parser.add_argument(
        "--compatible-only",
        action="store_true",
        help="list only pairs accepted by both project and upstream compatibility policy",
    )
    parser.add_argument("--python", dest="python_version", help="Python version to check, such as 3.12")
    parser.add_argument("--pytest", dest="pytest_version", help="pytest version/factor to check, or latest")
    parser.add_argument("--expand-tox", action="store_true", help="list configured tox environments for accepted pairs")
    parser.add_argument("--audit-migration", action="store_true", help="audit feature and Python scenario identities")
    parser.add_argument("--features-root", type=Path, help="feature inventory root (default: PROJECT/features)")
    parser.add_argument("--tests-root", type=Path, help="Python registration root (default: PROJECT/tests)")
    parser.add_argument("--threshold-percent", type=int, help="override the configured migration threshold (0-100)")
    parser.add_argument("--json", action="store_true", help="emit the documented JSON payload")


def run_compatibility_command(namespace: argparse.Namespace) -> int:
    """Load project settings, run one compatibility operation and return its status."""
    operation = _selected_operation(namespace)
    if operation is None:
        return 2

    try:
        config = load_compatibility_config(
            namespace.config,
            require_matrix=operation in {"list", "tox"},
        )
        if operation == "pair":
            status = _run_pair_check(config, namespace)
        elif operation == "tox":
            status = _run_tox_expansion(config, namespace)
        elif operation == "audit":
            status = _run_migration_audit(config, namespace)
        else:
            status = _run_matrix_listing(config, namespace)
    except (CompatibilityConfigurationError, MigrationAuditError, OSError) as error:
        print(f"cuke compatibility: {error}", file=sys.stderr)
        status = 2
    return status


def _selected_operation(namespace: argparse.Namespace) -> str | None:
    """Validate command mode flags and return the selected operation name."""
    pair_requested = namespace.python_version is not None or namespace.pytest_version is not None
    if pair_requested and (namespace.python_version is None or namespace.pytest_version is None):
        print("cuke compatibility: pair checks require both --python and --pytest", file=sys.stderr)
        return None

    selected = [
        operation
        for enabled, operation in (
            (bool(namespace.list or namespace.compatible_only), "list"),
            (pair_requested, "pair"),
            (bool(namespace.expand_tox), "tox"),
            (bool(namespace.audit_migration), "audit"),
        )
        if enabled
    ]
    if len(selected) != 1:
        print(
            "cuke compatibility: choose exactly one of --list, --python/--pytest, --expand-tox, or --audit-migration",
            file=sys.stderr,
        )
        return None
    return selected[0]


def _run_pair_check(config: CompatibilityConfig, namespace: argparse.Namespace) -> int:
    entry = pair_entry(config, namespace.python_version, namespace.pytest_version)
    payload = entry_payload(entry)
    payload["message"] = _REASON_MESSAGES.get(entry.reason_code, entry.reason_code)
    if namespace.json:
        _emit_json(payload)
    else:
        _emit_pair_text(payload)
    return 0 if entry.is_compatible and entry.is_supported else 1


def _run_tox_expansion(config: CompatibilityConfig, namespace: argparse.Namespace) -> int:
    names = expanded_tox_env_names(config)
    if namespace.json:
        _emit_json({"toxEnvNames": names})
    else:
        for name in names:
            print(name)
    return 0


def _run_migration_audit(config: CompatibilityConfig, namespace: argparse.Namespace) -> int:
    result = build_migration_audit(
        config,
        features_root=namespace.features_root,
        tests_root=namespace.tests_root,
        threshold_percent=namespace.threshold_percent,
    )
    payload = result.to_payload()
    if namespace.json:
        _emit_json(payload)
    else:
        _emit_audit_text(payload)
    return 0 if result.summary.threshold_met else 1


def _run_matrix_listing(config: CompatibilityConfig, namespace: argparse.Namespace) -> int:
    entries = build_matrix(config)
    if namespace.compatible_only:
        entries = [entry for entry in entries if entry.is_compatible and entry.is_supported]
    if namespace.json:
        _emit_json({"entries": [entry_payload(entry) for entry in entries]})
    else:
        _emit_matrix_text(entries)
    return 0


def _emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _emit_pair_text(payload: dict[str, Any]) -> None:
    if payload["isCompatible"] and payload["isSupported"]:
        status = "supported"
    elif payload["isCompatible"]:
        status = "compatible but unsupported by the project"
    else:
        status = "incompatible"
    print(
        f"Python {payload['pythonVersion']} / pytest {payload['pytestVersion']}: "
        f"{status} ({payload['reasonCode']}) — {payload['message']}"
    )


def _emit_matrix_text(entries: list[Any]) -> None:
    for entry in entries:
        status = "supported" if entry.is_compatible and entry.is_supported else "excluded"
        targets = ",".join(entry.execution_targets)
        print(
            f"Python {entry.python_version} / pytest {entry.pytest_version}: {status} "
            f"({entry.reason_code}; targets={targets}; source={entry.compatibility_source})"
        )


def _emit_audit_text(payload: dict[str, Any]) -> None:
    status = "pass" if payload["thresholdMet"] else "fail"
    print(
        f"coverage={payload['coveragePercent']}% "
        f"threshold={payload['thresholdPercent']}% "
        f"scenarios={payload['totalUserFacingScenarios']} "
        f"in_features={payload['userFacingInFeatures']} "
        f"duplicates={payload['duplicatesInTests']} status={status}"
    )


__all__ = ["configure_compatibility_parser", "run_compatibility_command"]
