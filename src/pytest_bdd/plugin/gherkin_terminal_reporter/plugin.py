"""
Provide plugin helpers.

Responsibility:
    Provide plugin helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_terminal_reporter.plugin` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - canonical_terminal_step_status: owns nested behavior below this boundary
    - GherkinTerminalReporter: owns nested behavior below this boundary
    - GherkinTerminalReporterPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py: imports or references `plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `plugin`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `plugin`

State and side effects:
    mutates word_markup, word, has_already_failed, cat, letter; depends on typing.cast,
    pytest_bdd.compatibility.pytest.Config, pytest_bdd.compatibility.pytest.TerminalReporter,
    pytest_bdd.compatibility.pytest.TestReport, pytest_bdd.model.scenario_report.ScenarioReportData.

Invariants:
    - `pytest_bdd.plugin.gherkin_terminal_reporter.plugin` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from typing import cast

from pytest_bdd.compatibility.pytest import Config, TerminalReporter, TestReport
from pytest_bdd.model.scenario_report import ScenarioReportData, StepReportData, normalize_runtime_step_status


def canonical_terminal_step_status(step: StepReportData) -> str:
    """
    Get canonical terminal step status.

    Returns:
        Normalized step status string.

    Responsibility:
        Get canonical terminal step status. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.canonical_terminal_step_status` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_runtime_step_status: collaborator call used by this boundary
        - step.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return normalize_runtime_step_status(step.get("status", ""), failed_fallback=step["failed"])


class GherkinTerminalReporter(TerminalReporter):  # mypy limitation with singledispatchmethod/dynamic typing
    """
    Represent gherkin terminal reporter state.

    Responsibility:
        Represent gherkin terminal reporter state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporter` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - pytest_runtest_logreport: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates word_markup, word, has_already_failed, cat, letter.

    Invariants:
        - `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporter` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize the gherkin terminal reporter.

        Responsibility:
            Initialize the gherkin terminal reporter. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporter.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        super().__init__(config)

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """
        Handle the pytest runtest logreport pytest hook.

        Responsibility:
            Handle the pytest runtest logreport pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporter.pytest_runtest_logreport`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._tw.write: collaborator call used by this boundary
            - self.config.hook.pytest_report_teststatus: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - hasattr: collaborator call used by this boundary
            - super.pytest_runtest_logreport: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates word_markup, word, has_already_failed, cat, letter.

        Invariants:
            - `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporter.pytest_runtest_logreport`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
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
            return super().pytest_runtest_logreport(report)  # type: ignore[no-any-return]  # pytest base class is untyped

        scenario = cast("ScenarioReportData", report.scenario)
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


class GherkinTerminalReporterPlugin(
    GherkinTerminalReporter,
):  # mypy limitation with singledispatchmethod/dynamic typing
    """
    Represent gherkin terminal reporter plugin state.

    Responsibility:
        Represent gherkin terminal reporter plugin state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporterPlugin` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_terminal_reporter/entrypoint.py: imports or references
          `GherkinTerminalReporterPlugin`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_terminal_reporter.plugin.GherkinTerminalReporterPlugin` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """
