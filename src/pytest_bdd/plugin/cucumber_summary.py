"""Provide cucumber summary helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest, ResolveOutputPath


class SummaryFormatterPlugin(FormatterReporterPlugin):
    """Represent summary formatter plugin state."""

    output_mode = FormatterOutputMode.stdout
    writes_to_terminal = True

    def __init__(self) -> None:
        """Initialize the summary formatter plugin."""
        super().__init__(
            option_attr="cucumber_summary",
            cli_flag="--cucumber-summary",
            formatter="summary",
            package_name="@cucumber/cucumber",
            module_name=__name__,
            help_text="render the cucumber summary formatter to stdout.",
            discovery_order=0,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        """Build addoption kwargs."""
        return self.build_boolean_addoption_kwargs()

    def build_request_from_value(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
        """Build request from value."""
        _ = raw_value, resolve_output_path
        return self.build_builtin_terminal_request()


summary_plugin = SummaryFormatterPlugin()
