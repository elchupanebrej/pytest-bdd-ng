"""
Acts as an import redirect and re-export facade that delegates all actual utility implementations to subpackages unde.

Responsibility:
    Acts as an import redirect and re-export facade that delegates all actual utility implementations to subpackages
    under pytest_bdd.util.*. This module contains no executable code — it exists solely to provide a stable import path
    (pytest_bdd.utils) for consumers who previously depended on this location, while the real implementation lives in
    the utility layer (pytest_bdd.util) following the architectural layering defined in docs/architecture/layers.toml.

Reason for existence:
    Maintains backward compatibility for external consumers that were written to import from pytest_bdd.utils before the
    utility code was reorganized into the pytest_bdd.util subpackage structure. Without this stub, existing test suites
    and third-party plugins that `from pytest_bdd.utils import ...` would break upon upgrade. The module exists at the
    top-level package namespace even though it contains no logic, serving as a routing layer that prevents import
    breakage. This pattern follows the compatibility shim convention also used by pytest_bdd.parsers and
    pytest_bdd.message_stream_validation.

Delegates:
    - pytest_bdd.util.* (subpackage with multiple modules): All actual utility functionality — toolz_extra, other, url,
    test_group_ordering — is implemented there. This module delegates entirely, importing nothing and exporting nothing.

Cohesion:
    This module has perfect cohesion in a degenerate sense: it contains no code and therefore no conflicting concerns.
    Its single responsibility is maintaining the import compatibility contract. Any actual utility logic that might be
    added here would violate the delegation principle and should instead be placed in the appropriate pytest_bdd.util
    submodule.

Separation:
    - pytest_bdd.util.*: Kept separate because the util subpackage owns the actual utility implementations with proper
    sub-module organization (toolz_extra, other, url, test_group_ordering). This utils.py module must remain empty to
    avoid creating a second source of truth that would diverge from the util subpackage.
    - pytest_bdd.parsers (facade): Similar facade pattern — both are empty re-export modules serving as backward-
    compatible import targets, but they serve different consumer domains (utilities vs parser functions).

Main consumers:
    - External test suites: Any existing test code that imports from pytest_bdd.utils will continue to work, though the
    actual implementation is resolved through the util subpackage.
    - Legacy documentation and examples: Code samples that reference pytest_bdd.utils remain valid as long as this
    module exists.

State and side effects:
    None, keeps no persistent state. This module is completely empty aside from the docstring — no imports, no module-
    level variables, no side effects.

Invariants:
    - This module must never contain executable code or import any symbols — it must remain a pure empty module to avoid
    creating diverging implementations from pytest_bdd.util.*.
    - If any function previously accessed via pytest_bdd.utils is renamed or moved, this module's docstring should be
    updated to document the migration path.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=1
    #arch-eval:locational_stability=4
"""
