from __future__ import annotations

from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pytest_bdd import hooks
from pytest_bdd.compatibility.pytest import make_mark
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.plugin import (
    _build_filter,
    _build_scenario_locators_from_mark,
    attach,
    pytest_addhooks,
    pytest_bdd_get_mimetype,
    pytest_bdd_get_parser,
    pytest_bdd_is_collectible,
    pytest_configure,
    pytest_unconfigure,
    pytestbdd_id_generator,
    pytestbdd_step_runner,
    step_matcher,
    step_registry,
    steps_left,
)
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.scenario import FeaturePathType
from pytest_bdd.scenario_locator import FileScenarioLocator, UrlScenarioLocator
from pytest_bdd.steps import Matcher, Registry
from pytest_bdd.utils import IdGenerator

from pytest import mark

pytestmark = mark.unit


def test_pytest_addhooks() -> None:
    pluginmanager = MagicMock()
    pytest_addhooks(pluginmanager)
    pluginmanager.add_hookspecs.assert_called_once_with(hooks)


def test_pytest_configure_lifecycle() -> None:
    config = MagicMock()
    config.stash = {}
    config.pluginmanager = MagicMock()
    config.option = MagicMock()
    config.option.cucumber_json_path = None
    config.option.gherkin_terminal_reporter = None

    pytest_configure(config)

    config.addinivalue_line.assert_any_call("markers", "pytest_bdd_scenario: marker to identify pytest_bdd tests")
    config.addinivalue_line.assert_any_call("markers", "scenarios: marker to provide scenarios locator")
    assert IdGenerator.pytest_bdd_id_generator in config.stash
    assert config.pluginmanager.register.call_count >= 2


def test_pytest_unconfigure_lifecycle() -> None:
    config = MagicMock()
    config.pluginmanager = MagicMock()
    config.__allure_plugin__ = MagicMock()

    pytest_unconfigure(config)
    config.pluginmanager.unregister.assert_any_call(name="pytest_bdd_messages")
    config.__allure_plugin__.unregister.assert_called_once_with(config)


def _unwrap_fixture(fixture_obj):
    return getattr(fixture_obj, "_fixture_function", getattr(fixture_obj, "__wrapped__", fixture_obj))


def test_builtin_fixtures() -> None:
    config = MagicMock()
    config.stash = {}
    config.pytest_bdd_id_generator = IdGenerator()

    assert isinstance(_unwrap_fixture(pytestbdd_step_runner)(), ScenarioRunner)
    assert isinstance(_unwrap_fixture(pytestbdd_id_generator)(config), IdGenerator)
    assert isinstance(_unwrap_fixture(step_registry)(), Registry)
    assert isinstance(_unwrap_fixture(step_matcher)(config), Matcher)
    assert isinstance(_unwrap_fixture(steps_left)(), deque)

    request = MagicMock()
    attach_fn = _unwrap_fixture(attach)(request)
    attach_fn(b"data", media_type="text/plain")
    request.config.hook.pytest_bdd_attach.assert_called_once()

    assert pytest_bdd_is_collectible(config, Path("test.feature")) is True
    assert pytest_bdd_is_collectible(config, Path("test.py")) is False


def test_pytestbdd_id_generator_without_stash_support() -> None:
    config = SimpleNamespace()

    generator = _unwrap_fixture(pytestbdd_id_generator)(config)

    assert isinstance(generator, IdGenerator)


def test_build_filter_variants() -> None:
    assert _build_filter(None) is None

    def callable_filter(config, feature, scenario):
        return True

    assert _build_filter(callable_filter) is callable_filter

    by_name = _build_filter("my scenario")
    assert by_name(None, None, SimpleNamespace(name="my scenario")) is True
    assert by_name(None, None, SimpleNamespace(name="my scenario[table_rows:[line: 3]]")) is True
    assert by_name(None, None, SimpleNamespace(name="another scenario")) is False


def _config_with_ini(values: dict[str, str]) -> MagicMock:
    config = MagicMock()
    config.getini.side_effect = lambda name: values.get(name, "")
    config.rootpath = Path("/root")
    return config


def test_build_scenario_locators_defaults_from_ini_fallbacks() -> None:
    config = _config_with_ini({"bdd_features_base_dir": "/features", "bdd_features_base_url": "http://base"})

    file_locator, url_locator = list(_build_scenario_locators_from_mark(make_mark("scenarios"), config))

    assert isinstance(file_locator, FileScenarioLocator)
    assert isinstance(url_locator, UrlScenarioLocator)
    assert file_locator.features_base_dir == "/features"
    assert url_locator.features_base_url == "http://base"

    failing_config = MagicMock()
    failing_config.getini.side_effect = ValueError("unknown ini option")
    failing_config.rootpath = Path("/root")
    file_locator, url_locator = list(_build_scenario_locators_from_mark(make_mark("scenarios"), failing_config))
    assert file_locator.features_base_dir == Path("/root")
    assert url_locator.features_base_url is None


def test_build_scenario_locators_callable_base_dir_and_url() -> None:
    config = _config_with_ini({})

    def base_dir(_config):
        return Path("/from-callable")

    def base_url(_config):
        return "http://from-callable"

    file_locator, url_locator = list(
        _build_scenario_locators_from_mark(
            make_mark(
                "scenarios",
                kwargs={"features_base_dir": base_dir, "features_base_url": base_url},
            ),
            config,
        )
    )

    assert file_locator.features_base_dir == Path("/from-callable")
    assert url_locator.features_base_url == "http://from-callable"


def test_build_scenario_locators_path_type_dispatch() -> None:
    config = _config_with_ini({})

    url_mark = make_mark("scenarios", args=("features/a.feature",), kwargs={"features_path_type": FeaturePathType.URL})
    file_locator, url_locator = list(_build_scenario_locators_from_mark(url_mark, config))
    assert file_locator.feature_paths == []
    assert url_locator.url_paths == ["features/a.feature"]

    string_mark = make_mark("scenarios", args=("features/a.feature",), kwargs={"features_path_type": "undefined"})
    file_locator, url_locator = list(_build_scenario_locators_from_mark(string_mark, config))
    assert file_locator.feature_paths == ["features/a.feature"]
    assert url_locator.url_paths == ["features/a.feature"]

    undefined_mark = make_mark(
        "scenarios",
        args=("features/a.feature",),
        kwargs={"features_path_type": None},
    )
    file_locator, url_locator = list(_build_scenario_locators_from_mark(undefined_mark, config))
    assert file_locator.feature_paths == ["features/a.feature"]
    assert url_locator.url_paths == ["features/a.feature"]


def test_build_scenario_locators_rejects_unknown_path_type() -> None:
    config = _config_with_ini({})
    unknown_mark = make_mark("scenarios", kwargs={"features_path_type": object()})

    with pytest.raises(ValueError, match="Unknown feature path type"):
        list(_build_scenario_locators_from_mark(unknown_mark, config))


def test_pytest_bdd_get_mimetype_and_parser(monkeypatch) -> None:
    assert pytest_bdd_get_mimetype(None, Path("features/test.feature")) == Mimetype.gherkin_plain.value
    assert pytest_bdd_get_mimetype(None, Path("features/test.txt")) is None
    assert pytest_bdd_get_parser(None, "application/unknown") is None

    monkeypatch.setattr("pytest_bdd.plugin.is_npm_gherkin_installed", True)
    assert pytest_bdd_get_mimetype(None, Path("features/test.feature.md")) == Mimetype.markdown.value
