import json
import os
from collections.abc import Iterator, Mapping
from typing import Protocol, cast
from unittest.mock import patch

import pytest
from attr import asdict
from attr.exceptions import NotAnAttrsClassError
from cucumber_messages import GherkinDocument, Pickle  # type:ignore[attr-defined, import-untyped]
from pluggy import HookimplMarker
from pydantic import BaseModel as PydanticBaseModel

from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import FixtureRequest, Item
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.plugin.pickle_runner.run_access import (
    require_feature_object,
    require_pickle_object,
    require_step_object,
)
from pytest_bdd.steps import StepDefinitionManager

if ALLURE_INSTALLED:
    from allure_commons import hookimpl as allure_hookimpl
    from allure_commons._allure import StepContext
    from allure_commons.model2 import Label, Parameter, Status, TestStepResult
    from allure_commons.types import LabelType
    from allure_commons.utils import md5, now, platform_label
else:
    allure_hookimpl = HookimplMarker("allure")


class _CallSpecProtocol(Protocol):
    params: Mapping[str, object]


class _AllureCacheProtocol(Protocol):
    def get(self, key: object) -> str | None: ...

    def push(self, key: object) -> str: ...


class _AllureResultProtocol(Protocol):
    fullName: str  # noqa: N815 -- mirrors allure_commons.model2 field name.
    name: str
    start: int
    stop: int
    historyId: str  # noqa: N815 -- mirrors allure_commons.model2 field name.
    labels: list[object]
    parameters: list[object] | None
    status: object
    status_details: object


class _AllureLoggerProtocol(Protocol):
    def start_step(self, parent_uuid: str | None, uuid: str, result: object) -> None: ...

    def stop_step(self, uuid: str | None) -> None: ...

    def get_test(self, uuid: str | None) -> _AllureResultProtocol: ...

    def get_item(self, uuid: str | None) -> _AllureResultProtocol: ...


class _AllureListenerProtocol(Protocol):
    allure_logger: _AllureLoggerProtocol
    _cache: _AllureCacheProtocol


class ValueSerializer(Protocol):
    def __call__(self, instance: object, field: object, value: object) -> object: ...


class AttrsAsDict(Protocol):
    def __call__(self, instance: object, **kwargs: object) -> dict[str, object]: ...


def _node_callspec(node: object) -> _CallSpecProtocol | None:
    callspec = getattr(node, "callspec", None)
    return callspec if hasattr(callspec, "params") else None


def _patched_asdict(
    *args: object,
    recurse: bool = True,
    value_serializer: ValueSerializer | None = None,
    **kwargs: object,
) -> dict[str, object]:
    def patched_value_serializer(instance: object, field: object, value: object) -> object:
        if isinstance(value, PydanticBaseModel):
            # Maybe possible to speedup; Some values are not serialized when used value.dict()
            return json.loads(value.model_dump_json())
        if value_serializer is not patched_value_serializer:
            if value_serializer is None:
                return value
            return value_serializer(instance, field, value)
        if recurse:
            try:
                return _patched_asdict(
                    value,
                    *args[1:],
                    recurse=True,
                    value_serializer=patched_value_serializer,
                    **kwargs,
                )
            except NotAnAttrsClassError:
                return value
        else:
            return value

    if value_serializer is None:
        value_serializer = patched_value_serializer

    kwargs["value_serializer"] = patched_value_serializer
    attrs_asdict = cast(AttrsAsDict, asdict)
    return attrs_asdict(*args, **kwargs)


class PatchedAllureListener:
    def __init__(self, allure_listener: _AllureListenerProtocol) -> None:
        self.allure_listener = allure_listener
        self.allure_logger, self._cache = allure_listener.allure_logger, allure_listener._cache

    @allure_hookimpl(hookwrapper=True, tryfirst=True)
    def report_result(
        self,
        result: object,  # noqa: ARG002 hookspec
    ) -> Iterator[None]:
        with patch("allure_commons.logger.asdict", new=_patched_asdict):
            yield


class AllureLogger:
    plugin_name = "pytest-bdd-internal-allure-logger"

    def __init__(self, allure_listener: _AllureListenerProtocol) -> None:
        self.allure_logger, self._cache = allure_listener.allure_logger, allure_listener._cache

    @pytest.hookimpl
    def pytest_bdd_before_step_call(
        self,
        request: FixtureRequest,  # noqa: ARG002 hookspec
        run: Run,
        step_func: object,
        step_func_args: Mapping[str, object],
        step_definition: StepDefinitionManager.Definition,
    ) -> None:
        """Called before step function is set up."""
        step = require_step_object(run, hook_name="pytest_bdd_before_step_call")
        step_definition.func = StepContext(f"{step.keyword} {step.text}", step_func_args)(step_func)

    @pytest.hookimpl
    def pytest_bdd_before_scenario(self, request: FixtureRequest, run: Run) -> None:
        gherkin_document = require_feature_object(run, hook_name="pytest_bdd_before_scenario")
        pickle = require_pickle_object(run, hook_name="pytest_bdd_before_scenario")
        scenario_result_uuid = self._cache.get(pickle)
        test_result_uuid = self._cache.get(request.node.nodeid)

        if not scenario_result_uuid:
            scenario_result_uuid = self._cache.push(pickle)

        self.allure_logger.start_step(test_result_uuid, scenario_result_uuid, TestStepResult())

        scenario_result = self.allure_logger.get_test(scenario_result_uuid)
        test_result = self.allure_logger.get_item(test_result_uuid)
        full_name = self.get_full_name(gherkin_document, pickle)
        name = self.get_name(request.node, pickle)

        scenario_result.fullName = full_name
        scenario_result.name = name
        scenario_result.start = now()
        scenario_result.historyId = md5(request.node.nodeid)
        test_result.labels.append(Label(name=LabelType.FRAMEWORK, value="pytest-bdd"))
        test_result.labels.append(Label(name=LabelType.LANGUAGE, value=platform_label()))
        feature_name = getattr(getattr(gherkin_document, "feature", None), "name", None)
        if feature_name:
            test_result.labels.append(Label(name=LabelType.FEATURE, value=str(feature_name)))
        scenario_result.parameters = self.get_params(request.node)

    @pytest.hookimpl
    def pytest_bdd_after_scenario(
        self,
        request: FixtureRequest,  # noqa: ARG002 hookspec
        run: Run,
    ) -> None:
        pickle = require_pickle_object(run, hook_name="pytest_bdd_after_scenario")
        scenario_result_uuid = self._cache.get(pickle)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.stop = now()
        self.allure_logger.stop_step(scenario_result_uuid)

    @pytest.hookimpl
    def pytest_bdd_step_func_lookup_error(
        self,
        request: FixtureRequest,  # noqa: ARG002 hookspec
        run: Run,
        exception: Exception,
    ) -> None:
        pickle = require_pickle_object(run, hook_name="pytest_bdd_step_func_lookup_error")
        scenario_result_uuid = self._cache.get(pickle)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.status = Status.BROKEN
        scenario_result.status_details = exception
        self.allure_logger.stop_step(scenario_result_uuid)

    @staticmethod
    def get_params(node: object) -> list[object] | None:
        callspec = _node_callspec(node)
        if callspec is not None:
            params = callspec.params
            return [Parameter(name=name, value=value) for name, value in params.items()]
        return None

    @staticmethod
    def get_name(node: Item, pickle: Pickle) -> str:
        if _node_callspec(node) is not None:
            parts = node.nodeid.rsplit("[")
            return f"{pickle.name} [{parts[-1]}"
        return str(pickle.name)

    @staticmethod
    def get_full_name(gherkin_document: GherkinDocument, pickle: Pickle) -> str:
        uri = str(gherkin_document.uri)
        feature_path = uri.removeprefix("file:") if uri.startswith("file:") else uri
        return f"{os.path.normpath(feature_path)}:{pickle.name}"
