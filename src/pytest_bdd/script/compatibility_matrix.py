"""CLI for compatibility matrix inspection and validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pytest_bdd.compatibility.matrix import (
    REASON_COMPATIBLE,
    build_matrix,
    expand_tox_env_names,
    extract_factors_from_tox_ini,
    is_pair_compatible,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Python/pytest compatibility matrix")
    parser.add_argument("--tox-ini", type=Path, default=Path("tox.ini"), help="Path to tox.ini")
    parser.add_argument("--python", dest="python_factor", help="Python factor without prefix, e.g. 314")
    parser.add_argument("--pytest", dest="pytest_factor", help="pytest factor, e.g. 90 or latest")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--list", action="store_true", help="List all matrix entries")
    parser.add_argument("--compatible-only", action="store_true", help="List only compatible entries")
    return parser.parse_args(argv)


def _entry_payload(entry) -> dict[str, object]:
    return {
        "pythonVersion": entry.python_version,
        "pytestVersion": entry.pytest_version,
        "isCompatible": entry.is_compatible,
        "isSupported": entry.is_supported,
        "reasonCode": entry.reason_code,
        "toxEnvName": entry.tox_env_name,
    }


def _emit(payload: str) -> None:
    sys.stdout.write(payload)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    python_factors, pytest_factors = extract_factors_from_tox_ini(args.tox_ini)
    entries = build_matrix(python_factors, pytest_factors)

    if args.python_factor and args.pytest_factor:
        compatible, reason = is_pair_compatible(args.python_factor, args.pytest_factor)
        pair_payload: dict[str, object] = {
            "pythonVersion": f"{args.python_factor[0]}.{args.python_factor[1:]}"
            if args.python_factor.isdigit() and len(args.python_factor) == 3
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
