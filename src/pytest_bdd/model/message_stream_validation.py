from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    import messages


def validate_message_stream(envelopes: Iterable[messages.Envelope]) -> list[str]:
    errors: list[str] = []
    run_started = run_finished = False
    active_cases: set[str] = set()
    started_cases: set[str] = set()
    active_steps: set[str] = set()

    for pos, env in enumerate(envelopes):
        if env.test_run_started is not None:
            if run_started:
                errors.append(f"Duplicate test_run_started at pos {pos}")
            run_started = True
        elif env.test_run_finished is not None:
            if not run_started or active_cases:
                errors.append(f"Invalid test_run_finished at pos {pos}")
            run_finished = True
        elif env.test_case_started is not None:
            tc = env.test_case_started
            if not run_started or run_finished or tc.id in started_cases:
                errors.append(f"Invalid test_case_started '{tc.id}' at pos {pos}")
            started_cases.add(tc.id)
            active_cases.add(tc.id)
        elif env.test_case_finished is not None:
            tcf = env.test_case_finished
            if tcf.test_case_started_id not in active_cases:
                errors.append(f"Invalid test_case_finished '{tcf.test_case_started_id}' at pos {pos}")
            active_cases.discard(tcf.test_case_started_id)
        elif env.test_step_started is not None:
            tss = env.test_step_started
            if tss.test_case_started_id not in active_cases:
                errors.append(f"test_step_started outside active case at pos {pos}")
            active_steps.add(tss.test_step_id)
        elif env.test_step_finished is not None:
            tsf = env.test_step_finished
            if tsf.test_step_id not in active_steps:
                errors.append(f"Invalid test_step_finished '{tsf.test_step_id}' at pos {pos}")
            active_steps.discard(tsf.test_step_id)

    return errors


__all__ = ["validate_message_stream"]
