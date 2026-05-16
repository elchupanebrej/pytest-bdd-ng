"""Schema loading and validation for message capability governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from returns.maybe import Nothing

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject

DEFAULT_GOVERNANCE_SCHEMA_GLOB: Final[str] = "specs/*/contracts/governance-report.schema.json"
DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH: Final[Path] = Path(
    "specs/008-maximize-messages-coverage/contracts/governance-report.schema.json",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _candidate_repo_roots() -> tuple[Path, ...]:
    cwd = Path.cwd().resolve()
    repo_root = _repo_root().resolve()
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in (cwd, repo_root):
        for candidate in (base, *base.parents):
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    return tuple(candidates)


def discover_governance_schema_path() -> Path | None:
    """
    Discover the governance schema path.

    Returns:
        Path to governance schema or None if not found.

    """
    # Runtime lookup to respect monkeypatching on the package namespace
    import pytest_bdd.script.message_capability_governance as _pkg

    canonical_path = (_pkg._repo_root().resolve() / DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH).resolve()
    if canonical_path.exists():
        return canonical_path
    candidates: list[Path] = []
    for root in _pkg._candidate_repo_roots():
        candidates.extend(sorted(root.glob(DEFAULT_GOVERNANCE_SCHEMA_GLOB)))
    if not candidates:
        return Nothing.value_or(None)
    normalized_candidates = sorted({candidate.resolve() for candidate in candidates}, key=str)
    return normalized_candidates[0]


def load_governance_report_schema(schema_path: Path | None = None) -> JSONObject:
    """
    Load governance report schema from file.

    Args:
        schema_path: Optional explicit schema path.

    Returns:
        Loaded schema as JSON object.

    Raises:
        FileNotFoundError: If the operation cannot be completed.

    """
    effective_path = schema_path or discover_governance_schema_path()
    if effective_path is None:
        msg = "Unable to locate governance report schema."
        raise FileNotFoundError(msg)
    return cast("JSONObject", _load_json(effective_path))


def validate_governance_report_payload(payload: JSONObject, schema_path: Path | None = None) -> None:
    """
    Validate governance report payload.

    Raises:
        ValueError: If the operation cannot be completed.

    """
    schema = load_governance_report_schema(schema_path)
    from jsonschema.validators import validator_for

    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.absolute_path)
        msg = f"Governance report validation failed at '{path}': {error.message}"
        raise ValueError(msg)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))
