"""Unit tests for CucumberEnvelopeAdapter and EnvelopeStateCache."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_bdd.plugin.allure_formatter.message_adapter import (
    CucumberEnvelopeAdapter,
    EnvelopeStateCache,
    _map_status,
    _to_ms,
)

pytestmark = [pytest.mark.unit]


def test_set_and_get_case_uuid() -> None:
    cache = EnvelopeStateCache()
    cache.set_case_uuid("tcs1", "uuid-1")
    assert cache.get_case_uuid("tcs1") == "uuid-1"


def test_get_case_uuid_missing() -> None:
    cache = EnvelopeStateCache()
    assert cache.get_case_uuid("nonexistent") is None


def test_set_and_get_step_uuid() -> None:
    cache = EnvelopeStateCache()
    cache.set_step_uuid("tss1", "uuid-step-1")
    assert cache.get_step_uuid("tss1") == "uuid-step-1"


def test_get_step_uuid_missing() -> None:
    cache = EnvelopeStateCache()
    assert cache.get_step_uuid("nonexistent") is None


def test_clear_resets_all() -> None:
    cache = EnvelopeStateCache()
    cache.set_case_uuid("tcs1", "uuid-1")
    cache.set_step_uuid("tss1", "uuid-step-1")
    cache.clear()
    assert cache.get_case_uuid("tcs1") is None
    assert cache.get_step_uuid("tss1") is None


def test_map_status_passed() -> None:
    assert _map_status("passed") == "passed"


def test_map_status_failed() -> None:
    assert _map_status("failed") == "failed"


def test_map_status_skipped() -> None:
    assert _map_status("skipped") == "skipped"


def test_map_status_undefined_maps_to_broken() -> None:
    assert _map_status("undefined") == "broken"


def test_map_status_pending_maps_to_broken() -> None:
    assert _map_status("pending") == "broken"


def test_map_status_unknown_maps_to_broken() -> None:
    assert _map_status("unknown_status") == "broken"


def test_to_ms_none_returns_none() -> None:
    assert _to_ms(None) is None


def test_to_ms_seconds_nanos_object() -> None:
    ts = MagicMock()
    ts.seconds = 100
    ts.nanos = 500000000
    assert _to_ms(ts) == 100500


def test_to_ms_dict_timestamp() -> None:
    assert _to_ms({"seconds": 100, "nanos": 500000000}) == 100500


def test_to_ms_int_large_treated_as_millis() -> None:
    # Values > 1e11 are treated as already milliseconds
    assert _to_ms(1718400000000) == 1718400000000


def test_to_ms_int_small_treated_as_seconds() -> None:
    # Values <= 1e11 are treated as seconds and multiplied by 1000
    assert _to_ms(100) == 100000


def test_to_ms_float_seconds() -> None:
    assert _to_ms(100.5) == 100500


def test_to_ms_zero() -> None:
    assert _to_ms(0) == 0


def _make_projection(payload_kind: str, payload_id: str | None = None, **payload_attrs: object) -> MagicMock:
    proj = MagicMock()
    proj.payload_kind = payload_kind
    proj.payload = MagicMock()
    proj.registry = None
    if payload_id is not None:
        proj.payload_id = payload_id
    else:
        proj.payload_id = payload_attrs.pop("id", None)
    for k, v in payload_attrs.items():
        setattr(proj.payload, k, v)
    return proj


def test_route_envelope_dispatches_to_handler() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    proj = _make_projection("test_run_started")
    adapter.route_envelope(proj)
    assert adapter.state_cache._case_uuids == {}


def test_route_envelope_unknown_kind_no_error() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    proj = _make_projection("unknown_kind")
    adapter.route_envelope(proj)


def test_test_run_started_clears_cache() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    adapter.state_cache.set_case_uuid("tcs1", "uuid-1")
    proj = _make_projection("test_run_started")
    adapter.route_envelope(proj)
    assert adapter.state_cache.get_case_uuid("tcs1") is None


def test_test_case_started_creates_uuid_and_schedules() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    proj = _make_projection("test_case_started", payload_id="tcs1", timestamp=MagicMock(seconds=100, nanos=0))
    adapter.route_envelope(proj)

    case_uuid = adapter.state_cache.get_case_uuid("tcs1")
    assert case_uuid is not None
    adapter.lifecycle.schedule_test_case.assert_called_once()


def test_test_step_started_creates_uuid_and_starts_step() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    adapter.state_cache.set_case_uuid("tcs1", "case-uuid-1")

    proj = _make_projection(
        "test_step_started",
        payload_id="tss1",
        test_case_started_id="tcs1",
        test_step_id="tss1",
        timestamp=MagicMock(seconds=100, nanos=0),
    )
    adapter.route_envelope(proj)

    step_uuid = adapter.state_cache.get_step_uuid("tss1")
    assert step_uuid is not None
    adapter.lifecycle.start_step.assert_called_once()


def test_test_step_finished_updates_and_stops() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    adapter.state_cache.set_step_uuid("tss1", "step-uuid-1")

    result_mock = MagicMock()
    result_mock.status = "passed"
    proj = _make_projection(
        "test_step_finished",
        payload_id="tss1",
        test_step_id="tss1",
        test_step_result=result_mock,
        timestamp=MagicMock(seconds=100, nanos=0),
    )
    adapter.route_envelope(proj)

    adapter.lifecycle.update_step.assert_called_once_with("step-uuid-1")
    adapter.lifecycle.stop_step.assert_called_once_with("step-uuid-1")


def test_test_case_finished_updates_and_writes() -> None:
    adapter = CucumberEnvelopeAdapter(lifecycle=MagicMock())
    adapter.state_cache.set_case_uuid("tcs1", "case-uuid-1")

    result_mock = MagicMock()
    result_mock.status = "passed"
    proj = _make_projection(
        "test_case_finished",
        payload_id="tcs1",
        test_case_started_id="tcs1",
        test_case_result=result_mock,
        timestamp=MagicMock(seconds=100, nanos=0),
    )
    adapter.route_envelope(proj)

    adapter.lifecycle.update_test_case.assert_called_once_with("case-uuid-1")
    adapter.lifecycle.write_test_case.assert_called_once_with("case-uuid-1")
