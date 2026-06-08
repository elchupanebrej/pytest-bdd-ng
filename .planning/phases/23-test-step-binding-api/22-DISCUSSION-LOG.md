# Phase 22 Discussion Log: Test/Step binding API

## Launch handle carrier

Question: Preferred carrier for reliable launch handle metadata?

Decision: Use Cucumber Messages `Attachment`, not `Pickle.tags`.

Options considered:

- `Pickle.tags` with `@pytest-id:<nodeid>`
- `Attachment`
- custom envelope field outside cucumber-messages

Question: Attachment payload shape?

Decision: Emit one JSON attachment per `TestCase` with `testCaseId`, `pickleId`, and `nodeid`.

Options considered:

- one attachment per `Pickle`
- one attachment per `TestCase`
- one attachment per Feature

Question: Attachment identity and media type?

Decision: Use `application/vnd.pytest-bdd.launch+json`.

Question: Nodeid encoding?

Decision: Use raw pytest `nodeid` string in JSON.

## Stable source identity

Question: What should framework use as stable source identity when runtime has multiple `Pickle`/`TestCase` objects?

Decision: Use `uri + primary scenario astNodeId`; Examples row identity adds row ast id/breadcrumb.

Question: Where should source identity live?

Decision: Include `sourceIdentity` in the same launch attachment.

Question: How should multiple hookup warning be computed?

Decision: Group by `sourceIdentity` and count unique pytest `nodeid` / `TestCase` bindings. Runtime `Pickle` objects remain distinct; warning is source-level.

Question: How should `0` / `>1` hookup warnings be emitted?

Decision: Emit separate framework diagnostic attachment per `sourceIdentity`.

## Step-scope diagnostics shape

Question: What does "available steps for this Feature file" mean?

Decision: Step definitions visible to pytest item after normal collection/import/conftest scope resolution. Same matcher universe as runtime for bound `TestCase`/`nodeid`.

Question: When matcher finds no step definition, what should framework emit?

Decision: Emit missing diagnostic plus scoped available step definitions for that bound `TestCase`.

Question: What should ambiguous step diagnostic contain?

Decision: Include all matched candidates in same scoped matcher universe. Each candidate has pattern/type/sourceReference. `availableStepDefinitions` optional when useful.

Question: Where should `sourceReference` for matched Python step point?

Decision: Decorated Python function definition line.

Question: Should matched step bindings use explicit messages or only standard `TestStep` links?

Decision: Emit explicit binding attachment per matched step with `testCaseId`, `pickleStepId`, `stepDefinitionId`, `sourceReference`, and `matchArguments`. Keep standard links too.

## Mock-run message timing

Question: At what phase should `--mock-run --messages-ndjson` stop?

Decision: Use normal execution path but skip step function bodies.

Question: What may execute?

Decision: Some hooks may execute; fixture bodies and step bodies must be skipped.

Question: Which hooks belong in mock-run allowlist?

Decision: Hooks that could affect step execution or add steps may need to execute. Exact taxonomy remains gray zone.

Question: What should Phase 22 do with hook gray zone?

Decision: Define minimal mock-run contract and create explicit spike task for hook taxonomy. Fixture bodies and step bodies are skipped; hook execution limited to parts required for binding/matcher correctness.

## Todo folding

Question: Should todo "Create Gherkin E2E tests for Phase 19" be included in Phase 22?

Decision: Pull full Phase 19 E2E todo into Phase 22.

Question: How should Phase 22 close this todo?

Decision: Add both feature-level ATDD under `features/` and Python integration tests under `tests/feature/` or equivalent message-focused test area.
