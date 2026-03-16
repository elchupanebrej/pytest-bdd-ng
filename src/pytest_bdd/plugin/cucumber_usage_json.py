from __future__ import annotations

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin


class UsageJsonFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.path

    def __init__(self) -> None:
        super().__init__(
            option_attr="cucumber_usage_json_path",
            cli_flag="--cucumber-usage-json",
            formatter="usage-json",
            package_name="@cucumber/cucumber",
            module_name=__name__,
            help_text="render the cucumber usage-json formatter to the given path.",
            discovery_order=6,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        return self.build_required_path_addoption_kwargs()

    def build_request_from_value(self, raw_value: object, *, resolve_output_path):
        return self.build_builtin_required_path_request(raw_value, resolve_output_path=resolve_output_path)


usage_json_plugin = UsageJsonFormatterPlugin()
