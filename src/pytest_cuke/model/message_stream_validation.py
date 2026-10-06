"""Stateful validation for ordered Cucumber Messages streams."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytest_cuke.model import message_types as messages
from pytest_cuke.model.message_extension import get_payload_kind
from pytest_cuke.model.message_types import message_from_dict, message_to_dict
from pytest_cuke.model.message_validation import (
    MessageValidationCode,
    MessageValidationDiagnostic,
    MessageValidationError,
    validate_envelope,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


class MessageStreamValidator:
    """Accept valid envelopes and check lifecycle references across one stream.

    ``accept`` raises ``MessageValidationError`` before the rejected envelope can
    be passed to a consumer. An attempted envelope always consumes a 0-based
    position, including rejected envelopes. ``finish`` reports any lifecycle
    start that was not closed by its corresponding finish message.
    """

    def __init__(self) -> None:
        self._position = 0
        self._diagnostics: list[MessageValidationDiagnostic] = []
        self._pickles: set[str] = set()
        self._hooks: set[str] = set()
        self._step_definitions: set[str] = set()
        self._pickle_steps: set[str] = set()
        self._test_steps: set[str] = set()
        self._test_cases: dict[str, frozenset[str]] = {}
        self._started_cases: dict[str, str] = {}
        self._finished_cases: set[str] = set()
        self._active_steps: set[tuple[str, str]] = set()
        self._seen_steps: set[tuple[str, str]] = set()
        self._finished_steps: set[tuple[str, str]] = set()
        self._run_started = False
        self._run_started_id: str | None = None
        self._hook_types: dict[str, str | None] = {}
        self._started_run_hooks: dict[str, str] = {}
        self._started_run_hooks_by_definition: set[str] = set()
        self._active_run_hooks: set[str] = set()
        self._finished_run_hooks: set[str] = set()
        self._after_run_hook_started = False
        self._run_finished = False
        self._finished = False
        self._finish_diagnostics: tuple[MessageValidationDiagnostic, ...] = ()

    @property
    def diagnostics(self) -> tuple[MessageValidationDiagnostic, ...]:
        """Return all diagnostics produced by accepted, rejected, and final checks."""
        return tuple(self._diagnostics)

    def accept(self, envelope: messages.Envelope) -> messages.Envelope:
        """Validate and record one envelope, raising before invalid input is accepted."""
        position = self._position
        self._position += 1

        if self._finished:
            self._reject(
                (
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        get_payload_kind(envelope),
                        "Cannot accept an envelope after stream validation has finished",
                    ),
                )
            )

        diagnostics = list(validate_envelope(envelope, position=position))
        if diagnostics:
            self._reject(diagnostics)

        payload_kind = get_payload_kind(envelope)
        wire = message_to_dict(envelope)
        payload = wire[_snake_to_camel(payload_kind or "")]
        diagnostics = self._lifecycle_diagnostics(payload, payload_kind, position)
        if diagnostics:
            self._reject(diagnostics)

        self._record(payload, payload_kind)
        return message_from_dict(wire, messages.Envelope)

    def finish(self) -> tuple[MessageValidationDiagnostic, ...]:
        """Close the stream and return diagnostics for lifecycle starts left open."""
        if self._finished:
            return self._finish_diagnostics

        position = self._position
        diagnostics: list[MessageValidationDiagnostic] = []
        if self._run_started and not self._run_finished:
            diagnostics.append(
                self._make_diagnostic(
                    "INCOMPLETE_LIFECYCLE",
                    position,
                    "test_run_started",
                    "test_run_started has no matching test_run_finished",
                )
            )
        for started_id in sorted(self._active_run_hooks):
            diagnostics.append(
                self._make_diagnostic(
                    "INCOMPLETE_LIFECYCLE",
                    position,
                    "test_run_hook_started",
                    f"test_run_hook_started '{started_id}' has no matching test_run_hook_finished",
                    (started_id,),
                )
            )
        for hook_id, hook_type in sorted(self._hook_types.items()):
            if (
                hook_type in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}
                and hook_id not in self._started_run_hooks_by_definition
            ):
                diagnostics.append(
                    self._make_diagnostic(
                        "INCOMPLETE_LIFECYCLE",
                        position,
                        "hook",
                        f"run hook definition '{hook_id}' has no matching test_run_hook_started",
                        (hook_id,),
                    )
                )
        for started_id in sorted(set(self._started_cases) - self._finished_cases):
            diagnostics.append(
                self._make_diagnostic(
                    "INCOMPLETE_LIFECYCLE",
                    position,
                    "test_case_started",
                    f"test_case_started '{started_id}' has no matching test_case_finished",
                    (started_id,),
                )
            )
        for started_id, step_id in sorted(self._active_steps):
            diagnostics.append(
                self._make_diagnostic(
                    "INCOMPLETE_LIFECYCLE",
                    position,
                    "test_step_started",
                    f"test_step_started '{step_id}' for case attempt '{started_id}' has no matching test_step_finished",
                    (started_id, step_id),
                )
            )

        self._finished = True
        self._finish_diagnostics = tuple(diagnostics)
        self._diagnostics.extend(diagnostics)
        return self._finish_diagnostics

    def _lifecycle_diagnostics(
        self,
        payload: dict[str, Any],
        payload_kind: str | None,
        position: int,
    ) -> list[MessageValidationDiagnostic]:
        errors: list[MessageValidationDiagnostic] = []

        if self._run_finished:
            return [
                self._make_diagnostic(
                    "OUT_OF_ORDER_LIFECYCLE",
                    position,
                    payload_kind,
                    "No messages may follow test_run_finished",
                )
            ]

        if payload_kind == "test_run_started":
            if self._run_started:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_started may appear only once",
                    )
                )
        elif payload_kind == "test_run_finished":
            if not self._run_started:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_finished appeared before test_run_started",
                    )
                )
            active = sorted(set(self._started_cases) - self._finished_cases)
            if active:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_finished appeared while test case attempts were active",
                        tuple(active),
                    )
                )
            if self._active_steps:
                step_ids = tuple(
                    value for started_id, step_id in sorted(self._active_steps) for value in (started_id, step_id)
                )
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_finished appeared while test steps were active",
                        step_ids,
                    )
                )
            if self._active_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_finished appeared while test run hooks were active",
                        tuple(sorted(self._active_run_hooks)),
                    )
                )
            referenced_run_id = payload.get("testRunStartedId")
            if referenced_run_id is not None and referenced_run_id != self._run_started_id:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_run_finished refers to unknown test_run_started '{referenced_run_id}'",
                        (referenced_run_id,),
                        ("testRunStartedId",),
                    )
                )
        elif payload_kind == "test_run_hook_started":
            started_id = payload["id"]
            hook_id = payload["hookId"]
            run_id = payload["testRunStartedId"]
            hook_type = self._hook_types.get(hook_id)
            if not self._run_started:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_hook_started appeared before test_run_started",
                        (started_id,),
                    )
                )
            if run_id != self._run_started_id:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_run_hook_started refers to unknown test_run_started '{run_id}'",
                        (run_id,),
                        ("testRunStartedId",),
                    )
                )
            if hook_id not in self._hook_types:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_run_hook_started refers to unknown hook '{hook_id}'",
                        (hook_id,),
                        ("hookId",),
                    )
                )
            elif hook_type not in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_run_hook_started refers to hook '{hook_id}' that is not a run hook",
                        (hook_id,),
                        ("hookId",),
                    )
                )
            if started_id in self._started_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "DUPLICATE_LIFECYCLE_ID",
                        position,
                        payload_kind,
                        f"Duplicate test_run_hook_started id '{started_id}'",
                        (started_id,),
                    )
                )
            if self._active_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_run_hook_started appeared while another run hook was active",
                        (*sorted(self._active_run_hooks), started_id),
                    )
                )
            if hook_type == "BEFORE_TEST_RUN" and self._started_cases:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "before-test-run hook started after a test case had started",
                        (hook_id,),
                    )
                )
            if hook_type == "AFTER_TEST_RUN":
                active_cases = sorted(set(self._started_cases) - self._finished_cases)
                if active_cases:
                    errors.append(
                        self._make_diagnostic(
                            "OUT_OF_ORDER_LIFECYCLE",
                            position,
                            payload_kind,
                            "after-test-run hook started while test case attempts were active",
                            tuple(active_cases),
                        )
                    )
        elif payload_kind == "test_run_hook_finished":
            started_id = payload["testRunHookStartedId"]
            if started_id not in self._started_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_run_hook_finished refers to unknown test_run_hook_started '{started_id}'",
                        (started_id,),
                        ("testRunHookStartedId",),
                    )
                )
            elif started_id in self._finished_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        f"test_run_hook_started '{started_id}' was already finished",
                        (started_id,),
                    )
                )
        elif payload_kind == "test_case_started":
            case_id = payload["testCaseId"]
            started_id = payload["id"]
            referenced_run_id = payload.get("testRunStartedId")
            if not self._run_started:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_case_started appeared before test_run_started",
                        (started_id,),
                    )
                )
            if started_id in self._started_cases:
                errors.append(
                    self._make_diagnostic(
                        "DUPLICATE_LIFECYCLE_ID",
                        position,
                        payload_kind,
                        f"Duplicate test_case_started id '{started_id}'",
                        (started_id,),
                    )
                )
            if case_id not in self._test_cases:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_case_started refers to unknown test_case '{case_id}'",
                        (case_id,),
                        ("testCaseId",),
                    )
                )
            if referenced_run_id is not None and referenced_run_id != self._run_started_id:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_case_started refers to unknown test_run_started '{referenced_run_id}'",
                        (referenced_run_id,),
                        ("testRunStartedId",),
                    )
                )
            if self._active_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_case_started appeared while a test run hook was active",
                        tuple(sorted(self._active_run_hooks)),
                    )
                )
            if self._after_run_hook_started:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        "test_case_started appeared after an after-test-run hook started",
                        (started_id,),
                    )
                )
        elif payload_kind == "test_case_finished":
            started_id = payload["testCaseStartedId"]
            if started_id not in self._started_cases:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_case_finished refers to unknown test_case_started '{started_id}'",
                        (started_id,),
                        ("testCaseStartedId",),
                    )
                )
            elif started_id in self._finished_cases:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        f"test_case_started '{started_id}' was already finished",
                        (started_id,),
                    )
                )
            if any(case_started_id == started_id for case_started_id, _ in self._active_steps):
                active_ids = tuple(
                    value
                    for case_started_id, step_id in sorted(self._active_steps)
                    if case_started_id == started_id
                    for value in (case_started_id, step_id)
                )
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        f"test_case_finished appeared while steps for '{started_id}' were active",
                        active_ids,
                    )
                )
        elif payload_kind in {"test_step_started", "test_step_finished"}:
            started_id = payload["testCaseStartedId"]
            step_id = payload["testStepId"]
            pair = (started_id, step_id)
            if started_id not in self._started_cases:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"{payload_kind} refers to unknown test_case_started '{started_id}'",
                        (started_id,),
                        ("testCaseStartedId",),
                    )
                )
            elif started_id in self._finished_cases:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        f"{payload_kind} appeared after test_case_started '{started_id}' was finished",
                        (started_id,),
                    )
                )
            elif step_id not in self._test_cases[self._started_cases[started_id]]:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"{payload_kind} refers to unknown test_step '{step_id}' for case attempt '{started_id}'",
                        (started_id, step_id),
                        ("testStepId",),
                    )
                )
            if payload_kind == "test_step_started":
                if pair in self._seen_steps:
                    errors.append(
                        self._make_diagnostic(
                            "DUPLICATE_LIFECYCLE_ID",
                            position,
                            payload_kind,
                            f"Duplicate test_step_started for case attempt '{started_id}' and step '{step_id}'",
                            pair,
                        )
                    )
            elif pair not in self._active_steps:
                if pair in self._finished_steps:
                    errors.append(
                        self._make_diagnostic(
                            "OUT_OF_ORDER_LIFECYCLE",
                            position,
                            payload_kind,
                            f"test_step '{step_id}' for case attempt '{started_id}' was already finished",
                            pair,
                        )
                    )
                elif started_id in self._started_cases:
                    errors.append(
                        self._make_diagnostic(
                            "OUT_OF_ORDER_LIFECYCLE",
                            position,
                            payload_kind,
                            f"test_step_finished has no matching test_step_started for '{step_id}'",
                            pair,
                        )
                    )
        elif payload_kind == "test_case":
            pickle_id = payload["pickleId"]
            if pickle_id not in self._pickles:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_case refers to unknown pickle '{pickle_id}'",
                        (pickle_id,),
                        ("pickleId",),
                    )
                )
            referenced_run_id = payload.get("testRunStartedId")
            if referenced_run_id is not None and referenced_run_id != self._run_started_id:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"test_case refers to unknown test_run_started '{referenced_run_id}'",
                        (referenced_run_id,),
                        ("testRunStartedId",),
                    )
                )
            for index, test_step in enumerate(payload["testSteps"]):
                hook_id = test_step.get("hookId")
                if hook_id is not None and hook_id not in self._hooks:
                    errors.append(
                        self._make_diagnostic(
                            "ORPHAN_REFERENCE",
                            position,
                            payload_kind,
                            f"test_case test step refers to unknown hook '{hook_id}'",
                            (hook_id,),
                            ("testSteps", index, "hookId"),
                        )
                    )
                pickle_step_id = test_step.get("pickleStepId")
                if pickle_step_id is not None and pickle_step_id not in self._pickle_steps:
                    errors.append(
                        self._make_diagnostic(
                            "ORPHAN_REFERENCE",
                            position,
                            payload_kind,
                            f"test_case test step refers to unknown pickle step '{pickle_step_id}'",
                            (pickle_step_id,),
                            ("testSteps", index, "pickleStepId"),
                        )
                    )
                for definition_index, definition_id in enumerate(test_step.get("stepDefinitionIds", [])):
                    if definition_id not in self._step_definitions:
                        errors.append(
                            self._make_diagnostic(
                                "ORPHAN_REFERENCE",
                                position,
                                payload_kind,
                                f"test_case test step refers to unknown step definition '{definition_id}'",
                                (definition_id,),
                                ("testSteps", index, "stepDefinitionIds", definition_index),
                            )
                        )
        elif payload_kind == "attachment":
            run_id = payload.get("testRunStartedId")
            if run_id is not None and run_id != self._run_started_id:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"attachment refers to unknown test_run_started '{run_id}'",
                        (run_id,),
                        ("testRunStartedId",),
                    )
                )
            run_hook_started_id = payload.get("testRunHookStartedId")
            if run_hook_started_id is not None and run_hook_started_id not in self._started_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"attachment refers to unknown test_run_hook_started '{run_hook_started_id}'",
                        (run_hook_started_id,),
                        ("testRunHookStartedId",),
                    )
                )
            elif run_hook_started_id in self._finished_run_hooks:
                errors.append(
                    self._make_diagnostic(
                        "OUT_OF_ORDER_LIFECYCLE",
                        position,
                        payload_kind,
                        f"attachment appeared after test_run_hook_started '{run_hook_started_id}' finished",
                        (run_hook_started_id,),
                    )
                )
            started_id = payload.get("testCaseStartedId")
            if started_id is not None and started_id not in self._started_cases:
                errors.append(
                    self._make_diagnostic(
                        "ORPHAN_REFERENCE",
                        position,
                        payload_kind,
                        f"attachment refers to unknown test_case_started '{started_id}'",
                        (started_id,),
                        ("testCaseStartedId",),
                    )
                )
            step_id = payload.get("testStepId")
            if step_id is not None:
                if step_id not in self._test_steps:
                    errors.append(
                        self._make_diagnostic(
                            "ORPHAN_REFERENCE",
                            position,
                            payload_kind,
                            f"attachment refers to unknown test_step '{step_id}'",
                            (step_id,),
                            ("testStepId",),
                        )
                    )
                elif started_id is not None and started_id in self._started_cases:
                    case_id = self._started_cases[started_id]
                    if step_id not in self._test_cases[case_id]:
                        errors.append(
                            self._make_diagnostic(
                                "ORPHAN_REFERENCE",
                                position,
                                payload_kind,
                                f"attachment refers to test_step '{step_id}' outside test case '{case_id}'",
                                (started_id, step_id),
                                ("testStepId",),
                            )
                        )

        return errors

    def _record(self, payload: dict[str, Any], payload_kind: str | None) -> None:
        if payload_kind == "test_run_started":
            self._run_started = True
            self._run_started_id = payload.get("id")
        elif payload_kind == "test_run_finished":
            self._run_finished = True
        elif payload_kind == "hook":
            self._hooks.add(payload["id"])
            self._hook_types[payload["id"]] = payload.get("type")
        elif payload_kind == "test_run_hook_started":
            started_id = payload["id"]
            hook_id = payload["hookId"]
            self._started_run_hooks[started_id] = hook_id
            self._started_run_hooks_by_definition.add(hook_id)
            self._active_run_hooks.add(started_id)
            if self._hook_types.get(hook_id) == "AFTER_TEST_RUN":
                self._after_run_hook_started = True
        elif payload_kind == "test_run_hook_finished":
            started_id = payload["testRunHookStartedId"]
            self._active_run_hooks.discard(started_id)
            self._finished_run_hooks.add(started_id)
        elif payload_kind == "step_definition":
            self._step_definitions.add(payload["id"])
        elif payload_kind == "pickle":
            self._pickles.add(payload["id"])
            self._pickle_steps.update(step["id"] for step in payload["steps"])
        elif payload_kind == "test_case":
            case_id = payload["id"]
            step_ids = frozenset(step["id"] for step in payload["testSteps"])
            self._test_cases[case_id] = step_ids
            self._test_steps.update(step_ids)
        elif payload_kind == "test_case_started":
            self._started_cases[payload["id"]] = payload["testCaseId"]
        elif payload_kind == "test_case_finished":
            self._finished_cases.add(payload["testCaseStartedId"])
        elif payload_kind == "test_step_started":
            pair = (payload["testCaseStartedId"], payload["testStepId"])
            self._seen_steps.add(pair)
            self._active_steps.add(pair)
        elif payload_kind == "test_step_finished":
            pair = (payload["testCaseStartedId"], payload["testStepId"])
            self._active_steps.discard(pair)
            self._finished_steps.add(pair)

    def _make_diagnostic(
        self,
        code: MessageValidationCode,
        position: int,
        payload_kind: str | None,
        message: str,
        offending_ids: tuple[str, ...] = (),
        instance_path: tuple[str | int, ...] | None = None,
    ) -> MessageValidationDiagnostic:
        return MessageValidationDiagnostic(
            code=code,
            severity="error",
            position=position,
            payload_kind=payload_kind,
            message=message,
            offending_ids=offending_ids,
            instance_path=instance_path,
        )

    def _reject(self, diagnostics: Iterable[MessageValidationDiagnostic]) -> None:
        rejected = tuple(diagnostics)
        self._diagnostics.extend(rejected)
        raise MessageValidationError(rejected)


def validate_message_stream(envelopes: Iterable[messages.Envelope]) -> list[str]:
    """Compatibility wrapper returning readable strings for invalid streams."""
    validator = MessageStreamValidator()
    errors: list[str] = []
    for envelope in envelopes:
        try:
            validator.accept(envelope)
        except MessageValidationError as error:
            errors.extend(_format_diagnostic(diagnostic) for diagnostic in error.diagnostics)

    errors.extend(_format_diagnostic(diagnostic) for diagnostic in validator.finish())
    return errors


def _format_diagnostic(diagnostic: MessageValidationDiagnostic) -> str:
    return f"{diagnostic.code} at pos {diagnostic.position}: {diagnostic.message}"


def _snake_to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


__all__ = [
    "MessageStreamValidator",
    "MessageValidationDiagnostic",
    "MessageValidationError",
    "validate_message_stream",
]
