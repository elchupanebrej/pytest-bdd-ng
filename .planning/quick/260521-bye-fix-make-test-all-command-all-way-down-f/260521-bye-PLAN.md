# Quick Task 260521-bye: fix make test-all command all way down for all targets - Plan

**Status:** Ready for execution
**Tasks:** 1

## Task 1: Fix external_attachment emission point gap

**Files:** `tests/cases/integration/messages/test_message_emission_points.py`
**Action:** Add `external_attachment` to `EMITTED_OUTSIDE_REPORTER_PLUGIN` set
**Verify:** `uv run python -m pytest tests/cases/integration/messages/test_message_emission_points.py -q`
**Done:** `test_message_emission_points_cover_all_supported_payload_kinds` passes

### Context

- `make test-all` failed on `test-integration` target
- Only failure: `test_message_emission_points_cover_all_supported_payload_kinds` — `external_attachment` has no emission point
- `PAYLOAD_KINDS` is auto-derived from `cucumber_messages.Envelope.__annotations__` — includes all protocol fields
- `EMITTED_OUTSIDE_REPORTER_PLUGIN` exists for payload kinds emitted outside the reporter plugin runtime (currently only `parse_error`)
- `external_attachment` is a cucumber-messages protocol field handled at an external/cross-system layer, not by the reporter plugin
- Fix: add `external_attachment` to `EMITTED_OUTSIDE_REPORTER_PLUGIN` alongside `parse_error`
