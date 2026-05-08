"""Provide cucumber pretty helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin, FormatterRuntimeKind

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest, ResolveOutputPath


class PrettyFormatterPlugin(FormatterReporterPlugin):
    """Represent pretty formatter plugin state."""

    output_mode = FormatterOutputMode.stdout
    writes_to_terminal = True
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "pretty.cjs.j2"

    def __init__(self) -> None:
        """Initialize the pretty formatter plugin."""
        super().__init__(
            option_attr="cucumber_pretty",
            cli_flag="--cucumber-pretty",
            formatter="pretty",
            package_name="@cucumber/pretty-formatter",
            module_name=__name__,
            help_text="render the @cucumber/pretty-formatter output to stdout.",
            discovery_order=8,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        """
        Build addoption kwargs.

        Returns:
            Keyword arguments for addoption.

        """
        return self.build_boolean_addoption_kwargs()

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
        _ = raw_value, resolve_output_path
        return self.build_module_terminal_request(template_name=type(self).runtime_template_name)

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


pretty_plugin = PrettyFormatterPlugin()
