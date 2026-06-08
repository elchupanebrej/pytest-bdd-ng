"""
Provide resources helpers.

Responsibility:
    Provide resources helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.importlib.resources` because it keeps the
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
    - src/pytest_bdd/plugin/code_generator/rendering.py: imports or references `resources`
    - src/pytest_bdd/plugin/gherkin_message_reporter/session.py: imports or references `resources`
    - src/pytest_bdd/util/cucumber_formatter_support/base.py: imports or references `resources`

State and side effects:
    depends on importlib_resources.as_file, importlib_resources.files.

Invariants:
    - `pytest_bdd.compatibility.importlib.resources` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from importlib_resources import as_file, files  # noqa: F401
