"""
Provide feature locator helpers.

Responsibility:
    Provide feature locator helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.feature_locator` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - FeatureLocatorArgs: owns nested behavior below this boundary
    - enrich_feature_locator_args: owns nested behavior below this boundary
    - ScenarioLocatorBuilder: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `feature_locator`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `feature_locator`

State and side effects:
    mutates features_base_url, resolved_features_base_dir, feature_paths, filter_, file_locator_feature_paths; depends
    on platform, collections.abc.Callable, collections.abc.Iterable, contextlib.suppress, inspect.signature.

Invariants:
    - `pytest_bdd.feature_locator` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Failure semantics:
    Raises or re-raises ValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

import platform
from collections.abc import Callable, Iterable
from contextlib import suppress
from inspect import signature
from pathlib import Path
from typing import cast

from attrs import define
from cucumber_messages import (  # upstream library missing type stubs
    GherkinDocument,
    Pickle,  # library has no type stubs
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
    """
    Represent feature locator args state.

    Responsibility:
        Represent feature locator args state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.feature_locator.FeatureLocatorArgs` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `FeatureLocatorArgs`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `FeatureLocatorArgs`

    State and side effects:
        mutates feature_paths, filter_, return_test_decorator, encoding, features_base_dir.

    Invariants:
        - `pytest_bdd.feature_locator.FeatureLocatorArgs` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

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

    Responsibility:
        Retrieve and bind the arguments from the mark to their default values. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.feature_locator.enrich_feature_locator_args` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - signature.bind: collaborator call used by this boundary
        - signature: collaborator call used by this boundary
        - raw_mark_arguments.apply_defaults: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `enrich_feature_locator_args`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `enrich_feature_locator_args`

    State and side effects:
        mutates raw_mark_arguments.

    Invariants:
        - `pytest_bdd.feature_locator.enrich_feature_locator_args` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    return cast("FeatureLocatorArgs", raw_mark_arguments.arguments)


@define(slots=False)
class ScenarioLocatorBuilder:
    """
    A dataclass to encapsulate the logic of building scenario locators based on provided.

    marks and configuration.

    Responsibility:
        A dataclass to encapsulate the logic of building scenario locators based on provided. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.feature_locator.ScenarioLocatorBuilder` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - default_features_base_dir: owns nested behavior below this boundary
        - default_features_base_url: owns nested behavior below this boundary
        - build_for_pytest_mark: owns nested behavior below this boundary
        - build_for_feature_locator_args: owns nested behavior below this boundary
        - resolve_features_base_dir: owns nested behavior below this boundary
        - resolve_features_base_url: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `ScenarioLocatorBuilder`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `ScenarioLocatorBuilder`

    State and side effects:
        mutates resolved_features_base_dir, features_base_url, file_locator_feature_paths, url_locator_feature_paths,
        filter_.

    Invariants:
        - `pytest_bdd.feature_locator.ScenarioLocatorBuilder` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    config: Config

    @property
    def default_features_base_dir(self) -> str:
        """
        Handle default features base dir.

        Responsibility:
            Handle default features base dir. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.default_features_base_dir` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - self.config.getoption: collaborator call used by this boundary
            - self.config.getini: collaborator call used by this boundary
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `default_features_base_dir`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `default_features_base_dir`

        State and side effects:
            mutates base_dir_cli, base_dir_ini.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.default_features_base_dir` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        with suppress(ValueError, KeyError):
            base_dir_cli = self.config.getoption(str(FeatureBaseLoad.Cli.DIR_OPTION))
            base_dir_ini = self.config.getini(str(FeatureBaseLoad.Ini.DIR_OPTION))
            if bool(base_dir := base_dir_cli or base_dir_ini):
                return str(base_dir)
        return "."

    @property
    def default_features_base_url(self) -> Maybe[str]:
        """
        Handle default features base url.

        Responsibility:
            Handle default features base url. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.default_features_base_url` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - self.config.getoption: collaborator call used by this boundary
            - self.config.getini: collaborator call used by this boundary
            - bool: collaborator call used by this boundary
            - Some: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `default_features_base_url`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `default_features_base_url`

        State and side effects:
            mutates base_url_cli, base_url_ini.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.default_features_base_url` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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

        Responsibility:
            Build scenario locators for all provided marks. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_for_pytest_mark` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.build_for_feature_locator_args: collaborator call used by this boundary
            - enrich_feature_locator_args: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `build_for_pytest_mark`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build_for_pytest_mark`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        yield from self.build_for_feature_locator_args(enrich_feature_locator_args(mark))

    def build_for_feature_locator_args(self, feature_locator_args: FeatureLocatorArgs) -> Iterable[object]:
        """
        Build for feature locator args.

        Yields:
            Generated values.

        Responsibility:
            Build for feature locator args. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_for_feature_locator_args` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - feature_locator_args.get: collaborator call used by this boundary
            - self.resolve_features_base_dir: collaborator call used by this boundary
            - self.resolve_features_base_url.value_or: collaborator call used by this boundary
            - self.resolve_features_base_url: collaborator call used by this boundary
            - self.resolve_features_path_type: collaborator call used by this boundary
            - self.build_scenario_filter.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `build_for_feature_locator_args`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `build_for_feature_locator_args`

        State and side effects:
            mutates features_base_dir, features_base_url, features_path_type, filter_.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_for_feature_locator_args` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Resolve the base directory for the features from the mark or config. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_base_dir` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - callable: collaborator call used by this boundary
            - features_base_dir: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - is_absolute: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `resolve_features_base_dir`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_features_base_dir`

        State and side effects:
            mutates resolved_features_base_dir.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_base_dir` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        return cast("Path", (self.config.rootpath / resolved_features_base_dir).resolve())

    def resolve_features_base_url(self, features_base_url: str | Path | Callable[[Config], str] | None) -> Maybe[str]:
        """
        Resolve the base URL for the features from the mark or config.

        Returns:
            Resolved features base URL or None.

        Responsibility:
            Resolve the base URL for the features from the mark or config. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_base_url` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.default_features_base_url.value_or: collaborator call used by this boundary
            - callable: collaborator call used by this boundary
            - features_base_url: collaborator call used by this boundary
            - Some: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `resolve_features_base_url`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `resolve_features_base_url`

        State and side effects:
            mutates features_base_url.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_base_url` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Resolve the type of feature paths (PATH, URL, or UNDEFINED). It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_path_type` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - FeaturePathType: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `resolve_features_path_type`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `resolve_features_path_type`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_path_type` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Create a FileScenarioLocator instance if applicable. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder._create_file_locator` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - feature_locator_args.get: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - is_valid_filepath: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - Some: collaborator call used by this boundary
            - FileScenarioLocator: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `_create_file_locator`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_create_file_locator`

        State and side effects:
            mutates file_locator_feature_paths, feature_paths.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder._create_file_locator` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Create a UrlScenarioLocator instance if applicable. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder._create_url_locator` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - feature_locator_args.get: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - is_url_parsable: collaborator call used by this boundary
            - platform.python_implementation: collaborator call used by this boundary
            - Some: collaborator call used by this boundary
            - locator_class: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `_create_url_locator`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_create_url_locator`

        State and side effects:
            mutates url_locator_feature_paths, locator_class, feature_paths.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder._create_url_locator` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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
            locator_class(  # pydantic v1 compatibility in pydantic v2
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

        Responsibility:
            Build and return a scenario filter function. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_scenario_filter` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - updated_filter: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `build_scenario_filter`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build_scenario_filter`

        State and side effects:
            mutates filter_.

        Invariants:
            - `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_scenario_filter` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_scenario_filter.updated_filter` owns documented
                method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
                this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.feature_locator.ScenarioLocatorBuilder.build_scenario_filter.updated_filter` because it
                keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - bool: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `updated_filter`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `updated_filter`

            State and side effects:
                keeps no local persistent state beyond call-local values.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=3
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=3
            """
            return bool(filter_ == pickle.name)

        return Some(updated_filter)
