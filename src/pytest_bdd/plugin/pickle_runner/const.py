"""Provide const helpers."""

from pytest_bdd.compatibility.enum import StrEnum


class Steps:
    """Represent steps state."""

    class Ini(StrEnum):
        """INI option names for step execution."""

        LIBERAL_OPTION = "liberal_steps"

    class Cli(StrEnum):
        """CLI option names for step execution."""

        LIBERAL_OPTION = "liberal_steps"
