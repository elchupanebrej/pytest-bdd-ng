from collections.abc import Callable, Iterable
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.util.other import format_as_simplified_python_identifier
from pytest_bdd.util.toolz_extra import compose


class Args(NamedTuple):
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


def get_python_name_generator(name: str) -> Iterable[str]:
    """Generate a sequence of suitable python names out of given arbitrary string name."""
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
    PATH = "path"
    URL = "url"
    UNDEFINED = "undefined"


def scenario(
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url=None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators=(),
    *,
    return_test_decorator=True,
):
    """Scenario decorator.

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
    """
    return scenarios(
        *([feature_name] if feature_name is not None else []),
        filter_=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        features_base_url=features_base_url,
        features_path_type=features_path_type,
        features_mimetype=features_mimetype,
        return_test_decorator=return_test_decorator,
        locators=locators,
        parser_type=parser_type,
        parse_args=parse_args,
    )


def scenarios(
    *feature_paths: Path | str,
    filter_: str | Callable | None = None,
    return_test_decorator=False,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators=(),
):
    """Function to bind feature files to pytest runtime

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

    decorator = compose(
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
    )

    if return_test_decorator:
        return decorator

    @decorator
    def test(): ...

    test.__name__ = next(iter(test_names))

    return test
