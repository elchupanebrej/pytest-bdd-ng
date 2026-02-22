from pytest_bdd import scenarios
from pytest_bdd.compatibility.allure import ALLURE_INSTALLED


def _include_allure_features(config, feature, scenario):  # noqa: ARG001
    feature_uri = getattr(feature, "uri", "")
    feature_uri = str(feature_uri).lower()
    is_legacy_allure_feature = "report/allure/" in feature_uri and feature_uri.endswith(".feature")
    if is_legacy_allure_feature and not ALLURE_INSTALLED:
        return False
    return "report/allure/" in feature_uri or feature.name.lower().startswith("allure ")


test = scenarios(".", filter_=_include_allure_features)
