from __future__ import annotations

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin


class SnippetsFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.stdout
    writes_to_terminal = True

    def __init__(self) -> None:
        super().__init__(
            option_attr="cucumber_snippets",
            cli_flag="--cucumber-snippets",
            formatter="snippets",
            package_name="@cucumber/cucumber",
            module_name=__name__,
            help_text="render the cucumber snippets formatter to stdout.",
            discovery_order=7,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        return self.build_boolean_addoption_kwargs()

    def build_request_from_value(self, raw_value: object, *, resolve_output_path):
        _ = raw_value, resolve_output_path
        return self.build_builtin_terminal_request()


snippets_plugin = SnippetsFormatterPlugin()
