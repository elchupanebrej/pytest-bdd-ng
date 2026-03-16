from __future__ import annotations

from typing import Any

from attrs import define, field

_ZERO_DURATION = {"seconds": 0, "nanos": 0}
_ZERO_TIMESTAMP = {"seconds": 0, "nanos": 0}


@define
class _FormatterAttemptState:
    test_case_id: str
    recorded_test_step_ids: set[str] = field(factory=set)


class CucumberFormatterEnvelopeAdapter:
    """Normalize schema-valid streams for stricter upstream formatter assumptions.

    The canonical pytest-bdd-ng NDJSON stream remains untouched. This adapter is
    formatter-only compatibility glue for `@cucumber/cucumber`, whose formatter
    helpers assume every pickle-backed `testCase.testSteps[*].id` resolves to a
    `stepResults` entry by render time. That stronger invariant is not required
    by the message schema and has been observed to crash formatter helpers such
    as `summary_helpers.js`, `usage_helpers`, and `json_formatter` in
    `@cucumber/cucumber` 11.3.0. Keep this normalization until upstream tolerates
    missing step results or the reporter guarantees that stronger invariant.
    """

    def __init__(self) -> None:
        self._test_cases_by_id: dict[str, dict[str, Any]] = {}
        self._attempts_by_started_id: dict[str, _FormatterAttemptState] = {}

    def adapt_envelope_dict(self, envelope_dict: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        synthetic_envelopes: list[dict[str, Any]] = []

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
                            )
                        )
                    elif isinstance(envelope_dict.get("testRunFinished"), dict):
                        synthetic_envelopes.extend(
                            self.flush(timestamp_payload=envelope_dict["testRunFinished"].get("timestamp"))
                        )

        return (*synthetic_envelopes, envelope_dict)

    def flush(self, *, timestamp_payload: object | None = None) -> tuple[dict[str, Any], ...]:
        synthetic_envelopes: list[dict[str, Any]] = []
        for test_case_started_id in list(self._attempts_by_started_id):
            synthetic_envelopes.extend(
                self._synthesize_missing_pickle_step_results(
                    test_case_started_id=test_case_started_id,
                    timestamp_payload=timestamp_payload,
                )
            )
        return tuple(synthetic_envelopes)

    def _record_test_step_result(self, test_step_finished: dict[str, Any]) -> None:
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
    ) -> list[dict[str, Any]]:
        if not test_case_started_id:
            return []
        attempt_state = self._attempts_by_started_id.get(test_case_started_id)
        if attempt_state is None:
            return []
        test_case = self._test_cases_by_id.get(attempt_state.test_case_id)
        if test_case is None:
            return []
        resolved_timestamp = self._normalize_timestamp(timestamp_payload)
        synthetic_envelopes: list[dict[str, Any]] = []
        for test_step in test_case.get("testSteps", ()):
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
                    }
                }
            )
            attempt_state.recorded_test_step_ids.add(test_step_id)
        return synthetic_envelopes

    @staticmethod
    def _normalize_timestamp(timestamp_payload: object | None) -> dict[str, int]:
        if not isinstance(timestamp_payload, dict):
            return dict(_ZERO_TIMESTAMP)
        seconds = timestamp_payload.get("seconds")
        nanos = timestamp_payload.get("nanos")
        return {
            "seconds": int(seconds or 0),
            "nanos": int(nanos or 0),
        }


def normalize_formatter_envelope_dicts(envelope_dicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adapter = CucumberFormatterEnvelopeAdapter()
    normalized_envelopes: list[dict[str, Any]] = []
    for envelope_dict in envelope_dicts:
        normalized_envelopes.extend(adapter.adapt_envelope_dict(envelope_dict))
    normalized_envelopes.extend(adapter.flush())
    return normalized_envelopes
