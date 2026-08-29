from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_bdd.scenario import (
    FeaturePathType,
    add_options,
    get_python_name_generator,
    scenario,
    scenarios,
)


def test_feature_path_type_enum() -> None:
    assert FeaturePathType.PATH.value == "path"
    assert FeaturePathType.URL.value == "url"
    assert FeaturePathType.UNDEFINED.value == "undefined"


def test_python_name_generator() -> None:
    gen = get_python_name_generator("User Login")
    first = next(iter(gen))
    assert "user_login" in first


def test_add_options() -> None:
    mock_parser = MagicMock()
    add_options(mock_parser)
    mock_parser.getgroup.assert_called_once_with("bdd", "Scenario")


def test_scenario_decorator_validation() -> None:
    with pytest.raises(ValueError, match='Both "features_base_dir" and "features_base_url" were specified'):
        scenario("test.feature", features_base_dir="/tmp", features_base_url="http://example.com")


def test_scenario_and_scenarios_returns_test() -> None:
    test_fn = scenarios("tests/feature/test.feature", return_test_decorator=False)
    assert callable(test_fn)
    assert hasattr(test_fn, "pytestmark")

    decorator = scenario("tests/feature/test.feature", return_test_decorator=True)
    assert callable(decorator)

    @decorator
    def custom_test():
        pass

    assert callable(custom_test)
    assert hasattr(custom_test, "pytestmark")
