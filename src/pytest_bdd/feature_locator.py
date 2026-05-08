"""Provide feature locator helpers."""

from collections.abc import Callable, Iterable
from contextlib import suppress
from inspect import signature
from pathlib import Path
from typing import cast

from attrs import define
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    GherkinDocument,
    Pickle,  # type:ignore[import-untyped]
)
from pathvalidate import is_valid_filepath
from typing_extensions import TypedDict

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config, Mark, get_config_root_path
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.plugin.scenario_test_collector.const import FeatureBaseLoad
from pytest_bdd.scenario import Args, FeaturePathType, scenarios
from pytest_bdd.scenario_locator import FileScenarioLocator, ScenarioLocatorFilterT, UrlScenarioLocator
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import StringRepresentable
from pytest_bdd.util.url import is_url_parsable


class FeatureLocatorArgs(TypedDict):
    """Represent feature locator args state."""

    feature_paths: list[Path | str]  # List of paths to features
    filter_: ScenarioLocatorFilterT | str | StringRepresentable | None  # Callable or string filter
    return_test_decorator: bool | None
    encoding: str | None
    features_base_dir: Path | str | None
    features_base_url: str | None
    features_path_type: FeaturePathType | str | None  # Enum or string
    features_mimetype: Mimetype | str | None
    parser_type: type[ParserProtocol] | None
    parse_args: Args | None
    locators: Iterable[object] | None  # Iterable for locators


def enrich_feature_locator_args(mark: Mark) -> FeatureLocatorArgs:
    """
    Retrieve and bind the arguments from the mark to their default values.

    Args:
        mark: Pytest mark with feature arguments.

    Returns:
        Feature locator arguments dictionary.

    """
    raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    return cast("FeatureLocatorArgs", raw_mark_arguments.arguments)


@define(slots=False)
class ScenarioLocatorBuilder:
    """
    A dataclass to encapsulate the logic of building scenario locators based on provided.

    marks and configuration.
    """

    config: Config

    @property
    def default_features_base_dir(self) -> str:
        """Handle default features base dir."""
        with suppress(ValueError, KeyError):
            if bool(base_dir := self.config.getini(str(FeatureBaseLoad.Ini.DIR_OPTION))):
                return str(base_dir)
        return str(get_config_root_path(self.config))

    @property
    def default_features_base_url(self) -> str | None:
        """Handle default features base url."""
        with suppress(ValueError, KeyError):
            if bool(base_url := self.config.getini(str(FeatureBaseLoad.Ini.URL_OPTION))):
                return str(base_url)
        return None

    def build_for_pytest_mark(self, mark: Mark) -> Iterable[object]:
        """
        Build scenario locators for all provided marks.

        Yields:
            Scenario locators derived from the provided mark.

        """
        yield from self.build_for_feature_locator_args(enrich_feature_locator_args(mark))

    def build_for_feature_locator_args(self, feature_locator_args: FeatureLocatorArgs) -> Iterable[object]:
        """
        Build for feature locator args.

        Yields:
            Generated values.

        """
        yield from feature_locator_args.get("locators") or []
        features_base_dir = self.resolve_features_base_dir(feature_locator_args.get("features_base_dir"))
        features_base_url = self.resolve_features_base_url(feature_locator_args.get("features_base_url"))
        features_path_type = self.resolve_features_path_type(feature_locator_args.get("features_path_type"))
        filter_ = self.build_scenario_filter(feature_locator_args.get("filter_"))

        if file_locator := self._create_file_locator(
            feature_locator_args,
            filter_,
            features_base_dir,
            features_path_type,
        ):
            yield file_locator
        if url_locator := self._create_url_locator(
            feature_locator_args,
            filter_,
            features_base_url,
            features_path_type,
        ):
            yield url_locator

    def resolve_features_base_dir(self, features_base_dir: str | Path | Callable[[Config], str] | None) -> str:
        """
        Resolve the base directory for the features from the mark or config.

        Returns:
            Resolved features base directory path.

        """
        resolved_features_base_dir: str
        if features_base_dir is None:
            resolved_features_base_dir = self.default_features_base_dir
        elif callable(features_base_dir):
            resolved_features_base_dir = features_base_dir(self.config)
        else:
            resolved_features_base_dir = str(features_base_dir)
        return resolved_features_base_dir

    def resolve_features_base_url(self, features_base_url: str | Path | Callable[[Config], str] | None) -> str | None:
        """
        Resolve the base URL for the features from the mark or config.

        Returns:
            Resolved features base URL or None.

        """
        if features_base_url is None:
            features_base_url = self.default_features_base_url
        if callable(features_base_url):
            features_base_url = features_base_url(self.config)
        return None if features_base_url is None else str(features_base_url)

    @staticmethod
    def resolve_features_path_type(feature_path_type: FeaturePathType | str | None = None) -> FeaturePathType:
        """
        Resolve the type of feature paths (PATH, URL, or UNDEFINED).

        Returns:
            Resolved feature path type.

        Raises:
            ValueError: If the feature path type is unknown.

        """
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
        filter_: ScenarioLocatorFilterT | None,
        features_base_dir: str,
        features_path_type: FeaturePathType,
    ) -> FileScenarioLocator | None:
        """
        Create a FileScenarioLocator instance if applicable.

        Returns:
            FileScenarioLocator instance or None if not applicable.

        """
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
        filter_: ScenarioLocatorFilterT | None,
        features_base_url: str | None,
        features_path_type: FeaturePathType,
    ) -> UrlScenarioLocator | None:
        """
        Create a UrlScenarioLocator instance if applicable.

        Returns:
            UrlScenarioLocator instance or None if not applicable.

        """
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
        filter_: ScenarioLocatorFilterT | str | StringRepresentable | None,
    ) -> ScenarioLocatorFilterT | None:
        """
        Build and return a scenario filter function.

        Returns:
            Scenario filter function or None.

        """
        if callable(filter_):
            return filter_

        if filter_ is None:
            return None

        if not isinstance(filter_, str):
            filter_ = str(filter_)

        def updated_filter(
            config: Config | HasPytestStash,  # noqa: ARG001 typecheck
            gherkin_document: GherkinDocument,  # noqa: ARG001 typecheck
            pickle: Pickle,
        ) -> bool:
            return bool(filter_ == pickle.name)

        return updated_filter
