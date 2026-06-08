"""
Provide scenario helpers.

Responsibility:
    Provide scenario helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.scenario` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - ScenarioFunction: owns nested behavior below this boundary
    - Args: owns nested behavior below this boundary
    - get_python_name_generator: owns nested behavior below this boundary
    - FeaturePathType: owns nested behavior below this boundary
    - scenario: owns nested behavior below this boundary
    - scenario: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/__init__.py: imports or references `scenario`
    - src/pytest_bdd/collector.py: imports or references `scenario`
    - src/pytest_bdd/feature_locator.py: imports or references `scenario`
    - src/pytest_bdd/model/feature_binding.py: imports or references `scenario`
    - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `scenario`

State and side effects:
    mutates suffix, index, features_path_type, __name__, args; depends on collections.abc.Callable,
    collections.abc.Iterable, collections.abc.Iterator, enum.Enum, pathlib.Path.

Invariants:
    - `pytest_bdd.scenario` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

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
    #arch-eval:locational_stability=4
"""

from collections.abc import Callable, Iterable, Iterator
from enum import Enum
from pathlib import Path
from typing import Any, Literal, NamedTuple, Protocol, TypeAlias, cast, overload

import pytest
from returns.maybe import Nothing

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_collection import PYTEST_BDD_MARK, PYTEST_BDD_SCENARIOS_MARK
from pytest_bdd.util.other import format_as_simplified_python_identifier
from pytest_bdd.util.toolz_extra import compose


class ScenarioFunction(Protocol):
    """
    Represent scenario function state.

    Responsibility:
        Represent scenario function state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.ScenarioFunction` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `ScenarioFunction`
        - src/pytest_bdd/collector.py: imports or references `ScenarioFunction`
        - src/pytest_bdd/feature_locator.py: imports or references `ScenarioFunction`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `ScenarioFunction`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `ScenarioFunction`

    State and side effects:
        mutates __name__.

    Invariants:
        - `pytest_bdd.scenario.ScenarioFunction` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    __name__: str

    def __call__(self) -> object:
        """
        Handle call.

        Responsibility:
            Handle call. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.scenario.ScenarioFunction.__call__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/__init__.py: imports or references `__call__`
            - src/pytest_bdd/collector.py: imports or references `__call__`
            - src/pytest_bdd/feature_locator.py: imports or references `__call__`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `__call__`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `__call__`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...


class Args(NamedTuple):
    """
    Represent args state.

    Responsibility:
        Represent args state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.Args` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `Args`
        - src/pytest_bdd/collector.py: imports or references `Args`
        - src/pytest_bdd/feature_locator.py: imports or references `Args`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Args`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `Args`

    State and side effects:
        mutates args, kwargs.

    Invariants:
        - `pytest_bdd.scenario.Args` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    args: tuple[object, ...]
    kwargs: dict[str, object]


ScenarioDecorator: TypeAlias = Callable[[ScenarioFunction], ScenarioFunction]
ScenarioTest: TypeAlias = Callable[[], object]
ScenarioFilterT: TypeAlias = str | Callable[[Config, object, object], bool] | None


def get_python_name_generator(name: str) -> Iterator[str]:
    """
    Generate a sequence of suitable python names out of given arbitrary string name.

    Yields:
        Candidate Python test names.

    Responsibility:
        Generate a sequence of suitable python names out of given arbitrary string name. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.get_python_name_generator` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_name: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `get_python_name_generator`
        - src/pytest_bdd/collector.py: imports or references `get_python_name_generator`
        - src/pytest_bdd/feature_locator.py: imports or references `get_python_name_generator`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `get_python_name_generator`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `get_python_name_generator`

    State and side effects:
        mutates suffix, index, python_name, result.

    Invariants:
        - `pytest_bdd.scenario.get_python_name_generator` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    python_name = format_as_simplified_python_identifier(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.scenario.get_python_name_generator.get_name` owns documented
            function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.scenario.get_python_name_generator.get_name` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - join: collaborator call used by this boundary
            - filter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/__init__.py: imports or references `get_name`
            - src/pytest_bdd/collector.py: imports or references `get_name`
            - src/pytest_bdd/feature_locator.py: imports or references `get_name`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `get_name`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `get_name`

        State and side effects:
            mutates result.

        Invariants:
            - `pytest_bdd.scenario.get_python_name_generator.get_name` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        result = "_".join(filter(bool, ["test", python_name, suffix]))
        # Ensure pytest collection pattern (test_*) matches when name is bare "test"
        return result if result != "test" else "test_"

    while True:
        yield get_name()
        index += 1
        suffix = f"{index}"


class FeaturePathType(Enum):
    """
    Controls how non-absolute feature paths are resolved during loading.

    This enum determines whether relative paths are treated as filesystem
    paths or HTTP/HTTPS URLs when loading Gherkin feature files.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:4
    #arch-eval:score=why_not_split:4
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:5
    #arch-eval:score=module_location:5

    Args:
        value: The string value of the enum member. One of ``"path"``,
            ``"url"``, or ``"undefined"``.

    Attributes:
        PATH: Resolve relative paths against the filesystem. Paths are
            resolved relative to ``features_base_dir`` or the current
            working directory. This is the default behavior.
        URL: Treat relative paths as URLs. Features are fetched over
            HTTP/HTTPS relative to ``features_base_url``.
        UNDEFINED: Path resolution mode is not explicitly set. The
            system attempts to auto-detect based on whether
            ``features_base_dir`` or ``features_base_url`` is provided.

    Example:
        Using PATH (default)::

            @scenario("features/login.feature", "Successful login")
            def test_login():
                pass

        Using URL::

            @scenario(
                "https://example.com/features/login.feature",
                "Successful login",
                features_path_type=FeaturePathType.URL,
            )
            def test_login_remote():
                pass

    See Also:
        :func:`scenario`: Single scenario loader that uses this enum.
        :func:`scenarios`: Bulk scenario loader that uses this enum.

    Returns:
        A ``FeaturePathType`` enum member (``PATH``, ``URL``, or
        ``UNDEFINED``) representing the path resolution mode.

    Responsibility:
        Controls how non-absolute feature paths are resolved during loading. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.FeaturePathType` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `FeaturePathType`
        - src/pytest_bdd/collector.py: imports or references `FeaturePathType`
        - src/pytest_bdd/feature_locator.py: imports or references `FeaturePathType`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `FeaturePathType`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `FeaturePathType`

    State and side effects:
        mutates PATH, URL, UNDEFINED.

    Invariants:
        - `pytest_bdd.scenario.FeaturePathType` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4

    """

    PATH = "path"
    URL = "url"
    UNDEFINED = "undefined"


@overload
def scenario(
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
    *,
    return_test_decorator: Literal[True] = True,
) -> ScenarioDecorator:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.scenario.scenario` owns documented function behavior. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.scenario` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `scenario`
        - src/pytest_bdd/collector.py: imports or references `scenario`
        - src/pytest_bdd/feature_locator.py: imports or references `scenario`
        - src/pytest_bdd/model/feature_binding.py: imports or references `scenario`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `scenario`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """


@overload
def scenario(
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
    *,
    return_test_decorator: Literal[False],
) -> ScenarioTest:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.scenario.scenario` owns documented function behavior. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.scenario` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `scenario`
        - src/pytest_bdd/collector.py: imports or references `scenario`
        - src/pytest_bdd/feature_locator.py: imports or references `scenario`
        - src/pytest_bdd/model/feature_binding.py: imports or references `scenario`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `scenario`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """


def scenario(  # noqa: PLR0913, PLR0917
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
    *,
    return_test_decorator: bool = True,
) -> ScenarioDecorator | ScenarioTest:
    """
    Load and bind a single Gherkin scenario to a pytest test function.

    Supports file-based and URL-based feature loading, custom parsers,
    and MIME type detection. Returns either a decorator (default) or
    a generated test function depending on ``return_test_decorator``.

    When ``return_test_decorator=True`` (default), the result is a
    decorator that must be applied to a test function. When
    ``return_test_decorator=False``, a test function is generated
    directly without requiring a decorator.

    Feature files can be loaded from the filesystem or over HTTP/HTTPS
    by setting ``features_path_type`` to ``FeaturePathType.PATH`` or
    ``FeaturePathType.URL`` respectively. Custom parsers can be
    supplied via ``parser_type`` for non-standard feature file formats.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:5
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5

    Args:
        feature_name: Absolute or relative path to the feature file.
            If ``None``, scenarios are loaded from ``feature_paths``
            via the :func:`scenarios` bulk loader. Accepts ``Path``
            objects or strings.
        scenario_name: Exact scenario name to match from the feature
            file. If ``None``, all scenarios in the feature are bound.
        encoding: Feature file encoding. Defaults to ``"utf-8"``.
        features_base_dir: Base directory for resolving relative
            feature paths. Mutually exclusive with ``features_base_url``.
        features_base_url: Base URL for loading features over HTTP/HTTPS.
            Mutually exclusive with ``features_base_dir``.
        features_path_type: Controls how non-absolute paths are
            resolved. Use ``FeaturePathType.PATH`` (default) for
            filesystem paths or ``FeaturePathType.URL`` for HTTP URLs.
            Can also be passed as a string (``"path"`` or ``"url"``).
        features_mimetype: Override MIME type detection to select
            a specific parser. Useful for non-standard file extensions.
        parser_type: Custom parser class implementing ``ParserProtocol``.
            Allows loading feature files in custom formats.
        parse_args: Arguments passed to the parser during feature
            parsing. An ``Args`` named tuple with ``args`` and
            ``kwargs`` fields.
        locators: Custom feature locators for loading features from
            non-standard sources. An iterable of locator objects.
        return_test_decorator: If ``True`` (default), returns a
            decorator to apply to a test function. If ``False``,
            returns a generated test function directly.

    Returns:
        A ``ScenarioDecorator`` when ``return_test_decorator=True``,
        or a ``ScenarioTest`` function when ``return_test_decorator=False``.
        The overload signatures provide precise return types based on
        the ``Literal`` value of ``return_test_decorator``.

    Note:
        A ``ValueError`` is raised if both ``features_base_dir`` and
        ``features_base_url`` are specified (delegated to :func:`scenarios`).

    Example:
        Basic usage with a feature file::

            from pytest_bdd import scenario

            @scenario("features/login.feature", "Successful login")
            def test_login():
                pass

        Loading from a URL::

            from pytest_bdd import scenario, FeaturePathType

            @scenario(
                "https://example.com/features/login.feature",
                "Successful login",
                features_path_type=FeaturePathType.URL,
            )
            def test_login_remote():
                pass

        Generating test function directly::

            test_login = scenario(
                "features/login.feature",
                "Successful login",
                return_test_decorator=False,
            )

    See Also:
        :func:`scenarios`: Bulk-load all scenarios from feature files.
        :class:`FeaturePathType`: Enum for path resolution modes.

    Responsibility:
        Load and bind a single Gherkin scenario to a pytest test function. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.scenario` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - scenarios: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `scenario`
        - src/pytest_bdd/collector.py: imports or references `scenario`
        - src/pytest_bdd/feature_locator.py: imports or references `scenario`
        - src/pytest_bdd/model/feature_binding.py: imports or references `scenario`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `scenario`

    State and side effects:
        mutates feature_paths.

    Invariants:
        - `pytest_bdd.scenario.scenario` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    feature_paths = [feature_name] if feature_name is not None else []
    if return_test_decorator:
        return scenarios(
            *feature_paths,
            filter_=scenario_name,
            encoding=encoding,
            features_base_dir=features_base_dir,
            features_base_url=features_base_url,
            features_path_type=features_path_type,
            features_mimetype=features_mimetype,
            return_test_decorator=True,
            locators=locators,
            parser_type=parser_type,
            parse_args=parse_args,
        )
    return scenarios(
        *feature_paths,
        filter_=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        features_base_url=features_base_url,
        features_path_type=features_path_type,
        features_mimetype=features_mimetype,
        return_test_decorator=False,
        locators=locators,
        parser_type=parser_type,
        parse_args=parse_args,
    )


@overload
def scenarios(
    *feature_paths: Path | str,
    filter_: ScenarioFilterT = None,
    return_test_decorator: Literal[True],
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
) -> ScenarioDecorator:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.scenario.scenarios` owns documented function behavior. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.scenarios` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `scenarios`
        - src/pytest_bdd/collector.py: imports or references `scenarios`
        - src/pytest_bdd/feature_locator.py: imports or references `scenarios`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `scenarios`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `scenarios`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """


@overload
def scenarios(
    *feature_paths: Path | str,
    filter_: ScenarioFilterT = None,
    return_test_decorator: Literal[False] = False,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
) -> ScenarioTest:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.scenario.scenarios` owns documented function behavior. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.scenarios` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `scenarios`
        - src/pytest_bdd/collector.py: imports or references `scenarios`
        - src/pytest_bdd/feature_locator.py: imports or references `scenarios`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `scenarios`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `scenarios`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """


def scenarios(  # noqa: PLR0913
    *feature_paths: Path | str,
    filter_: ScenarioFilterT = None,
    return_test_decorator: bool = False,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
) -> ScenarioDecorator | ScenarioTest:
    """
    Bulk-load scenarios from feature files and bind them to pytest test functions.

    Unlike :func:`scenario`, which loads a single scenario, this function
    can load multiple scenarios from one or more feature files. It
    composes a chain of pytest markers (``pytest.mark.pytest_bdd`` and
    ``pytest.mark.pytest_bdd_scenarios``) that integrate with pytest's
    collection and execution lifecycle.

    Scenarios can be filtered by name (string) or by a custom callable
    that receives the pytest config, feature, and scenario objects.
    The ``filter_`` parameter enables selective scenario binding
    without modifying feature files.

    When ``return_test_decorator=True``, the result is a decorator to
    apply to a test function. When ``False`` (default), a generated
    test function is returned directly.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:5
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5

    Args:
        feature_paths: Variable number of feature file paths (absolute
            or relative to ``features_base_dir``). Each path can be a
            ``Path`` object or a string.
        filter_: Scenario filter. Can be a string (exact scenario name
            match), a callable with signature
            ``(Config, feature, scenario) -> bool``, or ``None`` to
            include all scenarios.
        return_test_decorator: If ``True``, returns a decorator to
            apply to a test function. If ``False`` (default), returns
            a generated test function directly.
        encoding: Feature file encoding. Defaults to ``"utf-8"``.
        features_base_dir: Base directory for resolving relative
            feature paths. Mutually exclusive with ``features_base_url``.
        features_base_url: Base URL for loading features over HTTP/HTTPS.
            Mutually exclusive with ``features_base_dir``.
        features_path_type: Controls how non-absolute paths are
            resolved. Use ``FeaturePathType.PATH`` (default) for
            filesystem paths or ``FeaturePathType.URL`` for HTTP URLs.
        features_mimetype: Override MIME type detection to select
            a specific parser. Useful for non-standard file extensions.
        parser_type: Custom parser class implementing ``ParserProtocol``.
        parse_args: Arguments passed to the parser during feature
            parsing. An ``Args`` named tuple with ``args`` and
            ``kwargs`` fields.
        locators: Custom feature locators for loading features from
            non-standard sources. An iterable of locator objects.

    Returns:
        A ``ScenarioDecorator`` when ``return_test_decorator=True``,
        or a ``ScenarioTest`` function when ``return_test_decorator=False``.
        The overload signatures provide precise return types based on
        the ``Literal`` value of ``return_test_decorator``.

    Raises:
        ValueError: If both ``features_base_dir`` and
            ``features_base_url`` are specified.

    Example:
        Bulk-load all scenarios from a feature file::

            from pytest_bdd import scenarios

            @scenarios("features/login.feature")
            def test_login():
                pass

        Filter by scenario name::

            @scenarios("features/login.feature", filter_="Successful login")
            def test_login():
                pass

        Load from multiple feature files::

            @scenarios(
                "features/login.feature",
                "features/logout.feature",
            )
            def test_auth():
                pass

    See Also:
        :func:`scenario`: Load and bind a single scenario.
        :class:`FeaturePathType`: Enum for path resolution modes.

    Responsibility:
        Bulk-load scenarios from feature files and bind them to pytest test functions. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario.scenarios` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - test: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `scenarios`
        - src/pytest_bdd/collector.py: imports or references `scenarios`
        - src/pytest_bdd/feature_locator.py: imports or references `scenarios`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `scenarios`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `scenarios`

    State and side effects:
        mutates features_path_type, parse_args, msg, decorator, test.__name__.

    Invariants:
        - `pytest_bdd.scenario.scenarios` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

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
        #arch-eval:locational_stability=4

    """
    if parse_args is None:
        parse_args = Args((), {})

    if features_base_dir and features_base_url:
        msg = 'Both "features_base_dir" and "features_base_url" were specified'
        raise ValueError(msg)
    if features_base_dir:
        features_path_type = FeaturePathType.PATH
    elif features_base_url:
        features_path_type = FeaturePathType.URL

    decorator = cast(
        "ScenarioDecorator",
        compose(
            cast("Callable[..., Any]", getattr(pytest.mark, PYTEST_BDD_MARK)),
            pytest.mark.usefixtures("gherkin_document", "pickle", "feature_source"),  # type: ignore[attr-defined]  # pytest.mark module attribute, not the function
            cast("Callable[..., Any]", getattr(pytest.mark, PYTEST_BDD_SCENARIOS_MARK))(
                *feature_paths,
                filter_=filter_,
                encoding=encoding,
                features_base_dir=features_base_dir,
                features_base_url=features_base_url,
                features_path_type=features_path_type,
                features_mimetype=features_mimetype,
                parser_type=parser_type,
                parse_args=parse_args,
                locators=locators,
            ),
        ),
    )

    if return_test_decorator:
        return decorator

    @decorator
    def test() -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.scenario.scenarios.test` owns documented function behavior. It
            directly owns the observable contract, local decisions, and maintenance boundary for this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.scenario.scenarios.test` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/__init__.py: imports or references `test`
            - src/pytest_bdd/collector.py: imports or references `test`
            - src/pytest_bdd/feature_locator.py: imports or references `test`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `test`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `test`

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
            #arch-eval:locational_stability=4
        """
        return Nothing.value_or(None)

    test.__name__ = next(get_python_name_generator(""))

    return test
