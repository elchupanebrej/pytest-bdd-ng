# Research: E2E Conversion to Feature Documentation

## Decision 1: Classification model and canonical markers

- Decision: Use three canonical pytest markers: `e2e_convert_candidate`, `e2e_retain_technical`, and `e2e_deferred_conversion`.
- Rationale: Structured, filterable states reduce ambiguity and keep conversion, retention, and deferred queues explicit.
- Alternatives considered:
  - Free-text classification in inventory only: rejected due to inconsistent filtering and review drift.
  - Two-state model only: rejected because blocked-but-convertible tests need explicit deferred tracking.

## Decision 2: Mandatory rubric for conversion eligibility

- Decision: Every evaluated pytest test must include rubric-based classification in `e2e-migration-inventory.md`.
- Rationale: Prevents subjective conversion choices and makes status auditable per cycle.
- Alternatives considered:
  - Ad hoc contributor judgment: rejected because it produces inconsistent conversion quality.
  - Convert-all-default strategy: rejected because technical/regression tests lose precision and maintainability.

## Decision 3: Retained technical test lifecycle

- Decision: Tests marked `e2e_retain_technical` stay in CI and are re-evaluated each feature cycle.
- Rationale: Maintains regression coverage while allowing future conversion when constraints change.
- Alternatives considered:
  - Permanent retention without re-evaluation: rejected due to stagnant technical debt.
  - Archive retained tests outside default CI: rejected due to reduced defect detection.

## Decision 4: Parity enforcement and remediation workflow

- Decision: Conversion parity requires explicit audit entries and remediation in follow-up commits only.
- Rationale: Preserves traceability and aligns with constitutional no-history-rewrite enforcement.
- Alternatives considered:
  - Rewrite/squash remediation into original conversion commit: rejected due to review opacity.
  - Optional audit logging: rejected because parity intent can silently regress.

## Decision 5: Cross-platform validation execution

- Decision: Use Docker skill for non-native platform validation; Windows targets are exception.
- Rationale: Ensures deterministic non-native runs while honoring constitution exception for Windows environments.
- Alternatives considered:
  - Local host-only cross-platform assumptions: rejected due to false confidence on incompatible hosts.
