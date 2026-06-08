"""
Schema loading and validation for message capability governance.

Responsibility:
    Schema loading and validation for message capability governance. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance.schema` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _GovernancePackage: owns nested behavior below this boundary
    - _repo_root: owns nested behavior below this boundary
    - _candidate_repo_roots: owns nested behavior below this boundary
    - discover_governance_schema_path: owns nested behavior below this boundary
    - load_governance_report_schema: owns nested behavior below this boundary
    - validate_governance_report_payload: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/coverage/inventory.py: imports or references `schema`
    - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `schema`
    - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `schema`
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `schema`
    - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `schema`

State and side effects:
    mutates candidates, msg, DEFAULT_GOVERNANCE_SCHEMA_GLOB, DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH, source_path;
    depends on __future__.annotations, json, sys, pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.script.message_capability_governance.schema` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises FileNotFoundError, ValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, cast

from returns.maybe import Nothing

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject


class _GovernancePackage(Protocol):
    """
    Responsibility:
        Responsibility: `pytest_bdd.script.message_capability_governance.schema._GovernancePackage` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.schema._GovernancePackage` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _repo_root: owns nested behavior below this boundary
        - _candidate_repo_roots: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_GovernancePackage`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `_GovernancePackage`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_GovernancePackage`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_GovernancePackage`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.schema._GovernancePackage` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def _repo_root(self) -> Path:
        """
        Responsibility:
            Responsibility: `pytest_bdd.script.message_capability_governance.schema._GovernancePackage._repo_root` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.script.message_capability_governance.schema._GovernancePackage._repo_root` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_repo_root`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_repo_root`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_repo_root`
            - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_repo_root`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...

    def _candidate_repo_roots(self) -> tuple[Path, ...]:
        """
        Responsibility:
            Responsibility:
            `pytest_bdd.script.message_capability_governance.schema._GovernancePackage._candidate_repo_roots` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.script.message_capability_governance.schema._GovernancePackage._candidate_repo_roots` because it
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
            - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
              `_candidate_repo_roots`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `_candidate_repo_roots`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `_candidate_repo_roots`
            - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
              `_candidate_repo_roots`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...


DEFAULT_GOVERNANCE_SCHEMA_GLOB: Final[str] = "specs/*/contracts/governance-report.schema.json"
DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH: Final[Path] = Path(
    "specs/008-maximize-messages-coverage/contracts/governance-report.schema.json",
)


def _repo_root() -> Path:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.message_capability_governance.schema._repo_root` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.message_capability_governance.schema._repo_root`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path.resolve: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - is_file: collaborator call used by this boundary
        - is_dir: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_repo_root`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_repo_root`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_repo_root`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_repo_root`

    State and side effects:
        mutates source_path.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.schema._repo_root` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    source_path = Path(__file__).resolve()
    for candidate in (source_path.parent, *source_path.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "specs").is_dir():
            return candidate
    return source_path.parents[4]


def _candidate_repo_roots() -> tuple[Path, ...]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.message_capability_governance.schema._candidate_repo_roots`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.schema._candidate_repo_roots` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path.cwd.resolve: collaborator call used by this boundary
        - Path.cwd: collaborator call used by this boundary
        - _repo_root.resolve: collaborator call used by this boundary
        - _repo_root: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - seen.add: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_candidate_repo_roots`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `_candidate_repo_roots`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_candidate_repo_roots`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `_candidate_repo_roots`

    State and side effects:
        mutates cwd, repo_root, candidates, seen.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.schema._candidate_repo_roots` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    Responsibility:
        Discover the governance schema path. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.schema.discover_governance_schema_path` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sorted: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - resolve: collaborator call used by this boundary
        - _pkg._repo_root.resolve: collaborator call used by this boundary
        - _pkg._repo_root: collaborator call used by this boundary
        - canonical_path.exists: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `discover_governance_schema_path`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `discover_governance_schema_path`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `discover_governance_schema_path`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `discover_governance_schema_path`

    State and side effects:
        mutates _pkg, canonical_path, candidates, normalized_candidates.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.schema.discover_governance_schema_path` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    _pkg = cast("_GovernancePackage", sys.modules["pytest_bdd.script.message_capability_governance"])
    canonical_path = (_pkg._repo_root().resolve() / DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH).resolve()
    if canonical_path.exists():
        return canonical_path
    candidates: list[Path] = []
    for root in _pkg._candidate_repo_roots():
        candidates.extend(sorted(root.glob(DEFAULT_GOVERNANCE_SCHEMA_GLOB)))
    if not candidates:
        return Nothing.value_or(None)
    normalized_candidates = sorted({candidate.resolve() for candidate in candidates}, key=str)
    return Path(normalized_candidates[0])


def load_governance_report_schema(schema_path: Path | None = None) -> JSONObject:
    """
    Load governance report schema from file.

    Args:
        schema_path: Optional explicit schema path.

    Returns:
        Loaded schema as JSON object.

    Raises:
        FileNotFoundError: If the operation cannot be completed.

    Responsibility:
        Load governance report schema from file. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.schema.load_governance_report_schema` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - discover_governance_schema_path: collaborator call used by this boundary
        - FileNotFoundError: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - _load_json: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `load_governance_report_schema`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `load_governance_report_schema`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `load_governance_report_schema`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `load_governance_report_schema`

    State and side effects:
        mutates effective_path, msg.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.schema.load_governance_report_schema` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises FileNotFoundError; callers must treat these as boundary failures.

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

    Responsibility:
        Validate governance report payload. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.schema.validate_governance_report_payload` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - load_governance_report_schema: collaborator call used by this boundary
        - validator_for: collaborator call used by this boundary
        - validator_class.check_schema: collaborator call used by this boundary
        - validator_class: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - validator.iter_errors: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `validate_governance_report_payload`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `validate_governance_report_payload`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `validate_governance_report_payload`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `validate_governance_report_payload`

    State and side effects:
        mutates schema, validator_class, validator, errors, error; depends on jsonschema.validators.validator_for.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.schema.validate_governance_report_payload` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.message_capability_governance.schema._load_json` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.message_capability_governance.schema._load_json`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - json.loads: collaborator call used by this boundary
        - path.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_load_json`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_load_json`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_load_json`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_load_json`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    return json.loads(path.read_text(encoding="utf-8"))
