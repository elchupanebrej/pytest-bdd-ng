from __future__ import annotations

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin, FormatterRuntimeKind


class JunitFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.path
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "junit.cjs.j2"

    def __init__(self) -> None:
        super().__init__(
            option_attr="cucumber_junit_path",
            cli_flag="--cucumber-junit",
            formatter="junit",
            package_name="@cucumber/junit-xml-formatter",
            module_name=__name__,
            help_text="render the cucumber junit formatter to the given path.",
            discovery_order=4,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        return self.build_required_path_addoption_kwargs()

    def build_request_from_value(self, raw_value: object, *, resolve_output_path):
        return self.build_module_required_path_request(
            raw_value,
            resolve_output_path=resolve_output_path,
            template_name=type(self).runtime_template_name,
        )

    def render_runtime_assets(self, formatter_request, formatter_requests):
        return self.build_module_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=formatter_requests,
            template_name=type(self).runtime_template_name,
        )


junit_plugin = JunitFormatterPlugin()
