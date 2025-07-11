from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from inspect import signature
from pathlib import Path
from typing import Any, Callable, Optional, Union, cast

from cucumber_messages import Pickle
from pathvalidate import is_valid_filepath
from typing_extensions import TypedDict

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config, Mark
from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.plugin.scenario_test_collector.const import FeatureBaseLoad
from pytest_bdd.scenario import Args, FeaturePathType, scenarios
from pytest_bdd.scenario_locator import FileScenarioLocator, ScenarioLocatorFilterT, UrlScenarioLocator
from pytest_bdd.util.other import StringRepresentable
from pytest_bdd.util.url import is_url_parsable


class FeatureLocatorArgs(TypedDict):
    feature_paths: list[Union[Path, str]]  # List of paths to features
    filter_: Optional[Callable[[Config, Feature, Any], tuple[Feature, Any]]]  # Callable or string filter
    return_test_decorator: Optional[bool]
    encoding: Optional[str]
    features_base_dir: Optional[Union[Path, str]]
    features_base_url: Optional[str]
    features_path_type: Optional[Union[FeaturePathType, str]]  # Enum or string
    features_mimetype: Optional[str]
    parser_type: Optional[type[ParserProtocol]]
    parse_args: Optional[Args]
    locators: Optional[Iterable[Any]]  # Iterable for locators


def enrich_feature_locator_args(mark: Mark) -> FeatureLocatorArgs:
    """Retrieve and bind the arguments from the mark to their default values."""
    raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    return FeatureLocatorArgs(**cast(FeatureLocatorArgs, raw_mark_arguments.arguments))


@dataclass
class ScenarioLocatorBuilder:
    """A dataclass to encapsulate the logic of building scenario locators based on provided
    marks and configuration.
    """

    config: Config

    @property
    def default_features_base_dir(self):
        with suppress(ValueError, KeyError):
            return self.config.getini(str(FeatureBaseLoad.Ini.DIR_OPTION)) or None
        return self.config.rootpath

    @property
    def default_features_base_url(self):
        with suppress(ValueError, KeyError):
            return self.config.getini(str(FeatureBaseLoad.Ini.URL_OPTION)) or None
        return None

    def build_for_pytest_mark(self, mark: Mark) -> Iterable[Any]:
        """Build scenario locators for all provided marks."""
        yield from self.build_for_feature_locator_args(enrich_feature_locator_args(mark))

    def build_for_feature_locator_args(self, feature_locator_args: FeatureLocatorArgs) -> Iterable[Any]:
        yield from feature_locator_args.get("locators") or []
        features_base_dir = self.resolve_features_base_dir(feature_locator_args.get("features_base_dir"))
        features_base_url = self.resolve_features_base_url(feature_locator_args.get("features_base_url"))
        features_path_type = self.resolve_features_path_type(feature_locator_args.get("features_path_type"))
        filter_ = self.build_scenario_filter(feature_locator_args.get("filter_"))

        if file_locator := self._create_file_locator(
            feature_locator_args, filter_, features_base_dir, features_path_type
        ):
            yield file_locator
        if url_locator := self._create_url_locator(
            feature_locator_args, filter_, features_base_url, features_path_type
        ):
            yield url_locator

    def resolve_features_base_dir(self, features_base_dir: Optional[Union[str, Path, Callable[[Config], str]]]) -> str:
        """Resolve the base directory for the features from the mark or config."""

        if features_base_dir is None:
            features_base_dir = self.default_features_base_dir
        if callable(features_base_dir):
            features_base_dir = features_base_dir(self.config)
        return features_base_dir

    def resolve_features_base_url(self, features_base_url: Optional[Union[str, Path, Callable[[Config], str]]]) -> Any:
        """Resolve the base URL for the features from the mark or config."""
        if features_base_url is None:
            features_base_url = self.default_features_base_url
        if callable(features_base_url):
            features_base_url = features_base_url(self.config)
        return features_base_url

    @staticmethod
    def resolve_features_path_type(feature_path_type: Optional[FeaturePathType] = None) -> Any:
        """Resolve the type of feature paths (PATH, URL, or UNDEFINED)."""
        if feature_path_type is None:
            return FeaturePathType.UNDEFINED
        if isinstance(feature_path_type, str):
            return FeaturePathType(feature_path_type)
        if isinstance(feature_path_type, FeaturePathType):
            return feature_path_type
        msg = "Unknown feature path type"
        raise ValueError(msg)

    @staticmethod
    def _create_file_locator(
        feature_locator_args: FeatureLocatorArgs,
        filter_: Optional[ScenarioLocatorFilterT],
        features_base_dir: Any,
        features_path_type: Any,
    ) -> Any:
        """Create a FileScenarioLocator instance if applicable."""
        feature_paths = list(feature_locator_args.get("feature_paths", []) or [])
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
            encoding=feature_locator_args.get("encoding"),
            features_base_dir=features_base_dir,
            mimetype=feature_locator_args.get("features_mimetype"),
            parser_type=feature_locator_args.get("parser_type"),
            parse_args=feature_locator_args.get("parse_args"),
        )

    @staticmethod
    def _create_url_locator(
        feature_locator_args: FeatureLocatorArgs,
        filter_: Optional[ScenarioLocatorFilterT],
        features_base_url: Any,
        features_path_type: Any,
    ) -> Any:
        """Create a UrlScenarioLocator instance if applicable."""
        feature_paths = list(feature_locator_args.get("feature_paths", []) or [])

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
            encoding=feature_locator_args.get("encoding"),
            features_base_url=features_base_url,
            mimetype=feature_locator_args.get("features_mimetype"),
            parser_type=feature_locator_args.get("parser_type"),
            parse_args=feature_locator_args.get("parse_args"),
        )

    @staticmethod
    def build_scenario_filter(
        filter_: Optional[Union[ScenarioLocatorFilterT, str, StringRepresentable]],
    ) -> Optional[ScenarioLocatorFilterT]:
        """Build and return a scenario filter function."""
        if callable(filter_):
            return filter_

        if filter_ is None:
            return None

        if not isinstance(filter_, str):
            filter_ = str(filter_)

        def updated_filter(
            config: Config,  # noqa: ARG001 typecheck
            feature: Feature,  # noqa: ARG001 typecheck
            scenario: Pickle,
        ) -> bool:
            return bool(filter_ == scenario.name)

        return updated_filter
