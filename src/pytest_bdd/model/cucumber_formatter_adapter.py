"""
Provide cucumber formatter adapter helpers.

Responsibility:
    Provide cucumber formatter adapter helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.cucumber_formatter_adapter` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _FormatterAttemptState: owns nested behavior below this boundary
    - CucumberFormatterEnvelopeAdapter: owns nested behavior below this boundary
    - normalize_formatter_envelope_dicts: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
      `cucumber_formatter_adapter`
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `cucumber_formatter_adapter`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
      `cucumber_formatter_adapter`

State and side effects:
    mutates test_case_id, synthetic_envelopes, test_case, test_step_id, attempt_state; depends on
    __future__.annotations, typing.TYPE_CHECKING, attrs.define, attrs.field, pytest_bdd.types.json.JSONArray.

Invariants:
    - `pytest_bdd.model.cucumber_formatter_adapter` keeps its documented import path, ownership boundary, and observable
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

from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONArray, JSONObject, JSONValue

_ZERO_DURATION = {"seconds": 0, "nanos": 0}
_ZERO_TIMESTAMP = {"seconds": 0, "nanos": 0}


@define
class _FormatterAttemptState:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.cucumber_formatter_adapter._FormatterAttemptState` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.cucumber_formatter_adapter._FormatterAttemptState`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_FormatterAttemptState`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_FormatterAttemptState`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_FormatterAttemptState`

    State and side effects:
        mutates test_case_id, recorded_test_step_ids.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_adapter._FormatterAttemptState` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    test_case_id: str
    recorded_test_step_ids: set[str] = field(factory=set)


class CucumberFormatterEnvelopeAdapter:
    """
    Normalize schema-valid streams for stricter upstream formatter assumptions.

    Responsibility:
        Normalize schema-valid streams for stricter upstream formatter assumptions. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - adapt_envelope_dict: owns nested behavior below this boundary
        - flush: owns nested behavior below this boundary
        - _record_test_step_result: owns nested behavior below this boundary
        - _synthesize_missing_pickle_step_results: owns nested behavior below this boundary
        - _normalize_timestamp: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `CucumberFormatterEnvelopeAdapter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `CucumberFormatterEnvelopeAdapter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `CucumberFormatterEnvelopeAdapter`

    State and side effects:
        mutates synthetic_envelopes, test_case, test_case_id, test_step_id, attempt_state.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    def __init__(self) -> None:
        """
        Initialize the cucumber formatter envelope adapter.

        Responsibility:
            Initialize the cucumber formatter envelope adapter. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            mutates self._test_cases_by_id, self._attempts_by_started_id.

        Invariants:
            - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter.__init__` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self._test_cases_by_id: dict[str, JSONObject] = {}
        self._attempts_by_started_id: dict[str, _FormatterAttemptState] = {}

    def adapt_envelope_dict(self, envelope_dict: JSONObject) -> tuple[JSONObject, ...]:
        """
        Process envelope dict, injecting synthetic step results.

        Returns:
            A tuple of processed envelope dicts.

        Responsibility:
            Process envelope dict, injecting synthetic step results. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter.adapt_envelope_dict` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - envelope_dict.get: collaborator call used by this boundary
            - test_case_started.get: collaborator call used by this boundary
            - synthetic_envelopes.extend: collaborator call used by this boundary
            - test_case_finished.get: collaborator call used by this boundary
            - test_case.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py: imports or references
              `adapt_envelope_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `adapt_envelope_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `adapt_envelope_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `adapt_envelope_dict`

        State and side effects:
            mutates test_case_id, synthetic_envelopes, test_case, test_case_started, started_id.

        Invariants:
            - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter.adapt_envelope_dict` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        synthetic_envelopes: list[JSONObject] = []

        test_case = envelope_dict.get("testCase")
        if isinstance(test_case, dict):
            test_case_id = test_case.get("id")
            if isinstance(test_case_id, str) and test_case_id:
                self._test_cases_by_id[test_case_id] = test_case
        else:
            test_case_started = envelope_dict.get("testCaseStarted")
            if isinstance(test_case_started, dict):
                started_id = test_case_started.get("id")
                test_case_id = test_case_started.get("testCaseId")
                if isinstance(started_id, str) and started_id and isinstance(test_case_id, str) and test_case_id:
                    self._attempts_by_started_id[started_id] = _FormatterAttemptState(test_case_id=test_case_id)
            else:
                test_step_finished = envelope_dict.get("testStepFinished")
                if isinstance(test_step_finished, dict):
                    self._record_test_step_result(test_step_finished)
                else:
                    test_case_finished = envelope_dict.get("testCaseFinished")
                    if isinstance(test_case_finished, dict):
                        synthetic_envelopes.extend(
                            self._synthesize_missing_pickle_step_results(
                                test_case_started_id=str(test_case_finished.get("testCaseStartedId") or ""),
                                timestamp_payload=test_case_finished.get("timestamp"),
                            ),
                        )
                    else:
                        test_run_finished = envelope_dict.get("testRunFinished")
                        if isinstance(test_run_finished, dict):
                            synthetic_envelopes.extend(self.flush(timestamp_payload=test_run_finished.get("timestamp")))

        return (*synthetic_envelopes, envelope_dict)

    def flush(self, *, timestamp_payload: object | None = None) -> tuple[JSONObject, ...]:
        """
        Emit synthetic step-finished envelopes for any test attempts that were not properly closed by the stream.

        Returns:
            A tuple of synthetic testStepFinished envelopes for all unclosed attempts.

        Responsibility:
            Emit synthetic step-finished envelopes for any test attempts that were not properly closed by the stream. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter.flush` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - synthetic_envelopes.extend: collaborator call used by this boundary
            - self._synthesize_missing_pickle_step_results: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `flush`

        State and side effects:
            mutates synthetic_envelopes.

        Invariants:
            - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter.flush` keeps its documented
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
            #arch-eval:locational_stability=4

        """
        synthetic_envelopes: list[JSONObject] = []
        for test_case_started_id in list(self._attempts_by_started_id):
            synthetic_envelopes.extend(
                self._synthesize_missing_pickle_step_results(
                    test_case_started_id=test_case_started_id,
                    timestamp_payload=timestamp_payload,
                ),
            )
        return tuple(synthetic_envelopes)

    def _record_test_step_result(self, test_step_finished: JSONObject) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._record_test_step_result` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._record_test_step_result`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - test_step_finished.get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - self._attempts_by_started_id.get: collaborator call used by this boundary
            - attempt_state.recorded_test_step_ids.add: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_record_test_step_result`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_record_test_step_result`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_record_test_step_result`

        State and side effects:
            mutates test_case_started_id, test_step_id, attempt_state.

        Invariants:
            - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._record_test_step_result`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        test_case_started_id = test_step_finished.get("testCaseStartedId")
        test_step_id = test_step_finished.get("testStepId")
        if not isinstance(test_case_started_id, str) or not test_case_started_id:
            return
        if not isinstance(test_step_id, str) or not test_step_id:
            return
        attempt_state = self._attempts_by_started_id.get(test_case_started_id)
        if attempt_state is None:
            return
        attempt_state.recorded_test_step_ids.add(test_step_id)

    def _synthesize_missing_pickle_step_results(
        self,
        *,
        test_case_started_id: str,
        timestamp_payload: object | None,
    ) -> list[JSONObject]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._synthesize_missing_pickle_step_results`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._synthesize_missing_pickle_step_results`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - test_step.get: collaborator call used by this boundary
            - dict: collaborator call used by this boundary
            - self._attempts_by_started_id.get: collaborator call used by this boundary
            - self._test_cases_by_id.get: collaborator call used by this boundary
            - self._normalize_timestamp: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_synthesize_missing_pickle_step_results`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_synthesize_missing_pickle_step_results`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_synthesize_missing_pickle_step_results`

        State and side effects:
            mutates attempt_state, test_case, resolved_timestamp, synthetic_envelopes, raw_test_steps.

        Invariants:
            - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._synthesize_missing_pickle_step_results`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if not test_case_started_id:
            return []
        attempt_state = self._attempts_by_started_id.get(test_case_started_id)
        if attempt_state is None:
            return []
        test_case = self._test_cases_by_id.get(attempt_state.test_case_id)
        if test_case is None:
            return []
        resolved_timestamp = self._normalize_timestamp(timestamp_payload)
        synthetic_envelopes: list[JSONObject] = []
        raw_test_steps = test_case.get("testSteps", [])
        test_steps = raw_test_steps if isinstance(raw_test_steps, list) else []
        for test_step in test_steps:
            if not isinstance(test_step, dict):
                continue
            test_step_id = test_step.get("id")
            pickle_step_id = test_step.get("pickleStepId")
            if not isinstance(test_step_id, str) or not test_step_id:
                continue
            if not isinstance(pickle_step_id, str) or not pickle_step_id:
                continue
            if test_step_id in attempt_state.recorded_test_step_ids:
                continue
            synthetic_envelopes.append(
                {
                    "testStepFinished": {
                        "testCaseStartedId": test_case_started_id,
                        "testStepId": test_step_id,
                        "timestamp": dict(resolved_timestamp),
                        "testStepResult": {
                            "duration": dict(_ZERO_DURATION),
                            "status": "UNKNOWN",
                        },
                    },
                },
            )
            attempt_state.recorded_test_step_ids.add(test_step_id)
        return synthetic_envelopes

    @staticmethod
    def _normalize_timestamp(timestamp_payload: object | None) -> dict[str, int]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._normalize_timestamp` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._normalize_timestamp` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - timestamp_payload.get: collaborator call used by this boundary
            - int: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_normalize_timestamp`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_normalize_timestamp`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_normalize_timestamp`

        State and side effects:
            mutates seconds, nanos.

        Invariants:
            - `pytest_bdd.model.cucumber_formatter_adapter.CucumberFormatterEnvelopeAdapter._normalize_timestamp` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if not isinstance(timestamp_payload, dict):
            return dict(_ZERO_TIMESTAMP)
        seconds = timestamp_payload.get("seconds")
        nanos = timestamp_payload.get("nanos")
        return {
            "seconds": int(seconds or 0),
            "nanos": int(nanos or 0),
        }


def normalize_formatter_envelope_dicts(envelope_dicts: JSONArray) -> JSONArray:
    """
    Pass NDJSON stream through adapter to ensure all test steps are accounted for.

    Returns:
        A JSON array of normalized envelope dicts.

    Responsibility:
        Pass NDJSON stream through adapter to ensure all test steps are accounted for. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.cucumber_formatter_adapter.normalize_formatter_envelope_dicts` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalized_envelopes.extend: collaborator call used by this boundary
        - CucumberFormatterEnvelopeAdapter: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - adapter.adapt_envelope_dict: collaborator call used by this boundary
        - adapter.flush: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `normalize_formatter_envelope_dicts`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `normalize_formatter_envelope_dicts`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `normalize_formatter_envelope_dicts`

    State and side effects:
        mutates adapter, normalized_envelopes.

    Invariants:
        - `pytest_bdd.model.cucumber_formatter_adapter.normalize_formatter_envelope_dicts` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    adapter = CucumberFormatterEnvelopeAdapter()
    normalized_envelopes: list[JSONValue] = []
    for envelope_dict in envelope_dicts:
        if not isinstance(envelope_dict, dict):
            continue
        normalized_envelopes.extend(adapter.adapt_envelope_dict(envelope_dict))
    normalized_envelopes.extend(adapter.flush())
    return normalized_envelopes
