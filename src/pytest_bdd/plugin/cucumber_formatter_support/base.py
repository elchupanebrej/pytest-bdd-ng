"""Provide base helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest
from attrs import frozen

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.compatibility.importlib.resources import files

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_bdd.compatibility.pytest import Config, Parser
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest

    ResolveOutputPath = Callable[[str], Path]


def _load_template_asset(package: str, template_name: str) -> str:
    """
    Load a template asset from a package.

    Args:
        package: Package name.
        template_name: Template filename.

    Returns:
        Template content as string.

    """
    return files(package).joinpath(template_name).read_text(encoding="utf-8")


def load_formatter_adapter_support_template() -> str:
    """
    Load formatter adapter support template.

    Returns:
        Template content as string.

    """
    return _load_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates",
        "formatter_adapter_support.cjs.j2",
    )


def load_formatter_adapter_template(template_name: str) -> str:
    """
    Load formatter adapter template.

    Args:
        template_name: Template filename.

    Returns:
        Template content as string.

    """
    return _load_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates.formatters",
        template_name,
    )


def _coerce_cli_aliases(raw_value: object) -> tuple[str, ...]:
    """
    Coerce CLI aliases to a tuple.

    Args:
        raw_value: Raw value from argparse.

    Returns:
        Tuple of alias strings.

    Raises:
        TypeError: If value is invalid.

    """
    if raw_value in {None, ()}:
        return ()
    if not isinstance(raw_value, tuple):
        message = f"Unexpected formatter CLI aliases value: {raw_value!r}"
        raise TypeError(message)
    if not all(isinstance(alias, str) for alias in raw_value):
        message = f"Formatter CLI aliases must be strings: {raw_value!r}"
        raise TypeError(message)
    return raw_value


class FormatterOutputMode(StrEnum):
    """Represent formatter output mode state."""

    stdout = "stdout"
    path = "path"
    optional_path = "optional_path"


class FormatterRuntimeKind(StrEnum):
    """Represent formatter runtime kind state."""

    builtin = "builtin"
    module = "module"


@frozen
class FormatterReporterPlugin(ABC):
    """
    Represent formatter reporter plugin state.

    Raises:
        NotImplementedError: If the operation cannot be completed.
        ValueError: If the operation cannot be completed.

    """

    option_attr: str
    cli_flag: str
    formatter: str
    package_name: str
    module_name: str
    help_text: str
    discovery_order: int = 0
    cli_aliases: tuple[str, ...] = ()
    runtime_specifier: str | None = None
    runtime_export_name: str | None = None

    output_mode: ClassVar[FormatterOutputMode] = FormatterOutputMode.stdout
    writes_to_terminal: ClassVar[bool] = False
    runtime_kind: ClassVar[FormatterRuntimeKind] = FormatterRuntimeKind.builtin
    runtime_template_name: ClassVar[str | None] = None

    @property
    def plugin_name(self) -> str:
        """Handle plugin name."""
        return f"pytest-bdd-cucumber-formatter-{self.formatter}"

    @property
    def plugin_object_name(self) -> str:
        """Handle plugin object name."""
        return f"{self.formatter.replace('-', '_')}_plugin"

    @property
    def plugin_entrypoint_target(self) -> str:
        """Handle plugin entrypoint target."""
        return f"{self.module_name}:{self.plugin_object_name}"

    @property
    def has_module_runtime(self) -> bool:
        """Return module runtime."""
        return self.runtime_kind == FormatterRuntimeKind.module

    @property
    def module_runtime_template_name(self) -> str:
        """
        Handle module runtime template name.

        Raises:
            ValueError: If the operation cannot be completed.

        """
        template_name = type(self).runtime_template_name
        if template_name is None:
            message = f"Formatter {self.formatter} does not define a module runtime template"
            raise ValueError(message)
        return template_name

    @property
    def module_runtime_path(self) -> str:
        """Handle module runtime path."""
        return f"formatters/{Path(self.module_runtime_template_name).stem}"

    def _option_value(self, option_source: object) -> object:
        if isinstance(option_source, dict):
            return option_source.get(self.option_attr)
        option_values = getattr(option_source, "__dict__", None)
        if isinstance(option_values, dict):
            return option_values.get(self.option_attr)
        return getattr(option_source, self.option_attr, None)

    def addoption(self, parser: Parser) -> None:
        """Handle addoption."""
        group = parser.getgroup("bdd", "Cucumber Formatters")
        addoption_kwargs = self.build_addoption_kwargs()
        cli_aliases = _coerce_cli_aliases(addoption_kwargs.pop("cli_aliases", ()))
        group.addoption(self.cli_flag, *cli_aliases, **addoption_kwargs)

    @abstractmethod
    def build_addoption_kwargs(self) -> dict[str, object]:
        """
        Build addoption kwargs.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        """
        raise NotImplementedError

    def build_boolean_addoption_kwargs(self) -> dict[str, object]:
        """
        Build boolean addoption kwargs.

        Returns:
            Keyword arguments for boolean addoption.

        """
        return {
            "dest": self.option_attr,
            "help": self.help_text,
            "cli_aliases": self.cli_aliases,
            "action": "store_true",
            "default": False,
        }

    def build_required_path_addoption_kwargs(self) -> dict[str, object]:
        """
        Build required path addoption kwargs.

        Returns:
            Keyword arguments for required path addoption.

        """
        return {
            "dest": self.option_attr,
            "help": self.help_text,
            "cli_aliases": self.cli_aliases,
            "action": "store",
            "metavar": "path",
            "default": None,
        }

    def build_optional_path_addoption_kwargs(self) -> dict[str, object]:
        """
        Build optional path addoption kwargs.

        Returns:
            Keyword arguments for optional path addoption.

        """
        return {
            "dest": self.option_attr,
            "help": self.help_text,
            "cli_aliases": self.cli_aliases,
            "action": "store",
            "nargs": "?",
            "const": "-",
            "metavar": "path",
            "default": None,
        }

    def _build_request(
        self,
        *,
        output_path: Path | None,
        runtime_kind: FormatterRuntimeKind,
        runtime_template_name: str | None = None,
    ) -> CucumberFormatterRequest:
        from pytest_bdd.plugin.gherkin_message_reporter.session import (  # noqa: PLC0415 -- circular import with session.py
            CucumberFormatterRequest,
        )

        runtime_specifier = self.runtime_specifier or self.formatter
        runtime_module_path = None
        if runtime_kind == FormatterRuntimeKind.module:
            if runtime_template_name is None:
                message = f"Formatter {self.formatter} requires a runtime template"
                raise ValueError(message)
            runtime_module_path = f"formatters/{Path(runtime_template_name).stem}"

        return CucumberFormatterRequest(
            option_attr=self.option_attr,
            cli_flag=self.cli_flag,
            formatter=self.formatter,
            package_name=self.package_name,
            output_path=output_path,
            plugin_module=self.module_name,
            runtime_kind=runtime_kind,
            runtime_specifier=runtime_specifier,
            runtime_module_path=runtime_module_path,
            runtime_export_name=self.runtime_export_name,
            runtime_template_name=runtime_template_name,
            discovery_order=self.discovery_order,
        )

    def build_builtin_terminal_request(self) -> CucumberFormatterRequest:
        """
        Build builtin terminal request.

        Returns:
            Cucumber formatter request.

        """
        return self._build_request(output_path=None, runtime_kind=FormatterRuntimeKind.builtin)

    def build_module_terminal_request(self, *, template_name: str) -> CucumberFormatterRequest:
        """
        Build module terminal request.

        Returns:
            Cucumber formatter request.

        """
        return self._build_request(
            output_path=None,
            runtime_kind=FormatterRuntimeKind.module,
            runtime_template_name=template_name,
        )

    def build_builtin_required_path_request(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
        """
        Build builtin required path request.

        Returns:
            Cucumber formatter request.

        """
        return self._build_request(
            output_path=resolve_output_path(str(raw_value)),
            runtime_kind=FormatterRuntimeKind.builtin,
        )

    def build_module_required_path_request(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
        template_name: str,
    ) -> CucumberFormatterRequest:
        """
        Build module required path request.

        Returns:
            Cucumber formatter request.

        """
        return self._build_request(
            output_path=resolve_output_path(str(raw_value)),
            runtime_kind=FormatterRuntimeKind.module,
            runtime_template_name=template_name,
        )

    def build_builtin_optional_path_request(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
        """
        Build builtin optional path request.

        Returns:
            Cucumber formatter request.

        """
        output_path = None if raw_value == "-" else resolve_output_path(str(raw_value))
        return self._build_request(output_path=output_path, runtime_kind=FormatterRuntimeKind.builtin)

    def build_module_optional_path_request(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
        template_name: str,
    ) -> CucumberFormatterRequest:
        """
        Build module optional path request.

        Returns:
            Cucumber formatter request.

        """
        output_path = None if raw_value == "-" else resolve_output_path(str(raw_value))
        return self._build_request(
            output_path=output_path,
            runtime_kind=FormatterRuntimeKind.module,
            runtime_template_name=template_name,
        )

    @abstractmethod
    def build_request_from_value(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
        """
        Build request from value.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        """
        raise NotImplementedError

    def iter_requests_from_options(
        self,
        option_source: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> tuple[CucumberFormatterRequest, ...]:
        """
        Yield requests from options.

        Returns:
            Tuple of cucumber formatter requests.

        """
        raw_value = self._option_value(option_source)
        if raw_value in {None, False}:
            return ()
        return (self.build_request_from_value(raw_value, resolve_output_path=resolve_output_path),)

    @pytest.hookimpl
    def pytest_addoption(self, parser: Parser) -> None:
        """Handle the pytest addoption pytest hook."""
        self.addoption(parser)

    @pytest.hookimpl
    def pytest_bdd_cucumber_formatter_request(
        self,
        config: Config,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest | None:
        """
        Handle the pytest bdd cucumber formatter request pytest hook.

        Returns:
            Cucumber formatter request or None.

        """
        requests = self.iter_requests_from_options(config.option, resolve_output_path=resolve_output_path)
        if not requests:
            return None
        request = requests[0]
        if request.output_path is not None:
            setattr(config.option, self.option_attr, str(request.output_path))
        return request

    def build_builtin_runtime_assets(  # noqa: PLR6301 -- overrides FormatterReporterPlugin ABC method
        self,
        formatter_request: CucumberFormatterRequest,  # noqa: ARG002
        formatter_requests: tuple[CucumberFormatterRequest, ...],  # noqa: ARG002
    ) -> dict[str, str]:
        """
        Build builtin runtime assets.

        Returns:
            Empty runtime assets dictionary.

        """
        return {}

    def build_module_runtime_assets(
        self,
        *,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],  # noqa: ARG002
        template_name: str,
    ) -> dict[str, str]:
        """
        Build module runtime assets.

        Returns:
            Runtime assets dictionary.

        """
        if formatter_request.formatter != self.formatter:
            return {}
        return {
            "formatters/support.cjs": load_formatter_adapter_support_template(),
            f"formatters/{Path(template_name).stem}": load_formatter_adapter_template(template_name),
        }

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
        return self.build_builtin_runtime_assets(formatter_request, formatter_requests)

    @pytest.hookimpl
    def pytest_bdd_cucumber_formatter_runtime_assets(
        self,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        """
        Handle the pytest bdd cucumber formatter runtime assets pytest hook.

        Returns:
            Runtime assets dictionary.

        """
        return self.render_runtime_assets(formatter_request, formatter_requests)
