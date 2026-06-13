"""
Serves as the Extra Plugins (order 8) module for YAML/JSON/TOML/HOCON BDD feature definitions.

Responsibility:
    Serves as the Extra Plugins (order 8) module for YAML/JSON/TOML/HOCON BDD feature definitions. Defines classes and
    functions that collectively implement Collection and execution behavior of the 'hook' component. This module is the
    sole owner of its specific BDD plugin contract within the Extra Plugins (order 8).

Reason for existence:
    This module exists as a distinct architectural unit because it encapsulates all logic for YAML/JSON/TOML/HOCON BDD
    feature definitions within the Extra Plugins (order 8). It is the information expert for its specific domain, owning
    the transformation from pytest events to its output format. Changes to YAML/JSON/TOML/HOCON BDD feature definitions
    behavior belong exclusively in this module, not in sibling plugins or the core pytest-bdd library. Its import
    boundary isolates it from other reporting/runtime concerns.

Delegates:
    - (internal classes and functions): Implement specific aspects of YAML/JSON/TOML/HOCON BDD feature definitions
    within the Collection and execution.

Cohesion:
    All entities in this module serve the single purpose of YAML/JSON/TOML/HOCON BDD feature definitions. They share
    common import
    dependencies and operate on the same domain types. No unrelated utilities are present.

Separation:
    - (sibling plugins in Extra Plugins (order 8)): Each owns a distinct output format or lifecycle concern.
    - (runtime plugins): Handled by separate modules in the Runtime layer (order 6).

Main consumers:
    - pytest: Hooks into the Collection and execution via standard pytest hook mechanisms.
    - (downstream tools): CI/CD systems and test reporting tools consume the generated output.

State and side effects:
    Accumulates state across pytest hook calls during the session. Accesses pytest Config for
    options. May perform file I/O for report generation.

Invariants:
    - Output format must conform to the expected schema for hook.
    - Hook implementations must respect pytest's hook calling conventions.

Failure semantics:
    Raises pytest.UsageError for configuration issues. May raise LookupError when required
    resources are missing from pytest stash or fixtures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""
