"""
Project Cucumber Messages execution envelopes into Cucumber JSON scenarios.

Responsibility:
    Correlates Cucumber Messages lifecycle envelopes and projects completed test-case attempts into the legacy
    Cucumber JSON feature/scenario shape used by the JSON and terminal reporting adapters.

Reason for existence:
    Cucumber Messages is the canonical reporting bus, while existing consumers still need Cucumber JSON-compatible
    projections. This store is the single correlation boundary for documents, pickles, test cases, attempts, step
    results, durations, statuses, tags, and feature ordering.

Delegates:
    - `message_converter.envelope_to_dict`: Converts typed Envelope messages at the protocol boundary.
    - `cucumber_json` and `gherkin_terminal_reporter`: Render the completed projections for their respective outputs.
    - Cucumber Messages producers: Supply the lifecycle events and source metadata consumed here.

Cohesion:
    Every helper supports the same message-to-projection pipeline: normalize identifiers, retain lifecycle records,
    correlate a finished attempt, and build one Cucumber JSON scenario element. The store contains no pytest report
    handling or output I/O.

Separation:
    - The message reporter bridge owns event production and transport; this module only correlates envelopes.
    - Legacy pytest `TestReport` compatibility remains in each adapter's fallback path.
    - File writing and terminal styling stay in the reporting plugins rather than this model component.

Main consumers:
    - `LogBDDCucumberJSON`: Writes message-derived feature projections to its configured JSON file.
    - `GherkinTerminalReporter`: Streams finished scenario projections to the terminal.
    - Unit tests and future Cucumber-compatible adapters: Consume the stable `render` and `consume` contract.

State and side effects:
    The store keeps only in-memory correlation maps and ordered feature projections. `consume` mutates that local store;
    it performs no filesystem, pytest, network, or process-global operations.

Invariants:
    - A projection is emitted only after a TestCaseFinished envelope can be correlated to its lifecycle records.
    - Cucumber JSON durations are integer nanoseconds and statuses use lowercase Cucumber JSON spellings.
    - Feature output order follows the first completed message attempt for each feature.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

# The projection helpers share this single model boundary; their short local docstrings avoid repeating the module
# contract for every JSON narrowing helper.
# pylint: disable=missing-responsibility-doc,missing-architecture-score,no-return-none

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import unquote, urlparse

from attrs import define, field

from pytest_bdd.model.message_converter import envelope_to_dict

if TYPE_CHECKING:
    from pytest_bdd.model.message_extension import EventEnvelope
    from pytest_bdd.types.json import JSONObject, JSONValue


def _location(node: JSONObject | None) -> int:
    """Read a Gherkin line number from a raw message node."""
    if not isinstance(node, dict):
        return 1
    location = node.get("location")
    if not isinstance(location, dict):
        return 1
    line = location.get("line", 1)
    return int(line) if isinstance(line, (int, float, str)) else 1


def _uri_key(uri: object) -> str:
    """Normalize a message URI for matching documents and pickles."""
    value = str(uri or "")
    if not value.startswith("file:"):
        return value
    parsed = urlparse(value)
    path = unquote(parsed.path or value.removeprefix("file:"))
    return str(Path(path).resolve())


def _duration(result: JSONObject | None) -> int:
    """Convert a Cucumber duration object to Cucumber JSON nanoseconds."""
    duration = result.get("duration") if isinstance(result, dict) else None
    if not isinstance(duration, dict):
        return 0
    seconds = duration.get("seconds", 0)
    nanos = duration.get("nanos", 0)
    seconds_value = int(seconds) if isinstance(seconds, (int, float, str)) else 0
    nanos_value = int(nanos) if isinstance(nanos, (int, float, str)) else 0
    return seconds_value * 10**9 + nanos_value


def _status(result: JSONObject | None) -> str:
    """Convert a Cucumber step result status to Cucumber JSON spelling."""
    raw_status = result.get("status", "UNKNOWN") if isinstance(result, dict) else "UNKNOWN"
    return str(raw_status).lower()


def _tags(raw_tags: object) -> list[JSONObject]:
    """Convert raw Cucumber tag messages to Cucumber JSON tags."""
    if not isinstance(raw_tags, list):
        return []
    return [{"name": str(tag.get("name", "")), "line": _location(tag)} for tag in raw_tags if isinstance(tag, dict)]


def _dict_list(value: object) -> list[JSONObject]:
    """Narrow an arbitrary JSON value to a list of JSON objects."""
    if not isinstance(value, list):
        return []
    return [cast("JSONObject", item) for item in value if isinstance(item, dict)]


def _string_list(value: object) -> list[str]:
    """Narrow an arbitrary JSON value to a list of string identifiers."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _find_scenario(node: JSONObject, ast_node_ids: set[str]) -> JSONObject | None:
    """Find the scenario AST node referenced by a pickle."""
    feature = node.get("feature")
    if not isinstance(feature, dict):
        return None

    def visit(children: object) -> JSONObject | None:
        if not isinstance(children, list):
            return None
        for child in children:
            if not isinstance(child, dict):
                continue
            scenario = child.get("scenario")
            if isinstance(scenario, dict) and str(scenario.get("id", "")) in ast_node_ids:
                return scenario
            rule = child.get("rule")
            if isinstance(rule, dict):
                found = visit(rule.get("children"))
                if found is not None:
                    return found
        return None

    return visit(feature.get("children"))


def _ast_steps(scenario: JSONObject | None) -> dict[str, JSONObject]:
    """Index scenario AST steps by their message IDs."""
    steps = scenario.get("steps", []) if isinstance(scenario, dict) else []
    return {str(step["id"]): step for step in _dict_list(steps) if "id" in step}


def _step_result(result: JSONObject | None) -> JSONObject:
    """Build a Cucumber JSON result from a TestStepResult message."""
    output: JSONObject = {"status": _status(result), "duration": _duration(result)}
    if isinstance(result, dict):
        message = result.get("message")
        exception = result.get("exception")
        if message is None and isinstance(exception, dict):
            message = exception.get("message") or exception.get("stackTrace")
        if message is not None:
            output["error_message"] = str(message)
    return output


def _feature_id(uri: str, name: str) -> str:
    """Build the stable legacy Cucumber JSON feature identifier."""
    return (uri or name).lower().replace(" ", "-")


@define
class CucumberMessageReportStore:
    """Accumulate Cucumber Messages and expose Cucumber JSON projections."""

    documents: dict[str, JSONObject] = field(factory=dict)
    pickles: dict[str, JSONObject] = field(factory=dict)
    test_cases: dict[str, JSONObject] = field(factory=dict)
    attempts: dict[str, JSONObject] = field(factory=dict)
    step_results: dict[tuple[str, str], JSONObject] = field(factory=dict)
    features: dict[str, JSONObject] = field(factory=dict)
    feature_order: list[str] = field(factory=list)

    def consume(self, message: EventEnvelope) -> JSONObject | None:
        """Consume one Envelope and return a finished scenario projection when available."""
        envelope = envelope_to_dict(message)
        if "gherkinDocument" in envelope:
            document = cast("JSONObject", envelope["gherkinDocument"])
            self.documents[_uri_key(document.get("uri"))] = document
        elif "pickle" in envelope:
            pickle = cast("JSONObject", envelope["pickle"])
            self.pickles[str(pickle.get("id", ""))] = pickle
        elif "testCase" in envelope:
            test_case = cast("JSONObject", envelope["testCase"])
            self.test_cases[str(test_case.get("id", ""))] = test_case
        elif "testCaseStarted" in envelope:
            started = cast("JSONObject", envelope["testCaseStarted"])
            self.attempts[str(started.get("id", ""))] = started
        elif "testStepFinished" in envelope:
            finished = cast("JSONObject", envelope["testStepFinished"])
            self.step_results[
                str(finished.get("testCaseStartedId", "")),
                str(finished.get("testStepId", "")),
            ] = cast("JSONObject", finished.get("testStepResult", {}))
        elif "testCaseFinished" in envelope:
            finished = cast("JSONObject", envelope["testCaseFinished"])
            return self._finish_attempt(str(finished.get("testCaseStartedId", "")))
        return None

    def _finish_attempt(self, attempt_id: str) -> JSONObject | None:
        """Project one finished test-case attempt into a Cucumber JSON element."""
        started = self.attempts.get(attempt_id)
        if started is None:
            return None
        test_case = self.test_cases.get(str(started.get("testCaseId", "")))
        if test_case is None:
            return None
        pickle = self.pickles.get(str(test_case.get("pickleId", "")))
        if pickle is None:
            return None
        document = self.documents.get(_uri_key(pickle.get("uri")), {})
        feature_node = document.get("feature") if isinstance(document, dict) else None
        feature = feature_node if isinstance(feature_node, dict) else {}
        uri = _uri_key(document.get("uri") if isinstance(document, dict) else pickle.get("uri"))
        feature_name = str(feature.get("name") or uri)
        feature_key = uri or feature_name
        if feature_key not in self.features:
            self.feature_order.append(feature_key)
            self.features[feature_key] = {
                "keyword": str(feature.get("keyword") or "Feature"),
                "uri": uri,
                "name": feature_name,
                "id": _feature_id(uri, feature_name),
                "line": _location(feature),
                "description": str(feature.get("description") or ""),
                "tags": cast("JSONValue", _tags(feature.get("tags"))),
                "elements": cast("JSONValue", []),
            }
        scenario = self._scenario_element(pickle, test_case, attempt_id, document, feature)
        cast("list[JSONObject]", self.features[feature_key]["elements"]).append(scenario)
        return {"feature": self.features[feature_key], "scenario": scenario}

    def _scenario_element(
        self,
        pickle: JSONObject,
        test_case: JSONObject,
        attempt_id: str,
        document: JSONObject,
        feature: JSONObject,
    ) -> JSONObject:
        """Build a Cucumber JSON scenario element from pickle lifecycle messages."""
        ast_node_ids = set(_string_list(pickle.get("astNodeIds")))
        scenario_ast = _find_scenario(document, ast_node_ids)
        ast_steps = _ast_steps(scenario_ast)
        step_elements: list[JSONObject] = []
        test_steps = _dict_list(test_case.get("testSteps"))
        pickle_steps = _dict_list(pickle.get("steps"))
        for pickle_step in pickle_steps:
            pickle_step_id = str(pickle_step.get("id", ""))
            ast_step = next(
                (ast_steps[ast_id] for ast_id in _string_list(pickle_step.get("astNodeIds")) if ast_id in ast_steps),
                {},
            )
            test_step = next(
                (candidate for candidate in test_steps if str(candidate.get("pickleStepId", "")) == pickle_step_id),
                {},
            )
            test_step_id = str(test_step.get("id", ""))
            result = self.step_results.get((attempt_id, test_step_id))
            step_elements.append(
                {
                    "keyword": str(ast_step.get("keyword") or ""),
                    "name": str(pickle_step.get("text") or ast_step.get("text") or ""),
                    "line": _location(ast_step),
                    "match": {"location": ""},
                    "result": _step_result(result),
                },
            )
        scenario = scenario_ast or {}
        scenario_name = str(pickle.get("name") or scenario.get("name") or "")
        return {
            "keyword": str(scenario.get("keyword") or "Scenario"),
            "id": str(pickle.get("id") or scenario_name),
            "name": scenario_name,
            "line": _location(scenario or None),
            "description": str(scenario.get("description") or ""),
            "tags": cast("JSONValue", _tags(pickle.get("tags") or feature.get("tags"))),
            "type": "scenario",
            "steps": cast("JSONValue", step_elements),
        }

    def render(self) -> list[JSONObject]:
        """Return completed features in stable message-stream order."""
        return [self.features[key] for key in self.feature_order]
