# Contract: Governance Gate for Runtime Coverage

## Scope

Defines CI gate behavior for message capability coverage using real runtime NDJSON evidence and explicit decisions metadata after removal of `Feature` wrappers from the runtime/reporting surface.

## Inputs

- Runtime NDJSON (`--messages-file`)
- Capability decisions (`--decisions`)
- Mandatory capabilities (`--mandatory-capabilities-file`)
- Runtime-required capabilities (`--runtime-required-capabilities-file`)

## Rules

1. Runtime-required capabilities:
- MUST be covered by real runtime events.
- Missing runtime evidence fails the gate when strict runtime coverage is enabled.

2. Non-runtime-required capabilities:
- MUST be runtime-covered or explicitly classified.
- Uncovered and unclassified capabilities fail the strict classification gate.

3. Classification quality:
- `Non-Implementable` requires objective hard technical limitation, evidence refs, and recheck trigger.
- `Partly-Applicable` requires explicit language/runtime mismatch rationale.
- Runtime-observed capability cannot remain classified as `Non-Implementable`.

4. Collection/runtime evidence:
- Feature-level evidence must come from canonical `Source`, `GherkinDocument`, `Pickle`, and emitted envelopes.
- Presence or absence of a `Feature` wrapper never counts as runtime evidence.

5. Fully governed mode:
- Deferred, pending, or blocked states fail when `--require-fully-governed` is enabled.

## Determinism Requirements

- Identical NDJSON plus identical decisions inputs produce identical gate output.
- No synthetic runtime evidence generation is allowed.
- Reporter fallback diagnostics do not count as runtime coverage evidence.

## Output Contract

Governance report MUST include:
- aggregate counters for runtime-required and optional coverage compliance;
- per-capability row with `status`, `runtime_required`, `observed_runtime`, and `disposition`;
- rationale and evidence fields for every non-runtime-covered capability.

## Validation Requirements

- Regression test: runtime-required uncovered capability fails strict gate.
- Regression test: valid `Partly-Applicable` path passes with required rationale.
- Regression test: valid `Non-Implementable` path passes only with hard-limitation evidence.
- End-to-end strict suite passes on `tests/messages_coverage` with `PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1`.
