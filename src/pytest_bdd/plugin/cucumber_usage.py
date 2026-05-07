from __future__ import annotations

from typing import TYPE_CHECKING

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin, FormatterRuntimeKind

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest, ResolveOutputPath


class UsageFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.optional_path
    writes_to_terminal = True
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "usage.cjs.j2"

    def __init__(self) -> None:
        super().__init__(
            option_attr="cucumber_usage_output",
            cli_flag="--cucumber-usage",
            formatter="usage",
            package_name="@cucumber/cucumber",
            module_name=__name__,
            help_text="render the cucumber usage formatter to stdout or to the optional given path.",
            discovery_order=5,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        return self.build_optional_path_addoption_kwargs()

    def build_request_from_value(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
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
        return self.build_module_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=formatter_requests,
            template_name=type(self).runtime_template_name,
        )


usage_plugin = UsageFormatterPlugin()
