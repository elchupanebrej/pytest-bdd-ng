# init: allow  # init: no-check
"""
Provide a cross-Python-version compatibility shim for `pytest`, encapsulating all version-
detection logic and condi.

Responsibility:
    Provides a cross-Python-version compatibility shim for `pytest`, encapsulating all version-
    detection logic and conditional imports so that higher layers import a single stable name
    regardless of the runtime Python interpreter version (3.10-3.14).

Reason for existence:
    Centralizing Python version-gating for `pytest` in this module prevents `if sys.version_info`
    checks from contaminating domain logic. This module is the single information expert for which
    stdlib/third-party names and APIs are available on each supported Python version for this
    specific concern.

Delegates:
    - Python stdlib/third-party: delegates actual implementation to the version-appropriate module

Cohesion:
    All symbols re-export a single compatibility concern (pytest); no unrelated utilities.

Separation:
    - Sibling compatibility modules: each handles a distinct stdlib version gap.

Main consumers:
    - `pytest_bdd.*`: all higher layers import compatibility shims to avoid inline version-gated logic

State and side effects:
    None, this module keeps no persistent state and performs only import-time version detection.

Invariants:
    - The public API surface matches the target stdlib module interface across supported Python versions.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
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
    Perform the `is_pytest_version_greater_or_equal` operation within its module boundary,
    implementing a focused helper.

    Responsibility:
        Performs the `is_pytest_version_greater_or_equal` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `is_pytest_version_greater_or_equal` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the is_pytest_version_greater_or_equal operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke is_pytest_version_greater_or_equal for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The is_pytest_version_greater_or_equal function returns consistent results for equivalent inputs.

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
        Encapsulates the Item concern within pytest-bdd, providing a focused set of collaborating
        operations that together de.

        Responsibility:
        Encapsulates the Item concern within pytest-bdd, providing a focused set of collaborating
        operations that together deliver a single well-defined capability consumed by the broader BDD
        runtime infrastructure.

        Reason for existence:
        Item is a distinct class because its methods share internal state and collaborate on a cohesive
        task that would be awkward to express as standalone functions with shared mutable parameters.

        Delegates:
        - BaseItem: Item specializes behavior from its parent(s) without duplicating their contracts

        Cohesion:
        All methods and attributes serve the single Item domain concern.

        Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

        Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate Item for error handling and type checking

        State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

        Invariants:
        - Instances of Item maintain internal consistency across all method calls.

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

        _request: FixtureRequest

else:
    from _pytest.nodes import Item


class Module(pytest.Module):
    """
    Encapsulates the Module concern within pytest-bdd, providing a focused set of collaborating
    operations that together .

    Responsibility:
        Encapsulates the Module concern within pytest-bdd, providing a focused set of collaborating
        operations that together deliver a single well-defined capability consumed by the broader BDD
        runtime infrastructure.

    Reason for existence:
        Module is a distinct class because its methods share internal state and collaborate on a
        cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - pytest.Module: Module specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single Module domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate Module for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of Module maintain internal consistency across all method calls.

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

    @classmethod
    def build(cls, parent: Collector, file_path: str | PathLike[str]) -> Module:
        """
        Perform the build operation within the Module boundary, handling its specific sub-task as part
        of the broader Module.

        Responsibility:
            Performs the build operation within the Module boundary, handling its specific sub-task as part
            of the broader Module responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            build is a distinct method because it encapsulates a specific behavioral concern that must be
            independently callable and potentially overridable by subclasses of Module without affecting
            other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the build operation on Module instances.

        Separation:
            - Other Module methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch Module implicitly invoke this method

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
        return cast("Module", cls.from_parent(parent, path=Path(file_path)))

    def get_path(self) -> Path:
        """
        Perform the get_path operation within the Module boundary, handling its specific sub-task as
        part of the broader Mod.

        Responsibility:
            Performs the get_path operation within the Module boundary, handling its specific sub-task as
            part of the broader Module responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            get_path is a distinct method because it encapsulates a specific behavioral concern that must
            be independently callable and potentially overridable by subclasses of Module without affecting
            other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the get_path operation on Module instances.

        Separation:
            - Other Module methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch Module implicitly invoke this method

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
        return getattr(self, "path", Path(self.fspath))


def fail(reason: str, *, pytrace: bool = True) -> NoReturn:
    """
    Perform the `fail` operation within its module boundary, implementing a focused helper
    function that is consumed by .

    Responsibility:
        Performs the `fail` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `fail` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the fail operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke fail for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The fail function returns consistent results for equivalent inputs.

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
    __tracebackhide__ = True
    pytest.fail(reason, pytrace=pytrace)


def is_set(obj: object) -> bool:
    """
    Perform the `is_set` operation within its module boundary, implementing a focused helper
    function that is consumed b.

    Responsibility:
        Performs the `is_set` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `is_set` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the is_set operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke is_set for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The is_set function returns consistent results for equivalent inputs.

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
    return not isinstance(obj, NotSetType)


def is_testrun_success(exitstatus: int | pytest.ExitCode) -> bool:
    """
    Perform the `is_testrun_success` operation within its module boundary, implementing a focused
    helper function that i.

    Responsibility:
        Performs the `is_testrun_success` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `is_testrun_success` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the is_testrun_success operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke is_testrun_success for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The is_testrun_success function returns consistent results for equivalent inputs.

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
    return (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is pytest.ExitCode.OK


class _LegacyFixtureDefFactory(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: _LegacyFixtureDefFactory specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate _LegacyFixtureDefFactory for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

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

    def __call__(  # noqa: PLR0913, PLR0917  -- suppressed warning
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
        Perform the __call__ operation within the _LegacyFixtureDefFactory boundary, handling its
        specific sub-task as part .

        Responsibility:
            Performs the __call__ operation within the _LegacyFixtureDefFactory boundary, handling its
            specific sub-task as part of the broader _LegacyFixtureDefFactory responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            __call__ is a distinct method because it encapsulates a specific behavioral concern that must
            be independently callable and potentially overridable by subclasses of _LegacyFixtureDefFactory
            without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __call__ operation on _LegacyFixtureDefFactory instances.

        Separation:
            - Other _LegacyFixtureDefFactory methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch _LegacyFixtureDefFactory implicitly invoke this method

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
        ...


def build_fixture_def(  # noqa: PLR0913  -- suppressed warning
    request: FixtureRequest,
    *,
    baseid: str | None,
    argname: str,
    func: Callable[[], object],
    scope: _ScopeName | Scope | Callable[[str, Config], _ScopeName] | None,
    params: Sequence[object] | None,
) -> FixtureDef:
    """
    Perform the `build_fixture_def` operation within its module boundary, implementing a focused
    helper function that is.

    Responsibility:
        Performs the `build_fixture_def` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `build_fixture_def` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the build_fixture_def operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke build_fixture_def for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The build_fixture_def function returns consistent results for equivalent inputs.

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
    return legacy_fixture_def(request._fixturemanager, baseid, argname, func, scope, params)  # noqa: SLF001  -- suppressed warning


Expression = _mark_expression.Expression
ParseError = getattr(_mark_expression, "ParseError", ValueError)
prepareconfig = _prepareconfig


def make_mark(
    name: str,
    args: tuple[object, ...] = (),
    kwargs: dict[str, object] | None = None,
) -> Mark:
    """
    Perform the `make_mark` operation within its module boundary, implementing a focused helper
    function that is consume.

    Responsibility:
        Performs the `make_mark` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `make_mark` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the make_mark operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke make_mark for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The make_mark function returns consistent results for equivalent inputs.

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
    if kwargs is None:
        kwargs = {}
    return Mark(name, args=args, kwargs=kwargs, _ispytest=True)  # type: ignore[call-arg]  # pytest private API


def make_mark_decorator(mark: Mark) -> MarkDecorator:
    """
    Perform the `make_mark_decorator` operation within its module boundary, implementing a focused
    helper function that .

    Responsibility:
        Performs the `make_mark_decorator` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `make_mark_decorator` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the make_mark_decorator operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke make_mark_decorator for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The make_mark_decorator function returns consistent results for equivalent inputs.

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
    return MarkDecorator(mark, _ispytest=True)  # type: ignore[call-arg]  # pytest private API
