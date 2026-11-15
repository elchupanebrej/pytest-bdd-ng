from __future__ import annotations

import plistlib
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse
from uuid import uuid4

from pytest_cuke.batch_collection import get_batch_service
from pytest_cuke.compatibility.pytest import Item as PytestItem
from pytest_cuke.compatibility.pytest import Module as PytestModule
from pytest_cuke.compatibility.pytest import Package as PytestPackage
from pytest_cuke.feature_sources import FeatureSourceError, resolve_feature_sources
from pytest_cuke.scenario import FeaturePathType as PathType
from pytest_cuke.scenario import scenarios
from pytest_cuke.scenario_locator import FileScenarioLocator
from pytest_cuke.steps import StepDefinitionManager
from pytest_cuke.utils import convert_str_to_python_name
from pytest_cuke.webloc import read as webloc_read

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType

    from pytest_cuke.compatibility.pytest import Config


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


_LINK_SUFFIXES = frozenset({".url", ".desktop", ".webloc"})


def link_suffix(path: Path) -> str | None:
    """Return the normalized link-file suffix, if the path names one."""
    suffixes = path.suffixes
    if not suffixes:
        return None
    suffix = suffixes[-1].casefold()
    return suffix if suffix in _LINK_SUFFIXES else None


def _broken_link(path: Path, detail: str) -> FeatureSourceError:
    return FeatureSourceError(f"Broken feature link '{path}': {detail}.")


class FeatureFileModule(Module):
    def _getobj(self) -> ModuleType:
        self._prime_autoload_batch()
        path: Path = self.get_path()
        feature_pathlike: str | Path | None
        features_path_type: PathType
        base_dir: str | Path | None
        suffix = link_suffix(path)
        if suffix == ".url":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_url_file(path)
        elif suffix == ".desktop":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_desktop_file(path)
        elif suffix == ".webloc":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_weblock_file(path)
        else:
            feature_pathlike, features_path_type, base_dir = path, PathType.PATH, None
        return self._build_test_module(feature_pathlike, features_path_type, base_dir)

    def _prime_autoload_batch(self) -> None:
        config = self.config
        service = get_batch_service(config)
        if service is None or service.autoload_primed:
            return
        enabled = config.getoption("cuke_autoload")
        if enabled is None:
            enabled = config.getini("cuke_autoload")
        if not enabled:
            return

        feature_root = resolve_feature_sources(config).features_base_dir
        if not feature_root.is_dir():
            return

        rootpath = getattr(config, "rootpath", getattr(config, "rootdir", Path.cwd()))
        selected_roots = []
        for argument in getattr(config, "args", ()):
            argument_path = Path(str(argument).split("::", maxsplit=1)[0])
            if not argument_path.is_absolute():
                argument_path = Path(rootpath) / argument_path
            selected_roots.append(argument_path.resolve())

        def selected_for_collection(candidate: Path) -> bool:
            if not selected_roots:
                return True
            resolved = candidate.resolve()
            for selected_root in selected_roots:
                if resolved == selected_root:
                    return True
                try:
                    resolved.relative_to(selected_root)
                except ValueError:
                    continue
                return True
            return False

        def requests() -> list[Any]:
            candidate_paths: list[str | Path] = [
                candidate
                for candidate in feature_root.rglob("*")
                if candidate.is_file()
                and selected_for_collection(candidate)
                and config.hook.pytest_cuke_is_collectible(config=config, path=candidate)
            ]
            locator = FileScenarioLocator(feature_paths=candidate_paths, features_base_dir=feature_root)
            return locator.build_batch_requests(config)

        service.prime_autoload(requests())

    def _build_test_module(
        self, path: str | Path | None, features_path_type: PathType, base_dir: str | Path | None
    ) -> ModuleType:
        module_name = convert_str_to_python_name(f"{path}_{uuid4()}")

        module_spec = ModuleSpec(module_name, None)
        module = module_from_spec(module_spec)

        module.__dict__["test_scenarios"] = scenarios(
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

    @staticmethod
    def _read_link_section(path: Path, section: str) -> Any:
        config_parser = ConfigParser()
        try:
            config_parser.read(path)
        except (ConfigParserError, OSError) as error:
            raise _broken_link(path, f"cannot read link file: {error}") from error
        if not config_parser.has_section(section):
            raise _broken_link(path, f"missing [{section}] section")
        return config_parser[section]

    @staticmethod
    def _relative_link_base_dir(path: Path, raw_path: str | None, path_type: PathType) -> Path | None:
        if raw_path is None or path_type is PathType.URL:
            return None
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return None
        for parent in path.parents:
            if (parent / candidate).exists():
                return parent
        return None

    @classmethod
    def get_feature_pathlike_from_url_file(cls, path: Path) -> tuple[str | None, PathType, str | None]:
        config_data = cls._read_link_section(path, "InternetShortcut")
        working_dir = config_data.get("WorkingDirectory", None)
        url = config_data.get("URL", None)
        if not url:
            raise _broken_link(path, "missing URL in [InternetShortcut]")
        raw_path, path_type = cls.detect_uri_pathtype(url)
        return raw_path, path_type, working_dir

    @classmethod
    def get_feature_pathlike_from_desktop_file(cls, path: Path) -> tuple[str | None, PathType, Path | str | None]:
        config_data = cls._read_link_section(path, "Desktop Entry")
        url = config_data.get("URL") if config_data.get("Type") == "Link" else None
        if not url:
            raise _broken_link(path, "missing URL for a [Desktop Entry] Type=Link")
        raw_path, path_type = cls.detect_uri_pathtype(url)
        return raw_path, path_type, cls._relative_link_base_dir(path, raw_path, path_type)

    @classmethod
    def get_feature_pathlike_from_weblock_file(cls, path: Path) -> tuple[str | None, PathType, Path | str | None]:
        try:
            url = webloc_read(str(path))
        except (OSError, ValueError, plistlib.InvalidFileException) as error:
            raise _broken_link(path, f"cannot read property list: {error}") from error
        if not url:
            raise _broken_link(path, "missing URL")
        raw_path, path_type = cls.detect_uri_pathtype(url)
        return raw_path, path_type, cls._relative_link_base_dir(path, raw_path, path_type)


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

    def runtest(self) -> None:
        """Execute scenario test."""
        pass

    def reportinfo(self) -> tuple[Any, int | None, str]:
        path = getattr(self, "path", getattr(self, "fspath", None))
        line = getattr(self.scenario, "line", None) if self.scenario else None
        return path, line, f"Scenario: {self.name}"
