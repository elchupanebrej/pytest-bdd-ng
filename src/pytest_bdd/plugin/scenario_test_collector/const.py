"""Provide const helpers."""

from pytest_bdd.compatibility.enum import StrEnum

PYTEST_BDD_MARK = "pytest_bdd_scenario"
PYTEST_BDD_SCENARIOS_MARK = "scenarios"


class FeatureAutoLoad:
    """Represent feature auto load state."""

    class Ini(StrEnum):
        """INI option names for feature autoload."""

        DISABLE_OPTION = "disable_feature_autoload"

    class Cli(StrEnum):
        """CLI option names for feature autoload."""

        DISABLE_OPTION = "feature_autoload"


class FeatureBaseLoad:
    """Represent feature base load state."""

    class Ini(StrEnum):
        """INI option names for feature base loading."""

        DIR_OPTION = "bdd_features_base_dir"
        URL_OPTION = "bdd_features_base_url"

    class Cli(StrEnum):
        """CLI option names for feature base loading."""

        DIR_OPTION = "features_base_dir"
        URL_OPTION = "features_base_url"
