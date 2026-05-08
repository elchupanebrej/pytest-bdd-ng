from pytest_bdd.compatibility.enum import StrEnum


class Steps:
    class Ini(StrEnum):
        """INI option names for step execution."""

        LIBERAL_OPTION = "liberal_steps"

    class Cli(StrEnum):
        """CLI option names for step execution."""

        LIBERAL_OPTION = "liberal_steps"
