from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from attrs import frozen

from pytest_bdd.plugin.cucumber_formatter_support.standalone import (
    resolve_standalone_formatter_catalog,
    resolve_standalone_formatter_requests,
)
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
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

    def __init__(
        self,
        *,
        config: _StandaloneRuntimeConfig,
        requested_cucumber_formatters: tuple[CucumberFormatterRequest, ...],
        formatter_catalog: FormatterPluginCatalog,
    ) -> None:
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "requested_cucumber_formatters", requested_cucumber_formatters)
        object.__setattr__(self, "formatter_catalog", formatter_catalog)

    def render_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        renderer = cast(
            Callable[
                [list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...]],
                dict[str, str],
            ],
            self.formatter_catalog.render_runtime_assets,
        )
        return renderer(formatter_requests)


class _StandaloneLiveFormatterService(LiveFormatterService):
    def __init__(self, reporter: _StandaloneReporterRuntime) -> None:
        self.reporter = cast(GherkinMessageReporter, reporter)


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
        return cast(
            tuple[CucumberFormatterRequest, ...],
            resolve_standalone_formatter_requests(
                rootpath=rootpath,
                formatter_option_values=formatter_option_values,
                catalog=self.catalog,
            ),
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
        live_formatter_service = _StandaloneLiveFormatterService(reporter=runtime)
        envelopes = TransportService.read_envelopes_from_path(messages_path)
        return live_formatter_service.run_requested_cucumber_formatters(envelopes)


__all__ = (
    "CucumberFormatterConfigurationError",
    "StandaloneCucumberFormatterRenderer",
)
