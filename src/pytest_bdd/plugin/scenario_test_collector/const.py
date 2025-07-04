from enum import StrEnum

PYTEST_BDD_MARK = "pytest_bdd_scenario"


class FeatureAutoLoad:
    class Ini(StrEnum):
        DISABLE_OPTION = "disable_feature_autoload"

    class Cli(StrEnum):
        DISABLE_OPTION = "feature_autoload"


class FeatureBaseLoad:
    class Ini(StrEnum):
        DIR_OPTION = "bdd_features_base_dir"
        URL_OPTION = "bdd_features_base_url"
