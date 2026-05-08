"""Provide exception helpers."""


class IncompatiblePluginError(Exception):
    """Represent incompatible plugin error failures."""

    def __init__(self, reporter: object) -> None:
        """Initialize the incompatible plugin error."""
        super().__init__(
            "gherkin-terminal-reporter is not compatible with any other terminal reporter."
            "You can use only one terminal reporter."
            f"Currently '{reporter.__class__}' is used."
            f"Please decide to use one by deactivating {reporter.__class__} or gherkin-terminal-reporter.",
        )


class IncompatiblePluginConfigurationError(Exception):
    """Represent incompatible plugin configuration error failures."""

    def __init__(self, plugin: object) -> None:
        """Initialize the incompatible plugin configuration error."""
        super().__init__(f"gherkin-terminal-reporter is not compatible with '{plugin}' plugin.")
