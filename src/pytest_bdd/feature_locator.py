"""Provide feature locator helpers."""

import platform
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
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result
from typing_extensions import TypedDict

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config, Mark
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_collection import FeatureBaseLoad
from pytest_bdd.scenario import Args, FeaturePathType, scenarios
from pytest_bdd.scenario_locator import (
    FileScenarioLocator,
    PyPyUrlScenarioLocator,
    ScenarioLocatorFilterT,
    UrlScenarioLocator,
)
from pytest_bdd.types.failure_reasons import FeatureLocatorFailure
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import StringRepresentable
from pytest_bdd.util.url import is_url_parsable

FileLocatorResult = Result[FileScenarioLocator, FeatureLocatorFailure]


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
            base_dir_cli = self.config.getoption(str(FeatureBaseLoad.Cli.DIR_OPTION))
            base_dir_ini = self.config.getini(str(FeatureBaseLoad.Ini.DIR_OPTION))
            if bool(base_dir := base_dir_cli or base_dir_ini):
                return str(base_dir)
        return "."

    @property
    def default_features_base_url(self) -> Maybe[str]:
        """Handle default features base url."""
        with suppress(ValueError, KeyError):
            base_url_cli = self.config.getoption(str(FeatureBaseLoad.Cli.URL_OPTION))
            base_url_ini = self.config.getini(str(FeatureBaseLoad.Ini.URL_OPTION))
            if bool(base_url := base_url_cli or base_url_ini):
                return Some(str(base_url))
        return Nothing

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
        features_base_url = self.resolve_features_base_url(feature_locator_args.get("features_base_url")).value_or(None)
        features_path_type = self.resolve_features_path_type(feature_locator_args.get("features_path_type"))
        filter_ = self.build_scenario_filter(feature_locator_args.get("filter_")).value_or(None)

        if file_locator := self._create_file_locator(
            feature_locator_args,
            filter_,
            features_base_dir,
            features_path_type,
        ).value_or(None):
            yield file_locator
        if url_locator := self._create_url_locator(
            feature_locator_args,
            filter_,
            features_base_url,
            features_path_type,
        ).value_or(None):
            yield url_locator

    def resolve_features_base_dir(self, features_base_dir: str | Path | Callable[[Config], str] | None) -> Path:
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

        if (resolved_path := Path(resolved_features_base_dir)).is_absolute():
            return resolved_path

        return (self.config.rootpath / resolved_features_base_dir).resolve()

    def resolve_features_base_url(self, features_base_url: str | Path | Callable[[Config], str] | None) -> Maybe[str]:
        """
        Resolve the base URL for the features from the mark or config.

        Returns:
            Resolved features base URL or None.

        """
        if features_base_url is None:
            features_base_url = self.default_features_base_url.value_or(None)
        if callable(features_base_url):
            features_base_url = features_base_url(self.config)
        return Nothing if features_base_url is None else Some(str(features_base_url))

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
        features_base_dir: Path,
        features_path_type: FeaturePathType,
    ) -> Maybe[FileScenarioLocator]:
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
            return Nothing

        return Some(
            FileScenarioLocator(
                feature_paths=file_locator_feature_paths,
                filter_=filter_,
                features_base_dir=features_base_dir,
                encoding=feature_locator_args.get("encoding"),
                mimetype=feature_locator_args.get("features_mimetype"),
                parser_type=feature_locator_args.get("parser_type"),
                parse_args=feature_locator_args.get("parse_args"),
            ),
        )

    @staticmethod
    def _create_url_locator(
        feature_locator_args: FeatureLocatorArgs,
        filter_: ScenarioLocatorFilterT | None,
        features_base_url: str | None,
        features_path_type: FeaturePathType,
    ) -> Maybe[UrlScenarioLocator]:
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
            return Nothing

        if platform.python_implementation() == "PyPy":
            locator_class: type[UrlScenarioLocator] = PyPyUrlScenarioLocator
        else:
            locator_class = UrlScenarioLocator

        return Some(
            locator_class(  # type: ignore[call-arg]
                url_paths=url_locator_feature_paths,
                filter_=filter_,
                encoding=feature_locator_args.get("encoding"),
                features_base_url=features_base_url,
                mimetype=feature_locator_args.get("features_mimetype"),
                parser_type=feature_locator_args.get("parser_type"),
                parse_args=feature_locator_args.get("parse_args"),
            ),
        )

    @staticmethod
    def build_scenario_filter(
        filter_: ScenarioLocatorFilterT | str | StringRepresentable | None,
    ) -> Maybe[ScenarioLocatorFilterT]:
        """
        Build and return a scenario filter function.

        Returns:
            Scenario filter function or None.

        """
        if callable(filter_):
            return Some(filter_)

        if filter_ is None:
            return Nothing

        if not isinstance(filter_, str):
            filter_ = str(filter_)

        def updated_filter(
            config: Config | HasPytestStash,  # noqa: ARG001 typecheck
            gherkin_document: GherkinDocument,  # noqa: ARG001 typecheck
            pickle: Pickle,
        ) -> bool:
            return bool(filter_ == pickle.name)

        return Some(updated_filter)
