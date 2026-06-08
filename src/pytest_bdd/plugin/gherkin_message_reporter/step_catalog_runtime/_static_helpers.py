"""
Static helper methods extracted from StepCatalogService.

Responsibility:
    Static helper methods extracted from StepCatalogService. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for
    `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - _collect_available_defs_for_diagnostic: owns nested behavior below this boundary
    - _build_candidate_dicts: owns nested behavior below this boundary
    - _build_step_match_arguments_lists: owns nested behavior below this boundary
    - _build_parameter_type_source_reference: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
      `_static_helpers`
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py: imports or references
      `_static_helpers`

State and side effects:
    mutates result, reg, sd_msg, sr, source_ref; depends on __future__.annotations, contextlib.suppress,
    inspect.getfile, inspect.signature, pathlib.Path.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers` keeps its documented import
      path, ownership boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from contextlib import suppress
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING

from cucumber_messages import (
    Group,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    SourceReference,
    StepMatchArgument,
    StepMatchArgumentsList,
)

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.parsers import _CucumberExpression
from pytest_bdd.steps import Definition
from pytest_bdd.util.inspect_extra import get_first_source_line

if TYPE_CHECKING:
    from cucumber_expressions.group import Group as CucumberExpressionGroup

    from pytest_bdd.compatibility.pytest import Config, FixtureLookupError, FixtureRequest


def _collect_available_defs_for_diagnostic(
    config: Config,
    request: FixtureRequest,
) -> list[dict[str, object]]:
    """
    Collect serialized step definitions from the scoped registry for diagnostic payloads.

    Returns:
        Serialized step definitions visible to this request.

    Responsibility:
        Collect serialized step definitions from the scoped registry for diagnostic payloads. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._collect_available_defs_for_diagnostic`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - id: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - request.getfixturevalue: collaborator call used by this boundary
        - seen.add: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_collect_available_defs_for_diagnostic`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py: imports or references
          `_collect_available_defs_for_diagnostic`

    State and side effects:
        mutates reg, result, seen, sd_msg, sr.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._collect_available_defs_for_diagnostic`
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
        #arch-eval:locational_stability=3

    """
    result: list[dict[str, object]] = []
    seen: set[int] = set()
    try:
        reg = request.getfixturevalue("step_registry")
    except (FixtureLookupError, AssertionError):
        return result
    while reg is not None:
        for step_definition in reg:
            if id(step_definition) in seen:
                continue
            seen.add(id(step_definition))
            with suppress(Exception):
                sd_msg = step_definition.as_message(config)
                sr = sd_msg.source_reference
                source_ref: dict[str, object] = {}
                if sr is not None:
                    source_ref["uri"] = getattr(sr, "uri", None) or ""
                    loc = getattr(sr, "location", None)
                    source_ref["line"] = getattr(loc, "line", 1) if loc is not None else 1
                pat = getattr(sd_msg, "pattern", None)
                result.append(
                    {
                        "id": sd_msg.id,
                        "pattern": str(getattr(pat, "source", "") if pat is not None else ""),
                        "sourceReference": source_ref,
                    },
                )
        reg = getattr(reg, "parent", None)
    return result


def _build_candidate_dicts(
    config: Config,
    candidates: list[Definition],
) -> list[dict[str, object]]:
    """
    Serialize candidate Definition objects for an ambiguous-step diagnostic payload.

    Returns:
        Serialized candidate definition payloads.

    Responsibility:
        Serialize candidate Definition objects for an ambiguous-step diagnostic payload. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_candidate_dicts` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - cand.as_message: collaborator call used by this boundary
        - result.append: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_build_candidate_dicts`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py: imports or references
          `_build_candidate_dicts`

    State and side effects:
        mutates result, sd_msg, sr, source_ref, loc.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_candidate_dicts` keeps
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
        #arch-eval:locational_stability=3

    """
    result: list[dict[str, object]] = []
    for cand in candidates:
        with suppress(Exception):
            sd_msg = cand.as_message(config)
            sr = sd_msg.source_reference
            source_ref: dict[str, object] = {}
            if sr is not None:
                source_ref["uri"] = getattr(sr, "uri", None) or ""
                loc = getattr(sr, "location", None)
                source_ref["line"] = getattr(loc, "line", 1) if loc is not None else 1
            pat = getattr(sd_msg, "pattern", None)
            result.append(
                {
                    "stepDefinitionId": sd_msg.id,
                    "pattern": str(getattr(pat, "source", "") if pat is not None else ""),
                    "sourceReference": source_ref,
                },
            )
    return result


def _build_step_match_arguments_lists(
    *,
    request: FixtureRequest,
    step_definition: Definition,
    step_text: str,
) -> list[StepMatchArgumentsList]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_step_match_arguments_lists`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_step_match_arguments_lists`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - Group: collaborator call used by this boundary
        - build_group: collaborator call used by this boundary
        - StepMatchArgument: collaborator call used by this boundary
        - StepMatchArgumentsList: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_build_step_match_arguments_lists`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py: imports or references
          `_build_step_match_arguments_lists`

    State and side effects:
        mutates parser, matches, step_match_arguments, anon_groups, parameter_name.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_step_match_arguments_lists`
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
        #arch-eval:locational_stability=3
    """
    parser = step_definition.parser

    if isinstance(parser, _CucumberExpression):
        matches = parser.rebuild_expression_in_test_context(request).match(step_text)
        if matches:

            def build_group(group: CucumberExpressionGroup) -> Group:
                """
                Responsibility:
                    Responsibility: Responsibility:
                    `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_step_match_arguments_lists.build_group`
                    owns documented function behavior. It directly owns the observable contract, local decisions, and
                    maintenance boundary for this function.

                Reason for existence:
                    This entity is the information expert for
                    `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_step_match_arguments_lists.build_group`
                    because it keeps the nearest code, data shape, call signature, and failure knowledge together.

                Delegates:
                    - Group: collaborator call used by this boundary
                    - build_group: collaborator call used by this boundary

                Cohesion:
                    The implementation stays together because its imports, calls, state writes, and return contract
                    describe one maintainable decision unit.

                Separation:
                    - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                      changeable without widening caller knowledge.

                Main consumers:
                    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or
                      references `build_group`
                    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py: imports or
                      references `build_group`

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
                    #arch-eval:locational_stability=3
                """
                return Group(
                    **({"start": group.start} if group.start is not None else {}),
                    **({"value": group.value} if group.value is not None else {}),
                    children=[build_group(child) for child in (group.children or [])],
                )

            step_match_arguments = []
            for i, match in enumerate(matches):
                anon_groups = (
                    list(step_definition.anonymous_group_names) if step_definition.anonymous_group_names else []
                )
                parameter_name = anon_groups[i] if i < len(anon_groups) else None
                step_match_arguments.append(
                    StepMatchArgument(
                        group=build_group(match.group),
                        **({"parameter_type_name": str(parameter_name)} if parameter_name is not None else {}),
                    ),
                )
            return [StepMatchArgumentsList(step_match_arguments=step_match_arguments)]

    parsed_arguments = (
        step_definition.parser.parse_arguments(
            request,
            step_text,
            anonymous_group_names=step_definition.anonymous_group_names,
        )
        or {}
    )
    if not parsed_arguments:
        return []

    parsed_step_match_arguments: list[StepMatchArgument] = []
    for parameter_name, parameter_value in parsed_arguments.items():
        parameter_value_text = "" if parameter_value is None else str(parameter_value)
        parameter_start_index = step_text.find(parameter_value_text) if parameter_value_text else -1
        group = Group(
            children=[],
            **({"start": parameter_start_index} if parameter_start_index >= 0 else {}),
            **({"value": parameter_value_text} if parameter_value_text else {}),
        )
        parsed_step_match_arguments.append(
            StepMatchArgument(
                group=group,
                **({"parameter_type_name": str(parameter_name)} if parameter_name is not None else {}),
            ),
        )
    return [StepMatchArgumentsList(step_match_arguments=parsed_step_match_arguments)]


def _build_parameter_type_source_reference(config: Config, parameter_type: object) -> SourceReference | None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_parameter_type_source_reference`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_parameter_type_source_reference`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - getfile: collaborator call used by this boundary
        - get_first_source_line: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_build_parameter_type_source_reference`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py: imports or references
          `_build_parameter_type_source_reference`

    State and side effects:
        mutates transformer, source_file, source_line, parameter_types.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers._build_parameter_type_source_reference`
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
        #arch-eval:locational_stability=3
    """
    transformer = getattr(parameter_type, "transformer", None)
    if transformer is None:
        return None

    with suppress(OSError, TypeError, ValueError):
        source_file = getfile(transformer)
        source_line = get_first_source_line(transformer)
        parameter_types = list(signature(transformer).parameters.keys())
        return SourceReference(
            uri=Path(resolvepath(source_file, config.rootpath)).as_uri(),
            location=Location(line=source_line, column=1),
            java_method=JavaMethod(
                class_name=str(getattr(transformer, "__module__", "pytest_bdd.parameter_type")),
                method_name=str(getattr(transformer, "__name__", "transformer")),
                method_parameter_types=parameter_types,
            ),
            java_stack_trace_element=JavaStackTraceElement(
                class_name=str(getattr(transformer, "__module__", "pytest_bdd.parameter_type")),
                file_name=Path(source_file).name,
                method_name=str(getattr(transformer, "__name__", "transformer")),
            ),
        )
    return None
