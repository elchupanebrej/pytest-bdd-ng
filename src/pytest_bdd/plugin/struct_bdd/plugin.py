"""
Provide plugin helpers.

Responsibility:
    Provide plugin helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.plugin` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - _HookCallOutcome: owns nested behavior below this boundary
    - _ParserFactory: owns nested behavior below this boundary
    - StructBDDPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py: imports or references `plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `plugin`

State and side effects:
    mutates extension_to_mimetype, suffixes, last, ext_to_mime, mimetype_string; depends on mimetypes,
    collections.abc.Generator, collections.abc.Mapping, contextlib.suppress, functools.partial.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.plugin` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises ValueError; callers must treat these as boundary failures.

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

import mimetypes
from collections.abc import Generator, Mapping
from contextlib import suppress
from functools import partial
from inspect import getmembers
from operator import contains
from pathlib import Path
from typing import ClassVar, Protocol

import pytest

from pytest_bdd.compatibility.pytest import Config, Module
from pytest_bdd.mimetype import Mimetype, struct_bdd_suffixes

from .model import StepPrototype
from .parser import StructBDDParser


class _HookCallOutcome(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.plugin._HookCallOutcome` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.plugin._HookCallOutcome` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_result: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `_HookCallOutcome`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.plugin._HookCallOutcome` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def get_result(self) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.plugin._HookCallOutcome.get_result` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.plugin._HookCallOutcome.get_result`
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
            - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `get_result`
            - src/pytest_bdd/plugin/scenario_reporter/plugin.py: imports or references `get_result`
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `get_result`

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


class _ParserFactory(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.plugin._ParserFactory` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.plugin._ParserFactory` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `_ParserFactory`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.plugin._ParserFactory` keeps its documented import path, ownership boundary, and
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
        #arch-eval:locational_stability=3
    """

    def __call__(self, *, loader: object | None = None) -> StructBDDParser:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.plugin._ParserFactory.__call__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.plugin._ParserFactory.__call__`
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
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `__call__`

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
            #arch-eval:locational_stability=3
        """
        ...


class StructBDDPlugin:
    """
    Represent struct bddplugin state.

    Yields:
        Generated values.

    Raises:
        ValueError: If the operation cannot be completed.

    Responsibility:
        Represent struct bddplugin state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_get_parser: owns nested behavior below this boundary
        - _get_mimetype: owns nested behavior below this boundary
        - pytest_bdd_get_mimetype: owns nested behavior below this boundary
        - pytest_bdd_is_collectible: owns nested behavior below this boundary
        - _pytest_pycollect_makemodule: owns nested behavior below this boundary
        - pytest_pycollect_makemodule: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `StructBDDPlugin`

    State and side effects:
        mutates extension_to_mimetype, suffixes, last, ext_to_mime, mimetype_string.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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

    extension_to_mimetype: ClassVar[Mapping[StructBDDParser.KIND, Mimetype]] = {
        StructBDDParser.KIND.YAML: Mimetype.struct_bdd_yaml,
        StructBDDParser.KIND.HOCON: Mimetype.struct_bdd_hocon,
        StructBDDParser.KIND.JSON5: Mimetype.struct_bdd_json5,
        StructBDDParser.KIND.JSON: Mimetype.struct_bdd_json,
        StructBDDParser.KIND.HJSON: Mimetype.struct_bdd_hjson,
        StructBDDParser.KIND.TOML: Mimetype.struct_bdd_toml,
    }

    @pytest.hookimpl
    def pytest_bdd_get_parser(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        config: Config,  # noqa: ARG002 hookspec
        mimetype: str,
    ) -> _ParserFactory | None:
        """
        Handle the pytest bdd get parser pytest hook.

        Args:
            config: Pytest config.
            mimetype: Mimetype string.

        Returns:
            Parser factory or None.

        Responsibility:
            Handle the pytest bdd get parser pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin.pytest_bdd_get_parser` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - suppress: collaborator call used by this boundary
            - partial: collaborator call used by this boundary
            - Mimetype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `pytest_bdd_get_parser`

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
        with suppress(KeyError, ValueError):
            return partial(  # pydantic v1 compatibility in pydantic v2
                StructBDDParser,
                kind={
                    Mimetype.struct_bdd_yaml: StructBDDParser.KIND.YAML,
                    Mimetype.struct_bdd_hocon: StructBDDParser.KIND.HOCON,
                    Mimetype.struct_bdd_json5: StructBDDParser.KIND.JSON5,
                    Mimetype.struct_bdd_json: StructBDDParser.KIND.JSON,
                    Mimetype.struct_bdd_hjson: StructBDDParser.KIND.HJSON,
                    Mimetype.struct_bdd_toml: StructBDDParser.KIND.TOML,
                }[Mimetype(mimetype)],
            )
        return None

    @staticmethod
    def _get_mimetype(path: Path) -> Mimetype:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin._get_mimetype` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin._get_mimetype` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - any: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - partial: collaborator call used by this boundary
            - lower: collaborator call used by this boundary
            - mimetypes.guess_type: collaborator call used by this boundary
            - Mimetype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `_get_mimetype`

        State and side effects:
            mutates suffixes, last, ext_to_mime, mimetype_string, _encoding.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin._get_mimetype` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
            #arch-eval:locational_stability=3
        """
        suffixes = path.suffixes
        if any(map(partial(contains, struct_bdd_suffixes), suffixes)):
            last = suffixes[-1].lower()
            ext_to_mime = {
                ".yaml": Mimetype.struct_bdd_yaml,
                ".yml": Mimetype.struct_bdd_yaml,
                ".hocon": Mimetype.struct_bdd_hocon,
                ".json5": Mimetype.struct_bdd_json5,
                ".json": Mimetype.struct_bdd_json,
                ".hjson": Mimetype.struct_bdd_hjson,
                ".toml": Mimetype.struct_bdd_toml,
                ".bdd": Mimetype.struct_bdd_yaml,
            }
            if last in ext_to_mime:
                return ext_to_mime[last]
        mimetype_string, _encoding = mimetypes.guess_type(path)
        if mimetype_string is None:
            raise ValueError
        mimetype = Mimetype(mimetype_string)
        if any(map(partial(contains, struct_bdd_suffixes), suffixes)):
            try:
                return {
                    Mimetype.yaml: Mimetype.struct_bdd_yaml,
                    Mimetype.hocon: Mimetype.struct_bdd_hocon,
                    Mimetype.json5: Mimetype.struct_bdd_json5,
                    Mimetype.json: Mimetype.struct_bdd_json,
                    Mimetype.hjson: Mimetype.struct_bdd_hjson,
                    Mimetype.toml: Mimetype.struct_bdd_toml,
                }[mimetype]
            except KeyError as e:
                raise ValueError from e
        raise ValueError

    @pytest.hookimpl
    def pytest_bdd_get_mimetype(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ) -> Mimetype | None:
        """
        Handle the pytest bdd get mimetype pytest hook.

        Args:
            config: Pytest config.
            path: File path.

        Returns:
            Mimetype or None.

        Responsibility:
            Handle the pytest bdd get mimetype pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin.pytest_bdd_get_mimetype` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - suppress: collaborator call used by this boundary
            - self._get_mimetype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `pytest_bdd_get_mimetype`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_mimetype`

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
        with suppress(ValueError):
            return self._get_mimetype(path)
        return None

    @pytest.hookimpl
    def pytest_bdd_is_collectible(
        self,
        config: Config,  # noqa: ARG002 hookspec
        path: Path,
    ) -> bool | None:
        """
        Check if path is collectible as struct BDD.

        Returns:
            True if collectible, None otherwise.

        Responsibility:
            Check if path is collectible as struct BDD. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin.pytest_bdd_is_collectible` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - suppress: collaborator call used by this boundary
            - self._get_mimetype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_is_collectible`
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `pytest_bdd_is_collectible`

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
        with suppress(ValueError):
            self._get_mimetype(path)
            return True
        return None

    @staticmethod
    def _pytest_pycollect_makemodule() -> Generator[None, _HookCallOutcome, None]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin._pytest_pycollect_makemodule` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin._pytest_pycollect_makemodule` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - outcome.get_result: collaborator call used by this boundary
            - getmembers: collaborator call used by this boundary
            - member_name.startswith: collaborator call used by this boundary
            - setattr: collaborator call used by this boundary
            - member.as_test: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `_pytest_pycollect_makemodule`
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `_pytest_pycollect_makemodule`

        State and side effects:
            mutates outcome, res.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin._pytest_pycollect_makemodule` keeps its documented
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
            #arch-eval:locational_stability=3
        """
        outcome = yield
        res = outcome.get_result()
        if isinstance(res, Module):
            for member_name, member in getmembers(res.module):  # type: ignore[attr-defined]  # pytest Module.module attribute
                # TODO: check startwith test_ usage to be aligned with pytest options itself
                if isinstance(member, StepPrototype) and member_name.startswith("test_"):
                    setattr(res.module, member_name, member.as_test(res.module.__file__))  # type: ignore[attr-defined]  # pytest Module.module attribute

    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(
        self,
        parent: object,  # noqa: ARG002 hookspec
        module_path: Path,  # noqa: ARG002 hookspec
    ) -> Generator[None, _HookCallOutcome, None]:
        """
        Handle the pytest pycollect makemodule pytest hook.

        Yields:
            Generated values.

        Responsibility:
            Handle the pytest pycollect makemodule pytest hook. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.plugin.StructBDDPlugin.pytest_pycollect_makemodule` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._pytest_pycollect_makemodule: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `pytest_pycollect_makemodule`

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
        yield from self._pytest_pycollect_makemodule()
