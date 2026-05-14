"""Provide cucumber json formatter helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.util.cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin

if TYPE_CHECKING:
    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, ResolveOutputPath


class JsonFormatterPlugin(FormatterReporterPlugin):
    """Represent json formatter plugin state."""

    output_mode = FormatterOutputMode.path

    def __init__(self) -> None:
        """Initialize the json formatter plugin."""
        super().__init__(
            option_attr="cucumber_js_json_path",
            cli_flag="--cucumber-json",
            formatter="json",
            package_name="@cucumber/cucumber",
            module_name="pytest_bdd.plugin.cucumber_json_formatter.entrypoint",
            help_text="render the cucumber json formatter to the given path.",
            discovery_order=3,
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
        return self.build_builtin_required_path_request(raw_value, resolve_output_path=resolve_output_path)
