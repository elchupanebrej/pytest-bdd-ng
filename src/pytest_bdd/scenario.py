"""Provide scenario helpers."""

from collections.abc import Callable, Iterable, Iterator
from enum import Enum
from pathlib import Path
from typing import Literal, NamedTuple, Protocol, TypeAlias, cast, overload

import pytest

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.mimetype import Mimetype
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
    """Represent feature path type state."""

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
    return_test_decorator: bool = True,
) -> ScenarioDecorator | ScenarioTest:
    """
    Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param features_base_url: Feature base url from where features will be loaded
    :param features_path_type: If feature path is not absolute helps to select if filepath or url will be used
    :param features_mimetype: Helps to select appropriate parser if non-standard file extension is used
    :param parser_type: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    :param locators: Feature locators to load Features; Could be custom
    :param return_test_decorator; Return test decorator or generated test

    Returns:
        Scenario decorator or test function.

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


def scenarios(
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
    Bind feature files to pytest runtime.

    :param feature_paths: Features file names. Absolute or relative to the configured feature base path.
    :param filter_: Callable to filter scenarios
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param features_base_url: Feature base url from where features will be loaded
    :param features_path_type: If feature path is not absolute helps to select if filepath or url will be used
    :param features_mimetype: Helps to select appropriate parser if non-standard file extension is used
    :param return_test_decorator; Return test decorator or generated test
    :param parser_type: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    :param return_test_decorator; Return test decorator or generated test
    :param locators: Feature locators to load Features; Could be custom

    Returns:
        Scenario decorator or test function.

    Raises:
        ValueError: If both features_base_dir and features_base_url are specified.

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
            pytest.mark.pytest_bdd_scenario,
            pytest.mark.usefixtures("gherkin_document", "pickle", "feature_source"),
            pytest.mark.scenarios(
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
        return None

    test.__name__ = next(iter(test_names))

    return test
