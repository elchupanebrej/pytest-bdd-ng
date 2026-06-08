# init: allow  # init: no-check
"""
Provide src.pytest_bdd.util.cucumber_formatter_support package helpers.

Responsibility:
    Provide src.pytest_bdd.util.cucumber_formatter_support package helpers. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

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
    depends on pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin,
    pytest_bdd.util.cucumber_formatter_support.base.load_formatter_adapter_support_template,
    pytest_bdd.util.cucumber_formatter_support.base.load_formatter_adapter_template.

Invariants:
    - `pytest_bdd.util.cucumber_formatter_support` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from pytest_bdd.util.cucumber_formatter_support.base import (
    FormatterReporterPlugin,
    load_formatter_adapter_support_template,
    load_formatter_adapter_template,
)
