"""
AST-aware target-file rewrite helpers for code generation.

Responsibility:
    AST-aware target-file rewrite helpers for code generation. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - TargetRewriteError: owns nested behavior below this boundary
    - bind_features_to_target: owns nested behavior below this boundary
    - append_missing_step_skeletons: owns nested behavior below this boundary
    - validate_target_file: owns nested behavior below this boundary
    - _read_target: owns nested behavior below this boundary
    - _parse_existing: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates tree, original, content, snippets, proposed; depends on __future__.annotations, ast, subprocess, sys,
    pathlib.Path.

Invariants:
    - `pytest_bdd.plugin.code_generator.rewrite` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises TargetRewriteError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import ast
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .events import MissingStepDefinitionEvent
from .rendering import make_string_literal, render_missing_step_skeleton

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from pytest_bdd.plugin.code_generator.events import CodeGenerationEvent


STEP_KEYWORD_TO_DECORATOR = {
    "*": "step",
    "Given": "given",
    "When": "when",
    "Then": "then",
}


class TargetRewriteError(RuntimeError):
    """
    Raised when a target rewrite cannot be validated.

    Responsibility:
        Raised when a target rewrite cannot be validated. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite.TargetRewriteError` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `TargetRewriteError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite.TargetRewriteError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """


def bind_features_to_target(target_file: Path, feature_paths: Sequence[Path], *, keep_on_error: bool) -> bool:
    """
    Add scenarios(...) feature bindings to a target file.

    Args:
        target_file: Python target file.
        feature_paths: Feature files to bind.
        keep_on_error: Keep edited file on validation failure.

    Returns:
        True when target content changed.

    Responsibility:
        Add scenarios(...) feature bindings to a target file. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite.bind_features_to_target`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _read_target: collaborator call used by this boundary
        - _parse_existing_or_empty: collaborator call used by this boundary
        - _pytest_bdd_imported_names: collaborator call used by this boundary
        - _has_pytest_bdd_import: collaborator call used by this boundary
        - _existing_scenarios_bindings: collaborator call used by this boundary
        - _relative_feature_path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `bind_features_to_target`

    State and side effects:
        mutates original, tree, imports, has_pytest_bdd_import, existing_bindings.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite.bind_features_to_target` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    original = _read_target(target_file)
    tree = _parse_existing_or_empty(original)
    imports = _pytest_bdd_imported_names(tree)
    has_pytest_bdd_import = _has_pytest_bdd_import(tree)
    existing_bindings = _existing_scenarios_bindings(tree, imports=imports, has_pytest_bdd_import=has_pytest_bdd_import)
    relative_paths = [_relative_feature_path(target_file, feature_path) for feature_path in feature_paths]
    missing_paths = [path for path in relative_paths if path not in existing_bindings]
    if not missing_paths:
        return False

    content = _ensure_pytest_bdd_import(original, ["scenarios"])
    snippets = [f"scenarios({make_string_literal(path)})" for path in missing_paths]
    proposed = _append_block(content, "\n\n".join(snippets))
    return _write_transactional(target_file, original, proposed, keep_on_error=keep_on_error)


def append_missing_step_skeletons(
    target_file: Path,
    events: Sequence[CodeGenerationEvent],
    *,
    keep_on_error: bool,
) -> bool:
    """
    Append skeletons for missing step-definition events.

    Args:
        target_file: Python target file.
        events: Missing artifact events.
        keep_on_error: Keep edited file on validation failure.

    Returns:
        True when target content changed.

    Responsibility:
        Append skeletons for missing step-definition events. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.rewrite.append_missing_step_skeletons` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - STEP_KEYWORD_TO_DECORATOR.get: collaborator call used by this boundary
        - _read_target: collaborator call used by this boundary
        - _parse_existing_or_empty: collaborator call used by this boundary
        - _existing_step_decorators: collaborator call used by this boundary
        - _unique_missing_step_events: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `append_missing_step_skeletons`

    State and side effects:
        mutates original, tree, existing_steps, missing_events, decorators.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite.append_missing_step_skeletons` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    original = _read_target(target_file)
    tree = _parse_existing_or_empty(original)
    existing_steps = _existing_step_decorators(tree)
    missing_events = _unique_missing_step_events(events, existing_steps)
    if not missing_events:
        return False

    decorators = sorted({STEP_KEYWORD_TO_DECORATOR.get(event.keyword, "step") for event in missing_events})
    content = _ensure_pytest_bdd_import(original, [*decorators, "not_implemented"])
    snippets = [
        render_missing_step_skeleton(decorator=STEP_KEYWORD_TO_DECORATOR.get(event.keyword, "step"), text=event.text)
        for event in missing_events
    ]
    proposed = _append_block(content, "\n\n".join(snippet.rstrip() for snippet in snippets))
    return _write_transactional(target_file, original, proposed, keep_on_error=keep_on_error)


def validate_target_file(target_file: Path) -> None:
    """
    Validate code-generation target path.

    Args:
        target_file: Target path.

    Raises:
        TargetRewriteError: If target is not a Python file.

    Responsibility:
        Validate code-generation target path. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite.validate_target_file`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - TargetRewriteError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `validate_target_file`

    State and side effects:
        mutates msg.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite.validate_target_file` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TargetRewriteError; callers must treat these as boundary failures.

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
    if target_file.suffix != ".py":
        msg = f"Target file must be a Python file: {target_file}"
        raise TargetRewriteError(msg)


def _read_target(target_file: Path) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._read_target` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._read_target` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - target_file.exists: collaborator call used by this boundary
        - target_file.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if target_file.exists():
        return target_file.read_text(encoding="utf-8")
    return ""


def _parse_existing(content: str) -> ast.Module:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._parse_existing` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._parse_existing` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ast.parse: collaborator call used by this boundary
        - content.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if not content.strip():
        return ast.parse("")
    return ast.parse(content)


def _parse_existing_or_empty(content: str) -> ast.Module:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._parse_existing_or_empty` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._parse_existing_or_empty`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _parse_existing: collaborator call used by this boundary
        - ast.parse: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    try:
        return _parse_existing(content)
    except SyntaxError:
        return ast.parse("")


def _pytest_bdd_imported_names(tree: ast.Module) -> set[str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._pytest_bdd_imported_names` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._pytest_bdd_imported_names`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - names.update: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates names.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._pytest_bdd_imported_names` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "pytest_bdd":
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def _has_pytest_bdd_import(tree: ast.Module) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._has_pytest_bdd_import` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._has_pytest_bdd_import`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - any: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return any(
        isinstance(node, ast.Import) and any(alias.name == "pytest_bdd" for alias in node.names) for node in tree.body
    )


def _existing_scenarios_bindings(tree: ast.Module, *, imports: set[str], has_pytest_bdd_import: bool) -> set[str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._existing_scenarios_bindings` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.rewrite._existing_scenarios_bindings` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - ast.walk: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - _is_scenarios_call: collaborator call used by this boundary
        - bindings.update: collaborator call used by this boundary
        - _literal_strings: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates bindings.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._existing_scenarios_bindings` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    bindings: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if _is_scenarios_call(node, imports=imports, has_pytest_bdd_import=has_pytest_bdd_import):
            bindings.update(_literal_strings(node.args[0]))
    return bindings


def _is_scenarios_call(node: ast.Call, *, imports: set[str], has_pytest_bdd_import: bool) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._is_scenarios_call` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._is_scenarios_call` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if isinstance(node.func, ast.Name):
        return node.func.id == "scenarios" and "scenarios" in imports
    return (
        has_pytest_bdd_import
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "scenarios"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pytest_bdd"
    )


def _literal_strings(node: ast.AST) -> set[str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._literal_strings` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._literal_strings` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - values.update: collaborator call used by this boundary
        - _literal_strings: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates values.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._literal_strings` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        values: set[str] = set()
        for element in node.elts:
            values.update(_literal_strings(element))
        return values
    return set()


def _existing_step_decorators(tree: ast.Module) -> set[tuple[str, str]]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._existing_step_decorators` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._existing_step_decorators`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - ast.walk: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - _step_decorator_signature: collaborator call used by this boundary
        - steps.add: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates steps, step.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._existing_step_decorators` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    steps: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            step = _step_decorator_signature(decorator)
            if step is not None:
                steps.add(step)
    return steps


def _step_decorator_signature(decorator: ast.AST) -> tuple[str, str] | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._step_decorator_signature` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._step_decorator_signature`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - _decorator_name: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - STEP_KEYWORD_TO_DECORATOR.values: collaborator call used by this boundary
        - _literal_strings: collaborator call used by this boundary
        - next: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates decorator_name, text_values.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._step_decorator_signature` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if not isinstance(decorator, ast.Call) or not decorator.args:
        return None
    decorator_name = _decorator_name(decorator.func)
    if decorator_name not in set(STEP_KEYWORD_TO_DECORATOR.values()):
        return None
    text_values = _literal_strings(decorator.args[0])
    if not text_values:
        return None
    return decorator_name, next(iter(text_values))


def _decorator_name(func: ast.AST) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._decorator_name` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._decorator_name` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _unique_missing_step_events(
    events: Sequence[CodeGenerationEvent],
    existing_steps: set[tuple[str, str]],
) -> list[MissingStepDefinitionEvent]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._unique_missing_step_events` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._unique_missing_step_events`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - STEP_KEYWORD_TO_DECORATOR.get: collaborator call used by this boundary
        - seen.add: collaborator call used by this boundary
        - unique.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates seen, unique, decorator, key.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._unique_missing_step_events` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    seen: set[tuple[str, str]] = set()
    unique: list[MissingStepDefinitionEvent] = []
    for event in events:
        if not isinstance(event, MissingStepDefinitionEvent):
            continue
        decorator = STEP_KEYWORD_TO_DECORATOR.get(event.keyword, "step")
        key = (decorator, event.text)
        if key in existing_steps or key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return unique


def _ensure_pytest_bdd_import(content: str, required_names: Iterable[str]) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._ensure_pytest_bdd_import` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._ensure_pytest_bdd_import`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - dict.fromkeys: collaborator call used by this boundary
        - _parse_existing_or_empty: collaborator call used by this boundary
        - content.splitlines: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates required, tree, lines, existing, missing.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._ensure_pytest_bdd_import` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    required = list(dict.fromkeys(required_names))
    if not required:
        return content
    tree = _parse_existing_or_empty(content)
    lines = content.splitlines()
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module != "pytest_bdd":
            continue
        existing = [alias.asname or alias.name for alias in node.names]
        missing = [name for name in required if name not in existing]
        if not missing:
            return content
        updated = sorted({*existing, *missing})
        line_index = node.lineno - 1
        lines[line_index] = f"from pytest_bdd import {', '.join(updated)}"
        return "\n".join(lines) + ("\n" if content.endswith("\n") else "")

    import_line = f"from pytest_bdd import {', '.join(sorted(required))}"
    if not content.strip():
        return f"{import_line}\n"
    return f"{import_line}\n\n{content}"


def _append_block(content: str, block: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._append_block` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._append_block` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - block.rstrip: collaborator call used by this boundary
        - content.rstrip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates prefix.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._append_block` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    prefix = content.rstrip()
    if not prefix:
        return f"{block.rstrip()}\n"
    return f"{prefix}\n\n\n{block.rstrip()}\n"


def _relative_feature_path(target_file: Path, feature_path: Path) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._relative_feature_path` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._relative_feature_path`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - Path.cwd: collaborator call used by this boundary
        - feature_path.resolve.relative_to.as_posix: collaborator call used by this boundary
        - feature_path.resolve.relative_to: collaborator call used by this boundary
        - feature_path.resolve: collaborator call used by this boundary
        - target_parent.resolve: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates target_parent.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._relative_feature_path` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    target_parent = target_file.parent if target_file.parent != Path() else Path.cwd()
    try:
        return feature_path.resolve().relative_to(target_parent.resolve()).as_posix()
    except ValueError:
        return feature_path.as_posix()


def _write_transactional(target_file: Path, original: str, proposed: str, *, keep_on_error: bool) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._write_transactional` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._write_transactional`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - target_file.write_text: collaborator call used by this boundary
        - target_file.read_text: collaborator call used by this boundary
        - validate_target_file: collaborator call used by this boundary
        - target_file.parent.mkdir: collaborator call used by this boundary
        - _format_target_file: collaborator call used by this boundary
        - ast.parse: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates msg.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rewrite._write_transactional` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TargetRewriteError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    validate_target_file(target_file)
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(proposed, encoding="utf-8")
    try:
        _format_target_file(target_file)
        ast.parse(target_file.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, subprocess.SubprocessError) as exception:
        if not keep_on_error:
            target_file.write_text(original, encoding="utf-8")
        msg = f"Generated target file failed validation: {target_file}"
        raise TargetRewriteError(msg) from exception
    return target_file.read_text(encoding="utf-8") != original


def _format_target_file(target_file: Path) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rewrite._format_target_file` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rewrite._format_target_file` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - subprocess.run: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "ruff", "format", str(target_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
