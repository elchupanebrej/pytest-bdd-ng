# init: allow  # init: no-check
"""
Compatibility module for pytest.

Responsibility:
    Compatibility module for pytest. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.pytest` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - is_pytest_version_greater_or_equal: owns nested behavior below this boundary
    - Module: owns nested behavior below this boundary
    - fail: owns nested behavior below this boundary
    - is_set: owns nested behavior below this boundary
    - is_testrun_success: owns nested behavior below this boundary
    - _LegacyFixtureDefFactory: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector.py: imports or references `pytest`
    - src/pytest_bdd/compatibility/parser.py: imports or references `pytest`
    - src/pytest_bdd/feature_locator.py: imports or references `pytest`
    - src/pytest_bdd/hook.py: imports or references `pytest`
    - src/pytest_bdd/model/message_registry.py: imports or references `pytest`

State and side effects:
    mutates PYTEST8, PYTEST81, PYTEST83, FixtureRequest, Testdir; depends on __future__.annotations, operator.ge,
    pathlib.Path, typing.TYPE_CHECKING, typing.NoReturn.

Invariants:
    - `pytest_bdd.compatibility.pytest` keeps its documented import path, ownership boundary, and observable behavior
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

from operator import ge
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from os import PathLike

    from _pytest.scope import Scope, _ScopeName

from _pytest.compat import NotSetType
from _pytest.config import Config as Config
from _pytest.config import ExitCode as ExitCode
from _pytest.config import PytestPluginManager as PytestPluginManager
from _pytest.config import _prepareconfig
from _pytest.config.argparsing import Parser as Parser
from _pytest.fixtures import FixtureDef as FixtureDef
from _pytest.fixtures import FixtureLookupError as FixtureLookupError
from _pytest.fixtures import call_fixture_func as call_fixture_func
from _pytest.main import Session as Session
from _pytest.main import wrap_session as wrap_session
from _pytest.mark import Mark as Mark
from _pytest.mark import MarkDecorator as MarkDecorator
from _pytest.mark import MarkMatcher as MarkMatcher
from _pytest.mark import expression as _mark_expression
from _pytest.nodes import Collector as Collector
from _pytest.pytester import RunResult as RunResult
from _pytest.python import Metafunc as Metafunc
from _pytest.reports import TestReport as TestReport
from _pytest.runner import CallInfo as CallInfo
from _pytest.stash import Stash as Stash
from _pytest.terminal import TerminalReporter as TerminalReporter

import pytest
from pytest_bdd.util.packaging import compare_distribution_version


# region pytest version dependent imports
def is_pytest_version_greater_or_equal(version: str) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.compatibility.pytest.is_pytest_version_greater_or_equal` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.is_pytest_version_greater_or_equal`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - compare_distribution_version: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `is_pytest_version_greater_or_equal`
        - src/pytest_bdd/compatibility/parser.py: imports or references `is_pytest_version_greater_or_equal`
        - src/pytest_bdd/feature_locator.py: imports or references `is_pytest_version_greater_or_equal`
        - src/pytest_bdd/hook.py: imports or references `is_pytest_version_greater_or_equal`
        - src/pytest_bdd/model/message_registry.py: imports or references `is_pytest_version_greater_or_equal`

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
    return compare_distribution_version("pytest", version, ge)


PYTEST8, PYTEST81, PYTEST83 = map(
    is_pytest_version_greater_or_equal,
    [
        "8.0",
        "8.1",
        "8.3",
    ],
)
# endregion

FixtureRequest = pytest.FixtureRequest
Testdir = pytest.Testdir

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.nodes import Item as BaseItem

    class Item(BaseItem):
        """
        Represent item state.

        Responsibility:
            Represent item state. It directly owns the observable contract, local decisions, and maintenance boundary
            for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.compatibility.pytest.Item` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `Item`
            - src/pytest_bdd/compatibility/parser.py: imports or references `Item`
            - src/pytest_bdd/feature_locator.py: imports or references `Item`
            - src/pytest_bdd/hook.py: imports or references `Item`
            - src/pytest_bdd/model/message_registry.py: imports or references `Item`

        State and side effects:
            mutates _request.

        Invariants:
            - `pytest_bdd.compatibility.pytest.Item` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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

        _request: FixtureRequest

else:
    from _pytest.nodes import Item


class Module(pytest.Module):
    """
    Represent a pytest module with path helpers.

    Responsibility:
        Represent a pytest module with path helpers. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.Module` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - build: owns nested behavior below this boundary
        - get_path: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/checkers/file_size_rules.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/init_rules.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/noqa_rules.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `Module`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.compatibility.pytest.Module` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    @classmethod
    def build(cls, parent: Collector, file_path: str | PathLike[str]) -> Module:
        """
        Build module instance.

        Returns:
            Module instance configured with the given file path.

        Responsibility:
            Build module instance. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.compatibility.pytest.Module.build` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - cls.from_parent: collaborator call used by this boundary
            - Path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `build`
            - src/pytest_bdd/compatibility/parser.py: imports or references `build`
            - src/pytest_bdd/feature_locator.py: imports or references `build`
            - src/pytest_bdd/hook.py: imports or references `build`
            - src/pytest_bdd/model/message_registry.py: imports or references `build`

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
        return cast("Module", cls.from_parent(parent, path=Path(file_path)))

    def get_path(self) -> Path:
        """
        Get the module's path.

        Returns:
            Path to the module file.

        Responsibility:
            Get the module's path. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.compatibility.pytest.Module.get_path` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - Path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `get_path`
            - src/pytest_bdd/compatibility/parser.py: imports or references `get_path`
            - src/pytest_bdd/feature_locator.py: imports or references `get_path`
            - src/pytest_bdd/hook.py: imports or references `get_path`
            - src/pytest_bdd/model/message_registry.py: imports or references `get_path`

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
        return getattr(self, "path", Path(self.fspath))


def fail(reason: str, *, pytrace: bool = True) -> NoReturn:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.compatibility.pytest.fail` owns documented function behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.fail` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest.fail: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `fail`
        - src/pytest_bdd/compatibility/parser.py: imports or references `fail`
        - src/pytest_bdd/feature_locator.py: imports or references `fail`
        - src/pytest_bdd/hook.py: imports or references `fail`
        - src/pytest_bdd/model/message_registry.py: imports or references `fail`

    State and side effects:
        mutates __tracebackhide__.

    Invariants:
        - `pytest_bdd.compatibility.pytest.fail` keeps its documented import path, ownership boundary, and observable
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
    __tracebackhide__ = True
    pytest.fail(reason, pytrace=pytrace)


def is_set(obj: object) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.compatibility.pytest.is_set` owns documented function behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.is_set` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `is_set`
        - src/pytest_bdd/compatibility/parser.py: imports or references `is_set`
        - src/pytest_bdd/feature_locator.py: imports or references `is_set`
        - src/pytest_bdd/hook.py: imports or references `is_set`
        - src/pytest_bdd/model/message_registry.py: imports or references `is_set`

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
    return not isinstance(obj, NotSetType)


def is_testrun_success(exitstatus: int | pytest.ExitCode) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.compatibility.pytest.is_testrun_success` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.is_testrun_success` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `is_testrun_success`
        - src/pytest_bdd/compatibility/parser.py: imports or references `is_testrun_success`
        - src/pytest_bdd/feature_locator.py: imports or references `is_testrun_success`
        - src/pytest_bdd/hook.py: imports or references `is_testrun_success`
        - src/pytest_bdd/model/message_registry.py: imports or references `is_testrun_success`

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
    return (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is pytest.ExitCode.OK


class _LegacyFixtureDefFactory(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.compatibility.pytest._LegacyFixtureDefFactory` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest._LegacyFixtureDefFactory` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `_LegacyFixtureDefFactory`
        - src/pytest_bdd/compatibility/parser.py: imports or references `_LegacyFixtureDefFactory`
        - src/pytest_bdd/feature_locator.py: imports or references `_LegacyFixtureDefFactory`
        - src/pytest_bdd/hook.py: imports or references `_LegacyFixtureDefFactory`
        - src/pytest_bdd/model/message_registry.py: imports or references `_LegacyFixtureDefFactory`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.compatibility.pytest._LegacyFixtureDefFactory` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    def __call__(  # noqa: PLR0913, PLR0917
        self,
        fixturemanager: object,
        baseid: str | None,
        argname: str,
        func: Callable[[], object],
        scope: _ScopeName | Scope | Callable[[str, Config], _ScopeName] | None,
        params: Sequence[object] | None,
        ids: tuple[object | None, ...] | Callable[[object], object | None] | None = None,
        *,
        _ispytest: bool = False,
    ) -> FixtureDef:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.compatibility.pytest._LegacyFixtureDefFactory.__call__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.compatibility.pytest._LegacyFixtureDefFactory.__call__` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `__call__`
            - src/pytest_bdd/compatibility/parser.py: imports or references `__call__`
            - src/pytest_bdd/feature_locator.py: imports or references `__call__`
            - src/pytest_bdd/hook.py: imports or references `__call__`
            - src/pytest_bdd/model/message_registry.py: imports or references `__call__`

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


def build_fixture_def(  # noqa: PLR0913
    request: FixtureRequest,
    *,
    baseid: str | None,
    argname: str,
    func: Callable[[], object],
    scope: _ScopeName | Scope | Callable[[str, Config], _ScopeName] | None,
    params: Sequence[object] | None,
) -> FixtureDef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.compatibility.pytest.build_fixture_def` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.build_fixture_def` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - FixtureDef: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - legacy_fixture_def: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `build_fixture_def`
        - src/pytest_bdd/compatibility/parser.py: imports or references `build_fixture_def`
        - src/pytest_bdd/feature_locator.py: imports or references `build_fixture_def`
        - src/pytest_bdd/hook.py: imports or references `build_fixture_def`
        - src/pytest_bdd/model/message_registry.py: imports or references `build_fixture_def`

    State and side effects:
        mutates legacy_fixture_def.

    Invariants:
        - `pytest_bdd.compatibility.pytest.build_fixture_def` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    if PYTEST81:
        return FixtureDef(  # type: ignore[call-arg]  # pytest private API: _ispytest kwarg not in public types
            request.config,
            baseid,
            argname,
            func,
            scope,
            params,
            None,
            _ispytest=PYTEST8,
        )
    legacy_fixture_def = cast("_LegacyFixtureDefFactory", FixtureDef)
    return legacy_fixture_def(request._fixturemanager, baseid, argname, func, scope, params)  # noqa: SLF001


Expression = _mark_expression.Expression
ParseError = getattr(_mark_expression, "ParseError", ValueError)
prepareconfig = _prepareconfig


def make_mark(
    name: str,
    args: tuple[object, ...] = (),
    kwargs: dict[str, object] | None = None,
) -> Mark:
    """
    Create a pytest Mark using the private Mark constructor.

    The public pytest API expects ``pytest.mark.NAME()`` decorators, but programmatic
    mark creation requires the private ``Mark()`` constructor with the internal
    ``_ispytest`` flag. This helper isolates the ``type: ignore`` to a single
    well-documented location.

    Responsibility:
        Create a pytest Mark using the private Mark constructor. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.make_mark` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Mark: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `make_mark`
        - src/pytest_bdd/compatibility/parser.py: imports or references `make_mark`
        - src/pytest_bdd/feature_locator.py: imports or references `make_mark`
        - src/pytest_bdd/hook.py: imports or references `make_mark`
        - src/pytest_bdd/model/message_registry.py: imports or references `make_mark`

    State and side effects:
        mutates kwargs.

    Invariants:
        - `pytest_bdd.compatibility.pytest.make_mark` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    if kwargs is None:
        kwargs = {}
    return Mark(name, args=args, kwargs=kwargs, _ispytest=True)  # type: ignore[call-arg]  # pytest private API


def make_mark_decorator(mark: Mark) -> MarkDecorator:
    """
    Wrap a Mark in a MarkDecorator using the private constructor.

    See :func:`make_mark` for rationale.

    Responsibility:
        Wrap a Mark in a MarkDecorator using the private constructor. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.pytest.make_mark_decorator` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - MarkDecorator: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `make_mark_decorator`
        - src/pytest_bdd/compatibility/parser.py: imports or references `make_mark_decorator`
        - src/pytest_bdd/feature_locator.py: imports or references `make_mark_decorator`
        - src/pytest_bdd/hook.py: imports or references `make_mark_decorator`
        - src/pytest_bdd/model/message_registry.py: imports or references `make_mark_decorator`

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
    return MarkDecorator(mark, _ispytest=True)  # type: ignore[call-arg]  # pytest private API
