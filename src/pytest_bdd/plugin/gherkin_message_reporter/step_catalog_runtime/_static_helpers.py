"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    parser = step_definition.parser

    if isinstance(parser, _CucumberExpression):
        matches = parser.rebuild_expression_in_test_context(request).match(step_text)
        if matches:

            def build_group(group: CucumberExpressionGroup) -> Group:
                """
                Implement plugin module operations for pytest-bdd.

                Responsibility:
                    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined
                    capability consumed by the broader BDD infrastructure.

                Reason for existence:
                    Consolidates related logic within a single module boundary to maintain high cohesion and serve as
                    the information expert for its domain concepts.

                Delegates:
                    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

                Cohesion:
                    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

                Separation:
                    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

                Main consumers:
                    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

                State and side effects:
                    None, keeps no persistent state beyond local scope.

                Invariants:
                    - All public API contracts defined by this entity must be honored by callers.

                Architecture score:
                    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
                    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
                    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
                    #arch-eval:cohesion=4  # Internal logic focus (1-5)
                    #arch-eval:separation=4  # Distinctness from peers (1-5)
                    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
                    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
                    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
                    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
