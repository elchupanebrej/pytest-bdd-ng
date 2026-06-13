"""
Provides focused utility functions for the `base` concern within pytest-bdd utility layer,
offering helper operations.

Responsibility:
    Provides focused utility functions for the `base` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `base` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `base`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `base` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `base` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
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
    Perform the `_load_template_asset` operation within its module boundary, implementing a.
    focused helper function that.

    Responsibility:
        Performs the `_load_template_asset` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_load_template_asset` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _load_template_asset operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _load_template_asset for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _load_template_asset function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return str(files(package).joinpath(template_name).read_text(encoding="utf-8"))


def load_formatter_adapter_support_template() -> str:
    """
    Perform the `load_formatter_adapter_support_template` operation within its module boundary,.
    implementing a focused h.

    Responsibility:
        Performs the `load_formatter_adapter_support_template` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `load_formatter_adapter_support_template` exists as a standalone function because it
        encapsulates an operation that does not require shared instance state and benefits from being
        independently callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the load_formatter_adapter_support_template operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke load_formatter_adapter_support_template for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The load_formatter_adapter_support_template function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return _load_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates",
        "formatter_adapter_support.cjs.j2",
    )


def load_formatter_adapter_template(template_name: str) -> str:
    """
    Perform the `load_formatter_adapter_template` operation within its module boundary,.
    implementing a focused helper fu.

    Responsibility:
        Performs the `load_formatter_adapter_template` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `load_formatter_adapter_template` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the load_formatter_adapter_template operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke load_formatter_adapter_template for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The load_formatter_adapter_template function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return _load_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates.formatters",
        template_name,
    )


def _coerce_cli_aliases(raw_value: object) -> tuple[str, ...]:
    """
    Perform the `_coerce_cli_aliases` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `_coerce_cli_aliases` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_coerce_cli_aliases` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _coerce_cli_aliases operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _coerce_cli_aliases for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _coerce_cli_aliases function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
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
    Enumerates the possible states for the FormatterOutputMode domain as a StrEnum, providing
    symbolic constants that rep.

    Responsibility:
        Enumerates the possible states for the FormatterOutputMode domain as a StrEnum, providing
        symbolic constants that replace magic strings in error classification and reporting code
        throughout the pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for FormatterOutputMode ensures compile-time validation
        of failure codes, enables IDE autocompletion for error handlers, and centralizes the catalog of
        possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: FormatterOutputMode specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the FormatterOutputMode
        domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FormatterOutputMode for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a FormatterOutputMode state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    stdout = "stdout"
    path = "path"
    optional_path = "optional_path"


# FormatterRuntimeKind is imported from pytest_bdd.model.cucumber_formatter_contract above.


@frozen  # noqa: PLR0904  -- suppressed warning
class FormatterReporterPlugin(ABC):
    """
    Encapsulates the FormatterReporterPlugin concern within pytest-bdd, providing a focused set of
    collaborating operatio.

    Responsibility:
        Encapsulates the FormatterReporterPlugin concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        FormatterReporterPlugin is a distinct class because its methods share internal state and
        collaborate on a cohesive task that would be awkward to express as standalone functions with
        shared mutable parameters.

    Delegates:
        - ABC: FormatterReporterPlugin specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single FormatterReporterPlugin domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FormatterReporterPlugin for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of FormatterReporterPlugin maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
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
        Performs the plugin_name operation within the FormatterReporterPlugin boundary, handling its
        specific sub-task as par.

        Responsibility:
            Performs the plugin_name operation within the FormatterReporterPlugin boundary, handling its
            specific sub-task as part of the broader FormatterReporterPlugin responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            plugin_name is a distinct method because it encapsulates a specific behavioral concern that
            must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the plugin_name operation on FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return f"pytest-bdd-cucumber-formatter-{self.formatter}"

    @property
    def plugin_object_name(self) -> str:
        """
        Performs the plugin_object_name operation within the FormatterReporterPlugin boundary, handling
        its specific sub-task.

        Responsibility:
            Performs the plugin_object_name operation within the FormatterReporterPlugin boundary, handling
            its specific sub-task as part of the broader FormatterReporterPlugin responsibility in the
            pytest-bdd runtime lifecycle.

        Reason for existence:
            plugin_object_name is a distinct method because it encapsulates a specific behavioral concern
            that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the plugin_object_name operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return f"{self.formatter.replace('-', '_')}_plugin"

    @property
    def plugin_entrypoint_target(self) -> str:
        """
        Performs the plugin_entrypoint_target operation within the FormatterReporterPlugin boundary,
        handling its specific su.

        Responsibility:
            Performs the plugin_entrypoint_target operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            plugin_entrypoint_target is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the plugin_entrypoint_target operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return f"{self.module_name}:{self.plugin_object_name}"

    @property
    def has_module_runtime(self) -> bool:
        """
        Performs the has_module_runtime operation within the FormatterReporterPlugin boundary, handling
        its specific sub-task.

        Responsibility:
            Performs the has_module_runtime operation within the FormatterReporterPlugin boundary, handling
            its specific sub-task as part of the broader FormatterReporterPlugin responsibility in the
            pytest-bdd runtime lifecycle.

        Reason for existence:
            has_module_runtime is a distinct method because it encapsulates a specific behavioral concern
            that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the has_module_runtime operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return self.runtime_kind == FormatterRuntimeKind.module

    @property
    def module_runtime_template_name(self) -> str:
        """
        Performs the module_runtime_template_name operation within the FormatterReporterPlugin
        boundary, handling its specifi.

        Responsibility:
            Performs the module_runtime_template_name operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            module_runtime_template_name is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the module_runtime_template_name operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        template_name = type(self).runtime_template_name
        if template_name is None:
            message = f"Formatter {self.formatter} does not define a module runtime template"
            raise ValueError(message)
        return template_name

    @property
    def module_runtime_path(self) -> str:
        """
        Performs the module_runtime_path operation within the FormatterReporterPlugin boundary,
        handling its specific sub-tas.

        Responsibility:
            Performs the module_runtime_path operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            module_runtime_path is a distinct method because it encapsulates a specific behavioral concern
            that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the module_runtime_path operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return f"formatters/{Path(self.module_runtime_template_name).stem}"

    def _option_value(self, option_source: object) -> object:
        """
        Perform the _option_value operation within the FormatterReporterPlugin boundary, handling its.
        specific sub-task as p.

        Responsibility:
            Performs the _option_value operation within the FormatterReporterPlugin boundary, handling its
            specific sub-task as part of the broader FormatterReporterPlugin responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            _option_value is a distinct method because it encapsulates a specific behavioral concern that
            must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the _option_value operation on FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        if isinstance(option_source, dict):
            return option_source.get(self.option_attr)
        option_values = getattr(option_source, "__dict__", None)
        if isinstance(option_values, dict):
            return option_values.get(self.option_attr)
        return getattr(option_source, self.option_attr, None)

    def addoption(self, parser: Parser) -> None:
        """
        Perform the addoption operation within the FormatterReporterPlugin boundary, handling its.
        specific sub-task as part .

        Responsibility:
            Performs the addoption operation within the FormatterReporterPlugin boundary, handling its
            specific sub-task as part of the broader FormatterReporterPlugin responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            addoption is a distinct method because it encapsulates a specific behavioral concern that must
            be independently callable and potentially overridable by subclasses of FormatterReporterPlugin
            without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the addoption operation on FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        group = parser.getgroup("bdd", "Cucumber Formatters")
        addoption_kwargs = self.build_addoption_kwargs()
        cli_aliases = _coerce_cli_aliases(addoption_kwargs.pop("cli_aliases", ()))
        group.addoption(self.cli_flag, *cli_aliases, **addoption_kwargs)

    @abstractmethod
    def build_addoption_kwargs(self) -> dict[str, object]:
        """
        Perform the build_addoption_kwargs operation within the FormatterReporterPlugin boundary,.
        handling its specific sub-.

        Responsibility:
            Performs the build_addoption_kwargs operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_addoption_kwargs is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_addoption_kwargs operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        raise NotImplementedError

    def build_boolean_addoption_kwargs(self) -> dict[str, object]:
        """
        Perform the build_boolean_addoption_kwargs operation within the FormatterReporterPlugin.
        boundary, handling its speci.

        Responsibility:
            Performs the build_boolean_addoption_kwargs operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_boolean_addoption_kwargs is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_boolean_addoption_kwargs operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_required_path_addoption_kwargs operation within the FormatterReporterPlugin.
        boundary, handling its.

        Responsibility:
            Performs the build_required_path_addoption_kwargs operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_required_path_addoption_kwargs is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_required_path_addoption_kwargs operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_optional_path_addoption_kwargs operation within the FormatterReporterPlugin.
        boundary, handling its.

        Responsibility:
            Performs the build_optional_path_addoption_kwargs operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_optional_path_addoption_kwargs is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_optional_path_addoption_kwargs operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the _build_request operation within the FormatterReporterPlugin boundary, handling its.
        specific sub-task as .

        Responsibility:
            Performs the _build_request operation within the FormatterReporterPlugin boundary, handling its
            specific sub-task as part of the broader FormatterReporterPlugin responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            _build_request is a distinct method because it encapsulates a specific behavioral concern that
            must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the _build_request operation on FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_builtin_terminal_request operation within the FormatterReporterPlugin.
        boundary, handling its speci.

        Responsibility:
            Performs the build_builtin_terminal_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_builtin_terminal_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_builtin_terminal_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return self._build_request(output_path=None, runtime_kind=FormatterRuntimeKind.builtin)

    def build_module_terminal_request(self, *, template_name: str) -> CucumberFormatterRequest:
        """
        Perform the build_module_terminal_request operation within the FormatterReporterPlugin.
        boundary, handling its specif.

        Responsibility:
            Performs the build_module_terminal_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_module_terminal_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_module_terminal_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_builtin_required_path_request operation within the FormatterReporterPlugin.
        boundary, handling its .

        Responsibility:
            Performs the build_builtin_required_path_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_builtin_required_path_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_builtin_required_path_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_module_required_path_request operation within the FormatterReporterPlugin.
        boundary, handling its s.

        Responsibility:
            Performs the build_module_required_path_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_module_required_path_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_module_required_path_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_builtin_optional_path_request operation within the FormatterReporterPlugin.
        boundary, handling its .

        Responsibility:
            Performs the build_builtin_optional_path_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_builtin_optional_path_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_builtin_optional_path_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_module_optional_path_request operation within the FormatterReporterPlugin.
        boundary, handling its s.

        Responsibility:
            Performs the build_module_optional_path_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_module_optional_path_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_module_optional_path_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the build_request_from_value operation within the FormatterReporterPlugin boundary,.
        handling its specific su.

        Responsibility:
            Performs the build_request_from_value operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_request_from_value is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_request_from_value operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        raise NotImplementedError

    def iter_requests_from_options(
        self,
        option_source: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> tuple[CucumberFormatterRequest, ...]:
        """
        Perform the iter_requests_from_options operation within the FormatterReporterPlugin boundary,.
        handling its specific .

        Responsibility:
            Performs the iter_requests_from_options operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            iter_requests_from_options is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the iter_requests_from_options operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        raw_value = self._option_value(option_source)
        if raw_value in {None, False}:
            return ()
        return (self.build_request_from_value(raw_value, resolve_output_path=resolve_output_path),)

    @pytest.hookimpl
    def pytest_addoption(self, parser: Parser) -> None:
        """
        Perform the pytest_addoption operation within the FormatterReporterPlugin boundary, handling.
        its specific sub-task a.

        Responsibility:
            Performs the pytest_addoption operation within the FormatterReporterPlugin boundary, handling
            its specific sub-task as part of the broader FormatterReporterPlugin responsibility in the
            pytest-bdd runtime lifecycle.

        Reason for existence:
            pytest_addoption is a distinct method because it encapsulates a specific behavioral concern
            that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the pytest_addoption operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        self.addoption(parser)

    @pytest.hookimpl
    def pytest_bdd_cucumber_formatter_request(
        self,
        config: Config,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest | None:
        """
        Perform the pytest_bdd_cucumber_formatter_request operation within the FormatterReporterPlugin.
        boundary, handling it.

        Responsibility:
            Performs the pytest_bdd_cucumber_formatter_request operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            pytest_bdd_cucumber_formatter_request is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the pytest_bdd_cucumber_formatter_request operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        requests = self.iter_requests_from_options(config.option, resolve_output_path=resolve_output_path)
        if not requests:
            return None
        request = requests[0]
        if request.output_path is not None:
            setattr(config.option, self.option_attr, str(request.output_path))
        return request

    def build_builtin_runtime_assets(  # noqa: PLR6301  -- suppressed warning
        self,
        formatter_request: CucumberFormatterRequest,  # noqa: ARG002  -- suppressed warning
        formatter_requests: tuple[CucumberFormatterRequest, ...],  # noqa: ARG002  -- suppressed warning
    ) -> dict[str, str]:
        """
        Perform the build_builtin_runtime_assets operation within the FormatterReporterPlugin.
        boundary, handling its specifi.

        Responsibility:
            Performs the build_builtin_runtime_assets operation within the FormatterReporterPlugin
            boundary, handling its specific sub-task as part of the broader FormatterReporterPlugin
            responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_builtin_runtime_assets is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_builtin_runtime_assets operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return {}

    def build_module_runtime_assets(
        self,
        *,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],  # noqa: ARG002  -- suppressed warning
        template_name: str,
    ) -> dict[str, str]:
        """
        Perform the build_module_runtime_assets operation within the FormatterReporterPlugin boundary,.
        handling its specific.

        Responsibility:
            Performs the build_module_runtime_assets operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            build_module_runtime_assets is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build_module_runtime_assets operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the render_runtime_assets operation within the FormatterReporterPlugin boundary,.
        handling its specific sub-t.

        Responsibility:
            Performs the render_runtime_assets operation within the FormatterReporterPlugin boundary,
            handling its specific sub-task as part of the broader FormatterReporterPlugin responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            render_runtime_assets is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the render_runtime_assets operation on FormatterReporterPlugin
            instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return self.build_builtin_runtime_assets(formatter_request, formatter_requests)

    @pytest.hookimpl
    def pytest_bdd_cucumber_formatter_runtime_assets(
        self,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        """
        Perform the pytest_bdd_cucumber_formatter_runtime_assets operation within the.
        FormatterReporterPlugin boundary, hand.

        Responsibility:
            Performs the pytest_bdd_cucumber_formatter_runtime_assets operation within the
            FormatterReporterPlugin boundary, handling its specific sub-task as part of the broader
            FormatterReporterPlugin responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            pytest_bdd_cucumber_formatter_runtime_assets is a distinct method because it encapsulates a
            specific behavioral concern that must be independently callable and potentially overridable by
            subclasses of FormatterReporterPlugin without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the pytest_bdd_cucumber_formatter_runtime_assets operation on
            FormatterReporterPlugin instances.

        Separation:
            - Other FormatterReporterPlugin methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterReporterPlugin implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return self.render_runtime_assets(formatter_request, formatter_requests)
