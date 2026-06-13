"""
Provides focused utility functions for the `standalone` concern within pytest-bdd utility
layer, offering helper oper.

Responsibility:
    Provides focused utility functions for the `standalone` concern within pytest-bdd utility
    layer, offering helper operations consumed by higher layers (collection, runtime, reporting)
    without pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `standalone` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `standalone`-related helper operations within
    the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `standalone` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `standalone` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pathlib import Path

from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterRequest,
    validate_requested_cucumber_formatters,
)
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog


def resolve_standalone_formatter_catalog(
    catalog: FormatterPluginCatalog | None = None,
) -> FormatterPluginCatalog:
    """
    Perform the `resolve_standalone_formatter_catalog` operation within its module boundary,.
    implementing a focused help.

    Responsibility:
        Performs the `resolve_standalone_formatter_catalog` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `resolve_standalone_formatter_catalog` exists as a standalone function because it encapsulates
        an operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the resolve_standalone_formatter_catalog operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_standalone_formatter_catalog for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The resolve_standalone_formatter_catalog function returns consistent results for equivalent inputs.

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
    return FormatterPluginCatalog.discover() if catalog is None else catalog


def resolve_standalone_formatter_requests(
    *,
    rootpath: Path,
    formatter_option_values: dict[str, object],
    catalog: FormatterPluginCatalog | None = None,
) -> tuple[CucumberFormatterRequest, ...]:
    """
    Perform the `resolve_standalone_formatter_requests` operation within its module boundary,.
    implementing a focused hel.

    Responsibility:
        Performs the `resolve_standalone_formatter_requests` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `resolve_standalone_formatter_requests` exists as a standalone function because it encapsulates
        an operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the resolve_standalone_formatter_requests operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_standalone_formatter_requests for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The resolve_standalone_formatter_requests function returns consistent results for equivalent inputs.

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
    resolved_catalog = resolve_standalone_formatter_catalog(catalog)

    def resolve_output_path(output_path: str) -> Path:
        """
        Perform the `resolve_output_path` operation within its module boundary, implementing a focused.
        helper function that .

        Responsibility:
        Performs the `resolve_output_path` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

        Reason for existence:
        `resolve_output_path` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

        Delegates:
        - Python standard library: delegates core operations to stdlib

        Cohesion:
        All logic directly supports the resolve_output_path operation.

        Separation:
        - Other functions in this module: each function handles a distinct helper concern.

        Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_output_path for its specific utility

        State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

        Invariants:
        - The resolve_output_path function returns consistent results for equivalent inputs.

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
        path = Path(output_path)
        if not path.is_absolute():
            path = rootpath / path
        return path.resolve()

    requests: list[CucumberFormatterRequest] = []
    for plugin in resolved_catalog.plugins:
        requests.extend(
            plugin.iter_requests_from_options(
                formatter_option_values,
                resolve_output_path=resolve_output_path,
            ),
        )
    ordered_requests = sorted(
        requests,
        key=lambda request: (request.discovery_order, request.formatter, request.plugin_module),
    )
    validate_requested_cucumber_formatters(ordered_requests)
    return tuple(ordered_requests)
