# Phase 23 Context: Test/Step binding API

## Intent

Make `--mock-run --messages-ndjson` a reliable framework-owned IDE bootstrap contract for:

- launching exact pytest items from Gherkin scenarios and Examples rows;
- resolving feature steps to Python step definitions;
- reporting missing and ambiguous steps with the same scoped matcher universe that runtime uses;
- warning when a source Feature/Scenario is bound zero or multiple times.

No new `--cucumber-ide-sync` command is introduced. IDE plugins consume real mock-run messages.

## Decisions

### Launch handle carrier

- Do not encode pytest launch handles in `Pickle.tags`.
- Emit a Cucumber Messages `Attachment` per `TestCase`.
- Use `mediaType="application/vnd.pytest-bdd.launch+json"`.
- Payload includes at least `testCaseId`, `pickleId`, `nodeid`, and `sourceIdentity`.
- `nodeid` is raw pytest nodeid string inside JSON.
- System launch metadata remains isolated from user tag filtering.

### Stable source identity

- Runtime `Pickle` objects may be distinct, especially for Examples rows.
- Source identity is separate from runtime identity.
- Use `uri + primary scenario astNodeId` as stable scenario identity.
- For Examples rows, add row ast id / breadcrumb to identity.
- Store `sourceIdentity` in same launch attachment so IDE does not reconstruct framework rules.
- Multiple-hookup warnings group by `sourceIdentity -> set(nodeid/TestCase binding)`, not by `Pickle.id`.
- Emit cardinality warnings as diagnostic attachments with `mediaType="application/vnd.pytest-bdd.diagnostic+json"`.

### Step-scope diagnostics

- "Available steps for this Feature file" means step definitions visible to the pytest item after normal collection/import/conftest scope resolution.
- This is the same matcher universe runtime uses for that bound `TestCase`/`nodeid`.
- Missing-step diagnostics include scoped available step definitions for that bound `TestCase`.
- Ambiguous-step diagnostics include all matched candidates in that scoped matcher universe.
- Python `sourceReference` for Go to Definition points to the decorated function definition line.
- Matched steps emit explicit binding attachments per matched step.
- Binding attachment includes `testCaseId`, `pickleStepId`, `stepDefinitionId`, `sourceReference`, and `matchArguments`.
- Standard Cucumber Messages links remain, but IDE contract does not depend on reconstructing all joins itself.

### Mock-run timing

- Mock-run follows enough of the normal runtime path to produce real messages.
- Step function bodies are skipped.
- Fixture bodies are skipped.
- Some hooks may need to run when they affect step execution or add steps.
- Exact hook taxonomy is a gray zone and needs a spike.
- Phase 23 defines minimal contract now: hook execution is limited to parts required for binding/matcher correctness.

### Test folding

- Pull the full Phase 19 E2E todo into Phase 23.
- Phase 23 test work must cover both:
  - feature-level ATDD under `features/`;
  - Python integration tests under `tests/feature/` or another message-focused integration area.
- Coverage must include mock-run messages plus codegen/missing-step flows, not only narrow IDE binding payloads.

## Open Spike Items

- Define hook taxonomy for mock-run:
  - which pytest-bdd hooks can add or alter step execution;
  - which hooks can safely run in IDE bootstrap;
  - how mock mode is exposed to allowed hooks;
  - how to prevent fixture and step bodies from running while preserving binding correctness.

## Out Of Scope

- IDE plugin implementation.
- LSP registry maintenance.
- Step stub insertion in editor.
- Alternative-step parametrization mode.
- New `--cucumber-ide-sync` command.

## Canonical References

- `.planning/phases/23-test-step-binding-api/23-SPEC.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/TESTING.md`
- `.planning/codebase/INTEGRATIONS.md`
- `.planning/phases/21-codegen-step-binding-and-tolerant-steps/21-CONTEXT.md`
- `.planning/phases/22-pdb-mcp-integration-for-agentic-debugging-and-producing-expl/22-CONTEXT.md`
