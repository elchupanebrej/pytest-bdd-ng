from __future__ import annotations

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin, FormatterRuntimeKind


class ProgressFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.stdout
    writes_to_terminal = True
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "progress.cjs.j2"

    def __init__(self) -> None:
        super().__init__(
            option_attr="cucumber_progress",
            cli_flag="--cucumber-progress",
            formatter="progress",
            package_name="@cucumber/cucumber",
            module_name=__name__,
            help_text="render the cucumber progress formatter to stdout.",
            discovery_order=1,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        return self.build_boolean_addoption_kwargs()

    def build_request_from_value(self, raw_value: object, *, resolve_output_path):
        _ = raw_value, resolve_output_path
        return self.build_module_terminal_request(template_name=type(self).runtime_template_name)

    def render_runtime_assets(self, formatter_request, formatter_requests):
        return self.build_module_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=formatter_requests,
            template_name=type(self).runtime_template_name,
        )


progress_plugin = ProgressFormatterPlugin()
