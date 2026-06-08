"""
Provide stable cucumber formatter contract types.

These are narrow data-only value types shared across formatter plugins.
No plugin runtime behavior lives here — only frozen request/result descriptors
and the type aliases that accompany them.

Responsibility:
    Provide stable cucumber formatter contract types. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.cucumber_formatter_contract` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - FormatterRuntimeKind: owns nested behavior below this boundary
    - CucumberFormatterRequest: owns nested behavior below this boundary
    - CucumberFormatterRenderResult: owns nested behavior below this boundary
    - NodePackageProvisionResult: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `cucumber_formatter_contract`
    - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `cucumber_formatter_contract`
    - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `cucumber_formatter_contract`
    - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `cucumber_formatter_contract`
    - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `cucumber_formatter_contract`

State and side effects:
    mutates missing_node, missing_packages, ResolveOutputPath, builtin, module; depends on __future__.annotations,
    collections.abc.Callable, pathlib.Path, attrs.frozen, pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.model.cucumber_formatter_contract` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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

from collections.abc import Callable
from pathlib import Path

from attrs import frozen

from pytest_bdd.compatibility.enum import StrEnum

ResolveOutputPath = Callable[[str], Path]


class FormatterRuntimeKind(StrEnum):
    """
    Represent formatter runtime kind state.

    Responsibility:
        Represent formatter runtime kind state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.cucumber_formatter_contract.FormatterRuntimeKind`
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
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `FormatterRuntimeKind`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `FormatterRuntimeKind`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `FormatterRuntimeKind`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `FormatterRuntimeKind`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `FormatterRuntimeKind`

    State and side effects:
        mutates builtin, module.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_contract.FormatterRuntimeKind` keeps its documented import path,
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

    builtin = "builtin"
    module = "module"


@frozen
class CucumberFormatterRequest:
    """
    Represent cucumber formatter request state.

    Responsibility:
        Represent cucumber formatter request state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.cucumber_formatter_contract.CucumberFormatterRequest` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `CucumberFormatterRequest`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `CucumberFormatterRequest`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `CucumberFormatterRequest`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `CucumberFormatterRequest`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `CucumberFormatterRequest`

    State and side effects:
        mutates option_attr, cli_flag, formatter, package_name, output_path.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_contract.CucumberFormatterRequest` keeps its documented import path,
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

    option_attr: str
    cli_flag: str
    formatter: str
    package_name: str
    output_path: Path | None
    plugin_module: str
    runtime_kind: FormatterRuntimeKind
    runtime_specifier: str | None = None
    runtime_module_path: str | None = None
    runtime_export_name: str | None = None
    runtime_template_name: str | None = None
    discovery_order: int = 0


@frozen
class CucumberFormatterRenderResult:
    """
    Represent cucumber formatter render result state.

    Responsibility:
        Represent cucumber formatter render result state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.cucumber_formatter_contract.CucumberFormatterRenderResult` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `CucumberFormatterRenderResult`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `CucumberFormatterRenderResult`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `CucumberFormatterRenderResult`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `CucumberFormatterRenderResult`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `CucumberFormatterRenderResult`

    State and side effects:
        mutates success, rendered_formatters, missing_node, missing_packages, process_exit_code.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_contract.CucumberFormatterRenderResult` keeps its documented import path,
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

    success: bool
    rendered_formatters: tuple[CucumberFormatterRequest, ...]
    missing_node: bool = False
    missing_packages: tuple[str, ...] = ()
    process_exit_code: int | None = None


@frozen
class NodePackageProvisionResult:
    """
    Represent node package provision result state.

    Responsibility:
        Represent node package provision result state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.cucumber_formatter_contract.NodePackageProvisionResult` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py: imports or references `NodePackageProvisionResult`
        - src/pytest_bdd/plugin/cucumber_junit/plugin.py: imports or references `NodePackageProvisionResult`
        - src/pytest_bdd/plugin/cucumber_pretty/plugin.py: imports or references `NodePackageProvisionResult`
        - src/pytest_bdd/plugin/cucumber_progress/plugin.py: imports or references `NodePackageProvisionResult`
        - src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py: imports or references `NodePackageProvisionResult`

    State and side effects:
        mutates env, missing_packages, installed_packages, node_modules_roots, missing_node.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_contract.NodePackageProvisionResult` keeps its documented import path,
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

    env: dict[str, str]
    missing_packages: tuple[str, ...] = ()
    installed_packages: tuple[str, ...] = ()
    node_modules_roots: tuple[Path, ...] = ()
    missing_node: bool = False
    missing_npm: bool = False
