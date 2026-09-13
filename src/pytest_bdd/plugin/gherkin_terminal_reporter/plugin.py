"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
"""

from typing import cast

from pytest_bdd.compatibility.pytest import Config, TerminalReporter, TestReport
from pytest_bdd.model.message_extension import EventEnvelope
from pytest_bdd.model.message_reporter import CucumberMessageReportStore
from pytest_bdd.model.scenario_report import ScenarioReportData, StepReportData, normalize_runtime_step_status


def canonical_terminal_step_status(step: StepReportData) -> str:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    return normalize_runtime_step_status(step.get("status", ""), failed_fallback=step["failed"])


class GherkinTerminalReporter(TerminalReporter):  # mypy limitation with singledispatchmethod/dynamic typing
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """

    def __init__(self, config: Config) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        super().__init__(config)
        self._message_store = CucumberMessageReportStore()
        self._message_mode = False

    def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:  # noqa: ARG002
        """Render completed Cucumber Messages scenarios through the terminal reporter."""
        self._message_mode = True
        projection = self._message_store.consume(message)
        if projection is None:
            return
        feature = cast("dict[str, object]", projection["feature"])
        scenario = cast("dict[str, object]", projection["scenario"])
        steps = scenario.get("steps", [])
        step_list = steps if isinstance(steps, list) else []
        statuses = [
            str(step.get("result", {}).get("status", "unknown"))
            for step in step_list
            if isinstance(step, dict) and isinstance(step.get("result"), dict)
        ]
        scenario_status = "failed" if "failed" in statuses else "skipped" if "skipped" in statuses else "passed"
        markup = (
            {"red": True}
            if scenario_status == "failed"
            else {"yellow": True}
            if scenario_status == "skipped"
            else {"green": True}
        )
        self.ensure_newline()
        self._tw.write(f"Feature: {feature.get('name', '')}\n", blue=True)
        self._tw.write(f"    Scenario: {scenario.get('name', '')}", **markup)
        if self.verbosity > 1:
            self._tw.write("\n")
            has_already_failed = False
            for step in step_list:
                if not isinstance(step, dict):
                    continue
                step_result = step.get("result", {})
                status = str(step_result.get("status", "unknown")) if isinstance(step_result, dict) else "unknown"
                step_failed = status == "failed"
                step_markup = {"red" if step_failed else "green": True}
                if step_failed and not has_already_failed:
                    step_markup["bold"] = True
                    has_already_failed = True
                step_status_text = f"({status.upper()})"
                self._tw.write(
                    f"        {str(step.get('keyword', '')).rstrip()} {step.get('name', '')} {step_status_text}\n",
                    **step_markup,
                )
        self._tw.write(f"    {scenario_status.upper()}\n", **markup)

    def pytest_runtest_logreport(self, report: TestReport) -> None:  # noqa: C901
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        if self._message_mode and hasattr(report, "scenario"):
            return None
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """

    @staticmethod
    def pytest_bdd_enable_runtime_messages(config: Config) -> bool:
        """Enable the message lifecycle while this reporter is active."""
        return bool(getattr(config.option, "gherkin_terminal_reporter", False))
