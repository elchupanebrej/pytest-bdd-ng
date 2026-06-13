"""
Provides DataTable parsing utilities that convert Gherkin DataTable objects into structured
Python data formats (list.

Responsibility:
    Provides DataTable parsing utilities that convert Gherkin DataTable objects into structured
    Python data formats (list-of-lists, list-of-dicts, key-value pairs), bridging the gap between
    Cucumber Messages' DataTable representation and pytest-bdd step definition parameter injection.

Reason for existence:
    DataTable transformation is a cross-cutting concern used by multiple step definition patterns
    and matchers. Centralizing these conversions prevents duplication across the step definition
    system and ensures consistent DataTable handling regardless of step definition implementation
    style.

Delegates:
    - `cucumber_messages`: provides the DataTable and TableRow message types consumed here

Cohesion:
    All functions operate on cucumber_messages DataTable objects and produce standard Python data
    structures.

Separation:
    - `pytest_bdd.steps`: steps handles step matching while data_table provides transformation utilities.

Main consumers:
    - `pytest_bdd.steps`: uses data_table functions for parameter injection into step implementations

State and side effects:
    None, all functions are pure transformations from DataTable input to Python data structure
    output.

Invariants:
    - All functions handle empty DataTable rows (header-only tables) gracefully without crashing.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from cucumber_messages import (
        DataTable,  # upstream library missing type stubs
    )


def data_table_to_dicts(data_table: DataTable | None) -> dict[str, list[str]]:
    """
    Perform the `data_table_to_dicts` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `data_table_to_dicts` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `data_table_to_dicts` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the data_table_to_dicts operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke data_table_to_dicts for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The data_table_to_dicts function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if data_table is None:
        return {}
    return {row.cells[0].value: [cell.value for cell in row.cells[1:]] for row in data_table.rows}
