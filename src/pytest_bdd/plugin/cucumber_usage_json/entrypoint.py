"""
Provide cucumber usage json entrypoint.

Responsibility:
    Provide cucumber usage json entrypoint. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_usage_json.entrypoint` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - UsageJsonFormatterPlugin: collaborator call used by this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates usage_json_plugin; depends on plugin.UsageJsonFormatterPlugin.

Invariants:
    - `pytest_bdd.plugin.cucumber_usage_json.entrypoint` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
"""

from .plugin import UsageJsonFormatterPlugin

usage_json_plugin = UsageJsonFormatterPlugin()
