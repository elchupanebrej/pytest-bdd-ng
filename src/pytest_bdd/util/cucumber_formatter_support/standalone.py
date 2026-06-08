"""
Provide standalone helpers.

Responsibility:
    Provide standalone helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support.standalone` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - resolve_standalone_formatter_catalog: owns nested behavior below this boundary
    - resolve_standalone_formatter_requests: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references `standalone`

State and side effects:
    mutates path, resolved_catalog, requests, ordered_requests; depends on __future__.annotations, pathlib.Path,
    pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterRequest,
    pytest_bdd.plugin.gherkin_message_reporter.session.validate_requested_cucumber_formatters,
    pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.

Invariants:
    - `pytest_bdd.util.cucumber_formatter_support.standalone` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
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
    Resolve standalone formatter catalog.

    Returns:
        Formatter plugin catalog.

    Responsibility:
        Resolve standalone formatter catalog. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.standalone.resolve_standalone_formatter_catalog` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - FormatterPluginCatalog.discover: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `resolve_standalone_formatter_catalog`

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
    Resolve standalone formatter requests.

    Returns:
        Tuple of cucumber formatter requests.

    Responsibility:
        Resolve standalone formatter requests. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.standalone.resolve_standalone_formatter_requests` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve_output_path: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `resolve_standalone_formatter_requests`

    State and side effects:
        mutates path, resolved_catalog, requests, ordered_requests.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.standalone.resolve_standalone_formatter_requests` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    resolved_catalog = resolve_standalone_formatter_catalog(catalog)

    def resolve_output_path(output_path: str) -> Path:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.util.cucumber_formatter_support.standalone.resolve_standalone_formatter_requests.resolve_output_path`
            owns documented function behavior. It directly owns the observable contract, local decisions, and
            maintenance boundary for this function.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.standalone.resolve_standalone_formatter_requests.resolve_output_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - path.is_absolute: collaborator call used by this boundary
            - path.resolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `resolve_output_path`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `resolve_output_path`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `resolve_output_path`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `resolve_output_path`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `resolve_output_path`

        State and side effects:
            mutates path.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.standalone.resolve_standalone_formatter_requests.resolve_output_path`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
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
