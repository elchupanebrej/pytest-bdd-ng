from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pytest_bdd.model import message_converter as mc
from pytest_bdd.model.background import Background
from pytest_bdd.model.feature import Feature
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.message_serialization import dump_ndjson, load_ndjson
from pytest_bdd.model.message_stream_validation import validate_message_stream
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.step import Step

if TYPE_CHECKING:
    import messages


def test_seam3_execution_event_protocol_contract() -> None:
    st = Step(name="ready", keyword="Given ", line=2, id="st-1")
    sc = Scenario(name="Run", keyword="Scenario", line=3, id="sc-1", steps=(st,))
    feat = Feature(name="Seam3", line=1, id="feat-1", background=Background(line=1), scenarios=(sc,))

    doc_env = mc.feature_to_envelope(feat, uri="features/seam3.feature")
    pickle = mc.scenario_to_pickle(sc, uri="features/seam3.feature", default_id="p-1")
    pickle_env = mc.pickle_to_envelope(pickle)
    tc = mc.scenario_to_test_case(sc, pickle_id=pickle.id, default_id="tc-1")
    tc_env = mc.test_case_to_envelope(tc)

    envelopes: list[messages.Envelope] = [
        doc_env,
        pickle_env,
        tc_env,
        mc.make_test_run_started(100.0),
        mc.make_test_case_started(test_case_id=tc.id, id="tcs-1", timestamp=101.0),
        mc.make_test_step_started("tcs-1", test_step_id="sc-1-step-0", timestamp=101.1),
        mc.make_test_step_finished(
            test_case_started_id="tcs-1", test_step_id="sc-1-step-0", status="passed", duration=0.1, timestamp=101.2
        ),
        mc.make_test_case_finished("tcs-1", timestamp=101.3),
        mc.make_test_run_finished(timestamp=102.0, success=True),
    ]

    for env in envelopes:
        mc.validate_envelope_shape(env)
        json_obj = json.loads(env.model_dump_json(exclude_none=True, by_alias=True))
        assert not any("pytest" in k.lower() or "_pytest" in k.lower() for k in json_obj)

    assert validate_message_stream(envelopes) == []

    registry = EnvelopeRegistry()
    for env in envelopes:
        registry.add_envelope(env)
    assert registry.resolve("sc-1") is not None
    assert registry.resolve("st-1") is not None
    assert registry.resolve("sc-1-step-0") is not None
    assert registry.resolve("tcs-1") is not None

    ndjson_data = dump_ndjson(envelopes)
    reloaded = load_ndjson(ndjson_data)
    assert len(reloaded) == len(envelopes)
    assert validate_message_stream(reloaded) == []


def test_seam3_stream_order_violation_detection() -> None:
    bad_stream = [
        mc.make_test_step_finished(test_case_started_id="tcs-x", test_step_id="ts-x"),
        mc.make_test_run_finished(),
    ]
    errors = validate_message_stream(bad_stream)
    assert len(errors) >= 2
