from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.plugin.cucumber_formatter_support.standalone import (
    resolve_standalone_formatter_catalog,
    resolve_standalone_formatter_requests,
)
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterConfigurationError,
    CucumberFormatterRenderResult,
    CucumberFormatterRequest,
)
from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_bdd.plugin.cucumber_formatter_support.registry import FormatterPluginCatalog


@frozen
class _StandaloneRuntimeConfig:
    rootpath: Path


@frozen
class _StandaloneReporterRuntime:
    config: _StandaloneRuntimeConfig
    requested_cucumber_formatters: tuple[CucumberFormatterRequest, ...]
    formatter_catalog: FormatterPluginCatalog
    _auto_provisioned_node_modules_roots: tuple[Path, ...] = ()
    npm_formatter_package: str = "@cucumber/html-formatter"

    def render_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        return self.formatter_catalog.render_runtime_assets(formatter_requests)


@frozen
class StandaloneCucumberFormatterRenderer:
    catalog: FormatterPluginCatalog

    @classmethod
    def discover(
        cls,
        *,
        catalog: FormatterPluginCatalog | None = None,
    ) -> StandaloneCucumberFormatterRenderer:
        return cls(catalog=resolve_standalone_formatter_catalog(catalog))

    def resolve_requests(
        self,
        *,
        rootpath: Path,
        formatter_option_values: dict[str, object],
    ) -> tuple[CucumberFormatterRequest, ...]:
        return resolve_standalone_formatter_requests(
            rootpath=rootpath,
            formatter_option_values=formatter_option_values,
            catalog=self.catalog,
        )

    def render_from_messages_path(
        self,
        messages_path: Path,
        *,
        rootpath: Path,
        formatter_option_values: dict[str, object],
    ) -> CucumberFormatterRenderResult:
        formatter_requests = self.resolve_requests(
            rootpath=rootpath,
            formatter_option_values=formatter_option_values,
        )
        runtime = _StandaloneReporterRuntime(
            config=_StandaloneRuntimeConfig(rootpath=rootpath),
            requested_cucumber_formatters=formatter_requests,
            formatter_catalog=self.catalog,
        )
        live_formatter_service = LiveFormatterService(reporter=runtime)
        envelopes = TransportService.read_envelopes_from_path(messages_path)
        return live_formatter_service.run_requested_cucumber_formatters(envelopes)


__all__ = (
    "CucumberFormatterConfigurationError",
    "StandaloneCucumberFormatterRenderer",
)
