"""
Provide plugin helpers.

Responsibility:
    Provide plugin helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json.plugin` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - LogBDDCucumberJSON: owns nested behavior below this boundary
    - CucumberJsonPlugin: owns nested behavior below this boundary

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
    mutates result, error_message, self.logfile, self.features, raw_duration; depends on json, math, os, time,
    pathlib.Path.

Invariants:
    - `pytest_bdd.plugin.cucumber_json.plugin` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

import json
import math
import os
import time
from pathlib import Path
from typing import cast

from pytest_bdd.compatibility.pytest import TerminalReporter, TestReport
from pytest_bdd.plugin.cucumber_json.model import Feature
from pytest_bdd.types.json import JSONArray, JSONObject


class LogBDDCucumberJSON:
    """
    Logging plugin for cucumber like json output.

    Responsibility:
        Logging plugin for cucumber like json output. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _get_result: owns nested behavior below this boundary
        - _serialize_tags: owns nested behavior below this boundary
        - pytest_runtest_logreport: owns nested behavior below this boundary
        - pytest_sessionstart: owns nested behavior below this boundary
        - pytest_sessionfinish: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates result, error_message, self.logfile, self.features, raw_duration.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    def __init__(self, logfile: str) -> None:
        """
        Initialize the log bddcucumber json.

        Responsibility:
            Initialize the log bddcucumber json. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.__init__` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - Path.expanduser.resolve: collaborator call used by this boundary
            - Path.expanduser: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - os.path.expandvars: collaborator call used by this boundary

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
            mutates self.logfile, self.features.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.__init__` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.logfile = Path(os.path.expandvars(logfile)).expanduser().resolve()
        self.features: dict[str, JSONObject] = {}

    @staticmethod
    def _get_result(step: JSONObject, report: TestReport, *, error_message: bool = False) -> JSONObject:
        """
        Get scenario test run result.

        Args:
            step: Step we get result for.
            report: Pytest Report object.
            error_message: Whether to include error message.

        Returns:
            Dict in form {"status": "<passed|failed|skipped>", ["error_message": "<error_message>"]}.

        Responsibility:
            Get scenario test run result. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON._get_result` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - step.get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - float: collaborator call used by this boundary
            - math.floor: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates result, raw_duration, duration.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON._get_result` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        result: JSONObject = {}
        if report.passed or not step["failed"]:  # ignore setup/teardown
            result = {"status": "passed"}
        elif report.failed and step["failed"]:
            result = {
                "status": "failed",
                "error_message": str(report.longrepr) if error_message else "",
            }
        elif report.skipped:
            result = {"status": "skipped"}
        raw_duration = step.get("duration", 0)
        duration = float(raw_duration) if isinstance(raw_duration, (str, int, float)) else 0.0
        result["duration"] = math.floor((10**9) * duration)  # nanosec
        return result

    @staticmethod
    def _serialize_tags(item: JSONObject) -> JSONArray:
        """
        Serialize item's tags.

        Args:
            item: JSON-serialized Scenario or Feature.

        Returns:
            List of dicts in the form of [{"name": "<tag>", "line": 2}, ...].

        Responsibility:
            Serialize item's tags. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON._serialize_tags` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - item.get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - int: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates raw_tags, tags, line_number, line.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON._serialize_tags` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        raw_tags = item.get("tags", [])
        tags = raw_tags if isinstance(raw_tags, list) else []
        line_number = item.get("line_number", 1)
        line = int(line_number) if isinstance(line_number, (str, int, float)) else 1
        return cast("JSONArray", [{"name": str(tag), "line": line - 1} for tag in tags])

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """
        Handle the pytest runtest logreport pytest hook.

        Responsibility:
            Handle the pytest runtest logreport pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_runtest_logreport` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - stepmap: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py: imports or references
              `pytest_runtest_logreport`

        State and side effects:
            mutates error_message, scenario, step_name, feature, feature_filename.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_runtest_logreport` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        try:
            scenario = cast("JSONObject", report.scenario)
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not scenario["steps"] or report.when != "call":
            # skip if there isn't a result or scenario has no steps
            return

        def stepmap(step: JSONObject) -> JSONObject:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_runtest_logreport.stepmap` owns
                documented method behavior. It directly owns the observable contract, local decisions, and maintenance
                boundary for this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_runtest_logreport.stepmap` because it
                keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - scenario.setdefault: collaborator call used by this boundary
                - self._get_result: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - None found by static import/name scan; verify dynamic use before refactor

            State and side effects:
                mutates error_message, step_name.

            Invariants:
                - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_runtest_logreport.stepmap` keeps its
                  documented import path, ownership boundary, and observable behavior stable for callers.

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
            error_message = False
            if step["failed"] and not scenario.setdefault("failed", False):
                scenario["failed"] = True
                error_message = True

            step_name = step["name"]

            return {
                "keyword": step["keyword"],
                "name": step_name,
                "line": step["line_number"],
                "match": {"location": ""},
                "result": self._get_result(step, report, error_message=error_message),
            }

        feature = cast("JSONObject", scenario["feature"])
        feature_filename = str(feature["filename"])
        if feature_filename not in self.features:
            self.features[feature_filename] = {
                "keyword": "Feature",
                "uri": feature["rel_filename"],
                "name": feature["name"] or feature["rel_filename"],
                "id": str(feature["rel_filename"]).lower().replace(" ", "-"),
                "line": feature["line_number"],
                "description": feature["description"],
                "tags": self._serialize_tags(feature),
                "elements": [],
            }

        elements = cast("JSONArray", self.features[feature_filename]["elements"])
        raw_steps = scenario["steps"]
        steps = raw_steps if isinstance(raw_steps, list) else []
        elements.append(
            {
                "keyword": "Scenario",
                "id": report.item["name"],
                "name": scenario["name"],
                "line": scenario["line_number"],
                "description": "",
                "tags": self._serialize_tags(scenario),
                "type": "scenario",
                "steps": cast("JSONArray", [stepmap(cast("JSONObject", step)) for step in steps]),
            },
        )

    def pytest_sessionstart(self) -> None:
        """
        Handle the pytest sessionstart pytest hook.

        Responsibility:
            Handle the pytest sessionstart pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_sessionstart` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - time.time: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_sessionstart`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_sessionstart`

        State and side effects:
            mutates self.suite_start_time.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_sessionstart` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self) -> None:
        """
        Handle the pytest sessionfinish pytest hook.

        Responsibility:
            Handle the pytest sessionfinish pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_sessionfinish` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.features.values: collaborator call used by this boundary
            - Feature.model_validate: collaborator call used by this boundary
            - Path.write_text: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - list: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_sessionfinish`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_sessionfinish`

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
            #arch-eval:locational_stability=3
        """
        for feature in self.features.values():
            Feature.model_validate(feature)
        Path(self.logfile).write_text(json.dumps(list(self.features.values())), encoding="utf-8")

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        """
        Handle the pytest terminal summary pytest hook.

        Responsibility:
            Handle the pytest terminal summary pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json.plugin.LogBDDCucumberJSON.pytest_terminal_summary` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - terminalreporter.write_sep: collaborator call used by this boundary

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
        terminalreporter.write_sep("-", f"generated json file: {self.logfile}")


class CucumberJsonPlugin(LogBDDCucumberJSON):
    """
    Represent cucumber json plugin state.

    Responsibility:
        Represent cucumber json plugin state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.plugin.CucumberJsonPlugin` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `CucumberJsonPlugin`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.plugin.CucumberJsonPlugin` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
