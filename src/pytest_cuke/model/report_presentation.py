"""Shared preparation of Messages for live and replay report consumers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pytest_cuke.const import (
    PYTEST_OUTCOME_MEDIA_TYPE,
    PYTEST_SOURCE_MEDIA_TYPE,
    PYTEST_STEP_OUTCOME_MEDIA_TYPE,
)


def resolve_report_policy(
    preset: str,
    *,
    xfail_as_failed: bool | None = None,
    skip_as_failed: bool | None = None,
    tolerated_as_failed: bool | None = None,
    wip_as_failed: bool | None = None,
) -> dict[str, bool]:
    """Apply explicit category choices over a shared report preset."""
    if preset not in {"normal", "diagnostic"}:
        raise ValueError(f"Unknown report policy: {preset}")
    diagnostic = preset == "diagnostic"
    return {
        name: diagnostic if value is None else value
        for name, value in {
            "xfail_as_failed": xfail_as_failed,
            "skip_as_failed": skip_as_failed,
            "tolerated_as_failed": tolerated_as_failed,
            "wip_as_failed": wip_as_failed,
        }.items()
    }


if TYPE_CHECKING:
    from collections.abc import Mapping


def is_report_metadata(envelope: Mapping[str, Any]) -> bool:
    """Identify internal outcome metadata retained in the canonical event stream."""
    attachment = envelope.get("attachment")
    return isinstance(attachment, dict) and attachment.get("mediaType") in {
        PYTEST_OUTCOME_MEDIA_TYPE,
        PYTEST_STEP_OUTCOME_MEDIA_TYPE,
        PYTEST_SOURCE_MEDIA_TYPE,
    }


class ReportPresentation:
    """Prepare report events while keeping the saved execution stream unchanged."""

    def __init__(
        self,
        *,
        retain_metadata: bool = False,
        xfail_as_failed: bool = False,
        skip_as_failed: bool = False,
        tolerated_as_failed: bool = False,
        wip_as_failed: bool = False,
    ) -> None:
        self._retain_metadata = retain_metadata
        self._xfail_as_failed = xfail_as_failed
        self._skip_as_failed = skip_as_failed
        self._tolerated_as_failed = tolerated_as_failed
        self._wip_as_failed = wip_as_failed
        self._wip_attempts: set[str] = set()
        self._step_outcomes: dict[tuple[str, str], dict[str, Any]] = {}
        self._pending: dict[str, list[dict[str, Any]]] = {}
        self._outcomes: dict[str, dict[str, Any]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._completed_outcomes: dict[str, dict[str, Any]] = {}

    def accept(self, envelope: dict[str, Any]) -> list[dict[str, Any]]:
        if is_report_metadata(envelope):
            return self._accept_metadata(envelope)

        if "testRunFinished" in envelope:
            pending = [item for group in self._pending.values() for item in group]
            pending_metadata = list(self._metadata.values())
            self._pending.clear()
            self._outcomes.clear()
            self._metadata.clear()
            self._wip_attempts.clear()
            return [*pending, *pending_metadata, envelope]

        payload: Any = next(iter(envelope.values()), {})
        attempt_id = payload.get("testCaseStartedId") if isinstance(payload, dict) else None
        if not isinstance(attempt_id, str):
            return [envelope]

        if "testCaseFinished" in envelope:
            pending = self._pending.pop(attempt_id, [])
            outcome = self._outcomes.pop(attempt_id, {})
            wip_attempt = attempt_id in self._wip_attempts
            self._wip_attempts.discard(attempt_id)
            if outcome and wip_attempt:
                outcome = {**outcome, "wip": True}
            if outcome:
                self._completed_outcomes[attempt_id] = outcome
            metadata = self._metadata.pop(attempt_id, None)
            if (
                outcome.get("outcome") == "skip"
                and self._skip_as_failed
                and not wip_attempt
                and not self._retain_metadata
            ):
                pending = [self._diagnostic_skip(item, outcome) for item in pending]
            elif outcome.get("outcome") == "xfail" and self._xfail_as_failed and not self._retain_metadata:
                pending = [self._diagnostic_xfail(item, outcome) for item in pending]
            elif outcome.get("outcome") == "xfail":
                if metadata is not None:
                    actual_results = [
                        {"testStepId": step["testStepId"], "result": step["testStepResult"]}
                        for item in pending
                        if isinstance((step := item.get("testStepFinished")), dict)
                        and step.get("testStepResult", {}).get("status") == "FAILED"
                    ]
                    if actual_results:
                        outcome = {**outcome, "actualStepResults": actual_results}
                        metadata = {
                            **metadata,
                            "attachment": {**metadata["attachment"], "body": json.dumps(outcome, ensure_ascii=False)},
                        }
                pending = [self._expected_failure(item, outcome) for item in pending]
            return [*pending, *([metadata] if metadata is not None else []), envelope]

        step_finished = envelope.get("testStepFinished")
        if isinstance(step_finished, dict):
            step_id = step_finished.get("testStepId")
            actual = self._step_outcomes.pop((attempt_id, step_id), None) if isinstance(step_id, str) else None
            diagnostic = (
                self._wip_as_failed if actual and actual.get("outcome") == "wip-skipped" else self._tolerated_as_failed
            )
            if actual is not None and diagnostic:
                result_key = "diagnosticResult" if actual.get("outcome") == "wip-skipped" else "actualResult"
                result = {**step_finished["testStepResult"], **actual[result_key]}
                envelope = {**envelope, "testStepFinished": {**step_finished, "testStepResult": result}}
                step_finished = envelope["testStepFinished"]
        status = step_finished.get("testStepResult", {}).get("status") if isinstance(step_finished, dict) else None
        needs_outcome = status == "FAILED" or ((self._xfail_as_failed or self._skip_as_failed) and status == "SKIPPED")
        if needs_outcome or attempt_id in self._pending:
            self._pending.setdefault(attempt_id, []).append(envelope)
            return []
        return [envelope]

    def scenario_outcome(self, attempt_id: str) -> tuple[str, str] | None:
        """Return a scenario-level result that cannot be expressed by its step statuses."""
        outcome = self._completed_outcomes.get(attempt_id, {})
        if outcome.get("outcome") == "xpass-strict":
            return "failed", f"XPASS(strict): {outcome.get('reason', '')}"
        if outcome.get("outcome") == "skip":
            as_failed = self._wip_as_failed if outcome.get("wip") else self._skip_as_failed
            return ("failed" if as_failed else "skipped"), str(outcome.get("reason", ""))
        return None

    def _accept_metadata(self, envelope: dict[str, Any]) -> list[dict[str, Any]]:
        if envelope["attachment"].get("mediaType") == PYTEST_STEP_OUTCOME_MEDIA_TYPE:
            if not self._retain_metadata:
                try:
                    payload = json.loads(envelope["attachment"]["body"])
                except (KeyError, TypeError, ValueError):
                    return []
                if (
                    isinstance(payload, dict)
                    and isinstance(payload.get("testCaseStartedId"), str)
                    and isinstance(payload.get("testStepId"), str)
                    and isinstance(
                        payload.get("diagnosticResult" if payload.get("outcome") == "wip-skipped" else "actualResult"),
                        dict,
                    )
                ):
                    self._step_outcomes[(payload["testCaseStartedId"], payload["testStepId"])] = payload
                    if payload.get("outcome") == "wip-skipped":
                        self._wip_attempts.add(payload["testCaseStartedId"])
            return [envelope] if self._retain_metadata else []
        attempt_id = self._record_outcome(envelope["attachment"])
        if self._retain_metadata:
            if attempt_id is None:
                return [envelope]
            self._metadata[attempt_id] = envelope
        return []

    def _record_outcome(self, attachment: dict[str, Any]) -> str | None:
        try:
            outcome = json.loads(attachment["body"])
        except (KeyError, TypeError, ValueError):
            return None
        attempt_id = outcome.get("testCaseStartedId") if isinstance(outcome, dict) else None
        if isinstance(outcome, dict) and isinstance(attempt_id, str):
            self._outcomes[attempt_id] = outcome
            return attempt_id
        return None

    @staticmethod
    def _diagnostic_skip(envelope: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
        step = envelope.get("testStepFinished")
        if not isinstance(step, dict) or step.get("testStepResult", {}).get("status") != "SKIPPED":
            return envelope
        result = {
            **step["testStepResult"],
            "status": "FAILED",
            "message": f"skipped (not executed): {outcome.get('reason', '')}",
        }
        return {**envelope, "testStepFinished": {**step, "testStepResult": result}}

    @staticmethod
    def _diagnostic_xfail(envelope: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
        step = envelope.get("testStepFinished")
        if not isinstance(step, dict) or step.get("testStepResult", {}).get("status") != "SKIPPED":
            return envelope
        actual = next(
            (
                entry.get("result")
                for entry in outcome.get("actualStepResults", [])
                if isinstance(entry, dict) and entry.get("testStepId") == step.get("testStepId")
            ),
            None,
        )
        if isinstance(actual, dict):
            return {**envelope, "testStepFinished": {**step, "testStepResult": actual}}
        if outcome.get("executed") is False:
            result = {
                **step["testStepResult"],
                "status": "FAILED",
                "message": f"xfail (not executed): {outcome.get('reason', '')}",
            }
            return {**envelope, "testStepFinished": {**step, "testStepResult": result}}
        return envelope

    @staticmethod
    def _expected_failure(envelope: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
        step = envelope.get("testStepFinished")
        if not isinstance(step, dict) or step.get("testStepResult", {}).get("status") != "FAILED":
            return envelope
        result = dict(step["testStepResult"])
        result["status"] = "SKIPPED"
        reason = f"xfail: {outcome.get('reason', '')}"
        result["message"] = f"{reason}\n{result['message']}" if result.get("message") else reason
        return {**envelope, "testStepFinished": {**step, "testStepResult": result}}
