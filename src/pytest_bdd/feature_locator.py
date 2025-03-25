from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from inspect import signature
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Optional, Union, cast

from pathvalidate import is_valid_filepath
from typing_extensions import TypedDict

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config, Mark
from pytest_bdd.const import FeatureBaseLoad
from pytest_bdd.model import Feature
from pytest_bdd.scenario import Args, FeaturePathType, scenarios
from pytest_bdd.scenario_locator import FileScenarioLocator, ScenarioLocatorFilterT, UrlScenarioLocator
from pytest_bdd.util.other import StringRepresentable
from pytest_bdd.util.url import is_url_parsable


def add_options(parser):
    parser.addini(FeatureBaseLoad.Ini.DIR_OPTION.value, "Base features directory.")
    parser.addini(FeatureBaseLoad.Ini.URL_OPTION.value, "Base features url.")


class MarkArguments(TypedDict):
    feature_paths: list[Union[Path, str]]  # List of paths to features
    filter_: Optional[Callable[[Config, Feature, Any], tuple[Feature, Any]]]  # Callable or string filter
    return_test_decorator: bool
    encoding: str
    features_base_dir: Optional[Union[Path, str]]
    features_base_url: Optional[str]
    features_path_type: Optional[Union[FeaturePathType, str]]  # Enum or string
    features_mimetype: Optional[str]
    parser_type: Optional[type[ParserProtocol]]
    parse_args: Optional[Args]
    locators: Iterable[Any]  # Iterable for locators


@dataclass
class ScenarioLocatorBuilder:
    """
    A dataclass to encapsulate the logic of building scenario locators based on provided
    marks and configuration.
    """

    marks: Iterable[Mark]
    config: Any

    def build_locators(self) -> Iterable[Any]:
        """
        Build scenario locators for all provided marks.
        """
        locators_iterables = []
        for mark in self.marks:
            mark_arguments: MarkArguments = self._get_mark_arguments(mark)

            locators_iterables.append(mark_arguments["locators"])
            features_base_dir = self._resolve_features_base_dir(mark)
            features_base_url = self._resolve_features_base_url(mark)
            features_path_type = self._resolve_features_path_type(mark_arguments)
            filter_ = self._build_scenario_filter(mark_arguments.get("filter_"))

            # Add file-based locators
            file_locator = self._create_file_locator(mark_arguments, filter_, features_base_dir, features_path_type)
            if file_locator:
                locators_iterables.append([file_locator])

            # Add URL-based locators
            url_locator = self._create_url_locator(mark_arguments, filter_, features_base_url, features_path_type)
            if url_locator:
                locators_iterables.append([url_locator])

        return chain(*locators_iterables)

    @staticmethod
    def _get_mark_arguments(mark: Mark) -> MarkArguments:
        """
        Retrieve and bind the arguments from the mark to their default values.
        """
        raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
        raw_mark_arguments.apply_defaults()
        return MarkArguments(**cast(MarkArguments, raw_mark_arguments.arguments))

    def _resolve_features_base_dir(self, mark: Mark) -> Any:
        """
        Resolve the base directory for the features from the mark or config.
        """
        features_base_dir = mark.kwargs.get("features_base_dir")
        if features_base_dir is None:
            try:
                # TODO: check if possible to move usage higher
                features_base_dir = self.config.getini(FeatureBaseLoad.Ini.DIR_OPTION.value) or None
            except (ValueError, KeyError):
                features_base_dir = self.config.rootpath
        if callable(features_base_dir):
            features_base_dir = features_base_dir(self.config)
        return features_base_dir

    def _resolve_features_base_url(self, mark: Any) -> Any:
        """
        Resolve the base URL for the features from the mark or config.
        """
        features_base_url = mark.kwargs.get("features_base_url")
        if features_base_url is None:
            with suppress(ValueError, KeyError):
                features_base_url = self.config.getini(FeatureBaseLoad.Ini.URL_OPTION.value) or None
        if callable(features_base_url):
            features_base_url = features_base_url(self.config)
        return features_base_url

    @staticmethod
    def _resolve_features_path_type(mark_arguments: MarkArguments) -> Any:
        """
        Resolve the type of feature paths (PATH, URL, or UNDEFINED).
        """
        features_path_type = mark_arguments.get("features_path_type")
        if features_path_type is None:
            return FeaturePathType.UNDEFINED
        elif isinstance(features_path_type, str):
            return FeaturePathType(features_path_type)
        elif isinstance(features_path_type, FeaturePathType):
            return features_path_type
        else:
            raise ValueError("Unknown feature path type")

    @staticmethod
    def _create_file_locator(
        mark_arguments: MarkArguments,
        filter_: Optional[ScenarioLocatorFilterT],
        features_base_dir: Any,
        features_path_type: Any,
    ) -> Any:
        """
        Create a FileScenarioLocator instance if applicable.
        """
        feature_paths = list(mark_arguments.get("feature_paths", []) or [])
        if features_path_type is FeaturePathType.PATH:
            file_locator_feature_paths = feature_paths
        elif features_path_type is FeaturePathType.UNDEFINED:
            file_locator_feature_paths = [p for p in feature_paths if is_valid_filepath(Path(p), platform="auto")]
        else:
            file_locator_feature_paths = []

        if not file_locator_feature_paths:
            return None

        return FileScenarioLocator(  # type: ignore[call-arg]
            feature_paths=file_locator_feature_paths,
            filter_=filter_,
            encoding=mark_arguments.get("encoding"),
            features_base_dir=features_base_dir,
            mimetype=mark_arguments.get("features_mimetype"),
            parser_type=mark_arguments.get("parser_type"),
            parse_args=mark_arguments.get("parse_args"),
        )

    @staticmethod
    def _create_url_locator(
        mark_arguments: MarkArguments,
        filter_: Optional[ScenarioLocatorFilterT],
        features_base_url: Any,
        features_path_type: Any,
    ) -> Any:
        """
        Create a UrlScenarioLocator instance if applicable.
        """
        feature_paths = list(mark_arguments.get("feature_paths", []) or [])

        if features_path_type is FeaturePathType.URL:
            url_locator_feature_paths = feature_paths
        elif features_path_type is FeaturePathType.UNDEFINED:
            url_locator_feature_paths = [p for p in feature_paths if is_url_parsable(p)]
        else:
            url_locator_feature_paths = []

        if not url_locator_feature_paths:
            return None

        return UrlScenarioLocator(  # type: ignore[call-arg]
            url_paths=url_locator_feature_paths,
            filter_=filter_,
            encoding=mark_arguments.get("encoding"),
            features_base_url=features_base_url,
            mimetype=mark_arguments.get("features_mimetype"),
            parser_type=mark_arguments.get("parser_type"),
            parse_args=mark_arguments.get("parse_args"),
        )

    @staticmethod
    def _build_scenario_filter(
        filter_: Optional[Union[ScenarioLocatorFilterT, str, StringRepresentable]],
    ) -> Optional[ScenarioLocatorFilterT]:
        """
        Build and return a scenario filter function.
        """
        if callable(filter_):
            return filter_

        if filter_ is None:
            return None

        if not isinstance(filter_, str):
            filter_ = str(filter_)

        def updated_filter(config, feature, scenario):
            return scenario.name == filter_

        return updated_filter
