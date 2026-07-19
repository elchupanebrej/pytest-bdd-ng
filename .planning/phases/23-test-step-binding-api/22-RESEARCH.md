# Phase 22: Test/Step binding API - Research

**Researched:** 2026-06-05 [VERIFIED: system date]
**Domain:** pytest plugin runtime, Cucumber Messages NDJSON, IDE bootstrap binding contract [VERIFIED: 22-SPEC.md]
**Confidence:** HIGH [VERIFIED: codebase grep]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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
- Phase 22 defines minimal contract now: hook execution is limited to parts required for binding/matcher correctness.

### Test folding

- Pull the full Phase 19 E2E todo into Phase 22.
- Phase 22 test work must cover both:
  - feature-level ATDD under `features/`;
  - Python integration tests under `tests/feature/` or another message-focused integration area.
- Coverage must include mock-run messages plus codegen/missing-step flows, not only narrow IDE binding payloads.

### the agent's Discretion

No explicit discretion section exists beyond Open Spike Items in 22-CONTEXT.md. [VERIFIED: 22-CONTEXT.md]

### Deferred Ideas (OUT OF SCOPE)

- IDE plugin implementation.
- LSP registry maintenance.
- Step stub insertion in editor.
- Alternative-step parametrization mode.
- New `--cucumber-ide-sync` command.
</user_constraints>

## Project Constraints (from AGENTS.md)

- Prefix shell commands with `rtk`. [VERIFIED: AGENTS.md]
- Development guidance lives in `DEVELOPMENT.rst`; duplicated guidance should not be added to `AGENTS.md`. [VERIFIED: AGENTS.md]
- Project is a Python library/CLI plugin stack supporting Python 3.10-3.14. [VERIFIED: AGENTS.md]
- Core tooling includes pytest, pluggy, tox, pre-commit, ruff, mypy, and packaging. [VERIFIED: AGENTS.md]
- Runtime state should use in-memory `Run`/`ScenarioRun`/execution context plus `pytest.config.stash`; Phase 22 may add in-memory `{Path: GherkinDocument}` but no persistent storage. [VERIFIED: AGENTS.md]
- Use `attrs` over stdlib `dataclass` for new structured data. [VERIFIED: AGENTS.md]
- Outside pytest hook implementations, `return None` is an antipattern. [VERIFIED: AGENTS.md]
- Documentation, specification, and planning artifacts must be written in English. [VERIFIED: AGENTS.md]
- New features should include acceptance tests under `features/` with BDD/ATDD practice. [VERIFIED: AGENTS.md]
- Keep test grouping logic in `src/pytest_bdd/util/test_group_ordering.py`; do not add test-local grouping utilities. [VERIFIED: AGENTS.md]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| P22-01 | `--mock-run --messages-ndjson` is supported IDE startup sync and emits Source/GherkinDocument/Pickle/StepDefinition/TestCase without hooks/bodies. [VERIFIED: 22-SPEC.md] | Use `PickleRunner._verify_mock_run_bindings()` plus reporter `StepCatalogService.pytest_runtest_setup()`. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py; src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] |
| P22-02 | Every collected Pickle maps to exact pytest `nodeid`. [VERIFIED: 22-SPEC.md] | Emit launch `Attachment` from reporter setup after `TestCase.id` exists; use `item.nodeid`. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] |
| P22-03 | Examples rows map to row-specific nodeids. [VERIFIED: 22-SPEC.md] | Existing parametrization id includes `pickle_table_rows_breadcrumb()`, giving row-specific pytest item IDs. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py; src/pytest_bdd/model/feature_binding.py] |
| P22-04 | Source Feature/Scenario cardinality diagnostics distinguish 0/1/>1 hookups. [VERIFIED: 22-SPEC.md] | Compute during collection from collected items plus full feature/pickle inventory; codegen has similar missing-binding traversal. [VERIFIED: src/pytest_bdd/plugin/code_generator/collection.py] |
| P22-05 | Duplicate source scenario hookups warn even when runtime Pickles/items differ. [VERIFIED: 22-SPEC.md] | Group by `sourceIdentity`, not `pickle.id`, using `FeatureRuntimeBinding.linked_ast_nodes_for()`. [VERIFIED: src/pytest_bdd/model/feature_binding.py] |
| P22-06 | System launch metadata does not affect tags, marks, or hooks. [VERIFIED: 22-SPEC.md] | Use Attachment carrier; current mark conversion only iterates `pickle.tags`, so attachments do not enter `pytest_bdd_convert_tag_to_marks()`. [VERIFIED: 22-CONTEXT.md; src/pytest_bdd/plugin/scenario_test_collector/plugin.py] |
| P22-07 | Matched steps resolve to exact Python step definition `sourceReference` and match args. [VERIFIED: 22-SPEC.md] | `Definition.as_message()` already produces function file URI/line and `StepCatalogService` already builds `stepDefinitionIds` and match argument lists. [VERIFIED: src/pytest_bdd/steps/definition.py; src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] |
| P22-08 | Missing/ambiguous diagnostics include scoped available/candidate step definitions. [VERIFIED: 22-SPEC.md] | Use request-local `step_registry` parent chain and `Matcher`; missing suggestions already emit `Suggestion` but not scoped availability. [VERIFIED: src/pytest_bdd/steps/registry.py; src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py] |
</phase_requirements>

## Summary

Phase 22 should extend existing message reporter setup, not create a new command or parallel message pipeline. [VERIFIED: 22-CONTEXT.md] Existing `--mock-run` enters normal pytest setup, creates `ScenarioRun`, lets `StepCatalogService.pytest_runtest_setup()` emit `StepDefinition` and `TestCase`, then `PickleRunner.pytest_runtest_call()` verifies matches and returns before scenario/step lifecycle hooks and step bodies. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py; src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py]

Primary implementation should add three JSON attachment contracts emitted through Cucumber Messages `Attachment`: launch metadata per `TestCase`, matched-step binding metadata per matched `PickleStep`, and diagnostic metadata for source cardinality/missing/ambiguous step states. [VERIFIED: 22-CONTEXT.md] Current `AttachmentService` proves embedded JSON/text attachments already travel through the existing reporter, schema validation, NDJSON file output, and xdist transport paths. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py; tests/cases/integration/messages/test_message_attachments.py]

**Primary recommendation:** Add a small IDE binding service under `src/pytest_bdd/plugin/gherkin_message_reporter/` and call it from `StepCatalogService.pytest_runtest_setup()` after `TestCase` construction; add collection-time cardinality aggregation in reporter or scenario collector state keyed by source identity. [VERIFIED: codebase grep]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Message stream contract | Plugin / Reporter | Model | Reporter owns NDJSON emission and validation; model provides Cucumber object/source identity helpers. [VERIFIED: .planning/codebase/ARCHITECTURE.md] |
| Mock-run no-execution behavior | Plugin / Runner | Step definition layer | Runner already branches on `--mock-run` and resolves matches without invoking scenario/step hooks or bodies. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py] |
| Launch nodeid mapping | Plugin / Reporter | Pytest item collection | Reporter setup receives `item`; pytest item owns `nodeid`. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] |
| Source identity | Model | Reporter | `FeatureRuntimeBinding` owns AST/runtime linking for scenarios and examples rows. [VERIFIED: src/pytest_bdd/model/feature_binding.py] |
| Scoped step diagnostics | Step definition layer | Reporter / Runner | Request-local `step_registry` and `Matcher` define visible candidates; reporter should serialize diagnostics. [VERIFIED: src/pytest_bdd/steps/registry.py; src/pytest_bdd/plugin/scenario_test_collector/plugin.py] |
| Cardinality diagnostics | Collection / Reporter | Model | Collection sees all items; model resolves source AST identity. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py; src/pytest_bdd/model/feature_binding.py] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0.0 configured; local CLI reports 8.3.4 | Plugin hooks, item collection, `nodeid`, pytester tests. | Existing project runtime and tests are pytest-based. [VERIFIED: pyproject.toml; environment probe] |
| cucumber-messages | project dependency, current installed version not separately probed | Message classes such as `Attachment`, `StepDefinition`, `TestCase`, `TestStep`. | Existing reporter validates and writes Cucumber Messages envelopes. [VERIFIED: pyproject.toml; src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py] |
| attrs | project dependency | New structured runtime/service data. | Project requires `attrs` over stdlib dataclasses. [VERIFIED: pyproject.toml; AGENTS.md] |
| json stdlib | Python 3.10-3.14 | Attachment payload serialization. | Existing reporter serializes envelopes with stdlib `json`; custom attachment bodies can carry JSON strings. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py; 22-CONTEXT.md] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.0.3 | Strict validation if payload dataclasses need schema-like validation. | Use only if existing message validation style needs strict payload validation; plain `attrs` plus JSON is likely enough. [VERIFIED: pyproject.toml; ASSUMED] |
| returns | project dependency | Existing Maybe-style helpers. | Use only where local model helpers already return `Maybe`. [VERIFIED: pyproject.toml; src/pytest_bdd/model/feature_binding.py] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Attachment` payloads | Synthetic `Pickle.tags` | Rejected because tags affect mark/tag behavior and context explicitly forbids launch handles in `Pickle.tags`. [VERIFIED: 22-CONTEXT.md] |
| Reporter extension | New `--cucumber-ide-sync` CLI | Rejected by spec/context; existing `--mock-run --messages-ndjson` is contract. [VERIFIED: 22-SPEC.md; 22-CONTEXT.md] |
| IDE-side matching | Framework matcher diagnostics | Rejected by requirements; framework must compute using scoped runtime matcher universe. [VERIFIED: 22-SPEC.md] |

**Installation:** No new external package install is recommended for Phase 22. [VERIFIED: pyproject.toml; codebase grep]

## Package Legitimacy Audit

No external packages are recommended for installation in this phase. [VERIFIED: pyproject.toml; phase scope] Package legitimacy gate is not applicable. [VERIFIED: package_legitimacy_protocol]

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| None | - | - | - | - | - | No install. [VERIFIED: phase research] |

**Packages removed due to slopcheck [SLOP] verdict:** none. [VERIFIED: no packages recommended]
**Packages flagged as suspicious [SUS]:** none. [VERIFIED: no packages recommended]

## Architecture Patterns

### System Architecture Diagram

```text
pytest --mock-run --messages-ndjson report.ndjson
        |
        v
pytest collection / parametrization
        |
        +--> ScenarioTestCollector builds item params
        |       gherkin_document + pickle + feature_source
        |       id includes FeatureRuntimeBinding.pickle_table_rows_breadcrumb()
        |
        v
pytest_runtest_setup
        |
        +--> PickleRunner creates ScenarioRun in Run stash
        |
        +--> StepCatalogService emits StepDefinition + TestCase
                |
                +--> Phase 22 service emits launch attachment
                +--> Phase 22 service emits matched binding attachments
                +--> Phase 22 service records sourceIdentity cardinality
        |
        v
pytest_runtest_call
        |
        +--> if --mock-run:
        |       match each PickleStep via pytest_bdd_match_step_definition_to_step
        |       emit missing / ambiguous diagnostics
        |       skip scenario hooks, step hooks, fixtures, step bodies
        |
        +--> else:
                normal scenario lifecycle
```

Diagram reflects current setup/call split plus Phase 22 attachment insertion points. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py; src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py]

### Recommended Project Structure

```text
src/pytest_bdd/plugin/gherkin_message_reporter/
├── ide_binding_runtime.py       # launch, step-binding, diagnostic attachment builders [ASSUMED]
├── step_catalog_runtime.py      # call IDE binding service while TestCase is being built [VERIFIED: codebase grep]
└── runtime_assembly.py          # wire new service if separate lifecycle dependency is needed [VERIFIED: codebase grep]

tests/cases/integration/messages/
├── test_ide_binding_contract.py # mock-run + messages attachment contract [ASSUMED]
└── test_message_attachments.py  # existing attachment precedent [VERIFIED: codebase grep]

features/13 Code Generator/
└── 01 Code generation.feature.md # extend existing mock-run/codegen acceptance flow [VERIFIED: codebase grep]
```

### Pattern 1: Reporter Service Extension

**What:** Keep emission in reporter services and use `LifecycleService._emit_envelope()` so schema validation, NDJSON, live formatter, and xdist paths remain shared. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py]

**When to use:** Use for launch/binding/diagnostic attachments because they are message-stream artifacts, not runner behavior. [VERIFIED: 22-CONTEXT.md]

**Example:**

```python
# Source: src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py
self.lifecycle_service._emit_envelope(
    config,
    Message(
        attachment=Attachment(
            media_type="application/vnd.pytest-bdd.launch+json",
            content_encoding=AttachmentContentEncoding.identity,
            body=json.dumps(payload, sort_keys=True),
            timestamp=self.lifecycle_service.get_timestamp(),
        ),
    ),
)
```

### Pattern 2: Source Identity From FeatureRuntimeBinding

**What:** Build source identity from feature URI and AST IDs linked to Pickle/PickleStep, using row linked nodes for examples. [VERIFIED: 22-CONTEXT.md; src/pytest_bdd/model/feature_binding.py]

**When to use:** Use for duplicate binding/cardinality grouping and attachment payloads. [VERIFIED: 22-CONTEXT.md]

**Example:**

```python
# Source: src/pytest_bdd/model/feature_binding.py
scenario = feature_binding.pickle_ast_scenario(pickle)
row_ids = [row.id for row in feature_binding.pickle_ast_table_rows(pickle)]
source_identity = {
    "uri": feature_binding.uri,
    "scenarioAstNodeId": getattr(scenario, "id", None),
    "examplesRowAstNodeIds": row_ids,
}
```

### Pattern 3: Scoped Step Definition Enumeration

**What:** Enumerate `request.getfixturevalue("step_registry")` and its `.parent` chain, de-duplicating by object id. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py]

**When to use:** Use for scoped available steps and ambiguous candidate diagnostics. [VERIFIED: 22-CONTEXT.md]

**Example:**

```python
# Source: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py
seen_steps: set[int] = set()
while step_registry is not None:
    for step_definition in step_registry:
        if id(step_definition) in seen_steps:
            continue
        seen_steps.add(id(step_definition))
        yield step_definition.as_message(config)
    step_registry = step_registry.parent
```

### Anti-Patterns to Avoid

- **Synthetic tags for launch metadata:** Tags convert to pytest marks in `pytest_bdd_convert_tag_to_marks()`, so system metadata would affect user filtering. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py; 22-CONTEXT.md]
- **Implementing mock-run by replacing `pytest_bdd_get_step_caller`:** That hook is invoked after `pytest_bdd_before_step` and `pytest_bdd_before_step_call`; too late to satisfy hook/body suppression. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py; 20-RESEARCH.md]
- **IDE-side matcher reconstruction:** Step scope depends on pytest import/conftest fixture resolution and the request-local registry parent chain. [VERIFIED: src/pytest_bdd/steps/registry.py; 22-SPEC.md]
- **Counting duplicate bindings by `Pickle.id`:** Requirement says runtime Pickles can differ for same source; use source identity. [VERIFIED: 22-CONTEXT.md]

## Candidate Implementation Modules

| Module | Change | Reason |
|--------|--------|--------|
| `src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py` | New service/helper for JSON payload builders and attachment emission. [ASSUMED] | Keeps IDE contract near message reporter and avoids growing `step_catalog_runtime.py`. [VERIFIED: codebase structure] |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py` | Emit launch and matched-step binding attachments after `TestCase` is built. [VERIFIED: codebase grep] | This location has `item`, `request`, `runtime_pickle`, `test_case.id`, `TestStep` IDs, and matched `Definition` objects. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] |
| `src/pytest_bdd/plugin/pickle_runner/plugin.py` | Add mock-run missing/ambiguous diagnostic hook calls without executing lifecycle/body paths. [VERIFIED: codebase grep] | Mock-run currently verifies bindings in call phase and converts no-match to `StepDefinitionNotFoundError`. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py] |
| `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` | Optionally collect source cardinality during `pytest_collection_modifyitems`. [ASSUMED] | This hook sees all collected items and already validates zero-match scenarios. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py] |
| `src/pytest_bdd/model/feature_binding.py` | Add explicit `source_identity_for_pickle()` helper if needed. [ASSUMED] | Existing methods already resolve scenario AST, row AST, lines, and breadcrumbs. [VERIFIED: src/pytest_bdd/model/feature_binding.py] |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| NDJSON transport | Separate IDE report writer | Existing Cucumber Messages reporter | Existing reporter handles schema validation, file/stdout-compatible output, xdist aggregation, and formatter replay. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py; .planning/codebase/INTEGRATIONS.md] |
| Step matching | IDE-specific matcher | `pytest_bdd_match_step_definition_to_step` + `Matcher` | Matching depends on parser types, liberal steps, previous step, and scoped registry chain. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py; src/pytest_bdd/steps/manager.py] |
| Source line resolution | Manual Python AST scan | `Definition.as_message().source_reference` | Existing implementation resolves decorated function URI and first source line. [VERIFIED: src/pytest_bdd/steps/definition.py] |
| Examples row identity | String parsing of nodeids | `FeatureRuntimeBinding.pickle_ast_table_rows()` and `pickle_table_rows_breadcrumb()` | Existing model links Pickles to AST rows and current item IDs already include row breadcrumb. [VERIFIED: src/pytest_bdd/model/feature_binding.py; src/pytest_bdd/plugin/scenario_test_collector/plugin.py] |
| Attachments | Custom envelope shape | Cucumber `Attachment` payload | Envelope schema already includes `Attachment`; local tests validate attachment metadata. [VERIFIED: src/pytest_bdd/model/message_jsonschema/Envelope.schema.json; tests/cases/integration/messages/test_message_attachments.py] |

**Key insight:** Phase 22 is mostly a contract/composition phase; hard parts are placement, identity, and diagnostics scope, not new parsing or execution primitives. [VERIFIED: codebase grep]

## Common Pitfalls

### Pitfall 1: Mock-run Setup Emits TestCase But Call Phase Still Fails Before Diagnostics

**What goes wrong:** Missing or ambiguous match errors may abort before diagnostic attachments are emitted. [ASSUMED]
**Why it happens:** Current `_verify_mock_run_bindings()` raises `StepDefinitionNotFoundError` directly after match failure. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py]
**How to avoid:** Emit diagnostic attachments inside mock-run verification before re-raising, or add a reporter hook for lookup errors that works without scenario lifecycle. [ASSUMED]
**Warning signs:** `--mock-run --messages-ndjson` failure stream has `Suggestion` but lacks `application/vnd.pytest-bdd.diagnostic+json` attachment. [ASSUMED]

### Pitfall 2: Attachment Correlation Assumes `TestCaseStarted`

**What goes wrong:** Mock-run skips `pytest_bdd_before_scenario`, so `test_case_started_id` may be absent. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py; src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py]
**Why it happens:** `TestCaseStarted` is emitted from `pytest_bdd_before_scenario`, which mock-run bypasses. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py]
**How to avoid:** Link IDE attachments by JSON body fields (`testCaseId`, `pickleId`, `pickleStepId`) and optional `test_run_started_id`, not by `test_case_started_id`. [VERIFIED: 22-CONTEXT.md]
**Warning signs:** Launch attachments are missing in mock-run or have empty runtime correlation fields. [ASSUMED]

### Pitfall 3: Source Identity Uses Pickle Name Only

**What goes wrong:** Duplicate scenario names, rules, and examples rows collide. [ASSUMED]
**Why it happens:** Existing codegen tracks seen pickles by `(feature_uri, pickle.name)`, which is insufficient for IDE launch cardinality. [VERIFIED: src/pytest_bdd/plugin/code_generator/collection.py]
**How to avoid:** Use `uri + primary scenario astNodeId + examples row ids/breadcrumb`. [VERIFIED: 22-CONTEXT.md]
**Warning signs:** Scenario Outline rows produce one diagnostic/launch mapping instead of one per row. [VERIFIED: 22-SPEC.md]

### Pitfall 4: Available Steps Include Global Unscoped Definitions

**What goes wrong:** IDE stub/diagnostic suggestions show steps not visible to the actual pytest item. [ASSUMED]
**Why it happens:** Plugin/module registries differ from request-local fixture registry parent chains. [VERIFIED: src/pytest_bdd/steps/registry.py]
**How to avoid:** Resolve available definitions from the bound item's `request.getfixturevalue("step_registry")` and `.parent`, same as runtime matching. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py]
**Warning signs:** Diagnostic candidates differ from `pytest_bdd_match_step_definition_to_step()` results. [ASSUMED]

### Pitfall 5: Cardinality Emitted Too Early

**What goes wrong:** Diagnostics miss duplicate items because aggregation happens per item before full collection is known. [ASSUMED]
**Why it happens:** `StepCatalogService.pytest_runtest_setup()` sees one item at a time. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py]
**How to avoid:** Aggregate sourceIdentity-to-nodeid map at `pytest_collection_modifyitems` or session scope, emit per-TestCase launch attachments in setup, and emit cardinality diagnostics once per source identity. [ASSUMED]
**Warning signs:** Duplicate hookups from two test modules each emit normal launch attachments but no multiple-binding diagnostic. [VERIFIED: 22-SPEC.md]

## Risk List

| Risk | Severity | Mitigation |
|------|----------|------------|
| Mock-run fixture bodies execute while trying to collect scoped step registries. [VERIFIED: 22-CONTEXT.md] | HIGH | Limit fixture resolution to existing required fixture graph and add probe-file tests for fixture/step body suppression. [ASSUMED] |
| Existing `TestCase` contains no test steps for missing steps because `StepCatalogService` ignores `MatchNotFoundError`. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] | HIGH | Create undefined/ambiguous diagnostic attachments and consider preserving TestStep entries with empty/multiple definition IDs if feasible under schema. [ASSUMED] |
| Ambiguous match candidates are currently warning-oriented, not explicitly serialized for IDE. [VERIFIED: tests/cases/integration/feature/test_step_matching_ambiguous.py; src/pytest_bdd/steps/matcher.py] | MEDIUM | Add candidate enumeration helper in matcher or reporter; test warning plus attachment. [ASSUMED] |
| Nodeid stability may vary if pytest parametrized ID changes. [VERIFIED: src/pytest_bdd/plugin/scenario_test_collector/plugin.py] | MEDIUM | Test `pytest <nodeid>` for simple and examples rows; preserve existing param ID shape unless intentionally changed. [VERIFIED: 22-SPEC.md] |
| Attachment media type rejected by downstream formatter assumptions. [ASSUMED] | LOW | Existing attachment tests cover arbitrary media types; add contract tests that parse messages with local converter. [VERIFIED: tests/cases/integration/messages/test_message_attachments.py] |

## Code Examples

### Parse Message Attachments In Tests

```python
# Source: tests/cases/integration/messages/test_message_attachments.py
payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
attachments = list_filter_by_type(Attachment, payloads)
launch = [
    json.loads(attachment.body)
    for attachment in attachments
    if attachment.media_type == "application/vnd.pytest-bdd.launch+json"
]
```

### Assert Launch Nodeid Runs Exact Item

```python
# Source pattern: tests/cases/integration/* pytester tests
result = testdir.runpytest(*launch_payload["nodeid"].split(" ", maxsplit=0))
result.assert_outcomes(passed=1)
```

Use raw `nodeid` as a single pytest argument in implementation tests; do not split it. [VERIFIED: 22-CONTEXT.md]

### Emit Identity JSON Attachment

```python
# Source pattern: src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py
body = json.dumps(
    {
        "testCaseId": test_case.id,
        "pickleId": runtime_pickle.id,
        "nodeid": item.nodeid,
        "sourceIdentity": source_identity,
    },
    sort_keys=True,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Codegen missing-step NDJSON separate from message reporter. [VERIFIED: src/pytest_bdd/plugin/code_generator/plugin.py] | IDE bootstrap should consume Cucumber Messages NDJSON attachments. [VERIFIED: 22-CONTEXT.md] | Phase 22 context on 2026-06-05. [VERIFIED: 22-CONTEXT.md] | Planner should enhance reporter rather than codegen-only output. [VERIFIED: phase scope] |
| Mock-run only validates bindings. [VERIFIED: src/pytest_bdd/plugin/pickle_runner/plugin.py] | Mock-run plus messages becomes stable IDE sync contract. [VERIFIED: 22-SPEC.md] | Phase 22 spec on 2026-06-05. [VERIFIED: 22-SPEC.md] | Tests must assert messages and no execution. [VERIFIED: 22-SPEC.md] |
| Standard Cucumber `TestCase.testSteps[].stepDefinitionIds` enough for simple joins. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py] | Explicit binding attachments are required so IDE need not reconstruct all joins. [VERIFIED: 22-CONTEXT.md] | Phase 22 context on 2026-06-05. [VERIFIED: 22-CONTEXT.md] | Emit redundant but stable IDE payloads. [VERIFIED: 22-CONTEXT.md] |

**Deprecated/outdated:** Using `Pickle.tags` for launch metadata is rejected for this phase. [VERIFIED: 22-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Add a new `ide_binding_runtime.py` helper rather than placing all logic in `step_catalog_runtime.py`. | Candidate Implementation Modules | Planner may choose a different module boundary with same behavior. |
| A2 | Diagnostic attachments can be emitted before re-raising mock-run match errors without disrupting reporter finalization. | Common Pitfalls | Failed mock-run streams may need reporter/session finish adjustment. |
| A3 | Cardinality aggregation is best in `pytest_collection_modifyitems` or session scope. | Candidate Implementation Modules | Reporter may need a different hook placement to see both collection and emission state. |
| A4 | Pydantic is unnecessary unless strict payload validation is desired. | Standard Stack | Payload validation tasks could be underplanned if strict schemas are required. |

## Open Questions (RESOLVED)

1. **Mock-run hook taxonomy**
   - What we know: Phase 20 locked no scenario/step hooks or step bodies; Phase 22 context says some hooks may need to run if they affect step execution or add steps. [VERIFIED: 20-CONTEXT.md; 22-CONTEXT.md]
   - What's unclear: Which pytest-bdd hooks can safely run in IDE bootstrap without fixture/body execution. [VERIFIED: 22-CONTEXT.md]
   - Resolution: Plan 22-01 must create `22-HOOK-TAXONOMY.md` and probe tests before production edits. Baseline contract: collection/setup/matcher work needed to build bindings may run; scenario hooks, step hooks, `pytest_bdd_get_step_caller`, fixture bodies, and step bodies remain prohibited in mock-run. [RESOLVED: 22-01-PLAN.md]

2. **Ambiguous match candidate API**
   - What we know: Schema supports multiple `stepDefinitionIds` for ambiguous steps, and project has ambiguous-step tests. [VERIFIED: src/pytest_bdd/model/message_jsonschema/TestCase.schema.json; tests/cases/integration/feature/test_step_matching_ambiguous.py]
   - What's unclear: Whether current `Matcher` exposes all candidates cleanly or only warns/raises. [VERIFIED: codebase grep]
   - Resolution: Plan 22-03 must inspect the existing matcher path first, use it if it already exposes all ambiguous candidates, and otherwise add a narrow diagnostic-only candidate enumeration helper in `src/pytest_bdd/steps/matcher.py`. Runtime first-match behavior must not change except where ambiguity is already reported. [RESOLVED: 22-03-PLAN.md]

3. **Cardinality diagnostic timing**
   - What we know: Launch payload is naturally per `TestCase`, but cardinality needs whole-run grouping. [VERIFIED: 22-CONTEXT.md]
   - What's unclear: Whether diagnostic attachments should emit at collection end, first affected setup, or session finish. [ASSUMED]
   - Resolution: Plan 22-02 must emit duplicate-binding diagnostics only after TestCase IDs are known for all bindings in that source identity group. Zero-binding diagnostics may emit without TestCase IDs because no runnable TestCase exists. Diagnostics are de-duplicated by `sourceIdentity`. [RESOLVED: 22-02-PLAN.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Test/runtime | yes | 3.12.7 | Use project-supported Python 3.10-3.14 via `uv`. [VERIFIED: environment probe; pyproject.toml] |
| uv | Test command runner | yes | 0.11.16 | Use `python -m pytest` if uv unavailable. [VERIFIED: environment probe] |
| pytest | Test runner | yes | 8.3.4 | Install project test extra through existing dependency flow if missing. [VERIFIED: environment probe; pyproject.toml] |
| ruff | Lint/format | yes | 0.14.10 | Use `uv run ruff` if PATH ruff unavailable. [VERIFIED: environment probe] |
| rtk | Required command prefix | yes, but slow exit on some reads | available | Use `rtk powershell -NoProfile -Command ...` with higher timeout. [VERIFIED: AGENTS.md; environment behavior] |

**Missing dependencies with no fallback:** none found for research/planning. [VERIFIED: environment probe]

**Missing dependencies with fallback:** none found for research/planning. [VERIFIED: environment probe]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 locally; project requires pytest >=7.0.0. [VERIFIED: environment probe; pyproject.toml] |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`. [VERIFIED: pyproject.toml] |
| Quick run command | `rtk uv run pytest tests/cases/integration/messages tests/cases/integration/feature/test_mock_run.py -q`. [ASSUMED] |
| Full suite command | `rtk uv run pytest tests/cases -q`. [VERIFIED: .planning/codebase/TESTING.md] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| P22-01 | Mock-run messages emit Source/GherkinDocument/Pickle/StepDefinition/TestCase and skip hooks/bodies. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py -q -k mock_run_contract` | No, Wave 0. [ASSUMED] |
| P22-02 | Pickle launch payload nodeid runs exact item. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py -q -k launch_nodeid` | No, Wave 0. [ASSUMED] |
| P22-03 | Examples rows have distinct launch payload nodeids. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py -q -k examples_rows` | No, Wave 0. [ASSUMED] |
| P22-04 | Cardinality diagnostics distinguish 0/1/>1 hookups. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_binding_diagnostics.py -q -k cardinality` | No, Wave 0. [ASSUMED] |
| P22-05 | Duplicate source scenario hookups warn while preserving both handles. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_binding_diagnostics.py -q -k duplicate_hookups` | No, Wave 0. [ASSUMED] |
| P22-06 | Attachment metadata does not affect marks/tag hooks. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py -q -k metadata_isolation` | No, Wave 0. [ASSUMED] |
| P22-07 | Matched steps resolve through binding attachments to sourceReference. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_step_bindings.py -q -k matched_steps` | No, Wave 0. [ASSUMED] |
| P22-08 | Missing and ambiguous diagnostics include scoped available/candidates. | integration | `rtk uv run pytest tests/cases/integration/messages/test_ide_step_bindings.py -q -k 'missing or ambiguous'` | No, Wave 0. [ASSUMED] |

### Sampling Rate

- **Per task commit:** `rtk uv run pytest tests/cases/integration/messages tests/cases/integration/feature/test_mock_run.py -q`. [ASSUMED]
- **Per wave merge:** `rtk uv run pytest tests/cases/integration/messages tests/cases/integration/feature tests/cases/integration/generation -q`. [ASSUMED]
- **Phase gate:** `rtk uv run pytest tests/cases -q` plus targeted feature-level E2E for Code Generator docs. [VERIFIED: .planning/codebase/TESTING.md; 22-CONTEXT.md]

### Wave 0 Gaps

- [ ] `tests/cases/integration/messages/test_ide_binding_contract.py` - covers P22-01, P22-02, P22-03, P22-06. [ASSUMED]
- [ ] `tests/cases/integration/messages/test_ide_binding_diagnostics.py` - covers P22-04, P22-05. [ASSUMED]
- [ ] `tests/cases/integration/messages/test_ide_step_bindings.py` - covers P22-07, P22-08. [ASSUMED]
- [ ] `features/13 Code Generator/01 Code generation.feature.md` update or companion feature for IDE bootstrap contract. [VERIFIED: 22-CONTEXT.md; codebase grep]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth surface in local pytest plugin. [VERIFIED: .planning/codebase/INTEGRATIONS.md] |
| V3 Session Management | no | No web/user sessions. [VERIFIED: .planning/codebase/INTEGRATIONS.md] |
| V4 Access Control | no | Local developer test runner only. [VERIFIED: .planning/codebase/INTEGRATIONS.md] |
| V5 Input Validation | yes | JSON payloads should be deterministic and parseable; use existing message schema validation plus targeted JSON attachment tests. [VERIFIED: src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py; tests/cases/integration/messages/test_message_attachments.py] |
| V6 Cryptography | no | No cryptographic behavior in phase scope. [VERIFIED: 22-SPEC.md] |

### Known Threat Patterns for pytest/message stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection through nodeid launch metadata | Tampering / Elevation | Store raw nodeid as JSON data and tests should pass it as one pytest argv element; do not shell-compose command strings. [VERIFIED: 22-CONTEXT.md; ASSUMED] |
| User filtering altered by system metadata | Tampering | Use Attachment carrier, not tags/marks. [VERIFIED: 22-CONTEXT.md] |
| Leaking absolute source paths unexpectedly | Information Disclosure | Existing `sourceReference` already uses file URI from root-relative resolution; Phase 22 should not add broader filesystem data. [VERIFIED: src/pytest_bdd/steps/definition.py] |
| Executing untrusted test code in IDE bootstrap | Elevation | Mock-run must skip fixture bodies and step bodies; add probe-file tests. [VERIFIED: 22-SPEC.md; 22-CONTEXT.md] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/22-test-step-binding-api/22-SPEC.md` - phase requirements and acceptance criteria. [VERIFIED: file read]
- `.planning/phases/22-test-step-binding-api/22-CONTEXT.md` - locked decisions for attachments, source identity, diagnostics, mock-run timing, test folding. [VERIFIED: file read]
- `.planning/ROADMAP.md` - phase dependency and goal. [VERIFIED: file read]
- `.planning/REQUIREMENTS.md` - project requirements context. [VERIFIED: file read]
- `.planning/codebase/ARCHITECTURE.md` - runtime architecture, stash, collector, runner, reporter layers. [VERIFIED: file read]
- `.planning/codebase/TESTING.md` - pytester/integration/message test patterns. [VERIFIED: file read]
- `.planning/codebase/INTEGRATIONS.md` - local NDJSON, Cucumber Messages, storage/security context. [VERIFIED: file read]
- `.planning/phases/20-codegen-step-binding-and-tolerant-steps/20-CONTEXT.md` - mock-run/codegen prior decisions. [VERIFIED: file read]
- `.planning/phases/21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl/21-CONTEXT.md` - prior runtime/reporting integration context. [VERIFIED: file read]
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` - mock-run and execution lifecycle. [VERIFIED: codebase grep]
- `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py` - StepDefinition/TestCase/TestStep emission and scoped registry enumeration. [VERIFIED: codebase grep]
- `src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py` - Attachment emission. [VERIFIED: codebase grep]
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` - parametrization, tag-to-mark conversion, matcher hook. [VERIFIED: codebase grep]
- `src/pytest_bdd/model/feature_binding.py` - source AST and examples row helpers. [VERIFIED: codebase grep]
- `src/pytest_bdd/steps/definition.py`, `src/pytest_bdd/steps/registry.py` - step source references and scoped registry chain. [VERIFIED: codebase grep]
- `tests/cases/integration/messages/test_message_attachments.py`, `tests/cases/contract/messages/test_messages.py` - message parsing and attachment tests. [VERIFIED: codebase grep]

### Secondary (MEDIUM confidence)

- None used. [VERIFIED: research process]

### Tertiary (LOW confidence)

- Implementation module boundary recommendations marked `[ASSUMED]`. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing project dependencies and local environment were read/probed. [VERIFIED: pyproject.toml; environment probe]
- Architecture: HIGH - runner/reporter/collector/model integration points were inspected directly. [VERIFIED: codebase grep]
- Pitfalls: MEDIUM - placement risks are verified, but some diagnostics timing mitigations remain design assumptions. [VERIFIED: codebase grep; ASSUMED]

**Research date:** 2026-06-05 [VERIFIED: system date]
**Valid until:** 2026-07-05 for codebase-local planning unless Phase 22 context changes. [ASSUMED]
