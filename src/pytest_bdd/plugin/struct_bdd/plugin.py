"""Provide plugin helpers."""

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
    def get_result(self) -> object: ...


class _ParserFactory(Protocol):
    def __call__(self, *, loader: object | None = None) -> StructBDDParser: ...


class StructBDDPlugin:
    """
    Represent struct bddplugin state.

    Yields:
        Generated values.

    Raises:
        ValueError: If the operation cannot be completed.

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
    def pytest_bdd_get_parser(
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

        """
        with suppress(KeyError, ValueError):
            return partial(  # type:ignore[call-arg]
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
        mimetype_string, _encoding = mimetypes.guess_type(path)
        if mimetype_string is None:
            raise ValueError
        mimetype = Mimetype(mimetype_string)
        if any(map(partial(contains, struct_bdd_suffixes), path.suffixes)):
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

        """
        with suppress(ValueError):
            self._get_mimetype(path)
            return True
        return None

    @staticmethod
    def _pytest_pycollect_makemodule() -> Generator[None, _HookCallOutcome, None]:
        outcome = yield
        res = outcome.get_result()
        if isinstance(res, Module):
            for member_name, member in getmembers(res.module):
                # TODO: check startwith test_ usage to be aligned with pytest options itself
                if isinstance(member, StepPrototype) and member_name.startswith("test_"):
                    setattr(res.module, member_name, member.as_test(res.module.__file__))

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

        """
        yield from self._pytest_pycollect_makemodule()
