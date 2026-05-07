from typing import cast

from pytest_bdd.compatibility.pytest import Config, TerminalReporter, TestReport
from pytest_bdd.plugin.scenario_reporter.report import ScenarioReportData, StepReportData, normalize_runtime_step_status


def canonical_terminal_step_status(step: StepReportData) -> str:
    return normalize_runtime_step_status(step["status"], failed_fallback=step["failed"])


class GherkinTerminalReporter(TerminalReporter):  # type: ignore[misc]
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        cat, letter, word = self.config.hook.pytest_report_teststatus(report=report, config=self.config)

        if not letter and not word:
            # probably passed setup/teardown
            return None

        if isinstance(word, tuple):
            word, word_markup = word
        elif report.passed:
            word_markup = {"green": True}
        elif report.failed:
            word_markup = {"red": True}
        elif report.skipped:
            word_markup = {"yellow": True}
        scenario_markup = word_markup

        if self.verbosity <= 0 or not hasattr(report, "scenario"):
            return super().pytest_runtest_logreport(report)

        scenario = cast(ScenarioReportData, report.scenario)
        self.ensure_newline()
        self._tw.write(f"Feature: {scenario['feature']['name']}\n", blue=True)
        self._tw.write(f"    Scenario: {scenario['name']}", **scenario_markup)
        if self.verbosity > 1:
            self._tw.write("\n")
            has_already_failed = False
            for step in scenario["steps"]:
                step_status = canonical_terminal_step_status(step)
                step_failed = step_status == "failed"
                step_markup = {"red" if step_failed else "green": True}
                # Highlight first failed step
                if step_failed and not has_already_failed:
                    step_markup["bold"] = True
                    has_already_failed = True
                step_status_text = "(FAILED)" if step_failed else "(PASSED)"
                self._tw.write(
                    f"        {step['keyword']} {step['name']} {step_status_text}\n",
                    **step_markup,
                )
        self._tw.write(f"    {word}\n", **word_markup)
        self.stats.setdefault(cat, []).append(report)
        return None
