"""Provide cucumber json dispatcher constants."""

from pytest_bdd.compatibility.enum import StrEnum


class CucumberJsonDispatcher:
    """
    Dispatcher constants - locally duplicated to satisfy BLQ1002 cross-plugin import ban.

    WARNING: If INI/CLI option names change in cucumber_json or cucumber_json_formatter,
    update this file manually. Drift will cause silent misconfiguration.
    """

    class Ini(StrEnum):
        """INI option name for the Python JSON reporter backend."""

        PATH_OPTION = "cucumber_json_path"

    class Cli(StrEnum):
        """CLI option attribute name for the Node.js JSON formatter backend."""

        OPTION_ATTR = "cucumber_js_json_path"
        FLAG = "--cucumber-json"
