from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, ParamSpec, Protocol, TypeVar, cast
from unittest.mock import patch

import pytest
from attr import asdict
from attr.exceptions import NotAnAttrsClassError
from pluggy import HookimplMarker
from pydantic import BaseModel as PydanticBaseModel

from pytest_cuke.compatibility.allure import ALLURE_INSTALLED
from pytest_cuke.compatibility.pytest import PYTEST81
from pytest_cuke.model.run_access import get_scenario_run

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from pytest_cuke.compatibility.pytest import Config, FixtureRequest
    from pytest_cuke.model import Feature, Scenario, Step
    from pytest_cuke.steps import Definition


_P = ParamSpec("_P")
_R = TypeVar("_R")


class _StepDecorator(Protocol):
    def __call__(self, func: Callable[_P, _R]) -> Callable[_P, _R]: ...


class _StepContextFactory(Protocol):
    def __call__(self, title: str, params: dict[str, Any]) -> _StepDecorator: ...


class _PluginManager(Protocol):
    def get_plugins(self) -> Iterable[object]: ...

    def register(self, plugin: object) -> str | None: ...

    def unregister(self, name: str | None = ...) -> object | None: ...


class _StatusValues(Protocol):
    BROKEN: object


class _LabelTypes(Protocol):
    FRAMEWORK: str
    LANGUAGE: str
    FEATURE: str


class _LabelFactory(Protocol):
    def __call__(self, *, name: str, value: str) -> object: ...


class _ParameterFactory(Protocol):
    def __call__(self, *, name: str, value: object) -> object: ...


class _TestStepResultFactory(Protocol):
    def __call__(self) -> object: ...


class _AllureResult(Protocol):
    labels: list[object]
    fullName: str
    name: str
    start: int
    historyId: str
    parameters: list[object] | None
    stop: int
    status: object
    status_details: Exception


class _AllureLogger(Protocol):
    def start_step(self, parent_uuid: str | None, uuid: str, step_result: object) -> None: ...

    def get_test(self, uuid: str | None) -> _AllureResult: ...

    def get_item(self, uuid: str | None) -> _AllureResult: ...

    def stop_step(self, uuid: str | None) -> None: ...


class _AllureCache(Protocol):
    def get(self, item: object) -> str | None: ...

    def push(self, item: object) -> str: ...


class _AllureListener(Protocol):
    allure_logger: object
    _cache: object


class _CallSpec(Protocol):
    params: Mapping[str, object]


class _NodeWithCallSpec(Protocol):
    nodeid: str
    callspec: _CallSpec


if ALLURE_INSTALLED:
    from allure_commons import hookimpl
    from allure_commons import plugin_manager as _raw_allure_plugin_manager
    from allure_commons._allure import StepContext as _raw_step_context
    from allure_commons.model2 import Label as _raw_label
    from allure_commons.model2 import Parameter as _raw_parameter
    from allure_commons.model2 import Status as _raw_status
    from allure_commons.model2 import TestStepResult as _raw_test_step_result
    from allure_commons.types import LabelType as _raw_label_type
    from allure_commons.utils import md5 as _raw_md5
    from allure_commons.utils import now as _raw_now
    from allure_commons.utils import platform_label as _raw_platform_label
    from allure_pytest.listener import AllureListener as _raw_allure_listener

    allure_plugin_manager: _PluginManager | None = cast("_PluginManager", _raw_allure_plugin_manager)
    StepContext: _StepContextFactory | None = cast("_StepContextFactory", _raw_step_context)
    Label: _LabelFactory | None = cast("_LabelFactory", _raw_label)
    Parameter: _ParameterFactory | None = cast("_ParameterFactory", _raw_parameter)
    Status: _StatusValues | None = cast("_StatusValues", _raw_status)
    TestStepResult: _TestStepResultFactory | None = cast("_TestStepResultFactory", _raw_test_step_result)
    LabelType: _LabelTypes | None = cast("_LabelTypes", _raw_label_type)
    AllureListener: type[object] | None = cast("type[object]", _raw_allure_listener)
    md5: Callable[[str], str] | None = cast("Callable[[str], str]", _raw_md5)
    now: Callable[[], int] | None = cast("Callable[[], int]", _raw_now)
    platform_label: Callable[[], str] | None = cast("Callable[[], str]", _raw_platform_label)
else:
    hookimpl = HookimplMarker("allure")
    allure_plugin_manager = None
    StepContext = None
    Label = None
    Parameter = None
    Status = None
    TestStepResult = None
    LabelType = None
    AllureListener = None
    md5 = None
    now = None
    platform_label = None


class AllurePytestBDD:
    def __init__(self, allure_logger: _AllureLogger, allure_cache: _AllureCache) -> None:
        self.allure_logger = allure_logger
        self._cache = allure_cache

        self.allure_plugin_name: str | None = None
        self.pytest_plugin_name: str | None = None

    @classmethod
    def register_if_allure_accessible(cls, config: Config) -> AllurePytestBDD | None:
        if not ALLURE_INSTALLED or allure_plugin_manager is None or AllureListener is None:
            return None
        pluginmanager = config.pluginmanager
        allure_accessible = pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
        if allure_accessible and not PYTEST81:
            allure_plugin_manager.get_plugins()

            listener = next(
                filter(lambda plugin: isinstance(plugin, AllureListener), allure_plugin_manager.get_plugins())
            )

            allure_listener = cast("_AllureListener", listener)
            bdd_listener = cls(
                cast("_AllureLogger", allure_listener.allure_logger),
                cast("_AllureCache", allure_listener._cache),
            )
            bdd_listener.allure_plugin_name = allure_plugin_manager.register(bdd_listener)
            bdd_listener.pytest_plugin_name = pluginmanager.register(bdd_listener)
            return bdd_listener
        return None

    @hookimpl(hookwrapper=True)
    def report_result(self, result: Any) -> Iterator[None]:
        def patched_asdict(*args: Any, recurse: bool = True, value_serializer: Any = None, **kwargs: Any) -> Any:
            def patched_value_serializer(instance: Any, field: Any, value: Any) -> Any:
                if isinstance(value, PydanticBaseModel):
                    # Maybe possible to speedup; Some values are not serialized when used value.dict()
                    return json.loads(value.model_dump_json())
                if value_serializer is not patched_value_serializer:
                    return value_serializer(instance, field, value)
                if recurse:
                    try:
                        return patched_asdict(
                            value, *args[1:], recurse=True, value_serializer=patched_value_serializer, **kwargs
                        )
                    except NotAnAttrsClassError:
                        return value
                else:
                    return value

            if value_serializer is None:
                value_serializer = patched_value_serializer

            options = dict(kwargs)
            options["value_serializer"] = patched_value_serializer
            return asdict(*args, **options)

        with patch("allure_commons.logger.asdict", new=patched_asdict):
            yield

    def unregister(self, config: Config) -> None:
        if not ALLURE_INSTALLED or allure_plugin_manager is None:
            return
        pluginmanager = config.pluginmanager
        allure_accessible = pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
        if allure_accessible:
            allure_plugin_manager.unregister(name=self.allure_plugin_name)
            pluginmanager.unregister(name=self.pytest_plugin_name)

    @pytest.hookimpl
    def pytest_cuke_before_step_call(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Any,
        step_func_args: dict[str, Any],
        step_definition: Definition,
    ) -> None:
        """Called before step function is set up."""
        if StepContext is not None:
            step_definition.func = StepContext(f"{step.keyword} {step.text}", step_func_args)(step_func)

    @pytest.hookimpl
    def pytest_cuke_before_scenario(self, request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
        if TestStepResult is None or md5 is None or now is None:
            return
        scenario_ref = get_scenario_run(request) or scenario
        scenario_result_uuid = self._cache.get(scenario_ref)
        test_result_uuid = self._cache.get(request.node.nodeid)

        if not scenario_result_uuid:
            scenario_result_uuid = self._cache.push(scenario_ref)

        self.allure_logger.start_step(test_result_uuid, scenario_result_uuid, TestStepResult())

        scenario_result = self.allure_logger.get_test(scenario_result_uuid)
        test_result = self.allure_logger.get_item(test_result_uuid)
        full_name = self.get_full_name(feature, scenario)
        name = self.get_name(request.node, scenario)

        scenario_result.fullName = full_name
        scenario_result.name = name
        scenario_result.start = now()
        scenario_result.historyId = md5(request.node.nodeid)
        if Label is not None and LabelType is not None and platform_label is not None:
            test_result.labels.append(Label(name=LabelType.FRAMEWORK, value="pytest-bdd"))
            test_result.labels.append(Label(name=LabelType.LANGUAGE, value=platform_label()))
            test_result.labels.append(Label(name=LabelType.FEATURE, value=feature.name))
        scenario_result.parameters = self.get_params(request.node)

    @pytest.hookimpl
    def pytest_cuke_after_scenario(self, request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
        if now is None:
            return
        scenario_result_uuid = self._cache.get(get_scenario_run(request) or scenario)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.stop = now()
        self.allure_logger.stop_step(scenario_result_uuid)

    @pytest.hookimpl
    def pytest_cuke_step_func_lookup_error(
        self, request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, exception: Exception
    ) -> None:
        if Status is None:
            return
        scenario_result_uuid = self._cache.get(get_scenario_run(request) or scenario)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.status = Status.BROKEN
        scenario_result.status_details = exception
        self.allure_logger.stop_step(scenario_result_uuid)

    @staticmethod
    def get_params(node: object) -> list[object] | None:
        if hasattr(node, "callspec"):
            params = cast("_NodeWithCallSpec", node).callspec.params
            if Parameter is not None:
                return [Parameter(name=name, value=value) for name, value in params.items()]
            return [{"name": name, "value": value} for name, value in params.items()]
        return None

    @staticmethod
    def get_name(node: object, scenario: Scenario) -> str:
        if hasattr(node, "callspec"):
            parts = cast("_NodeWithCallSpec", node).nodeid.rsplit("[")
            return f"{scenario.name} [{parts[-1]}"
        return scenario.name

    @staticmethod
    def get_full_name(feature: Feature, scenario: Scenario) -> str:
        feature_path = os.path.normpath(feature.rel_filename)
        return f"{feature_path}:{scenario.name}"
