"""
`pytest_bdd_testing.e2e.cucumber_formatter_support` provides a flat re-export facade that exposes key formatter-support
functions from `pytest_bdd_testing.cucumber_formatters` to e2e test step definitions, decoupling step-def plugins from
the internal structure of the formatter testing library.

Responsibility:
    Acts as a thin re-export layer that imports three essential formatter-support functions (`install_fake_node`,
    `materialize_fake_node_runtime`, `run_pytest_via_real_entrypoint`) from `pytest_bdd_testing.cucumber_formatters` and
    exposes them under a flat, stable `__all__` surface. This module owns the contract between e2e step definitions and
    the formatter testing infrastructure: step definitions should never import directly from
    `pytest_bdd_testing.cucumber_formatters.registry` or `.rendering` submodules, as those internal boundaries may
    change independently of the e2e contract.

Reason for existence:
    Exists to provide a stable, minimal API surface for e2e test step definitions that need to configure fake Node.js
    runtimes and execute pytest subprocesses for Cucumber formatter output validation. The
    `pytest_bdd_testing.cucumber_formatters` package has a richer internal structure (separate `registry.py` and
    `rendering.py` modules with many more exports), but e2e step definitions only need three functions. This facade
    prevents step-def authors from coupling to internal module boundaries and ensures that refactoring the formatter
    testing library does not break e2e tests as long as the three re-exported functions maintain their signatures.

Delegates:
    - `pytest_bdd_testing.cucumber_formatters.registry`: Provides `run_pytest_via_real_entrypoint` and other formatter
    registry functions; this module selectively re-exports only the needed function.
    - `pytest_bdd_testing.cucumber_formatters.rendering`: Provides `install_fake_node` and
    `materialize_fake_node_runtime`; this module selectively re-exports only the needed functions, hiding
    `materialize_live_formatter_runtime` and other rendering internals from e2e consumers.

Cohesion:
    High — all logic in this module serves the single purpose of providing a curated re-export surface. The three re-
    exported functions share the common theme of "things e2e step definitions need to set up and execute Cucumber
    formatter tests." The module has no local state, no logic beyond imports, and a well-defined `__all__`.

Separation:
    - `pytest_bdd_testing.e2e.test_e2e`: Kept separate because `test_e2e.py` owns scenario collection, tag filtering,
    and message governance validation, while this module owns the formatter-support re-export contract. Separating them
    prevents the test module from growing to include formatter setup concerns.
    - `pytest_bdd_testing.cucumber_formatters/__init__.py`: Kept separate because the full
    `cucumber_formatters/__init__.py` exports a much broader API surface (15+ functions from registry plus 3 from
    rendering), while this e2e facade exports only the 3 functions needed by step definitions.
    - `pytest_bdd_testing.cucumber_formatters.registry` and `.rendering`: Kept separate as internal implementation
    modules; this facade is the only module in `pytest_bdd_testing.e2e` that imports from them, acting as the single
    coupling point.

Main consumers:
    - `pytest_bdd_testing.cases.e2e.steps_formatters`: Step definition plugin that imports from this module to set up
    fake Node runtimes and execute pytest for formatter output validation during e2e scenario execution.
    - Other e2e step definition plugins (`pytest_bdd_testing.cases.e2e.steps_*`) that may need to install fake Node.js
    or run pytest subprocesses as part of scenario setup.

State and side effects:
    None, keeps no persistent state. The module performs imports at load time but does not execute any runtime logic,
    modify global state, or perform I/O. Side effects occur only when consumers call the re-exported functions.

Invariants:
    - The `__all__` list must match exactly the set of re-exported names; adding a function to this module without
    updating `__all__` would break the public API contract.
    - Re-exported functions must preserve their original signatures from `pytest_bdd_testing.cucumber_formatters`.
    - This module must not import from any module outside `pytest_bdd_testing.cucumber_formatters`.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from pytest_bdd_testing.tool.cucumber_formatter import (
    install_fake_node,
    materialize_fake_node_runtime,
    run_pytest_via_real_entrypoint,
)

__all__ = [
    "install_fake_node",
    "materialize_fake_node_runtime",
    "run_pytest_via_real_entrypoint",
]
