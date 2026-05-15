"""Provide scenario helpers."""

from collections.abc import Callable, Iterable, Iterator
from enum import Enum
from pathlib import Path
from typing import Literal, NamedTuple, Protocol, TypeAlias, cast, overload

import pytest
from returns.maybe import Nothing

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_collection import PYTEST_BDD_MARK, PYTEST_BDD_SCENARIOS_MARK
from pytest_bdd.util.other import format_as_simplified_python_identifier
from pytest_bdd.util.toolz_extra import compose


class ScenarioFunction(Protocol):
    """Represent scenario function state."""

    __name__: str

    def __call__(self) -> object:
        """Handle call."""
        ...


class Args(NamedTuple):
    """Represent args state."""

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

    """
    python_name = format_as_simplified_python_identifier(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        return "_".join(filter(bool, ["test", python_name, suffix]))

    while True:
        yield get_name()
        index += 1
        suffix = f"{index}"


test_names = get_python_name_generator("")


class FeaturePathType(Enum):
    """
    Controls how non-absolute feature paths are resolved during loading.

    This enum determines whether relative paths are treated as filesystem
    paths or HTTP/HTTPS URLs when loading Gherkin feature files.

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
) -> ScenarioDecorator: ...


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
) -> ScenarioTest: ...


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

    """
    feature_paths = [feature_name] if feature_name is not None else []
    if return_test_decorator:
        return cast(
            "ScenarioDecorator",
            scenarios(
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
            ),
        )
    return cast(
        "ScenarioTest",
        scenarios(
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
        ),
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
) -> ScenarioDecorator: ...


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
) -> ScenarioTest: ...


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
            cast("Callable", getattr(pytest.mark, PYTEST_BDD_MARK)),
            pytest.mark.usefixtures("gherkin_document", "pickle", "feature_source"),
            cast("Callable", getattr(pytest.mark, PYTEST_BDD_SCENARIOS_MARK))(
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
        return Nothing.value_or(None)

    test.__name__ = next(iter(test_names))

    return test
