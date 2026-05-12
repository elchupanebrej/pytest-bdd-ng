"""Provide collector helpers."""

from collections.abc import Iterable
from configparser import ConfigParser
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from types import ModuleType
from typing import cast
from urllib.parse import urlparse
from uuid import uuid4

from _pytest.nodes import Collector

from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.compatibility.pytest import Item
from pytest_bdd.compatibility.pytest import Module as PytestModule
from pytest_bdd.scenario import FeaturePathType as PathType
from pytest_bdd.scenario import scenarios
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.other import format_as_python_identifier
from pytest_bdd.util.webloc import read as webloc_read


class Module(PytestModule):
    """Represent module state."""

    def collect(self) -> Iterable[Item | Collector]:
        """
        Collect tests from this module.

        Returns:
            Iterable of pytest items and collectors.

        """
        StepDefinitionManager.Registry.inject_registry_fixture_and_register_steps(self.obj)
        return cast("Iterable[Item | Collector]", super().collect())


class FeatureFileModule(Module):
    """Represent feature file module state."""

    def collect(self) -> Iterable[Item | Collector]:
        """
        Collect tests, flushing the batch parser if pending.

        Returns:
            Iterable of pytest items and collectors.

        """
        batch_parser = FeatureBatchParser.find_in_stash(self.config.stash).value_or(None)
        if batch_parser is not None and batch_parser.has_pending():
            batch_parser.flush()
        return super().collect()

    def _getobj(self) -> ModuleType:
        path: Path = self.get_path()
        feature_pathlike: str | Path | None
        features_path_type: PathType
        base_dir: str | Path | None
        if path.suffixes[-1] == ".url":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_url_file(path)
        elif path.suffixes[-1] == ".desktop":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_desktop_file(path)
        elif path.suffixes[-1] == ".webloc":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_weblock_file(path)
        else:
            feature_pathlike, features_path_type, base_dir = path, PathType.PATH, None
        return self._build_test_module(feature_pathlike, features_path_type, base_dir)

    def _build_test_module(
        self,
        path: Path | str | None,
        features_path_type: PathType,
        base_dir: Path | str | None,
    ) -> ModuleType:
        module_name = format_as_python_identifier(f"{path}_{uuid4()}")

        module_spec = ModuleSpec(module_name, None)
        module = cast("ModuleType", module_from_spec(module_spec))

        module.test_scenarios = scenarios(  # type:ignore[attr-defined]
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
        """
        Detect URI path type from a URL string.

        Args:
            path: URL string to parse.

        Returns:
            Tuple of (parsed_path, path_type).

        """
        try:
            parsed_url = urlparse(path)
        except Exception:  # noqa: BLE001 intentional
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
        """
        Get feature path from a .url file.

        Args:
            path: Path to the .url file.

        Returns:
            Tuple of (feature_path, path_type, working_dir).

        """
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["InternetShortcut"]
        working_dir = config_data.get("WorkingDirectory", None)
        url = config_data.get("URL", None)
        return *cls.detect_uri_pathtype(url), working_dir

    @classmethod
    def get_feature_pathlike_from_desktop_file(cls, path: Path) -> tuple[str | None, PathType, None]:
        """
        Get feature path from a .desktop file.

        Args:
            path: Path to the .desktop file.

        Returns:
            Tuple of (feature_path, path_type, None).

        """
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["Desktop Entry"]
        return *cls.detect_uri_pathtype(config_data["URL"] if config_data["Type"] == "Link" else None), None

    @classmethod
    def get_feature_pathlike_from_weblock_file(cls, path: Path) -> tuple[str | None, PathType, None]:
        """
        Get feature path from a .webloc file.

        Args:
            path: Path to the .webloc file.

        Returns:
            Tuple of (feature_path, path_type, None).

        """
        return *cls.detect_uri_pathtype(cast("str", webloc_read(str(path)))), None
