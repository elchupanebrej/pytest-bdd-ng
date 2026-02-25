from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.message_extension import EventEnvelope


class GherkinMessageReporterHookSpec:
    def pytest_bdd_message(self, config: Config, message: EventEnvelope):
        """Implement cucumber message protocol https://github.com/cucumber/messages"""
