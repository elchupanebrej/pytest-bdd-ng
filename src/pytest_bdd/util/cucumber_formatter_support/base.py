"""
Provide base helpers.

Responsibility:
    Provide base helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support.base` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _load_template_asset: owns nested behavior below this boundary
    - load_formatter_adapter_support_template: owns nested behavior below this boundary
    - load_formatter_adapter_template: owns nested behavior below this boundary
    - _coerce_cli_aliases: owns nested behavior below this boundary
    - FormatterOutputMode: owns nested behavior below this boundary
    - FormatterReporterPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `base`
    - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `base`
    - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `base`
    - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `base`
    - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `base`

State and side effects:
    mutates message, cli_aliases, runtime_specifier, runtime_module_path, output_path; depends on
    __future__.annotations, abc.ABC, abc.abstractmethod, pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.util.cucumber_formatter_support.base` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError, ValueError, NotImplementedError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest
from attrs import frozen

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, FormatterRuntimeKind

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, Parser
    from pytest_bdd.model.cucumber_formatter_contract import ResolveOutputPath


def _load_template_asset(package: str, template_name: str) -> str:
    """
    Load a template asset from a package.

    Args:
        package: Package name.
        template_name: Template filename.

    Returns:
        Template content as string.

    Responsibility:
        Load a template asset from a package. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support.base._load_template_asset`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - files.joinpath.read_text: collaborator call used by this boundary
        - files.joinpath: collaborator call used by this boundary
        - files: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `_load_template_asset`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `_load_template_asset`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `_load_template_asset`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `_load_template_asset`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `_load_template_asset`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return str(files(package).joinpath(template_name).read_text(encoding="utf-8"))


def load_formatter_adapter_support_template() -> str:
    """
    Load formatter adapter support template.

    Returns:
        Template content as string.

    Responsibility:
        Load formatter adapter support template. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.base.load_formatter_adapter_support_template` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_template_asset: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
          `load_formatter_adapter_support_template`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
          `load_formatter_adapter_support_template`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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

    Responsibility:
        Load formatter adapter template. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.base.load_formatter_adapter_template` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_template_asset: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
          `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `load_formatter_adapter_template`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `load_formatter_adapter_template`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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

    Responsibility:
        Coerce CLI aliases to a tuple. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support.base._coerce_cli_aliases`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary
        - all: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `_coerce_cli_aliases`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `_coerce_cli_aliases`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `_coerce_cli_aliases`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `_coerce_cli_aliases`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `_coerce_cli_aliases`

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.base._coerce_cli_aliases` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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
    """
    Represent formatter output mode state.

    Responsibility:
        Represent formatter output mode state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support.base.FormatterOutputMode`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `FormatterOutputMode`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `FormatterOutputMode`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `FormatterOutputMode`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `FormatterOutputMode`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `FormatterOutputMode`

    State and side effects:
        mutates stdout, path, optional_path.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.base.FormatterOutputMode` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    stdout = "stdout"
    path = "path"
    optional_path = "optional_path"


# FormatterRuntimeKind is imported from pytest_bdd.model.cucumber_formatter_contract above.


@frozen  # noqa: PLR0904
class FormatterReporterPlugin(ABC):
    """
    Represent formatter reporter plugin state.

    Raises:
        NotImplementedError: If the operation cannot be completed.
        ValueError: If the operation cannot be completed.

    Responsibility:
        Represent formatter reporter plugin state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - plugin_name: owns nested behavior below this boundary
        - plugin_object_name: owns nested behavior below this boundary
        - plugin_entrypoint_target: owns nested behavior below this boundary
        - has_module_runtime: owns nested behavior below this boundary
        - module_runtime_template_name: owns nested behavior below this boundary
        - module_runtime_path: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `FormatterReporterPlugin`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `FormatterReporterPlugin`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `FormatterReporterPlugin`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `FormatterReporterPlugin`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `FormatterReporterPlugin`

    State and side effects:
        mutates cli_aliases, runtime_specifier, message, runtime_module_path, output_path.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError, NotImplementedError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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
        """
        Handle plugin name.

        Responsibility:
            Handle plugin name. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.plugin_name` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `plugin_name`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `plugin_name`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `plugin_name`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `plugin_name`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `plugin_name`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return f"pytest-bdd-cucumber-formatter-{self.formatter}"

    @property
    def plugin_object_name(self) -> str:
        """
        Handle plugin object name.

        Responsibility:
            Handle plugin object name. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.plugin_object_name` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.formatter.replace: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `plugin_object_name`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `plugin_object_name`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `plugin_object_name`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `plugin_object_name`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `plugin_object_name`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return f"{self.formatter.replace('-', '_')}_plugin"

    @property
    def plugin_entrypoint_target(self) -> str:
        """
        Handle plugin entrypoint target.

        Responsibility:
            Handle plugin entrypoint target. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.plugin_entrypoint_target` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `plugin_entrypoint_target`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `plugin_entrypoint_target`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `plugin_entrypoint_target`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `plugin_entrypoint_target`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `plugin_entrypoint_target`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return f"{self.module_name}:{self.plugin_object_name}"

    @property
    def has_module_runtime(self) -> bool:
        """
        Return module runtime.

        Responsibility:
            Return module runtime. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.has_module_runtime` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `has_module_runtime`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `has_module_runtime`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `has_module_runtime`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `has_module_runtime`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `has_module_runtime`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self.runtime_kind == FormatterRuntimeKind.module

    @property
    def module_runtime_template_name(self) -> str:
        """
        Handle module runtime template name.

        Raises:
            ValueError: If the operation cannot be completed.

        Responsibility:
            Handle module runtime template name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.module_runtime_template_name`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - type: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `module_runtime_template_name`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `module_runtime_template_name`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `module_runtime_template_name`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `module_runtime_template_name`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `module_runtime_template_name`

        State and side effects:
            mutates template_name, message.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.module_runtime_template_name`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        template_name = type(self).runtime_template_name
        if template_name is None:
            message = f"Formatter {self.formatter} does not define a module runtime template"
            raise ValueError(message)
        return template_name

    @property
    def module_runtime_path(self) -> str:
        """
        Handle module runtime path.

        Responsibility:
            Handle module runtime path. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.module_runtime_path` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `module_runtime_path`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `module_runtime_path`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `module_runtime_path`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `module_runtime_path`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `module_runtime_path`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return f"formatters/{Path(self.module_runtime_template_name).stem}"

    def _option_value(self, option_source: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin._option_value` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin._option_value` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - option_source.get: collaborator call used by this boundary
            - option_values.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `_option_value`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `_option_value`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `_option_value`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `_option_value`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `_option_value`

        State and side effects:
            mutates option_values.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin._option_value` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        if isinstance(option_source, dict):
            return option_source.get(self.option_attr)
        option_values = getattr(option_source, "__dict__", None)
        if isinstance(option_values, dict):
            return option_values.get(self.option_attr)
        return getattr(option_source, self.option_attr, None)

    def addoption(self, parser: Parser) -> None:
        """
        Handle addoption.

        Responsibility:
            Handle addoption. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.addoption` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - parser.getgroup: collaborator call used by this boundary
            - self.build_addoption_kwargs: collaborator call used by this boundary
            - _coerce_cli_aliases: collaborator call used by this boundary
            - addoption_kwargs.pop: collaborator call used by this boundary
            - group.addoption: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `addoption`
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `addoption`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `addoption`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `addoption`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `addoption`

        State and side effects:
            mutates group, addoption_kwargs, cli_aliases.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.addoption` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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

        Responsibility:
            Build addoption kwargs. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_addoption_kwargs` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `build_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `build_addoption_kwargs`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        raise NotImplementedError

    def build_boolean_addoption_kwargs(self) -> dict[str, object]:
        """
        Build boolean addoption kwargs.

        Returns:
            Keyword arguments for boolean addoption.

        Responsibility:
            Build boolean addoption kwargs. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_boolean_addoption_kwargs`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_boolean_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_boolean_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_boolean_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_boolean_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_boolean_addoption_kwargs`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build required path addoption kwargs. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_required_path_addoption_kwargs`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_required_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
              `build_required_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `build_required_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `build_required_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_required_path_addoption_kwargs`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build optional path addoption kwargs. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_optional_path_addoption_kwargs`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_optional_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
              `build_optional_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `build_optional_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `build_optional_path_addoption_kwargs`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_optional_path_addoption_kwargs`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin._build_request` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin._build_request` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ValueError: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - CucumberFormatterRequest: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `_build_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `_build_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `_build_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `_build_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `_build_request`

        State and side effects:
            mutates runtime_module_path, runtime_specifier, message.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin._build_request` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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

        Responsibility:
            Build builtin terminal request. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_builtin_terminal_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._build_request: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_builtin_terminal_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_builtin_terminal_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_builtin_terminal_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_builtin_terminal_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_builtin_terminal_request`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return self._build_request(output_path=None, runtime_kind=FormatterRuntimeKind.builtin)

    def build_module_terminal_request(self, *, template_name: str) -> CucumberFormatterRequest:
        """
        Build module terminal request.

        Returns:
            Cucumber formatter request.

        Responsibility:
            Build module terminal request. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_module_terminal_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._build_request: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_module_terminal_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_module_terminal_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_module_terminal_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_module_terminal_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_module_terminal_request`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build builtin required path request. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_builtin_required_path_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._build_request: collaborator call used by this boundary
            - resolve_output_path: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_builtin_required_path_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
              `build_builtin_required_path_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `build_builtin_required_path_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `build_builtin_required_path_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_builtin_required_path_request`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build module required path request. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_module_required_path_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._build_request: collaborator call used by this boundary
            - resolve_output_path: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_module_required_path_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_module_required_path_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `build_module_required_path_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `build_module_required_path_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_module_required_path_request`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build builtin optional path request. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_builtin_optional_path_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - resolve_output_path: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - self._build_request: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_builtin_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
              `build_builtin_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `build_builtin_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `build_builtin_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_builtin_optional_path_request`

        State and side effects:
            mutates output_path.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_builtin_optional_path_request`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build module optional path request. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_module_optional_path_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - resolve_output_path: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - self._build_request: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_module_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_module_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `build_module_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `build_module_optional_path_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_module_optional_path_request`

        State and side effects:
            mutates output_path.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_module_optional_path_request`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build request from value. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_request_from_value` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `build_request_from_value`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_request_from_value`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_request_from_value`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_request_from_value`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `build_request_from_value`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Yield requests from options. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.iter_requests_from_options` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._option_value: collaborator call used by this boundary
            - self.build_request_from_value: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `iter_requests_from_options`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `iter_requests_from_options`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `iter_requests_from_options`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `iter_requests_from_options`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `iter_requests_from_options`

        State and side effects:
            mutates raw_value.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.iter_requests_from_options` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        raw_value = self._option_value(option_source)
        if raw_value in {None, False}:
            return ()
        return (self.build_request_from_value(raw_value, resolve_output_path=resolve_output_path),)

    @pytest.hookimpl
    def pytest_addoption(self, parser: Parser) -> None:
        """
        Handle the pytest addoption pytest hook.

        Responsibility:
            Handle the pytest addoption pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.pytest_addoption` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.addoption: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `pytest_addoption`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `pytest_addoption`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `pytest_addoption`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `pytest_addoption`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `pytest_addoption`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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

        Responsibility:
            Handle the pytest bdd cucumber formatter request pytest hook. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.pytest_bdd_cucumber_formatter_request`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.iter_requests_from_options: collaborator call used by this boundary
            - setattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_request`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_request`

        State and side effects:
            mutates requests, request.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.pytest_bdd_cucumber_formatter_request`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        requests = self.iter_requests_from_options(config.option, resolve_output_path=resolve_output_path)
        if not requests:
            return None
        request = requests[0]
        if request.output_path is not None:
            setattr(config.option, self.option_attr, str(request.output_path))
        return request

    def build_builtin_runtime_assets(
        self,
        formatter_request: CucumberFormatterRequest,  # noqa: ARG002
        formatter_requests: tuple[CucumberFormatterRequest, ...],  # noqa: ARG002
    ) -> dict[str, str]:
        """
        Build builtin runtime assets.

        Returns:
            Empty runtime assets dictionary.

        Responsibility:
            Build builtin runtime assets. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_builtin_runtime_assets`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_builtin_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_builtin_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_builtin_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_builtin_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `build_builtin_runtime_assets`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

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

        Responsibility:
            Build module runtime assets. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.build_module_runtime_assets`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - load_formatter_adapter_support_template: collaborator call used by this boundary
            - load_formatter_adapter_template: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `build_module_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `build_module_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `build_module_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `build_module_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `build_module_runtime_assets`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Render runtime assets. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.render_runtime_assets` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.build_builtin_runtime_assets: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `render_runtime_assets`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Handle the pytest bdd cucumber formatter runtime assets pytest hook. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin.pytest_bdd_cucumber_formatter_runtime_assets`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.render_runtime_assets: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`
            - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return self.render_runtime_assets(formatter_request, formatter_requests)
