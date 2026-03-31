<!-- markdownlint-disable MD013 -->

# Reporting Lifecycle Boundary

## Purpose

Describe how reporter-facing code consumes lifecycle state after the strict non-null refactor without reintroducing caller-side missing-value branching or inline lifecycle invariant checks.

## Boundary Rules

1. Reporter consumers MUST treat the reporting snapshot as a complete lifecycle contract.
2. Active snapshots MUST expose populated run/feature/scenario/step state required by the current stage.
3. Idle or teardown snapshots MUST use dedicated Empty-State Objects for inactive lifecycle slots and reporter values rather than omitted fields or `None`.
4. Reporter code MUST rely on centralized lifecycle guards and documented empty-state contracts rather than ad-hoc inline absence checks.
5. Genuine lifecycle violations MUST surface as deterministic diagnostics instead of silently degrading to missing values.

## Allowed Empty-State Objects

- `NoPreviousStep`
  - Meaning: the current scenario has not executed a prior step yet.
  - Consumer contract: reporter code may render previous-step metadata through the same contract subset without branching on `None`.

- `InactiveScenarioRun` or inactive lifecycle slot equivalents
  - Meaning: reporting is executing outside an active scenario while the session root still exists.
  - Consumer contract: reporter code may still read lifecycle metadata and explicit inactive slot state without a nullable lookup.

- `InactiveStepRun` or inactive lifecycle slot equivalents
  - Meaning: no step is currently executing, but the lifecycle contract still exposes the step position.
  - Consumer contract: reporter code may continue through the documented step contract subset or escalate through diagnostics.

- `IdleReportingValue`
  - Meaning: a reporting field is inactive because the current stage is idle or finished.
  - Consumer contract: reporter code may render the idle value directly through a contract-compatible display surface.

- `UnresolvedRuntimeEnrichment`
  - Meaning: external or historical metadata could not be enriched into populated runtime detail.
  - Consumer contract: reporter code may emit structured diagnostics while keeping the lifecycle slot present.

## Forbidden Patterns

- Returning `None` from snapshot builders to indicate "no lifecycle data".
- Omitting `feature`, `scenario`, `step`, or `previous_step` from the snapshot to communicate inactivity.
- Repeating lifecycle invariant checks inline inside reporter code for slots already governed by centralized guards.
- Using empty-state objects to mask transition-order bugs or missing required bindings.

## Validation Evidence

- `tests/hook/test_reporting_context_snapshot_unit.py`
- `tests/hook/test_run_diagnostics.py`
- `tests/contract/test_event_message_reporting_contract.py`
- `tests/contract/test_xdist_consolidated_stream_contract.py`
- `tests/contract/test_cucumber_formatter_cli_contract.py`
