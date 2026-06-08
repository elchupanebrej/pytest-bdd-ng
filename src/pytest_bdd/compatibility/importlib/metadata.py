"""
Provide metadata helpers.

Responsibility:
    Provide metadata helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.importlib.metadata` because it keeps the nearest
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
    - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py: imports or references `metadata`
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `metadata`
    - src/pytest_bdd/util/packaging.py: imports or references `metadata`

State and side effects:
    depends on importlib.metadata.Distribution, importlib.metadata.DistributionFinder,
    importlib.metadata.PackageMetadata, importlib.metadata.PackageNotFoundError, importlib.metadata.distribution.

Invariants:
    - `pytest_bdd.compatibility.importlib.metadata` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from importlib.metadata import (  # noqa: F401
    Distribution,
    DistributionFinder,
    PackageMetadata,
    PackageNotFoundError,
    distribution,
    distributions,
    entry_points,
    files,
    metadata,
    packages_distributions,
    requires,
    version,
)
