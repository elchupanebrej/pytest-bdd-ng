"""
Provide inspect extra helpers.

Responsibility:
    Provide inspect extra helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.inspect_extra` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - ObjectCallable: owns nested behavior below this boundary
    - get_args: owns nested behavior below this boundary
    - get_first_source_line: owns nested behavior below this boundary
    - get_caller_module_locals: owns nested behavior below this boundary
    - get_caller_module_path: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `inspect_extra`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `inspect_extra`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references `inspect_extra`
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
      `inspect_extra`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `inspect_extra`

State and side effects:
    mutates params, code, frame; depends on __future__.annotations, inspect.getframeinfo, inspect.getsourcelines,
    inspect.signature, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.util.inspect_extra` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from inspect import getframeinfo, getsourcelines, signature
from typing import TYPE_CHECKING, Protocol, cast

from pytest_bdd.compatibility.sys import get_frame

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import CodeType, FrameType, FunctionType, MethodType, ModuleType, TracebackType


class ObjectCallable(Protocol):
    """
    Represent object callable state.

    Responsibility:
        Represent object callable state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.inspect_extra.ObjectCallable` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `ObjectCallable`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `ObjectCallable`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ObjectCallable`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
          `ObjectCallable`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `ObjectCallable`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.util.inspect_extra.ObjectCallable` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __call__(self, *args: object, **kwargs: object) -> object:
        """
        Handle call.

        Responsibility:
            Handle call. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.inspect_extra.ObjectCallable.__call__` because it
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `__call__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__call__`

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
        ...


def get_args(func: ObjectCallable) -> Sequence[str]:
    """
    Get a list of argument names for a function.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list

    Returns:
        List of positional argument names.

    Responsibility:
        Get a list of argument names for a function. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.inspect_extra.get_args` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - signature.parameters.values: collaborator call used by this boundary
        - signature: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/message_extension.py: imports or references `get_args`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `get_args`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `get_args`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references `get_args`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `get_args`

    State and side effects:
        mutates params.

    Invariants:
        - `pytest_bdd.util.inspect_extra.get_args` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_first_source_line(obj: object) -> int:
    """
    Get the first source line number of an object.

    Args:
        obj: Object to inspect.

    Returns:
        First source line number.

    Responsibility:
        Get the first source line number of an object. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.inspect_extra.get_first_source_line` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getsourcelines: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - int: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `get_first_source_line`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `get_first_source_line`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
          `get_first_source_line`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `get_first_source_line`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `get_first_source_line`

    State and side effects:
        mutates code.

    Invariants:
        - `pytest_bdd.util.inspect_extra.get_first_source_line` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    try:
        return getsourcelines(
            cast("ModuleType | type[object] | MethodType | FunctionType | TracebackType | FrameType | CodeType", obj),
        )[1]
    except (OSError, TypeError):
        code = getattr(obj, "__code__", None)
        if code is not None:
            return int(code.co_firstlineno)
        return 1


def get_caller_module_locals(stacklevel: int = 1) -> dict[str, object]:
    """
    Get the caller module locals dictionary.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.

    Returns:
        Caller's module locals dictionary.

    Responsibility:
        Get the caller module locals dictionary. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.inspect_extra.get_caller_module_locals` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_frame: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `get_caller_module_locals`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `get_caller_module_locals`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
          `get_caller_module_locals`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `get_caller_module_locals`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `get_caller_module_locals`

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
    return get_frame(stacklevel).f_locals


def get_caller_module_path(stacklevel: int = 1) -> str:
    """
    Get the caller module path.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.

    Returns:
        Path to the caller's module file.

    Responsibility:
        Get the caller module path. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.inspect_extra.get_caller_module_path` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_frame: collaborator call used by this boundary
        - getframeinfo: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `get_caller_module_path`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `get_caller_module_path`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
          `get_caller_module_path`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `get_caller_module_path`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `get_caller_module_path`

    State and side effects:
        mutates frame.

    Invariants:
        - `pytest_bdd.util.inspect_extra.get_caller_module_path` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    frame = get_frame(stacklevel)
    return getframeinfo(frame, context=0).filename
