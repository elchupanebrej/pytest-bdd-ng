---
status: testing
phase: 20-codegen-step-binding-and-tolerant-steps
source:
  - .planning/phases/21-codegen-step-binding-and-tolerant-steps/21-01-SUMMARY.md
  - .planning/phases/21-codegen-step-binding-and-tolerant-steps/21-02-SUMMARY.md
  - .planning/phases/21-codegen-step-binding-and-tolerant-steps/21-03-SUMMARY.md
  - .planning/phases/21-codegen-step-binding-and-tolerant-steps/21-04-SUMMARY.md
  - .planning/phases/21-codegen-step-binding-and-tolerant-steps/21-05-SUMMARY.md
started: 2026-06-04T05:47:55.9794073Z
updated: 2026-06-04T06:07:58.6640725Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 6
name: WIP Step Status Policy
expected: |
  Steps decorated with @not_implemented follow the selected WIP policy: pytest marker wins over Gherkin tag, tag wins over CLI, CLI wins over default, and statuses pass, skip, or fail as configured.
awaiting: user response

## Tests

### 1. Gather Missing Steps
expected: Running pytest with --gather-missing-steps against feature files prints deterministic NDJSON events for missing scenario bindings and missing step definitions, suppresses normal pytest terminal prose, and exits with code 100 when missing artifacts exist.
result: pass

### 2. Bind Feature To Target File
expected: Running pytest with --bind-feature --target-file appends a formatted scenarios("...") binding and required imports to the target file, and rerunning the command leaves the file unchanged.
result: pass

### 3. Generate Missing Step Skeletons
expected: Running pytest with --generate-missing-steps --target-file appends formatted @not_implemented step skeletons for missing steps, skips existing decorators, and returns code 100 when missing steps are generated.
result: pass

### 4. Transactional Codegen Rollback
expected: If generated target-file content is invalid, the command restores the original file by default; with --keep-generated-on-error it preserves the generated content for inspection.
result: pass

### 5. Mock Run Mode
expected: Running pytest with --mock-run validates scenario and step bindings without executing scenario hooks, step hooks, or step bodies, while still failing when bindings are missing.
result: pass

### 6. WIP Step Status Policy
expected: Steps decorated with @not_implemented follow the selected WIP policy: pytest marker wins over Gherkin tag, tag wins over CLI, CLI wins over default, and statuses pass, skip, or fail as configured.
result: [pending]

### 7. Tolerant Step Status Policy
expected: Steps decorated with @tolerant fail by default, but when tolerant status is ignored, failed tolerant steps preserve failed-step evidence and allow later steps and the scenario outcome to continue successfully.
result: [pending]

### 8. Executable Code Generator Docs
expected: The Code Generator feature documentation exercises the Phase 21 flow end to end: gather NDJSON, bind features, generate skeletons, mock-run, WIP, and tolerant ignored behavior all pass through the E2E feature.
result: [pending]

### 9. Legacy Codegen Flags Removed
expected: Legacy codegen flags such as --generate, --generate-missing, and --feature are rejected, and updated tests/docs use only the new spec flags.
result: [pending]

## Summary

total: 9
passed: 5
issues: 0
pending: 4
skipped: 0

## Gaps

[none yet]
