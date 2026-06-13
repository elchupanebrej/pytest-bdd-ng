"""

Provide test xdist message consolidation helpers.
"""

from __future__ import annotations

from pathlib import Path

from cucumber_messages import (  # type:ignore[attr-defined] — upstream type stubs missing this attribute
    Duration,
    Hook,
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    Meta,
    Pickle,
    PickleStep,
    Product,
    SourceReference,
    StepDefinition,
    Timestamp,
)
from cucumber_messages import (
    Envelope as Message,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestCase as CucumberTestCase,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestCaseFinished as CucumberTestCaseFinished,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestCaseStarted as CucumberTestCaseStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestRunFinished as CucumberTestRunFinished,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestRunHookFinished as CucumberTestRunHookFinished,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestRunHookStarted as CucumberTestRunHookStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestRunStarted as CucumberTestRunStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestStep as CucumberTestStep,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestStepFinished as CucumberTestStepFinished,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestStepResult as CucumberTestStepResult,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestStepResultStatus as CucumberTestStepResultStatus,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestStepStarted as CucumberTestStepStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_consolidation import MessageFragment, consolidate_message_fragments
from pytest_bdd.model.message_extension import StepDefinitionPattern, StepDefinitionPatternType
from pytest_bdd.model.message_validation import validate_message_stream
from pytest_bdd_testing.tool.message.stream_assertions import (
    count_payload_kinds,
    filter_payloads,
    payload_ids,
    worker_ids_for_payloads,
)


def _source_reference() -> SourceReference:
    return SourceReference(
        uri="features/reporting.feature",
        location=Location(line=1, column=1),
        java_method=JavaMethod(class_name="steps", method_name="step_impl", method_parameter_types=[]),
        java_stack_trace_element=JavaStackTraceElement(
            class_name="steps",
            file_name="steps.py",
            method_name="step_impl",
        ),
    )


def _timestamp(seconds: int) -> Timestamp:
    return Timestamp(seconds=seconds, nanos=0)


def _serialize(*messages: Message) -> tuple[dict[str, object], ...]:
    return tuple(ExecutionMessageAdapter.serialize_to_dict(message) for message in messages)


def _controller_fragment() -> MessageFragment:
    return MessageFragment(
        worker_id="master",
        role="controller",
        path=Path("controller.ndjson"),
        complete=True,
        envelopes=_serialize(
            Message(
                meta=Meta(
                    protocol_version="1.0.0",
                    implementation=Product(name="pytest-bdd-ng", version="test"),
                    runtime=Product(name="python", version="3.14"),
                    os=Product(name="linux", version="1"),
                    cpu=Product(name="x86_64", version="1"),
                ),
            ),
            Message(
                hook=Hook(
                    id="hook-before",
                    name="before-test-run",
                    type=HookType.before_test_run,
                    source_reference=_source_reference(),
                ),
            ),
            Message(test_run_started=CucumberTestRunStarted(id="run-started", timestamp=_timestamp(1))),
            Message(
                test_run_hook_started=CucumberTestRunHookStarted(
                    hook_id="hook-before",
                    id="run-hook-started-master",
                    test_run_started_id="run-started",
                    timestamp=_timestamp(2),
                    worker_id="master",
                ),
            ),
            Message(
                test_run_hook_finished=CucumberTestRunHookFinished(
                    test_run_hook_started_id="run-hook-started-master",
                    timestamp=_timestamp(3),
                    result=CucumberTestStepResult(
                        duration=Duration(seconds=0, nanos=1),
                        status=CucumberTestStepResultStatus.passed,
                    ),
                ),
            ),
            Message(
                test_run_finished=CucumberTestRunFinished(
                    timestamp=_timestamp(99),
                    success=True,
                    test_run_started_id="run-started",
                ),
            ),
        ),
    )


def _worker_fragment(worker_id: str, scenario_name: str, *, complete: bool = True) -> MessageFragment:
    return MessageFragment(
        worker_id=worker_id,
        role="worker",
        path=Path(f"{worker_id}.ndjson"),
        complete=complete,
        envelopes=_serialize(
            Message(
                hook=Hook(
                    id="hook-before",
                    name="before-test-run",
                    type=HookType.before_test_run,
                    source_reference=_source_reference(),
                ),
            ),
            Message(
                step_definition=StepDefinition(
                    id="step-definition",
                    pattern=StepDefinitionPattern(
                        source="a passing step",
                        type=StepDefinitionPatternType.pytest_bdd_string_expression,
                    ),
                    source_reference=_source_reference(),
                ),
            ),
            Message(
                pickle=Pickle(
                    id="pickle",
                    uri="features/reporting.feature",
                    name=scenario_name,
                    language="en",
                    steps=[PickleStep(id="pickle-step", text="a passing step", ast_node_ids=["ast-step"])],
                    tags=[],
                    ast_node_ids=["ast-scenario"],
                ),
            ),
            Message(test_run_started=CucumberTestRunStarted(id="run-started", timestamp=_timestamp(1))),
            Message(
                test_run_hook_started=CucumberTestRunHookStarted(
                    hook_id="hook-before",
                    id="run-hook-started",
                    test_run_started_id="run-started",
                    timestamp=_timestamp(4),
                    worker_id=worker_id,
                ),
            ),
            Message(
                test_run_hook_finished=CucumberTestRunHookFinished(
                    test_run_hook_started_id="run-hook-started",
                    timestamp=_timestamp(5),
                    result=CucumberTestStepResult(
                        duration=Duration(seconds=0, nanos=1),
                        status=CucumberTestStepResultStatus.passed,
                    ),
                ),
            ),
            Message(
                test_case=CucumberTestCase(
                    id="test-case",
                    pickle_id="pickle",
                    test_run_started_id="run-started",
                    test_steps=[
                        CucumberTestStep(
                            id="test-step",
                            pickle_step_id="pickle-step",
                            step_definition_ids=["step-definition"],
                        ),
                    ],
                ),
            ),
            Message(
                test_case_started=CucumberTestCaseStarted(
                    id="test-case-started",
                    test_case_id="test-case",
                    attempt=0,
                    worker_id=worker_id,
                    timestamp=_timestamp(6),
                ),
            ),
            Message(
                test_step_started=CucumberTestStepStarted(
                    test_case_started_id="test-case-started",
                    test_step_id="test-step",
                    timestamp=_timestamp(7),
                ),
            ),
            Message(
                test_step_finished=CucumberTestStepFinished(
                    test_case_started_id="test-case-started",
                    test_step_id="test-step",
                    timestamp=_timestamp(8),
                    test_step_result=CucumberTestStepResult(
                        duration=Duration(seconds=0, nanos=1),
                        status=CucumberTestStepResultStatus.passed,
                    ),
                ),
            ),
            Message(
                test_case_finished=CucumberTestCaseFinished(
                    test_case_started_id="test-case-started",
                    timestamp=_timestamp(9),
                    will_be_retried=False,
                ),
            ),
            Message(
                test_run_finished=CucumberTestRunFinished(
                    timestamp=_timestamp(10),
                    success=True,
                    test_run_started_id="run-started",
                ),
            ),
        ),
    )


def test_consolidate_message_fragments_deduplicates_structure_and_preserves_worker_execution() -> None:
    """
    Verify consolidate message fragments deduplicates structure and preserves worker execution.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    consolidated = consolidate_message_fragments(
        [
            _controller_fragment(),
            _worker_fragment("gw0", "shared scenario"),
            _worker_fragment("gw1", "shared scenario"),
        ],
    )

    validation_result = validate_message_stream(list(consolidated.envelopes), track_coverage=False)
    payload_counts = count_payload_kinds(consolidated.envelopes)
    test_case_started_messages = filter_payloads(
        (message.test_case_started for message in consolidated.envelopes if message.test_case_started is not None),
        CucumberTestCaseStarted,
    )
    test_case_messages = filter_payloads(
        (message.test_case for message in consolidated.envelopes if message.test_case is not None),
        CucumberTestCase,
    )

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["hook"] == 1
    assert payload_counts["step_definition"] == 1
    assert payload_counts["pickle"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert payload_counts["test_case"] == 1
    assert payload_counts["test_case_started"] == 2
    assert worker_ids_for_payloads(consolidated.envelopes, CucumberTestCaseStarted) == {"gw0", "gw1"}
    assert len(payload_ids(test_case_messages)) == 1
    assert all(
        message.test_case_id == test_case_started_messages[0].test_case_id for message in test_case_started_messages
    )


def test_consolidate_message_fragments_reports_incomplete_worker_fragments() -> None:
    """
    Verify consolidate message fragments reports incomplete worker fragments.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    consolidated = consolidate_message_fragments(
        [
            _controller_fragment(),
            _worker_fragment("gw0", "shared scenario"),
            _worker_fragment("gw1", "shared scenario", complete=False),
        ],
    )

    assert any(
        diagnostic.code == "partial_stream" and diagnostic.worker_id == "gw1" for diagnostic in consolidated.diagnostics
    )


def test_consolidate_message_fragments_places_after_test_run_hook_before_final_run_finished() -> None:
    """
    Verify consolidate message fragments places after test run hook before final run finished.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    consolidated = consolidate_message_fragments(
        [
            _controller_fragment(),
            _worker_fragment("gw0", "scenario one"),
        ],
    )

    payload_kinds = [
        next(
            payload_kind
            for payload_kind in (
                "meta",
                "hook",
                "pickle",
                "step_definition",
                "test_run_started",
                "test_run_hook_started",
                "test_run_hook_finished",
                "test_case",
                "test_case_started",
                "test_step_started",
                "test_step_finished",
                "test_case_finished",
                "test_run_finished",
            )
            if getattr(message, payload_kind, None) is not None
        )
        for message in consolidated.envelopes
    ]

    assert payload_kinds.index("test_run_finished") > payload_kinds.index("test_case_finished")
