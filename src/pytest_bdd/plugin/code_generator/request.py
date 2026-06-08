"""
Request and option helpers for code generation.

Responsibility:
    Request and option helpers for code generation. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.request` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - check_existence: owns nested behavior below this boundary
    - get_feature_paths: owns nested behavior below this boundary
    - get_invocation_feature_paths: owns nested behavior below this boundary
    - validate_feature_option: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `request`
    - src/pytest_bdd/hook.py: imports or references `request`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `request`
    - src/pytest_bdd/model/run/transitions.py: imports or references `request`
    - src/pytest_bdd/model/run_access.py: imports or references `request`

State and side effects:
    mutates skip_next, _OPTION_VALUES, _FEATURE_OPTION_VALUES, msg, configured_paths; depends on __future__.annotations,
    argparse, pathlib.Path, typing.TYPE_CHECKING, py.

Invariants:
    - `pytest_bdd.plugin.code_generator.request` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises argparse.ArgumentTypeError; callers must treat these as boundary failures.

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

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import py

    from pytest_bdd.compatibility.pytest import Config, Session


_OPTION_VALUES = {"--target-file"}
_FEATURE_OPTION_VALUES = {"--feature"}


def check_existence(file_name: str) -> Path:
    """
    Check file or directory name for existence.

    Args:
        file_name: File or directory name.

    Returns:
        Path object if exists.

    Raises:
        argparse.ArgumentTypeError: If the file or directory does not exist.

    Responsibility:
        Check file or directory name for existence. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.request.check_existence` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - Path.exists: collaborator call used by this boundary
        - argparse.ArgumentTypeError: collaborator call used by this boundary

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
        - `pytest_bdd.plugin.code_generator.request.check_existence` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises argparse.ArgumentTypeError; callers must treat these as boundary failures.

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
    if not Path(file_name).exists():
        msg = f"{file_name} is an invalid file or directory name"
        raise argparse.ArgumentTypeError(msg)
    return Path(file_name)


def get_feature_paths(config: Config) -> list[Path]:
    """
    Return positional feature paths for code-generation commands.

    Returns:
        Feature paths.

    Responsibility:
        Return positional feature paths for code-generation commands. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.request.get_feature_paths` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - check_existence: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `get_feature_paths`

    State and side effects:
        mutates configured_paths, legacy_feature_paths.

    Invariants:
        - `pytest_bdd.plugin.code_generator.request.get_feature_paths` keeps its documented import path, ownership
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
    configured_paths = getattr(config.option, "codegen_feature_paths", None)
    if configured_paths is not None:
        return list(configured_paths)
    legacy_feature_paths = getattr(config.option, "feature", None)
    if legacy_feature_paths:
        return [check_existence(str(path)) for path in legacy_feature_paths]
    return [check_existence(arg) for arg in config.args]


def get_invocation_feature_paths(config: Config) -> list[Path]:
    """
    Return feature paths supplied in original pytest invocation args.

    Returns:
        Feature paths.

    Responsibility:
        Return feature paths supplied in original pytest invocation args. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.request.get_invocation_feature_paths` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - check_existence: collaborator call used by this boundary
        - arg.startswith: collaborator call used by this boundary
        - paths.append: collaborator call used by this boundary
        - paths.extend: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `get_invocation_feature_paths`

    State and side effects:
        mutates skip_next, paths.

    Invariants:
        - `pytest_bdd.plugin.code_generator.request.get_invocation_feature_paths` keeps its documented import path,
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
    paths: list[Path] = []
    skip_next = False
    for arg in config.invocation_params.args:
        if skip_next:
            skip_next = False
            continue
        if arg in _OPTION_VALUES:
            skip_next = True
            continue
        if arg in _FEATURE_OPTION_VALUES:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        paths.append(check_existence(arg))
    paths.extend(check_existence(str(path)) for path in getattr(config.option, "feature", []) or [])
    return paths


def validate_feature_option(config: Config, session: Session, tw: py.io.TerminalWriter) -> bool:
    """
    Validate if the --feature parameter is provided.

    Returns:
        True if valid, False otherwise.

    Responsibility:
        Validate if the --feature parameter is provided. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.request.validate_feature_option`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_feature_paths: collaborator call used by this boundary
        - tw.line: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `validate_feature_option`

    State and side effects:
        mutates session.exitstatus.

    Invariants:
        - `pytest_bdd.plugin.code_generator.request.validate_feature_option` keeps its documented import path, ownership
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
    if not get_feature_paths(config):
        tw.line("At least one feature path is required.", red=True)
        session.exitstatus = 100
        return False
    return True
