import json
import os
from unittest.mock import patch

import pytest
from attr import asdict
from attr.exceptions import NotAnAttrsClassError
from pluggy import HookimplMarker
from pydantic import BaseModel as PydanticBaseModel

from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.plugin.pickle_runner.run_access import (
    resolve_feature_object,
    resolve_pickle_object,
    resolve_step_object,
)

if ALLURE_INSTALLED:
    from allure_commons import hookimpl as allure_hookimpl
    from allure_commons._allure import StepContext
    from allure_commons.model2 import Label, Parameter, Status, TestStepResult
    from allure_commons.types import LabelType
    from allure_commons.utils import md5, now, platform_label
else:
    allure_hookimpl = HookimplMarker("allure")


def _patched_asdict(*args, recurse=True, value_serializer=None, **kwargs):
    def patched_value_serializer(instance, field, value):
        if isinstance(value, PydanticBaseModel):
            # Maybe possible to speedup; Some values are not serialized when used value.dict()
            return json.loads(value.model_dump_json())
        if value_serializer is not patched_value_serializer:
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

    return asdict(*args, value_serializer=patched_value_serializer, **kwargs)


class PatchedAllureListener:
    def __init__(self, allure_listener):
        self.allure_listener = allure_listener
        self.allure_logger, self._cache = allure_listener.allure_logger, allure_listener._cache

    @allure_hookimpl(hookwrapper=True, tryfirst=True)
    def report_result(
        self,
        result,  # noqa: ARG002 hookspec
    ):
        with patch("allure_commons.logger.asdict", new=_patched_asdict):
            yield


class AllureLogger:
    plugin_name = "pytest-bdd-internal-allure-logger"

    def __init__(self, allure_listener):
        self.allure_logger, self._cache = allure_listener.allure_logger, allure_listener._cache

    @pytest.hookimpl
    def pytest_bdd_before_step_call(
        self,
        request,  # noqa: ARG002 hookspec
        run,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Called before step function is set up."""
        step = resolve_step_object(run)
        if step is None:
            return
        step_definition.func = StepContext(f"{step.keyword} {step.text}", step_func_args)(step_func)

    @pytest.hookimpl
    def pytest_bdd_before_scenario(self, request, run):
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        if gherkin_document is None or pickle is None:
            return
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
        request,  # noqa: ARG002 hookspec
        run,
    ):
        pickle = resolve_pickle_object(run)
        if pickle is None:
            return
        scenario_result_uuid = self._cache.get(pickle)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.stop = now()
        self.allure_logger.stop_step(scenario_result_uuid)

    @pytest.hookimpl
    def pytest_bdd_step_func_lookup_error(
        self,
        request,  # noqa: ARG002 hookspec
        run,
        exception,
    ):
        pickle = resolve_pickle_object(run)
        if pickle is None:
            return
        scenario_result_uuid = self._cache.get(pickle)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.status = Status.BROKEN
        scenario_result.status_details = exception
        self.allure_logger.stop_step(scenario_result_uuid)

    @staticmethod
    def get_params(node):
        if hasattr(node, "callspec"):
            params = node.callspec.params
            return [Parameter(name=name, value=value) for name, value in params.items()]
        return None

    @staticmethod
    def get_name(node, pickle):
        if hasattr(node, "callspec"):
            parts = node.nodeid.rsplit("[")
            return f"{pickle.name} [{parts[-1]}"
        return pickle.name

    @staticmethod
    def get_full_name(gherkin_document, pickle):
        uri = str(getattr(gherkin_document, "uri", ""))
        feature_path = uri.removeprefix("file:") if uri.startswith("file:") else uri
        return f"{os.path.normpath(feature_path)}:{pickle.name}"
