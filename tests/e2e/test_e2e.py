import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e_retain_technical]


def _exclude_allure_features(config, feature, scenario):  # noqa: ARG001
    feature_uri = getattr(feature, "uri", "")
    return "report/allure/" not in str(feature_uri).lower() and not feature.name.lower().startswith("allure ")


test = scenarios(".", filter_=_exclude_allure_features)
