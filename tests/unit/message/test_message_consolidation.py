from __future__ import annotations

import json

import pytest

from pytest_cuke.model.message_consolidation import (
    ConsolidatedMessageStream,
    LiveMessageAdapter,
    MessageFragment,
    consolidate_message_fragments,
    namespace_envelope_ids,
)
from pytest_cuke.model.message_converter import feature_to_envelope, pickle_to_envelope, scenario_to_pickle
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.message_types import (
    Duration,
    Envelope,
    Pickle,
    PickleStep,
    Source,
    TestCase as CucumberTestCase,
    TestCaseFinished as CucumberTestCaseFinished,
    TestCaseStarted,
    TestRunFinished,
    TestRunStarted,
    TestStep as CucumberTestStep,
    TestStepFinished as CucumberTestStepFinished,
    TestStepResult,
    TestStepResultStatus,
    TestStepStarted as CucumberTestStepStarted,
    Timestamp,
    message_to_dict,
)
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.step import Step
from pytest_cuke.model.message_extension import (
    IDE_DIAGNOSTIC_MEDIA_TYPE,
    IDE_LAUNCH_MEDIA_TYPE,
    IDE_STEP_BINDING_MEDIA_TYPE,
)
from pytest_cuke.model.message_worker_transport import MessageBatcher, WorkerMessageReceiver

TestCaseStarted.__test__ = False
TestRunFinished.__test__ = False
TestRunStarted.__test__ = False
TestStepResult.__test__ = False
TestStepResultStatus.__test__ = False


def test_worker_namespaces_nested_message_ids_and_references_without_rewriting_worker_id() -> None:
    envelope = {
        "testCaseStarted": {
            "id": "attempt-1",
            "testCaseId": "case-1",
            "workerId": "gw0",
            "testRunStartedId": "run-1",
        }
    }
    assert namespace_envelope_ids(envelope, worker_id="gw0") == {
        "testCaseStarted": {
            "id": "gw0:attempt-1",
            "testCaseId": "gw0:case-1",
            "workerId": "gw0",
            "testRunStartedId": "gw0:run-1",
        }
    }


def test_live_adapter_collapses_worker_lifecycle_and_deduplicates_shared_definitions() -> None:
    adapter = LiveMessageAdapter()
    controller_run = {"testRunStarted": {"id": "controller-run"}}
    adapted: list[dict[str, object]] = [adapter.controller_envelope(controller_run)]

    source = {"source": {"uri": "features/live.feature", "data": "Feature: Live", "mediaType": "text/plain"}}
    document = {
        "gherkinDocument": {
            "uri": "features/live.feature",
            "feature": {
                "id": "feature-id",
                "keyword": "Feature",
                "name": "Live",
                "children": [
                    {
                        "scenario": {
                            "id": "scenario-id",
                            "keyword": "Scenario",
                            "name": "shared scenario",
                            "steps": [{"id": "step-id", "keyword": "Given", "text": "it runs"}],
                        }
                    }
                ],
            },
        }
    }
    pickle = {
        "pickle": {
            "id": "pickle-id",
            "uri": "features/live.feature",
            "name": "shared scenario",
            "language": "en",
            "astNodeIds": ["scenario-id"],
            "steps": [{"id": "pickle-step-id", "astNodeIds": ["step-id"], "text": "it runs"}],
            "tags": [],
        }
    }
    test_case = {
        "testCase": {
            "id": "test-case-id",
            "pickleId": "pickle-id",
            "testSteps": [
                {
                    "id": "test-step-id",
                    "pickleStepId": "pickle-step-id",
                    "stepDefinitionIds": [],
                }
            ],
        }
    }

    for worker_id in ("gw0", "gw1"):
        run_start = namespace_envelope_ids({"testRunStarted": {"id": f"{worker_id}-run"}}, worker_id=worker_id)
        assert adapter.worker_envelope(run_start, worker_id=worker_id) is None
        for structural in (source, document, pickle, test_case):
            normalized = adapter.worker_envelope(
                namespace_envelope_ids(structural, worker_id=worker_id),
                worker_id=worker_id,
            )
            if normalized is not None:
                adapted.append(normalized)
        started = namespace_envelope_ids(
            {
                "testCaseStarted": {
                    "id": f"{worker_id}-attempt",
                    "testCaseId": "test-case-id",
                    "testRunStartedId": f"{worker_id}-run",
                    "workerId": worker_id,
                    "attempt": 0,
                }
            },
            worker_id=worker_id,
        )
        normalized_started = adapter.worker_envelope(started, worker_id=worker_id)
        assert normalized_started is not None
        adapted.append(normalized_started)
        assert adapter.worker_envelope(
            namespace_envelope_ids({"testRunFinished": {"success": True}}, worker_id=worker_id),
            worker_id=worker_id,
        ) is None

    adapted.append(adapter.controller_envelope({"testRunFinished": {"success": True}}))

    kinds = [next(iter(envelope)) for envelope in adapted]
    assert kinds.count("testRunStarted") == kinds.count("testRunFinished") == 1
    assert kinds.count("source") == kinds.count("gherkinDocument") == kinds.count("pickle") == 1
    assert kinds.count("testCase") == 1
    starts = [envelope["testCaseStarted"] for envelope in adapted if "testCaseStarted" in envelope]
    assert len(starts) == 2
    assert {start["testRunStartedId"] for start in starts} == {"controller-run"}
    assert {start["testCaseId"] for start in starts} == {"gw0:test-case-id"}
    assert {start["workerId"] for start in starts} == {"gw0", "gw1"}


def test_live_adapter_rejects_worker_messages_before_controller_run_start() -> None:
    adapter = LiveMessageAdapter()
    worker_start = namespace_envelope_ids({"testRunStarted": {"id": "worker-run"}}, worker_id="gw0")

    with pytest.raises(ValueError, match="before the controller TestRunStarted"):
        adapter.worker_envelope(worker_start, worker_id="gw0")


def test_live_adapter_accepts_controller_run_start_without_optional_id() -> None:
    adapter = LiveMessageAdapter()
    controller_start = {
        "testRunStarted": {"timestamp": {"seconds": 100, "nanos": 0}},
    }

    assert adapter.controller_envelope(controller_start) == controller_start


def test_live_adapter_rewrites_controller_retry_references_after_deduplicating_test_case() -> None:
    adapter = LiveMessageAdapter()
    first_test_case = {
        "testCase": {
            "id": "test-case-attempt-0",
            "pickleId": "pickle-id",
            "testSteps": [{"id": "test-step-id", "pickleStepId": "pickle-step-id"}],
        }
    }
    retry_test_case = {
        "testCase": {
            "id": "test-case-attempt-1",
            "pickleId": "pickle-id",
            "testSteps": [{"id": "test-step-id", "pickleStepId": "pickle-step-id"}],
        }
    }

    assert adapter.controller_envelope(first_test_case) == first_test_case
    assert adapter.controller_envelope(retry_test_case) is None

    retry_started = adapter.controller_envelope(
        {
            "testCaseStarted": {
                "id": "attempt-1",
                "testCaseId": "test-case-attempt-1",
                "testRunStartedId": "run-id",
                "attempt": 1,
            }
        }
    )

    assert retry_started == {
        "testCaseStarted": {
            "id": "attempt-1",
            "testCaseId": "test-case-attempt-0",
            "testRunStartedId": "run-id",
            "attempt": 1,
        }
    }


def test_live_adapter_keeps_controller_run_hooks_and_suppresses_worker_duplicates() -> None:
    adapter = LiveMessageAdapter()
    controller_start = adapter.controller_envelope({"testRunStarted": {"id": "controller-run"}})
    controller_hook = {
        "hook": {
            "id": "controller-before-hook",
            "name": "pytest session start",
            "type": "BEFORE_TEST_RUN",
            "sourceReference": {"uri": "pytest-cuke:runtime", "location": {"line": 1}},
        }
    }
    assert controller_start is not None
    assert adapter.controller_envelope(controller_hook) is not None

    worker_start = namespace_envelope_ids({"testRunStarted": {"id": "worker-run"}}, worker_id="gw0")
    assert adapter.worker_envelope(worker_start, worker_id="gw0") is None

    worker_hook = namespace_envelope_ids(
        {
            "hook": {
                "id": "worker-before-hook",
                "name": "pytest session start",
                "type": "BEFORE_TEST_RUN",
                "sourceReference": {"uri": "pytest-cuke:runtime", "location": {"line": 1}},
            }
        },
        worker_id="gw0",
    )
    assert adapter.worker_envelope(worker_hook, worker_id="gw0") is None

    worker_hook_started = namespace_envelope_ids(
        {
            "testRunHookStarted": {
                "id": "worker-hook-started",
                "testRunStartedId": "worker-run",
                "hookId": "worker-before-hook",
            }
        },
        worker_id="gw0",
    )
    assert adapter.worker_envelope(worker_hook_started, worker_id="gw0") is None

    worker_hook_finished = namespace_envelope_ids(
        {"testRunHookFinished": {"testRunHookStartedId": "worker-hook-started"}},
        worker_id="gw0",
    )
    assert adapter.worker_envelope(worker_hook_finished, worker_id="gw0") is None


def test_worker_namespaces_nested_ast_ids_lists_and_test_case_references() -> None:
    envelope = {
        "gherkinDocument": {
            "uri": "features/login.feature",
            "feature": {
                "id": "feature-1",
                "children": [{"scenario": {"id": "scenario-1"}}],
            },
        },
        "pickle": {"id": "pickle-1", "astNodeIds": ["scenario-1", "step-1"]},
        "testCase": {
            "id": "case-1",
            "pickleId": "pickle-1",
            "testSteps": [{"id": "case-step-1", "pickleStepId": "pickle-step-1", "stepDefinitionIds": ["definition-1"]}],
        },
    }

    assert namespace_envelope_ids(envelope, worker_id="gw1") == {
        "gherkinDocument": {
            "uri": "features/login.feature",
            "feature": {
                "id": "gw1:feature-1",
                "children": [{"scenario": {"id": "gw1:scenario-1"}}],
            },
        },
        "pickle": {"id": "gw1:pickle-1", "astNodeIds": ["gw1:scenario-1", "gw1:step-1"]},
        "testCase": {
            "id": "gw1:case-1",
            "pickleId": "gw1:pickle-1",
            "testSteps": [{"id": "gw1:case-step-1", "pickleStepId": "gw1:pickle-step-1", "stepDefinitionIds": ["gw1:definition-1"]}],
        },
    }


def test_worker_namespaces_ids_inside_pytest_cuke_json_attachments() -> None:
    body = json.dumps({"testCaseId": "case-1", "nested": {"stepDefinitionIds": ["definition-1"]}})
    envelope = {
        "attachment": {
            "mediaType": IDE_STEP_BINDING_MEDIA_TYPE,
            "body": body,
            "testCaseStartedId": "attempt-1",
            "testStepId": "step-1",
        }
    }

    namespaced = namespace_envelope_ids(envelope, worker_id="gw0")

    assert namespaced["attachment"]["testCaseStartedId"] == "gw0:attempt-1"
    assert namespaced["attachment"]["testStepId"] == "gw0:step-1"
    assert json.loads(namespaced["attachment"]["body"]) == {
        "testCaseId": "gw0:case-1",
        "nested": {"stepDefinitionIds": ["gw0:definition-1"]},
    }


def test_controller_diagnostic_keeps_case_ids_namespaced_by_their_workers() -> None:
    body = json.dumps(
        {
            "kind": "duplicate-bindings",
            "bindings": [
                {"nodeid": "tests/test_north.py::test_case", "testCaseId": "case-1", "workerId": "gw0"},
                {"nodeid": "tests/test_south.py::test_case", "testCaseId": "case-2", "workerId": "gw1"},
            ],
        }
    )
    envelope = {"attachment": {"mediaType": IDE_DIAGNOSTIC_MEDIA_TYPE, "body": body}}

    namespaced = namespace_envelope_ids(envelope, worker_id="master")

    assert json.loads(namespaced["attachment"]["body"])["bindings"] == [
        {"nodeid": "tests/test_north.py::test_case", "testCaseId": "gw0:case-1", "workerId": "gw0"},
        {"nodeid": "tests/test_south.py::test_case", "testCaseId": "gw1:case-2", "workerId": "gw1"},
    ]


def test_consolidation_deduplicates_sources_and_preserves_worker_attempts_deterministically() -> None:
    timestamp = Timestamp(seconds=10, nanos=0)
    controller = MessageFragment(
        worker_id="master",
        role="controller",
        envelopes=(
            message_to_dict(Envelope(test_run_started=TestRunStarted(id="run-1", timestamp=timestamp))),
            message_to_dict(
                Envelope(source=Source(uri="features/login.feature", data="Feature: Login", media_type="text/x.cucumber.gherkin+plain"))
            ),
            message_to_dict(
                Envelope(
                    test_run_finished=TestRunFinished(
                        success=True,
                        timestamp=Timestamp(seconds=20, nanos=0),
                        test_run_started_id="run-1",
                    )
                )
            ),
        ),
    )

    def worker_fragment(worker_id: str) -> MessageFragment:
        return MessageFragment(
            worker_id=worker_id,
            role="worker",
            envelopes=(
                message_to_dict(Envelope(test_run_started=TestRunStarted(id="run-1", timestamp=timestamp))),
                message_to_dict(
                    Envelope(
                        source=Source(
                            uri="features/login.feature",
                            data="Feature: Login",
                            media_type="text/x.cucumber.gherkin+plain",
                        )
                    )
                ),
                message_to_dict(
                    Envelope(
                        test_case_started=TestCaseStarted(
                            id="attempt-1",
                            test_case_id="case-1",
                            worker_id=worker_id,
                            attempt=0,
                            timestamp=timestamp,
                        )
                    )
                ),
            ),
        )

    fragments = [worker_fragment("gw1"), controller, worker_fragment("gw0")]
    first = consolidate_message_fragments(fragments)
    second = consolidate_message_fragments(list(reversed(fragments)))

    assert first.envelope_dicts == second.envelope_dicts
    assert [next(iter(envelope)) for envelope in first.envelope_dicts] == [
        "source",
        "testRunStarted",
        "testCaseStarted",
        "testCaseStarted",
        "testRunFinished",
    ]
    assert [envelope["source"]["uri"] for envelope in first.envelope_dicts if "source" in envelope] == [
        "features/login.feature"
    ]
    attempts = [envelope["testCaseStarted"] for envelope in first.envelope_dicts if "testCaseStarted" in envelope]
    assert [(attempt["id"], attempt["workerId"]) for attempt in attempts] == [
        ("gw0:attempt-1", "gw0"),
        ("gw1:attempt-1", "gw1"),
    ]
    final_run = next(envelope["testRunFinished"] for envelope in first.envelope_dicts if "testRunFinished" in envelope)
    assert final_run["testRunStartedId"] == "master:run-1"


def test_consolidation_deduplicates_a_source_from_its_execnet_rsync_staged_path() -> None:
    source_data = "Feature: Socket gateway cases\n  Scenario: A worker case\n"
    media_type = "text/x.cucumber.gherkin+plain"
    controller_uri = (
        "file:///C:/Users/runneradmin/AppData/Local/Temp/pytest-of-unknown/pytest-0/"
        "pytest-cuke-group-consumer11/"
        "features/socket-worker-cases.feature"
    )
    worker_uri = (
        "file:///C:/Users/runneradmin/AppData/Local/Temp/pytest-cuke-execnet-remote-1-zqhlv78o/"
        "pyexecnetcache/"
        "pytest-cuke-group-consumer11/features/socket-worker-cases.feature"
    )
    fragments = (
        MessageFragment(
            worker_id="master",
            role="controller",
            envelopes=(message_to_dict(Envelope(source=Source(uri=controller_uri, data=source_data, media_type=media_type))),),
        ),
        MessageFragment(
            worker_id="gw0",
            role="worker",
            envelopes=(message_to_dict(Envelope(source=Source(uri=worker_uri, data=source_data, media_type=media_type))),),
        ),
    )

    consolidated = consolidate_message_fragments(fragments)
    sources = [envelope["source"] for envelope in consolidated.envelope_dicts if "source" in envelope]

    assert sources == [{"uri": controller_uri, "data": source_data, "mediaType": media_type}]


def test_consolidation_deduplicates_same_source_from_execnet_staging_roots_without_controller_source() -> None:
    source_data = "Feature: Socket gateway cases\n  Scenario: A worker case\n"
    media_type = "text/x.cucumber.gherkin+plain"
    worker_uris = (
        "file:///C:/Temp/pytest-cuke-execnet-remote-0-first/pyexecnetcache/"
        "pytest-cuke-group-consumer11/features/socket-worker-cases.feature",
        "file:///C:/Temp/pytest-cuke-execnet-remote-1-second/pyexecnetcache/"
        "pytest-cuke-group-consumer11/features/socket-worker-cases.feature",
    )
    fragments = (
        MessageFragment(worker_id="master", role="controller", envelopes=()),
        *(
            MessageFragment(
                worker_id=f"gw{index}",
                role="worker",
                envelopes=(message_to_dict(Envelope(source=Source(uri=uri, data=source_data, media_type=media_type))),),
            )
            for index, uri in enumerate(worker_uris)
        ),
    )

    consolidated = consolidate_message_fragments(fragments)
    reversed_consolidated = consolidate_message_fragments(tuple(reversed(fragments)))
    sources = [envelope["source"] for envelope in consolidated.envelope_dicts if "source" in envelope]

    assert sources == [{"uri": worker_uris[0], "data": source_data, "mediaType": media_type}]
    assert reversed_consolidated.envelope_dicts == consolidated.envelope_dicts


@pytest.mark.parametrize(
    ("second_path", "second_data"),
    (
        ("features/other.feature", "Feature: Shared content\n"),
        ("features/shared.feature", "Feature: Different content\n"),
    ),
)
def test_consolidation_preserves_execnet_staged_sources_with_different_paths_or_contents(
    second_path: str,
    second_data: str,
) -> None:
    first_uri = (
        "file:///C:/Temp/pytest-cuke-execnet-remote-0-first/pyexecnetcache/"
        "pytest-cuke-group-consumer11/features/shared.feature"
    )
    second_uri = (
        f"file:///C:/Temp/pytest-cuke-execnet-remote-1-second/pyexecnetcache/pytest-cuke-group-consumer11/{second_path}"
    )
    sources = (
        (first_uri, "Feature: Shared content\n"),
        (second_uri, second_data),
    )
    fragments = tuple(
        MessageFragment(
            worker_id=f"gw{index}",
            role="worker",
            envelopes=(
                message_to_dict(
                    Envelope(
                        source=Source(
                            uri=uri,
                            data=data,
                            media_type="text/x.cucumber.gherkin+plain",
                        )
                    )
                ),
            ),
        )
        for index, (uri, data) in enumerate(sources)
    )

    consolidated = consolidate_message_fragments(fragments)

    assert [envelope["source"]["uri"] for envelope in consolidated.envelope_dicts if "source" in envelope] == [
        first_uri,
        second_uri,
    ]


def test_consolidation_preserves_distinct_source_uris_with_identical_content() -> None:
    source_data = "Feature: Shared content\n"
    media_type = "text/x.cucumber.gherkin+plain"
    fragments = (
        MessageFragment(
            worker_id="gw0",
            role="worker",
            envelopes=(
                message_to_dict(
                    Envelope(
                        source=Source(
                            uri="features/first.feature",
                            data=source_data,
                            media_type=media_type,
                        )
                    )
                ),
            ),
        ),
        MessageFragment(
            worker_id="gw1",
            role="worker",
            envelopes=(
                message_to_dict(
                    Envelope(
                        source=Source(
                            uri="features/second.feature",
                            data=source_data,
                            media_type=media_type,
                        )
                    )
                ),
            ),
        ),
    )

    consolidated = consolidate_message_fragments(fragments)

    assert [envelope["source"]["uri"] for envelope in consolidated.envelope_dicts if "source" in envelope] == [
        "features/first.feature",
        "features/second.feature",
    ]


def test_consolidation_keeps_staged_source_when_controller_uri_match_is_ambiguous() -> None:
    source_data = "Feature: Shared content\n"
    media_type = "text/x.cucumber.gherkin+plain"
    staged_uri = (
        "file:///C:/Temp/pytest-cuke-execnet-remote-1-random/pyexecnetcache/"
        "pytest-cuke-group-consumer11/features/shared.feature"
    )
    source_uris = (
        "file:///C:/Temp/first/pytest-cuke-group-consumer11/features/shared.feature",
        "file:///C:/Temp/second/pytest-cuke-group-consumer11/features/shared.feature",
        staged_uri,
    )
    fragments = tuple(
        MessageFragment(
            worker_id=worker_id,
            role="controller" if worker_id == "master" else "worker",
            envelopes=(message_to_dict(Envelope(source=Source(uri=uri, data=source_data, media_type=media_type))),),
        )
        for worker_id, uri in zip(("master", "gw0", "gw1"), source_uris, strict=True)
    )

    consolidated = consolidate_message_fragments(fragments)

    assert [envelope["source"]["uri"] for envelope in consolidated.envelope_dicts if "source" in envelope] == list(
        source_uris
    )


def test_consolidation_orders_cases_by_pickle_collection_order_across_worker_assignments() -> None:
    timestamp = Timestamp(seconds=10, nanos=0)
    scenario_names = ("standalone", "row-10", "row-11", "row-12")

    def pickle_envelope(scenario_name: str) -> dict[str, object]:
        pickle_id = f"pickle-{scenario_name}"
        step_id = f"pickle-step-{scenario_name}"
        return message_to_dict(
            Envelope(
                pickle=Pickle(
                    ast_node_ids=[f"scenario-{scenario_name}"],
                    id=pickle_id,
                    language="en",
                    name=scenario_name,
                    steps=[
                        PickleStep(
                            ast_node_ids=[f"step-{scenario_name}"],
                            id=step_id,
                            text=f"Given {scenario_name} completes",
                        )
                    ],
                    tags=[],
                    uri="features/worker-cases.feature",
                )
            )
        )

    def json_attachment(media_type: str, body: dict[str, str]) -> dict[str, object]:
        return {
            "attachment": {
                "contentEncoding": "IDENTITY",
                "mediaType": media_type,
                "body": json.dumps(body, sort_keys=True),
            }
        }

    def worker_fragment(worker_id: str, assigned_scenarios: tuple[str, ...]) -> MessageFragment:
        envelopes = [pickle_envelope(scenario_name) for scenario_name in scenario_names]
        for scenario_name in assigned_scenarios:
            case_id = f"case-{scenario_name}"
            pickle_id = f"pickle-{scenario_name}"
            pickle_step_id = f"pickle-step-{scenario_name}"
            test_step_id = f"test-step-{scenario_name}"
            started_id = f"started-{scenario_name}"
            envelopes.extend(
                (
                    message_to_dict(
                        Envelope(
                            test_case=CucumberTestCase(
                                id=case_id,
                                pickle_id=pickle_id,
                                test_steps=[
                                    CucumberTestStep(
                                        id=test_step_id,
                                        pickle_step_id=pickle_step_id,
                                        step_definition_ids=[f"definition-{scenario_name}"],
                                    )
                                ],
                            )
                        )
                    ),
                    json_attachment(
                        IDE_LAUNCH_MEDIA_TYPE,
                        {"testCaseId": case_id, "pickleId": pickle_id},
                    ),
                    json_attachment(
                        IDE_STEP_BINDING_MEDIA_TYPE,
                        {"testCaseId": case_id, "pickleStepId": pickle_step_id},
                    ),
                    message_to_dict(
                        Envelope(
                            test_case_started=TestCaseStarted(
                                attempt=0,
                                id=started_id,
                                test_case_id=case_id,
                                timestamp=timestamp,
                                worker_id=worker_id,
                            )
                        )
                    ),
                    message_to_dict(
                        Envelope(
                            test_step_started=CucumberTestStepStarted(
                                test_case_started_id=started_id,
                                test_step_id=test_step_id,
                                timestamp=timestamp,
                            )
                        )
                    ),
                    message_to_dict(
                        Envelope(
                            test_step_finished=CucumberTestStepFinished(
                                test_case_started_id=started_id,
                                test_step_id=test_step_id,
                                test_step_result=TestStepResult(
                                    duration=Duration(nanos=0, seconds=0),
                                    status=TestStepResultStatus.passed,
                                ),
                                timestamp=timestamp,
                            )
                        )
                    ),
                    message_to_dict(
                        Envelope(
                            test_case_finished=CucumberTestCaseFinished(
                                test_case_started_id=started_id,
                                timestamp=timestamp,
                                will_be_retried=False,
                            )
                        )
                    ),
                )
            )
        return MessageFragment(worker_id=worker_id, role="worker", envelopes=tuple(envelopes))

    first_assignment = (
        worker_fragment("gw0", ("row-11", "row-12")),
        worker_fragment("gw1", ("standalone", "row-10")),
    )
    second_assignment = (
        worker_fragment("gw0", ("standalone", "row-10")),
        worker_fragment("gw1", ("row-11", "row-12")),
    )

    def semantic_scenario_order(stream: ConsolidatedMessageStream) -> tuple[list[str], list[str]]:
        envelope_dicts = stream.envelope_dicts
        pickles = {envelope["pickle"]["id"]: envelope["pickle"] for envelope in envelope_dicts if "pickle" in envelope}
        cases = {envelope["testCase"]["id"]: envelope["testCase"] for envelope in envelope_dicts if "testCase" in envelope}
        starts = {
            envelope["testCaseStarted"]["id"]: envelope["testCaseStarted"]
            for envelope in envelope_dicts
            if "testCaseStarted" in envelope
        }
        testcase_order = [
            pickles[envelope["testCase"]["pickleId"]]["name"]
            for envelope in envelope_dicts
            if "testCase" in envelope
        ]
        execution_order: list[str] = []
        for envelope in envelope_dicts:
            if "testCaseStarted" in envelope:
                case_id = envelope["testCaseStarted"]["testCaseId"]
            elif "testStepStarted" in envelope or "testStepFinished" in envelope or "testCaseFinished" in envelope:
                payload = next(iter(envelope.values()))
                case_id = starts[payload["testCaseStartedId"]]["testCaseId"]
            elif "attachment" in envelope:
                body = json.loads(envelope["attachment"]["body"])
                case_id = body.get("testCaseId")
                if case_id is None:
                    continue
            else:
                continue
            testcase = cases.get(case_id)
            if testcase is not None:
                execution_order.append(pickles[testcase["pickleId"]]["name"])
        return testcase_order, execution_order

    first = consolidate_message_fragments(first_assignment)
    second = consolidate_message_fragments(second_assignment)

    expected_testcases = list(scenario_names)
    expected_execution = [scenario_name for scenario_name in scenario_names for _ in range(6)]
    assert semantic_scenario_order(first) == semantic_scenario_order(second)
    assert semantic_scenario_order(first) == (expected_testcases, expected_execution)


def test_consolidation_orders_retry_attempts_by_attempt_number_across_workers() -> None:
    timestamp = Timestamp(seconds=10, nanos=0)

    def worker_fragment(worker_id: str, attempt: int) -> MessageFragment:
        pickle_id = "retry-pickle"
        pickle_step_id = "retry-pickle-step"
        case_id = "retry-case"
        test_step_id = "retry-test-step"
        started_id = f"attempt-{attempt}"
        launch = {
            "attachment": {
                "contentEncoding": "IDENTITY",
                "mediaType": IDE_LAUNCH_MEDIA_TYPE,
                "body": json.dumps(
                    {"testCaseId": case_id, "pickleId": pickle_id, "attemptLabel": f"launch-{attempt}"}
                ),
            }
        }
        return MessageFragment(
            worker_id=worker_id,
            role="worker",
            envelopes=(
                message_to_dict(
                    Envelope(
                        pickle=Pickle(
                            ast_node_ids=["retry-scenario"],
                            id=pickle_id,
                            language="en",
                            name="retry scenario",
                            steps=[PickleStep(ast_node_ids=["retry-step"], id=pickle_step_id, text="Given it retries")],
                            tags=[],
                            uri="features/retry.feature",
                        )
                    )
                ),
                message_to_dict(
                    Envelope(
                        test_case=CucumberTestCase(
                            id=case_id,
                            pickle_id=pickle_id,
                            test_steps=[
                                CucumberTestStep(
                                    id=test_step_id,
                                    pickle_step_id=pickle_step_id,
                                    step_definition_ids=[],
                                )
                            ],
                        )
                    )
                ),
                launch,
                message_to_dict(
                    Envelope(
                        test_case_started=TestCaseStarted(
                            attempt=attempt,
                            id=started_id,
                            test_case_id=case_id,
                            timestamp=timestamp,
                            worker_id=worker_id,
                        )
                    )
                ),
                message_to_dict(
                    Envelope(
                        test_step_started=CucumberTestStepStarted(
                            test_case_started_id=started_id,
                            test_step_id=test_step_id,
                            timestamp=timestamp,
                        )
                    )
                ),
                message_to_dict(
                    Envelope(
                        test_step_finished=CucumberTestStepFinished(
                            test_case_started_id=started_id,
                            test_step_id=test_step_id,
                            test_step_result=TestStepResult(
                                duration=Duration(nanos=0, seconds=0),
                                status=TestStepResultStatus.passed,
                            ),
                            timestamp=timestamp,
                        )
                    )
                ),
                message_to_dict(
                    Envelope(
                        test_case_finished=CucumberTestCaseFinished(
                            test_case_started_id=started_id,
                            timestamp=timestamp,
                            will_be_retried=attempt == 0,
                        )
                    )
                ),
            ),
        )

    expected_events = [
        "launch-0",
        "start-0",
        "step-start-0",
        "step-finish-0",
        "finish-0",
        "launch-1",
        "start-1",
        "step-start-1",
        "step-finish-1",
        "finish-1",
    ]

    def ordered_events(stream: ConsolidatedMessageStream) -> list[str]:
        started_by_id: dict[str, int] = {}
        result: list[str] = []
        for envelope in stream.envelope_dicts:
            if "attachment" in envelope:
                body = json.loads(envelope["attachment"]["body"])
                result.append(body["attemptLabel"])
            elif "testCaseStarted" in envelope:
                payload = envelope["testCaseStarted"]
                started_by_id[payload["id"]] = payload["attempt"]
                result.append(f"start-{payload['attempt']}")
            elif any(key in envelope for key in ("testStepStarted", "testStepFinished", "testCaseFinished")):
                kind, payload = next(iter(envelope.items()))
                attempt = started_by_id[payload["testCaseStartedId"]]
                label = {
                    "testStepStarted": "step-start",
                    "testStepFinished": "step-finish",
                    "testCaseFinished": "finish",
                }[kind]
                result.append(f"{label}-{attempt}")
        return result

    cross_worker = consolidate_message_fragments(
        (worker_fragment("gw0", attempt=1), worker_fragment("gw1", attempt=0))
    )
    assert ordered_events(cross_worker) == expected_events

    first_attempt = worker_fragment("gw0", attempt=1)
    second_attempt = worker_fragment("gw0", attempt=0)
    same_worker_fragment = MessageFragment(
        worker_id="gw0",
        role="worker",
        envelopes=(*first_attempt.envelopes, *second_attempt.envelopes[2:]),
    )
    same_worker = consolidate_message_fragments((same_worker_fragment,))
    assert ordered_events(same_worker) == expected_events


def test_consolidation_preserves_identical_outline_rows_with_distinct_ast_ids() -> None:
    scenarios = (
        Scenario(
            name="Repeated row",
            line=2,
            id="scenario-row-a",
            steps=(Step(name="same action", keyword="Given ", line=3, id="step-row-a"),),
        ),
        Scenario(
            name="Repeated row",
            line=5,
            id="scenario-row-b",
            steps=(Step(name="same action", keyword="Given ", line=6, id="step-row-b"),),
        ),
    )
    feature = Feature(name="Repeated rows", line=1, scenarios=scenarios)
    document = message_to_dict(feature_to_envelope(feature, uri="features/repeated.feature"))
    pickles = tuple(
        message_to_dict(
            pickle_to_envelope(
                scenario_to_pickle(
                    scenario,
                    uri="features/repeated.feature",
                    default_id=f"pickle-{index}",
                )
            )
        )
        for index, scenario in enumerate(scenarios)
    )
    fragment = MessageFragment(
        worker_id="gw0",
        role="worker",
        envelopes=(document, *pickles),
    )

    consolidated = consolidate_message_fragments((fragment,))
    pickle_payloads = [envelope["pickle"] for envelope in consolidated.envelope_dicts if "pickle" in envelope]

    assert len(pickle_payloads) == 2
    assert [pickle["name"] for pickle in pickle_payloads] == ["Repeated row", "Repeated row"]
    assert [pickle["astNodeIds"] for pickle in pickle_payloads] == [
        ["gw0:scenario-row-a"],
        ["gw0:scenario-row-b"],
    ]


def test_consolidation_rewrites_references_inside_json_attachments_after_structural_deduplication() -> None:
    hook = {
        "hook": {
            "id": "before-hook",
            "type": "BEFORE_TEST_RUN",
            "sourceReference": {"uri": "tests/hooks.py", "location": {"line": 1}},
        }
    }

    def fragment(worker_id: str) -> MessageFragment:
        attachment_body = json.dumps({"hookId": "before-hook", "testCaseId": f"case-{worker_id}"})
        return MessageFragment(
            worker_id=worker_id,
            role="worker",
            envelopes=(
                hook,
                {
                    "attachment": {
                        "contentEncoding": "IDENTITY",
                        "mediaType": IDE_STEP_BINDING_MEDIA_TYPE,
                        "body": attachment_body,
                    }
                },
            ),
        )

    consolidated = consolidate_message_fragments((fragment("gw0"), fragment("gw1")))
    attachment_bodies = [
        json.loads(envelope["attachment"]["body"])
        for envelope in consolidated.envelope_dicts
        if "attachment" in envelope
    ]

    assert len([envelope for envelope in consolidated.envelope_dicts if "hook" in envelope]) == 1
    assert attachment_bodies == [
        {"hookId": "gw0:before-hook", "testCaseId": "gw0:case-gw0"},
        {"hookId": "gw0:before-hook", "testCaseId": "gw1:case-gw1"},
    ]


def test_consolidation_preserves_valid_envelopes_and_diagnoses_malformed_worker_envelopes() -> None:
    fragment = MessageFragment(
        worker_id="gw0",
        role="worker",
        envelopes=(
            message_to_dict(
                Envelope(source=Source(uri="features/a.feature", data="Feature: A", media_type="text/x.cucumber.gherkin+plain"))
            ),
            {"source": {"uri": "features/b.feature"}, "pickle": {"id": "ambiguous"}},
        ),
    )

    consolidated = consolidate_message_fragments((fragment,))

    assert len(consolidated.envelope_dicts) == 1
    assert consolidated.envelope_dicts[0]["source"]["uri"] == "features/a.feature"
    assert [diagnostic.code for diagnostic in consolidated.diagnostics] == [
        "interrupted_worker_transfer",
        "partial_stream",
    ]


def test_worker_receiver_retains_batches_and_reports_missing_completion_manifest() -> None:
    event = message_to_dict(Envelope(source=Source(uri="features/a.feature", data="Feature: A", media_type="text/x.cucumber.gherkin+plain")))
    batcher = MessageBatcher("gw0")
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    receiver.receive_batch(batcher.make_batch((event,)).to_payload())
    result = receiver.finalize()

    assert len(result.fragments) == 1
    assert result.fragments[0].envelopes == (event,)
    assert not result.fragments[0].complete
    assert {diagnostic.code for diagnostic in result.diagnostics} == {
        "missing_worker_manifest",
        "partial_stream",
    }


def test_worker_receiver_rejects_duplicate_batch_sequences() -> None:
    event = {"attachment": {"body": "first"}}
    batch = MessageBatcher("gw0").make_batch((event,))
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    assert receiver.receive_batch(batch.to_payload())
    assert not receiver.receive_batch(batch.to_payload())

    result = receiver.finalize()

    assert result.fragments[0].envelopes == (event,)
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "duplicate_worker_batch",
        "missing_worker_manifest",
        "partial_stream",
    ]


def test_worker_receiver_reports_sequence_gaps_and_preserves_received_batches() -> None:
    first_event = {"attachment": {"body": "first"}}
    lost_event = {"attachment": {"body": "lost"}}
    last_event = {"attachment": {"body": "last"}}
    batcher = MessageBatcher("gw0")
    first = batcher.make_batch((first_event,))
    batcher.make_batch((lost_event,))
    last = batcher.make_batch((last_event,))
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    receiver.receive_batch(first.to_payload())
    receiver.receive_batch(last.to_payload())
    receiver.record_manifest(batcher.make_manifest(complete=True).to_payload())
    result = receiver.finalize()

    assert result.fragments[0].envelopes == (first_event, last_event)
    assert not result.fragments[0].complete
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "interrupted_worker_transfer",
        "interrupted_worker_transfer",
        "partial_stream",
    ]


def test_worker_receiver_releases_only_newly_contiguous_batches_in_order() -> None:
    events = [
        {"attachment": {"body": "first"}},
        {"attachment": {"body": "second"}},
        {"attachment": {"body": "third"}},
    ]
    batcher = MessageBatcher("gw0")
    batches = [batcher.make_batch((event,)) for event in events]
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    assert receiver.receive_batch(batches[2].to_payload())
    assert receiver.take_ready_batches("gw0") == ()

    assert receiver.receive_batch(batches[0].to_payload())
    first_ready = receiver.take_ready_batches("gw0")
    assert [batch.sequence for batch in first_ready] == [0]

    assert receiver.receive_batch(batches[1].to_payload())
    remaining_ready = receiver.take_ready_batches("gw0")
    assert [batch.sequence for batch in remaining_ready] == [1, 2]

    receiver.record_manifest(batcher.make_manifest(complete=True).to_payload())
    result = receiver.finalize()
    assert result.fragments[0].envelopes == tuple(events)
    assert result.fragments[0].complete


def test_worker_receiver_accepts_a_complete_ordered_manifest() -> None:
    event_1 = {"attachment": {"body": "one"}}
    event_2 = {"attachment": {"body": "two"}}
    batcher = MessageBatcher("gw0")
    first = batcher.make_batch((event_1,))
    second = batcher.make_batch((event_2,))
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    receiver.receive_batch(second.to_payload())
    receiver.receive_batch(first.to_payload())
    receiver.record_manifest(batcher.make_manifest(complete=True).to_payload())
    result = receiver.finalize()

    assert result.fragments[0].envelopes == (event_1, event_2)
    assert result.fragments[0].complete
    assert result.diagnostics == ()


def test_worker_receiver_reports_a_missing_fragment_for_a_worker_with_no_envelopes() -> None:
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    result = receiver.finalize()

    assert result.fragments[0].envelopes == ()
    assert not result.fragments[0].complete
    assert {diagnostic.code for diagnostic in result.diagnostics} == {
        "missing_worker_manifest",
        "missing_worker_fragment",
        "partial_stream",
    }


def test_worker_receiver_accepts_a_complete_empty_manifest_for_an_idle_worker() -> None:
    batcher = MessageBatcher("gw0")
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    receiver.record_manifest(batcher.make_manifest(complete=True).to_payload())
    result = receiver.finalize()

    assert result.fragments[0].envelopes == ()
    assert result.fragments[0].complete
    assert result.fragments[0].manifest_received
    assert result.diagnostics == ()


def test_worker_receiver_preserves_partial_batches_when_worker_reports_interruption() -> None:
    event = {"attachment": {"body": "available before interruption"}}
    batcher = MessageBatcher("gw0")
    batch = batcher.make_batch((event,))
    receiver = WorkerMessageReceiver(expected_workers=("gw0",))

    receiver.receive_batch(batch.to_payload())
    receiver.record_manifest(
        batcher.make_manifest(complete=False, interruption_reason="worker exited during teardown").to_payload()
    )
    result = receiver.finalize()

    assert result.fragments[0].envelopes == (event,)
    assert not result.fragments[0].complete
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["interrupted_worker_transfer", "partial_stream"]
