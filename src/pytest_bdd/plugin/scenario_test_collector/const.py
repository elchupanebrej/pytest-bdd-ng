from pytest_bdd.compatibility.enum import StrEnum

PYTEST_BDD_MARK = "pytest_bdd_scenario"


class FeatureAutoLoad:
    class Ini(StrEnum):
        """INI option names for feature auto-load."""

        DISABLE_OPTION = "disable_feature_autoload"

    class Cli(StrEnum):
        """CLI option names for feature auto-load."""

        DISABLE_OPTION = "feature_autoload"


class FeatureBaseLoad:
    class Ini(StrEnum):
        """INI option names for feature base loading."""

        DIR_OPTION = "bdd_features_base_dir"
        URL_OPTION = "bdd_features_base_url"
