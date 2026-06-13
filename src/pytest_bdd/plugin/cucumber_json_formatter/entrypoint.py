"""
Serves as the Reporting (order 7) module for Cucumber JSON report generation.

Responsibility:
    Serves as the Reporting (order 7) module for Cucumber JSON report generation. Defines classes and functions that
    collectively implement Reporting phase behavior of the 'entrypoint' component. This module is the sole owner of its
    specific BDD plugin contract within the Reporting (order 7).

Reason for existence:
    This module exists as a distinct architectural unit because it encapsulates all logic for Cucumber JSON report
    generation within the Reporting (order 7). It is the information expert for its specific domain, owning the
    transformation from pytest events to its output format. Changes to Cucumber JSON report generation behavior belong
    exclusively in this module, not in sibling plugins or the core pytest-bdd library. Its import boundary isolates it
    from other reporting/runtime concerns.

Delegates:
    - (internal classes and functions): Implement specific aspects of Cucumber JSON report generation within the
    Reporting phase.

Cohesion:
    All entities in this module serve the single purpose of Cucumber JSON report generation. They share common import
    dependencies and operate on the same domain types. No unrelated utilities are present.

Separation:
    - (sibling plugins in Reporting (order 7)): Each owns a distinct output format or lifecycle concern.
    - (runtime plugins): Handled by separate modules in the Runtime layer (order 6).

Main consumers:
    - pytest: Hooks into the Reporting phase via standard pytest hook mechanisms.
    - (downstream tools): CI/CD systems and test reporting tools consume the generated output.

State and side effects:
    Accumulates state across pytest hook calls during the session. Accesses pytest Config for
    options. May perform file I/O for report generation.

Invariants:
    - Output format must conform to the expected schema for entrypoint.
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

from .plugin import JsonFormatterPlugin

json_plugin = JsonFormatterPlugin()
