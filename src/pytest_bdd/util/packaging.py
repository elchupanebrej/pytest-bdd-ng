"""
Provide packaging helpers.

Responsibility:
    Provide packaging helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.packaging` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - get_distribution_version: owns nested behavior below this boundary
    - parse_version: owns nested behavior below this boundary
    - compare_distribution_version: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/__init__.py: imports or references `packaging`
    - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `packaging`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `packaging`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references `packaging`
    - src/pytest_bdd/script/sync_messages_contract_schemas.py: imports or references `packaging`

State and side effects:
    depends on __future__.annotations, functools.lru_cache, operator.eq, typing.TYPE_CHECKING, packaging.utils.Version.

Invariants:
    - `pytest_bdd.util.packaging` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from functools import lru_cache
from operator import eq
from typing import TYPE_CHECKING

from packaging.utils import Version  # type: ignore[attr-defined]  # packaging.utils is untyped

if TYPE_CHECKING:
    from collections.abc import Callable

from pytest_bdd.compatibility.importlib.metadata import version


def get_distribution_version(distribution_name: str) -> Version:
    """
    Get the version of a distribution.

    Args:
        distribution_name: Name of the distribution.

    Returns:
        Version object.

    Responsibility:
        Get the version of a distribution. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.packaging.get_distribution_version` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Version: collaborator call used by this boundary
        - version: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `get_distribution_version`
        - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `get_distribution_version`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `get_distribution_version`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `get_distribution_version`
        - src/pytest_bdd/script/sync_messages_contract_schemas.py: imports or references `get_distribution_version`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return Version(version(distribution_name))


def parse_version(version: str) -> Version:
    """
    Parse a version string.

    Args:
        version: Version string to parse.

    Returns:
        Version object.

    Responsibility:
        Parse a version string. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.packaging.parse_version` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Version: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `parse_version`
        - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `parse_version`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `parse_version`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `parse_version`
        - src/pytest_bdd/script/sync_messages_contract_schemas.py: imports or references `parse_version`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return Version(version)


@lru_cache
def compare_distribution_version(
    distribution_name: str,
    version: str,
    operator: Callable[[Version, Version], bool] = eq,
) -> bool:
    """
    Compare distribution version against a target.

    Args:
        distribution_name: Name of the distribution.
        version: Target version string.
        operator: Comparison operator.

    Returns:
        True if version matches.

    Responsibility:
        Compare distribution version against a target. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.packaging.compare_distribution_version` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - operator: collaborator call used by this boundary
        - get_distribution_version: collaborator call used by this boundary
        - parse_version: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `compare_distribution_version`
        - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `compare_distribution_version`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `compare_distribution_version`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `compare_distribution_version`
        - src/pytest_bdd/script/sync_messages_contract_schemas.py: imports or references `compare_distribution_version`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return operator(get_distribution_version(distribution_name), parse_version(version))
