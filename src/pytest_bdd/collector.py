from __future__ import annotations

from configparser import ConfigParser
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse
from uuid import uuid4

from pytest_bdd.compatibility.pytest import Item as PytestItem
from pytest_bdd.compatibility.pytest import Module as PytestModule
from pytest_bdd.compatibility.pytest import Package as PytestPackage
from pytest_bdd.scenario import FeaturePathType as PathType
from pytest_bdd.scenario import scenarios
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.utils import convert_str_to_python_name
from pytest_bdd.webloc import read as webloc_read

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_bdd.compatibility.pytest import Config


class Module(PytestModule):
    def collect(self) -> Iterable[Any]:
        StepDefinitionManager.Registry.inject_registry_fixture(self.obj)
        return super().collect()


ModuleCollector = Module


class PackageCollector(PytestPackage):
    """Pytest package collector that registers steps and injects registry fixtures at package level."""

    def collect(self) -> Iterable[Any]:
        if hasattr(self, "obj") and self.obj is not None:
            StepDefinitionManager.Registry.inject_registry_fixture(self.obj)
        return super().collect()


class FeatureFileModule(Module):
    def _getobj(self):
        path: Path = self.get_path()
        if path.suffixes and path.suffixes[-1] == ".url":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_url_file(path)
        elif path.suffixes and path.suffixes[-1] == ".desktop":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_desktop_file(path)
        elif path.suffixes and path.suffixes[-1] == ".webloc":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_weblock_file(path)
        else:
            feature_pathlike, features_path_type, base_dir = path, PathType.PATH, None
        return self._build_test_module(feature_pathlike, features_path_type, base_dir)

    def _build_test_module(self, path: Path | None, features_path_type: PathType, base_dir: Path | None):
        module_name = convert_str_to_python_name(f"{path}_{uuid4()}")

        module_spec = ModuleSpec(module_name, None)
        module = module_from_spec(module_spec)

        module.test_scenarios = scenarios(  # type: ignore[attr-defined]
            *((path,) if path is not None else []),
            filter_=None,
            return_test_decorator=False,
            parser_type=getattr(self, "parser_type", None),
            features_base_dir=base_dir,
            features_path_type=features_path_type,
        )

        return module

    @staticmethod
    def detect_uri_pathtype(path: str | None) -> tuple[str | None, PathType]:
        if path is None:
            return None, PathType.UNDEFINED
        try:
            parsed_url = urlparse(path)
        except Exception:
            features_path_type = PathType.UNDEFINED
        else:
            if parsed_url.scheme == "file":
                features_path_type = PathType.PATH
                path = parsed_url.path
            elif parsed_url.scheme:
                features_path_type = PathType.URL
            else:
                features_path_type = PathType.UNDEFINED
        return path, features_path_type

    @classmethod
    def get_feature_pathlike_from_url_file(cls, path: Path) -> tuple[str | None, PathType, str | None]:
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["InternetShortcut"]
        working_dir = config_data.get("WorkingDirectory", None)
        url = config_data.get("URL", None)
        raw_path, path_type = cls.detect_uri_pathtype(url)
        return raw_path, path_type, working_dir

    @classmethod
    def get_feature_pathlike_from_desktop_file(cls, path: Path) -> tuple[str | None, PathType, Path | str | None]:
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["Desktop Entry"]
        url = config_data["URL"] if config_data.get("Type") == "Link" else None
        raw_path, path_type = cls.detect_uri_pathtype(url)
        base_dir = None
        if raw_path is not None and path_type is not PathType.URL:
            p = Path(raw_path)
            if not p.is_absolute():
                for parent in path.parents:
                    if (parent / p).exists():
                        base_dir = parent
                        break
        return raw_path, path_type, base_dir

    @classmethod
    def get_feature_pathlike_from_weblock_file(cls, path: Path) -> tuple[str | None, PathType, Path | str | None]:
        raw_path, path_type = cls.detect_uri_pathtype(cast("str", webloc_read(str(path))))
        base_dir = None
        if raw_path is not None and path_type is not PathType.URL:
            p = Path(raw_path)
            if not p.is_absolute():
                for parent in path.parents:
                    if (parent / p).exists():
                        base_dir = parent
                        break
        return raw_path, path_type, base_dir


FeatureFileCollector = FeatureFileModule


class ScenarioItem(PytestItem):
    """Pytest Item representing an executable BDD scenario test item."""

    def __init__(
        self,
        name: str,
        parent: Any = None,
        config: Config | None = None,
        session: Any = None,
        nodeid: str | None = None,
        feature: Any = None,
        scenario: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name, parent=parent, config=config, session=session, nodeid=nodeid, **kwargs)
        self.feature = feature
        self.scenario = scenario

    @classmethod
    def from_parent(
        cls,
        parent: Any,
        *,
        name: str,
        feature: Any = None,
        scenario: Any = None,
        **kwargs: Any,
    ) -> ScenarioItem:
        return super().from_parent(
            parent=parent,
            name=name,
            feature=feature,
            scenario=scenario,
            **kwargs,
        )

    def runtest(self) -> None:
        """Execute scenario test."""
        pass

    def reportinfo(self) -> tuple[Any, int | None, str]:
        path = getattr(self, "path", getattr(self, "fspath", None))
        line = getattr(self.scenario, "line", None) if self.scenario else None
        return path, line, f"Scenario: {self.name}"
