# Contract: Governance Gate for Runtime Coverage

## Scope

Defines CI gate semantics for capability coverage using runtime NDJSON evidence and explicit classification decisions.

## Inputs

- Runtime NDJSON (`--messages-file`)
- Capability decisions JSON (`--decisions`)
- Mandatory capability list (`--mandatory-capabilities-file`)
- Runtime-required capability list (`--runtime-required-capabilities-file`)

## Rules

1. Runtime-required capabilities:
   - MUST be covered by real runtime events.
   - Missing runtime evidence fails gate when strict runtime coverage is enabled.

2. Non-runtime-required capabilities:
   - MUST be either runtime-covered or explicitly classified.
   - Uncovered + unclassified entries fail gate when strict classification is enabled.

3. Classification quality:
   - `Non-Implementable` requires objective hard technical limitation, evidence refs, and recheck trigger.
   - `Partly-Applicable` requires explicit language/runtime mismatch rationale.
   - Runtime-observed capability cannot be marked `Non-Implementable`.

4. Fully governed mode:
   - Deferred/pending/blocked states fail when `--require-fully-governed` is enabled.

## Output Contract

Governance report MUST include:
- summary counters for runtime-required coverage and non-runtime classification completeness;
- per-capability row with `status`, `disposition`, `runtime_required`, `observed_runtime`;
- required evidence metadata for deferred statuses.

## Determinism Requirements

- Same NDJSON + decisions input MUST produce same dispositions and counters.
- No synthetic runtime evidence generation is allowed in governance processing.

## Validation Requirements

- Regression tests for runtime-required uncovered failure.
- Regression tests for valid `Partly-Applicable` and `Non-Implementable` evidence paths.
- End-to-end strict governance suite over `tests/messages_coverage`.
