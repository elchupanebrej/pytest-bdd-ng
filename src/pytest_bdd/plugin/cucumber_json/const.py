from pytest_bdd.compatibility.enum import StrEnum


class CucumberJson:
    class Ini(StrEnum):
        """INI option names for Cucumber JSON output."""

        PATH_OPTION = "cucumber_json_path"

    class Cli(StrEnum):
        """CLI option names for Cucumber JSON output."""

        PATH_OPTION = "cucumber_json_path"
