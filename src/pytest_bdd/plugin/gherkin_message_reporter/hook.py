from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import Config


class GherkinMessageReporterHookSpec:
    def pytest_bdd_message(self, config: Config, message: Message):
        """Implement cucumber message protocol https://github.com/cucumber/messages"""
