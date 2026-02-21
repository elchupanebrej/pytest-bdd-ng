from pytest_bdd import scenarios


def _include_allure_features(config, feature, scenario):  # noqa: ARG001
    return feature.name.lower().startswith("allure ")


test = scenarios(".", filter_=_include_allure_features)
