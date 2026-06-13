"""
Serves as the package marker for the `pytest_bdd._pylint.checkers` subpackage, declaring an empty `__all__`
list to s.

Responsibility:
    Serves as the package marker for the `pytest_bdd._pylint.checkers` subpackage, declaring an empty `__all__`
    list to satisfy the `BLQ1401` rule against defining `__all__` in __init__.py files. This module contains no
    executable logic, no imports beyond `from __future__ import annotations`, and exists solely to make the
    `checkers/` directory a proper Python package so that sibling checker modules can be imported via relative
    paths from the parent `__init__.py` plugin entry point.

Reason for existence:
    This module exists because Python requires an `__init__.py` file (or a namespace package) for `checkers/` to
    be importable as `pytest_bdd._pylint.checkers`. It is intentionally kept minimal — no re-exports, no
    registrations, no utility functions — because all checker activation flows through the parent
    `pytest_bdd._pylint.register()` function which imports each checker class directly by its module path. The
    empty nature reflects the design decision that the checkers subpackage is a container, not a facade.

Delegates:
    - (none): This module delegates nothing; it is a pure package marker with zero logic.

Cohesion:
    The module has exactly one concern: being a valid Python package marker. The `__all__ = []` assignment and
    `from __future__ import annotations` import are both minimal boilerplate with no business logic coupling.

Separation:
    - pytest_bdd._pylint.__init__: The parent module owns checker registration; this module is a passive
      container that enables relative imports without exposing any public API surface.
    - Individual checker modules: Each checker module (file_size_rules, init_rules, etc.) owns its own
      validation logic; this module never touches or re-exports them.

Main consumers:
    - pytest_bdd._pylint.__init__: Imports checker classes via relative paths like
      `from .checkers.file_size_rules import FileSizeRulesChecker`.
    - Python import system: Resolves `pytest_bdd._pylint.checkers` as a package for relative imports.

State and side effects:
    None, keeps no persistent state. The module has no mutable state, no file/network I/O, and no side effects
    beyond Python's standard package initialization.

Invariants:
    - Must remain importable as `pytest_bdd._pylint.checkers`.
    - Must not export any names via `__all__` beyond the empty list.
    - Must not contain any executable logic that could fail during import.

Architecture score:
    #arch-eval:reason_for_existence=2
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

__all__: list[str] = []
