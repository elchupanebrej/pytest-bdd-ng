<!-- markdownlint-disable MD013 -->

# Research: Python/Pytest Compatibility Alignment

## Decision 1: Compatibility source of truth

- Decision: Use pytest compatibility matrix as canonical Python/pytest support logic.
- Rationale: Avoids project-specific drift and accidental version restrictions.
- Alternatives considered:
  - Project-maintained static compatibility list: rejected due to maintenance drift.
  - Latest-only pytest policy: rejected because it violates full compatible-pair support.

## Decision 2: Matrix validation completeness

- Decision: Keep explicit matrix coverage for all compatible pairs and report pass/fail deterministically.
- Rationale: Ensures auditability and complete regression signal.
- Alternatives considered:
  - Sampled subset matrix: rejected because coverage would be partial.
  - Dynamic ad-hoc runs only: rejected because results are not reproducible enough for release gating.

## Decision 3: Python 3.14 local provisioning

- Decision: Standardize local Python 3.14 environment setup using conda-forge.
- Rationale: Aligns with user requirement and gives reproducible maintainer workflow.
- Alternatives considered:
  - Depend on system Python availability: rejected as inconsistent.
  - pyenv-only workflow: rejected because conda-forge path was explicitly requested.

## Decision 4: Governance and commit hygiene

- Decision: Keep constitutional requirements for task-traceable commits and mandatory clean pre-commit before commit.
- Rationale: Governance is normative for this repository.
- Alternatives considered:
  - Enforce only in CI: rejected because local commit-time quality gate is required.
