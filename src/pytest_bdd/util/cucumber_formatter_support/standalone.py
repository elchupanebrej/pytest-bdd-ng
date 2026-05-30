"""Provide standalone helpers."""

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

    """
    resolved_catalog = resolve_standalone_formatter_catalog(catalog)

    def resolve_output_path(output_path: str) -> Path:
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
