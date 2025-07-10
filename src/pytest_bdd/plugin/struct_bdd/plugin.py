import mimetypes
from contextlib import suppress
from functools import partial
from inspect import getmembers
from operator import contains
from pathlib import Path
from typing import ClassVar

import pytest

from pytest_bdd.compatibility.pytest import PYTEST7, Config, Module
from pytest_bdd.mimetype import Mimetype, struct_bdd_suffixes

from .model import StepPrototype
from .parser import StructBDDParser


class StructBDDPlugin:
    extension_to_mimetype: ClassVar = {
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
    ):
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
    def _get_mimetype(path: Path):
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
    ):
        with suppress(ValueError):
            return self._get_mimetype(path)
        return None

    @pytest.hookimpl
    def pytest_bdd_is_collectible(
        self,
        config: Config,  # noqa: ARG002 hookspec
        path: Path,
    ):
        with suppress(ValueError):
            self._get_mimetype(path)
            return True
        return None

    @staticmethod
    def _pytest_pycollect_makemodule():
        outcome = yield
        res = outcome.get_result()
        if isinstance(res, Module):
            for member_name, member in getmembers(res.module):
                # TODO check startwith test_ usage to be aligned with pytest options itself
                if isinstance(member, StepPrototype) and member_name.startswith("test_"):
                    setattr(res.module, member_name, member.as_test(res.module.__file__))

    if PYTEST7:

        @pytest.hookimpl(hookwrapper=True)
        def pytest_pycollect_makemodule(
            self,
            parent,  # noqa: ARG002 hookspec
            module_path,  # noqa: ARG002 hookspec
        ):
            yield from self._pytest_pycollect_makemodule()

    else:

        @pytest.hookimpl(hookwrapper=True)
        def pytest_pycollect_makemodule(  # type:ignore[misc]
            self,
            path,  # noqa: ARG002 hookspec
            parent,  # noqa: ARG002 hookspec
        ):
            yield from self._pytest_pycollect_makemodule()
