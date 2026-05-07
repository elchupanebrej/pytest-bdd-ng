class IncompatiblePluginError(Exception):
    def __init__(self, reporter: object) -> None:
        super().__init__(
            "gherkin-terminal-reporter is not compatible with any other terminal reporter."
            "You can use only one terminal reporter."
            f"Currently '{reporter.__class__}' is used."
            f"Please decide to use one by deactivating {reporter.__class__} or gherkin-terminal-reporter.",
        )


class IncompatiblePluginConfigurationError(Exception):
    def __init__(self, plugin: object) -> None:
        super().__init__(f"gherkin-terminal-reporter is not compatible with '{plugin}' plugin.")
