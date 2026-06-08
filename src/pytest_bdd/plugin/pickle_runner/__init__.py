# init: allow  # init: no-check
"""
Provide src.pytest_bdd.plugin.pickle_runner package helpers.

Responsibility:
    Provide src.pytest_bdd.plugin.pickle_runner package helpers. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - __getattr__: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates msg; depends on run_transitions.apply_transition, api_compatibility.build_external_api_compatibility_record,
    api_compatibility.collect_hook_public_symbols.

Invariants:
    - `pytest_bdd.plugin.pickle_runner` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises AttributeError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=2
"""

from .run_transitions import apply_transition


def __getattr__(name: str) -> object:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.__getattr__` owns documented function behavior.
        It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.__getattr__` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - locals: collaborator call used by this boundary
        - AttributeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates msg; depends on api_compatibility.build_external_api_compatibility_record,
        api_compatibility.collect_hook_public_symbols.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.__getattr__` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises AttributeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if name in {"build_external_api_compatibility_record", "collect_hook_public_symbols"}:
        from .api_compatibility import (  # noqa: PLC0415 -- breaks circular import
            build_external_api_compatibility_record,
            collect_hook_public_symbols,
        )

        return locals()[name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
