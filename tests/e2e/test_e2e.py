from pytest_bdd import scenarios


def _exclude_allure_features(config, feature, scenario):  # noqa: ARG001
    return not feature.name.lower().startswith("allure ")


test = scenarios(".", filter_=_exclude_allure_features)
