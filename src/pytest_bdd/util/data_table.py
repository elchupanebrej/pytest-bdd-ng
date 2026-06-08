"""
Provide data table helpers.

Responsibility:
    Provide data table helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.data_table` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - data_table_to_dicts: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/scenario_run.py: imports or references `data_table`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `data_table`

State and side effects:
    depends on __future__.annotations, typing.TYPE_CHECKING, cucumber_messages.DataTable.

Invariants:
    - `pytest_bdd.util.data_table` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from cucumber_messages import (
        DataTable,  # upstream library missing type stubs
    )


def data_table_to_dicts(data_table: DataTable | None) -> dict[str, list[str]]:
    """
    Convert a Gherkin data table to dictionaries.

    Args:
        data_table: Gherkin data table or None.

    Returns:
        Dictionary mapping first column to list of other values.

    Responsibility:
        Convert a Gherkin data table to dictionaries. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.data_table.data_table_to_dicts` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2

    """
    if data_table is None:
        return {}
    return {row.cells[0].value: [cell.value for cell in row.cells[1:]] for row in data_table.rows}
