"""Provide cucumber junit helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.util.cucumber_formatter_support.base import (
    FormatterOutputMode,
    FormatterReporterPlugin,
    FormatterRuntimeKind,
)

if TYPE_CHECKING:
    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, ResolveOutputPath


class JunitFormatterPlugin(FormatterReporterPlugin):
    """Represent junit formatter plugin state."""

    output_mode = FormatterOutputMode.path
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "junit.cjs.j2"

    def __init__(self) -> None:
        """Initialize the junit formatter plugin."""
        super().__init__(
            option_attr="cucumber_junit_path",
            cli_flag="--cucumber-junit",
            formatter="junit",
            package_name="@cucumber/junit-xml-formatter",
            module_name="pytest_bdd.plugin.cucumber_junit.entrypoint",
            help_text="render the cucumber junit formatter to the given path.",
            discovery_order=4,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        """
        Build addoption kwargs.

        Returns:
            Keyword arguments for addoption.

        """
        return self.build_required_path_addoption_kwargs()

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
        return self.build_module_required_path_request(
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
