# init: allow  # init: no-check
"""
Implement concrete logic for the module-level entity as described by the owning module's architecture contract.

Responsibility:
    Implements concrete logic for the module-level entity as described by the owning module's architecture contract. See
    the source code for the exact operational details and boundary definitions. module directly implements and owns.
    This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion, prevent knowledge
    fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
    call signatures. module rather than being merged elsewhere. Why is it the information expert for this logical
    boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

Delegates:
    - Collaborating entities from sibling modules and standard library: see the source code for the specific delegation
    call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to support this
    boundary. Use actual names of children or called functions found in the source. Add more bullet points as needed.>

Cohesion:
    All logic within this module operates on shared state or a unified domain model, with imports and control flow
    focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
    actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag of
    unrelated utilities?>

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains,
    maintaining distinct boundaries between concerns as observed in the package structure and import hierarchy. from
    this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual peer entity. Add more
    bullet points as needed.>

Main consumers:
    - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the specific
    consumer paths and public API contracts that must remain stable. utilizes this entity, defining the public API
    contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as needed.>

State and side effects:
    None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
    access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash reads/writes
    this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no persistent state'.>

Invariants:
    - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
    specific data constraints, type requirements, and execution preconditions. that must always hold true for this
    entity and can never be broken. Analyze the actual source for implicit contracts.>

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
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
