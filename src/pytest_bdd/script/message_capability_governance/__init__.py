# init: allow  # init: no-check
"""
Message capability governance helpers.

Responsibility:
    Message capability governance helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    depends on __future__.annotations, pytest_bdd.model.coverage.inventory.generate_inventory,
    pytest_bdd.script.message_capability_governance.capabilities._load_capabilities,
    pytest_bdd.script.message_capability_governance.capabilities._load_capabilities_from_governance_report,
    pytest_bdd.script.message_capability_governance.capabilities._load_capability_ids.

Invariants:
    - `pytest_bdd.script.message_capability_governance` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from pytest_bdd.model.coverage.inventory import generate_inventory as generate_inventory
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capabilities as _load_capabilities,
)
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capabilities_from_governance_report as _load_capabilities_from_governance_report,
)
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capability_ids as _load_capability_ids,
)
from pytest_bdd.script.message_capability_governance.capabilities import (
    _validate_runtime_required_scope as _validate_runtime_required_scope,
)
from pytest_bdd.script.message_capability_governance.capabilities import (
    _validate_scope_capability_ids as _validate_scope_capability_ids,
)
from pytest_bdd.script.message_capability_governance.cli import (
    main as main,
)
from pytest_bdd.script.message_capability_governance.cli import (
    parse_args as parse_args,
)
from pytest_bdd.script.message_capability_governance.decisions import (
    _load_baseline_diff as _load_baseline_diff,
)
from pytest_bdd.script.message_capability_governance.decisions import (
    _load_decisions as _load_decisions,
)
from pytest_bdd.script.message_capability_governance.decisions import (
    _select_active_decisions as _select_active_decisions,
)
from pytest_bdd.script.message_capability_governance.decisions import (
    _validate_decisions as _validate_decisions,
)
from pytest_bdd.script.message_capability_governance.schema import (
    _candidate_repo_roots as _candidate_repo_roots,
)
from pytest_bdd.script.message_capability_governance.schema import (
    _repo_root as _repo_root,
)
from pytest_bdd.script.message_capability_governance.schema import (
    discover_governance_schema_path as discover_governance_schema_path,
)
from pytest_bdd.script.message_capability_governance.schema import (
    load_governance_report_schema as load_governance_report_schema,
)
from pytest_bdd.script.message_capability_governance.schema import (
    validate_governance_report_payload as validate_governance_report_payload,
)
