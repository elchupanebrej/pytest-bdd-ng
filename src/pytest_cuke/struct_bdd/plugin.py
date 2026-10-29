from __future__ import annotations

from collections.abc import Generator
from functools import partial
from inspect import getmembers
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from pytest_cuke.compatibility.pytest import PYTEST7, Module
from pytest_cuke.mimetypes import STRUCT_BDD_FORMATS, struct_bdd_format_for_mimetype, struct_bdd_format_for_path
from pytest_cuke.struct_bdd.model import StepPrototype
from pytest_cuke.struct_bdd.parser import StructBDDParser

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_cuke.compatibility.pytest import Config


class StructBDDPlugin:
    extension_to_mimetype: ClassVar[dict[str, str]] = {
        format_.suffix: format_.mimetype.value for format_ in STRUCT_BDD_FORMATS
    }

    def pytest_cuke_get_parser(self, config: Config, mimetype: str) -> Any:
        format_ = struct_bdd_format_for_mimetype(mimetype)
        if format_ is None:
            return None
        return partial(StructBDDParser, kind=format_.kind)

    def pytest_cuke_get_mimetype(self, config: Config, path: Path) -> str | None:
        format_ = struct_bdd_format_for_path(path)
        return format_.mimetype.value if format_ is not None else None

    def pytest_cuke_is_collectible(self, config: Config, path: Path) -> bool | None:
        return True if struct_bdd_format_for_path(path) is not None else None

    def _pytest_pycollect_makemodule(self) -> Generator[Any, Any, Any]:
        outcome = yield
        res = outcome.get_result()
        if isinstance(res, Module):
            for member_name, member in getmembers(res.module):
                if isinstance(member, StepPrototype) and member_name.startswith("test_"):
                    setattr(res.module, member_name, member.as_test(res.module.__file__))


def _pytest7_pycollect_makemodule(self: StructBDDPlugin, parent: Any, module_path: Any) -> Generator[Any, Any, Any]:
    yield from self._pytest_pycollect_makemodule()


def _pytest_legacy_pycollect_makemodule(self: StructBDDPlugin, path: Any, parent: Any) -> Generator[Any, Any, Any]:
    yield from self._pytest_pycollect_makemodule()


_pytest_pycollect_makemodule_hook: Any
_pytest_pycollect_makemodule_hook = _pytest7_pycollect_makemodule if PYTEST7 else _pytest_legacy_pycollect_makemodule

_pytest_pycollect_makemodule_hook_name = "pytest_pycollect_makemodule"
_decorated_hook = pytest.hookimpl(hookwrapper=True)(_pytest_pycollect_makemodule_hook)
setattr(StructBDDPlugin, _pytest_pycollect_makemodule_hook_name, _decorated_hook)
