<!-- markdownlint-disable MD013 -->

# Research: Non-empty BDD Headings Validation

## Decision 1: Validate heading titles from parsed AST nodes, not raw regex text

- Decision: Use parsed `Feature`/`Scenario` structures from the gherkin parser pipeline as the source of truth for title presence checks.
- Rationale: Parsed-node validation respects markdown and plain gherkin parsing rules and avoids false positives from incidental keyword text.
- Alternatives considered:
  - Raw file regex scanning only: rejected because it cannot reliably distinguish parsed headings from snippet content.
  - Reporter-stage validation: rejected because it is too late and depends on collection/execution success.

## Decision 2: Treat missing and whitespace-only heading names as the same violation class

- Decision: Classify titles as invalid when heading text is absent or trims to empty after whitespace normalization.
- Rationale: Both cases carry zero semantic intent and should be blocked consistently.
- Alternatives considered:
  - Reject only fully missing values: rejected because whitespace-only headings are equally ambiguous.
  - Auto-fill placeholder names: rejected because generated labels would hide authoring defects.

## Decision 3: Report deterministic diagnostics with file, line, heading type, and normalized error code

- Decision: Emit one violation record per empty heading with stable fields: `path`, `line`, `heading_type`, `code`, and `message`.
- Rationale: Deterministic diagnostics are required for reliable tests, CI logs, and contributor remediation.
- Alternatives considered:
  - Free-form text errors only: rejected due to brittle assertions and poor tooling integration.
  - Stop at first violation: rejected because one-pass full diagnostics are more actionable.

## Decision 4: Keep enforcement scoped to real parsed headings only

- Decision: Enforce non-empty-title policy only for parser-recognized BDD headings and ignore literal/code snippet sections.
- Rationale: This aligns with FR-007 and prevents noise from documentation examples.
- Alternatives considered:
  - Enforce on any keyword-like text in repository files: rejected due to high false-positive rate.

## Decision 5: Enforce rule in standard validation workflow (tests + pre-commit)

- Decision: Cover behavior in targeted test suites and include stale/invalid heading protection in contributor validation workflow.
- Rationale: Keeps fast local feedback and ensures baseline compliance remains stable over time.
- Alternatives considered:
  - CI-only enforcement: rejected because delayed feedback increases rework.
  - Manual audits only: rejected because policy drift is likely.

## Decision 6: Normalize current `features/` baseline to green before broad rollout

- Decision: Update existing files with empty parsed titles so repository baseline passes new policy immediately.
- Rationale: A failing baseline undermines future enforcement and blocks unrelated work.
- Alternatives considered:
  - Grandfather existing files: rejected because it creates dual policy and technical debt.

## Clarification Resolution Status

- Outstanding `NEEDS CLARIFICATION` items in plan technical context: **none**.
