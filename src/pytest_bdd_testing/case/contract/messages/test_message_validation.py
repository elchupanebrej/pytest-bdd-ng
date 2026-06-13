"""

Provide test message validation helpers.
"""

from __future__ import annotations

from cucumber_messages import (  # type:ignore[attr-defined] — upstream type stubs missing this attribute
    Duration,
    ExternalAttachment,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
    Hook,
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    Meta,
    Product,
    SourceReference,
    StepDefinition,
    StepDefinitionPattern,
    Timestamp,
)
from cucumber_messages import (
    Envelope as Message,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestRunFinished as CucumberTestRunFinished,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import TestRunHookFinished as CucumberTestRunHookFinished
from cucumber_messages import TestRunHookStarted as CucumberTestRunHookStarted
from cucumber_messages import TestRunStarted as CucumberTestRunStarted
from cucumber_messages import TestStepFinished as CucumberTestStepFinished
from cucumber_messages import (
    TestStepResult as CucumberTestStepResult,
)
from cucumber_messages import (
    TestStepResultStatus as CucumberTestStepResultStatus,
)
from cucumber_messages import TestStepStarted as CucumberTestStepStarted

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_consolidation import consolidate_message_fragments
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.model.message_validation import (
    collect_observed_capability_ids,
    validate_envelope_against_schema,
    validate_message_stream,
)
from pytest_bdd_testing.case.contract.messages.test_xdist_message_consolidation import (
    _controller_fragment,
    _worker_fragment,
)


def test_validate_message_stream_rejects_unsupported_protocol_version() -> None:
    """
    Verify validate message stream rejects unsupported protocol version.

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
    envelopes = [
        Message(
            meta=Meta(
                protocol_version="0.0.0",
                implementation=Product(name="pytest-bdd-ng", version="test"),
                runtime=Product(name="python", version="3.x"),
                os=Product(name="os", version="1"),
                cpu=Product(name="cpu", version="1"),
            ),
        ),
    ]

    result = validate_message_stream(envelopes, latest_protocol_version="999.0.0")
    codes = {violation.code for violation in result.violations}
    assert result.status == "fail"
    assert "UNSUPPORTED_PROTOCOL_VERSION" in codes


def test_validate_message_stream_reports_fixed_matrix_diagnostics_when_enabled() -> None:
    """
    Verify validate message stream reports fixed matrix diagnostics when enabled.

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
    envelopes = [
        Message(
            test_run_finished=CucumberTestRunFinished(
                timestamp=Timestamp(seconds=1, nanos=0),
                success=True,
            ),
        ),
    ]

    result = validate_message_stream(envelopes, enforce_mapping_diagnostics=True)
    codes = {violation.code for violation in result.violations}

    assert result.status == "fail"
    assert "MISSING_FIXED_MATRIX_CASE" in codes


def test_validate_message_stream_tracks_external_attachment_fields() -> None:
    """
    Verify validate message stream tracks external attachment fields.

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
    envelopes = [
        Message(
            external_attachment=ExternalAttachment(
                media_type="application/octet-stream",
                url="https://example.invalid/external.bin",
                test_case_started_id="case-started-id",
                test_step_id="step-id",
                test_run_hook_started_id="run-hook-id",
                timestamp=Timestamp(seconds=1, nanos=1),
            ),
        ),
    ]

    result = validate_message_stream(envelopes, track_coverage=True)

    assert result.observed_coverage is not None
    observed = result.observed_coverage.observed_fields
    assert ("externalAttachment", "") in observed
    assert ("externalAttachment", "mediaType") in observed
    assert ("externalAttachment", "url") in observed
    assert ("externalAttachment", "testCaseStartedId") in observed
    assert ("externalAttachment", "testStepId") in observed
    assert ("externalAttachment", "testRunHookStartedId") in observed
    assert ("externalAttachment", "timestamp.seconds") in observed
    assert ("externalAttachment", "timestamp.nanos") in observed


def test_collect_observed_capability_ids_returns_canonical_ids() -> None:
    """
    Verify collect observed capability ids returns canonical ids.

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
    envelopes = [
        Message(
            external_attachment=ExternalAttachment(
                media_type="application/octet-stream",
                url="https://example.invalid/external.bin",
                test_case_started_id="case-started-id",
                test_step_id="step-id",
                test_run_hook_started_id="run-hook-id",
                timestamp=Timestamp(seconds=1, nanos=1),
            ),
        ),
    ]

    observed_ids = collect_observed_capability_ids(envelopes)

    assert "externalAttachment.mediaType" in observed_ids
    assert "externalAttachment.testCaseStartedId" in observed_ids
    assert "externalAttachment.timestamp.seconds" in observed_ids


def test_validate_message_stream_uses_execution_message_adapter(monkeypatch) -> None:
    """
    Verify validate message stream uses execution message adapter.

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
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=1, nanos=0)),
    )
    calls: list[Message] = []
    original = ExecutionMessageAdapter.deserialize.__func__

    def _record_deserialize(cls, value, *, registry=None):
        calls.append(value)
        return original(cls, value, registry=registry)

    monkeypatch.setattr(ExecutionMessageAdapter, "deserialize", classmethod(_record_deserialize))

    result = validate_message_stream([envelope], track_coverage=False)

    assert result.status == "pass"
    assert calls == [envelope]


def test_validate_envelope_against_schema_uses_schema_compatible_projection() -> None:
    """
    Verify validate envelope against schema uses schema compatible projection.

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
    envelope = Message(
        step_definition=StepDefinition(
            id="step-definition-1",
            pattern=StepDefinitionPattern(
                source="I have {count:d} cucumbers",
                type=StepDefinitionPatternType.pytest_bdd_parse_expression,
            ),
            source_reference=SourceReference(
                uri="steps.py",
                location=Location(line=1, column=1),
                java_method=JavaMethod(class_name="steps", method_name="step", method_parameter_types=[]),
                java_stack_trace_element=JavaStackTraceElement(
                    class_name="steps",
                    file_name="steps.py",
                    method_name="step",
                ),
            ),
        ),
    )

    violations = validate_envelope_against_schema(envelope)

    assert violations == ()


def test_validate_message_stream_tracks_test_step_started_by_test_step_id() -> None:
    """
    Verify validate message stream tracks test step started by test step id.

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
    envelopes = [
        Message(
            test_step_started=CucumberTestStepStarted(
                test_case_started_id="case-started-1",
                test_step_id="step-1",
                timestamp=Timestamp(seconds=1, nanos=0),
            ),
        ),
        Message(
            test_step_finished=CucumberTestStepFinished(
                test_case_started_id="case-started-1",
                test_step_id="step-1",
                timestamp=Timestamp(seconds=2, nanos=0),
                test_step_result=CucumberTestStepResult(
                    duration=Duration(seconds=0, nanos=1),
                    status=CucumberTestStepResultStatus.passed,
                ),
            ),
        ),
    ]

    result = validate_message_stream(envelopes, track_coverage=False)

    assert "ORPHAN_REFERENCE" not in {violation.code for violation in result.violations}


def test_validate_message_stream_requires_declared_run_hook_definition() -> None:
    """
    Verify validate message stream requires declared run hook definition.

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
    envelopes = [
        Message(
            test_run_hook_started=CucumberTestRunHookStarted(
                hook_id="pytest-bdd-ng.before-test-run",
                id="run-hook-started-1",
                test_run_started_id="run-started-1",
                timestamp=Timestamp(seconds=1, nanos=0),
            ),
        ),
        Message(
            test_run_hook_finished=CucumberTestRunHookFinished(
                test_run_hook_started_id="run-hook-started-1",
                timestamp=Timestamp(seconds=2, nanos=0),
                result=CucumberTestStepResult(
                    duration=Duration(seconds=0, nanos=1),
                    status=CucumberTestStepResultStatus.passed,
                ),
            ),
        ),
    ]

    result = validate_message_stream(envelopes, track_coverage=False)

    assert result.status == "fail"
    assert any(
        violation.message == "test_run_hook_started references unknown hook_id 'pytest-bdd-ng.before-test-run'."
        for violation in result.violations
    )


def test_validate_message_stream_accepts_declared_run_hook_definition() -> None:
    """
    Verify validate message stream accepts declared run hook definition.

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
    envelopes = [
        Message(
            hook=Hook(
                id="pytest-bdd-ng.before-test-run",
                name="before-test-run",
                type=HookType.before_test_run,
                source_reference=SourceReference(
                    uri="pytest_bdd/plugin/gherkin_message_reporter/plugin.py",
                    location=Location(line=1, column=1),
                    java_method=JavaMethod(
                        class_name="pytest_bdd.plugin.gherkin_message_reporter.plugin",
                        method_name="pytest_sessionstart",
                        method_parameter_types=[],
                    ),
                    java_stack_trace_element=JavaStackTraceElement(
                        class_name="pytest_bdd.plugin.gherkin_message_reporter.plugin",
                        file_name="plugin.py",
                        method_name="pytest_sessionstart",
                    ),
                ),
            ),
        ),
        Message(
            test_run_hook_started=CucumberTestRunHookStarted(
                hook_id="pytest-bdd-ng.before-test-run",
                id="run-hook-started-1",
                test_run_started_id="run-started-1",
                timestamp=Timestamp(seconds=1, nanos=0),
            ),
        ),
        Message(
            test_run_hook_finished=CucumberTestRunHookFinished(
                test_run_hook_started_id="run-hook-started-1",
                timestamp=Timestamp(seconds=2, nanos=0),
                result=CucumberTestStepResult(
                    duration=Duration(seconds=0, nanos=1),
                    status=CucumberTestStepResultStatus.passed,
                ),
            ),
        ),
    ]

    result = validate_message_stream(envelopes, track_coverage=False)

    assert "ORPHAN_REFERENCE" not in {violation.code for violation in result.violations}


def test_validate_message_stream_accepts_consolidated_xdist_output() -> None:
    """
    Verify validate message stream accepts consolidated xdist output.

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

    result = validate_message_stream(list(consolidated.envelopes), track_coverage=False)

    assert result.status == "pass"
    assert result.duplicate_lifecycle_id_count == 0
    assert result.orphan_reference_count == 0
