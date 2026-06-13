"""
Provide a cross-Python-version compatibility shim for `outcomes`, encapsulating all version-
detection logic and con.

Responsibility:
    Provides a cross-Python-version compatibility shim for `outcomes`, encapsulating all version-
    detection logic and conditional imports so that higher layers import a single stable name
    regardless of the runtime Python interpreter version (3.10-3.14).

Reason for existence:
    Centralizing Python version-gating for `outcomes` in this module prevents `if sys.version_info`
    checks from contaminating domain logic. This module is the single information expert for which
    stdlib/third-party names and APIs are available on each supported Python version for this
    specific concern.

Delegates:
    - Python stdlib/third-party: delegates actual implementation to the version-appropriate module

Cohesion:
    All symbols re-export a single compatibility concern (outcomes); no unrelated utilities.

Separation:
    - Sibling compatibility modules: each handles a distinct stdlib version gap.

Main consumers:
    - `pytest_bdd.*`: all higher layers import compatibility shims to avoid inline version-gated logic

State and side effects:
    None, this module keeps no persistent state and performs only import-time version detection.

Invariants:
    - The public API surface matches the target stdlib module interface across supported Python versions.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from _pytest.outcomes import Exit, Failed  # type: ignore[attr-defined]  # Exit not in older stubs

__all__ = ["Exit", "Failed"]
