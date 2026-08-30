from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytest_bdd.compatibility.pytest import TerminalReporter

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, Parser, TestReport


def add_options(parser: Parser) -> None:
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="enable gherkin output",
    )


def configure(config: Config) -> None:
    if config.option.gherkin_terminal_reporter:
        # Get the standard terminal reporter plugin and replace it with our
        current_reporter = config.pluginmanager.getplugin("terminalreporter")
        if current_reporter.__class__ != TerminalReporter:
            msg = (
                "gherkin-terminal-reporter is not compatible with any other terminal reporter."
                "You can use only one terminal reporter."
                f"Currently '{current_reporter.__class__}' is used."
                f"Please decide to use one by deactivating {current_reporter.__class__} or gherkin-terminal-reporter."
            )
            raise Exception(msg)
        gherkin_reporter = GherkinTerminalReporter(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")
        if config.pluginmanager.getplugin("dsession"):
            msg = "gherkin-terminal-reporter is not compatible with 'xdist' plugin."
            raise Exception(msg)


class GherkinTerminalReporter(TerminalReporter):  # type: ignore[misc]
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def pytest_runtest_logreport(self, report: TestReport) -> Any:
        rep = report
        res = self.config.hook.pytest_report_teststatus(report=rep, config=self.config)
        cat, letter, word = res

        if not letter and not word:
            # probably passed setup/teardown
            return None

        if isinstance(word, tuple):
            word, word_markup = word
        elif rep.passed:
            word_markup = {"green": True}
        elif rep.failed:
            word_markup = {"red": True}
        elif rep.skipped:
            word_markup = {"yellow": True}
        else:
            word_markup = {}
        scenario_markup = word_markup

        if self.verbosity <= 0 or not hasattr(report, "scenario"):
            return super().pytest_runtest_logreport(report)

        scenario = report.scenario
        sc_name = scenario["name"].split("[table_rows:")[0]
        self.ensure_newline()
        self._tw.write(f"Feature: {scenario['feature']['name']}\n", blue=True)
        if self.verbosity == 1:
            self._tw.write(f"    Scenario: {sc_name}    {word}\n", **scenario_markup)
        elif self.verbosity > 1:
            self._tw.write(f"    Scenario: {sc_name}\n", **scenario_markup)
            has_already_failed = False
            for step in scenario["steps"]:
                if rep.skipped or step.get("skipped"):
                    step_markup = {"yellow": True}
                    step_status_text = "(SKIPPED)"
                elif step.get("failed"):
                    step_markup = {"red": True}
                    if not has_already_failed:
                        step_markup["bold"] = True
                        has_already_failed = True
                    step_status_text = "(FAILED)"
                else:
                    step_markup = {"green": True}
                    step_status_text = "(PASSED)"

                step_kw = step.get("keyword", "").strip()
                self._tw.write(
                    f"        {step_kw} {step.get('name', '')} {step_status_text}\n",
                    **step_markup,
                )
            self._tw.write(f"    {word}\n", **word_markup)
        else:
            self._tw.write(f"    Scenario: {sc_name} {word}\n", **scenario_markup)
        self.stats.setdefault(cat, []).append(rep)
        return None
