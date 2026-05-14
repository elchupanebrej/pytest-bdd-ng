"""Provide cucumber usage helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.plugin.cucumber_formatter_support.base import (
    FormatterOutputMode,
    FormatterReporterPlugin,
    FormatterRuntimeKind,
)

if TYPE_CHECKING:
    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, ResolveOutputPath


class UsageFormatterPlugin(FormatterReporterPlugin):
    """Represent usage formatter plugin state."""

    output_mode = FormatterOutputMode.optional_path
    writes_to_terminal = True
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "usage.cjs.j2"

    def __init__(self) -> None:
        """Initialize the usage formatter plugin."""
        super().__init__(
            option_attr="cucumber_usage_output",
            cli_flag="--cucumber-usage",
            formatter="usage",
            package_name="@cucumber/cucumber",
            module_name="pytest_bdd.plugin.cucumber_usage.entrypoint",
            help_text="render the cucumber usage formatter to stdout or to the optional given path.",
            discovery_order=5,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        """
        Build addoption kwargs.

        Returns:
            Keyword arguments for addoption.

        """
        return self.build_optional_path_addoption_kwargs()

    def build_request_from_value(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
        """
        Build request from value.

        Returns:
            Cucumber formatter request.

        """
        return self.build_module_optional_path_request(
            raw_value,
            resolve_output_path=resolve_output_path,
            template_name=type(self).runtime_template_name,
        )

    def render_runtime_assets(
        self,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        """
        Render runtime assets.

        Returns:
            Rendered runtime assets dictionary.

        """
        return self.build_module_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=formatter_requests,
            template_name=type(self).runtime_template_name,
        )
