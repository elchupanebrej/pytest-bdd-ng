# Phase 21: adapt-plugin-system-of-allure-python-commons - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the current file-first Allure pytest wrapper with a pytest-native Allure integration that consumes pytest-bdd-ng Cucumber Messages and writes Allure results through `allure-python-commons`.

This phase owns the pytest plugin path, live `pytest_bdd_message` ingestion, NDJSON import mode, `allure-python-commons` output, xdist total report behavior, option/config migration, and verification that generated Allure reports are correct.

</domain>

<spec_lock>
## Requirements (locked via SPEC.md)

**8 requirements are locked.** See `21-SPEC.md` for full requirements, boundaries, and acceptance criteria.

Downstream agents MUST read `21-SPEC.md` before planning or implementing. Requirements are not duplicated here.

**In scope (from SPEC.md):**
- New pytest-native Allure plugin behavior using `allure-python-commons`.
- `pytest_bdd_message` consumer implementation.
- Allure output option for normal pytest mode.
- NDJSON import mode behavior.
- Compatibility with `allure-pytest` absent or present, without depending on it.
- Shared hook/NDJSON ingestion adapter.
- xdist total aggregation for Allure output.
- Updated contracts, docs, and e2e UAT for new behavior.

**Out of scope (from SPEC.md):**
- Depending on `allure-pytest`.
- Preserving the old messages option as the main user API.
- Keeping the old "no allure-python-commons" decision for the pytest plugin path.
- Changing pytest-bdd-ng scenario execution semantics.
- Building or serving HTML report as plugin responsibility.

**Context override:** User explicitly overrode the SPEC option names during discussion. Use `--allure-cucumber-output` and `--allure-cucumber-messages-in` as the new pytest-native option names instead of the SPEC names `--allure-bdd-output` and `--allure-bdd-messages-in`. Planner must reconcile this conflict before implementation.

</spec_lock>

<decisions>
## Implementation Decisions

### Ingestion State Model
- **D-01:** Use the existing `EnvelopeRegistry` first for live hook mode, but make the design xdist-aware. Hook mode must read the consolidated controller stream/registry, not raw per-worker partial streams.
- **D-02:** NDJSON import mode feeds the same adapter after reading the file. Hook mode and import mode share conversion semantics.
- **D-03:** xdist Allure conversion happens on the controller only. Workers forward messages; the controller consolidates and writes one result directory.
- **D-04:** NDJSON import mode must avoid BDD scenario collection/execution as source of truth. Prefer narrow collection skip or early no-op behavior only when `--allure-cucumber-messages-in` is present, so normal pytest mode stays untouched.
- **D-05:** Supplying live mode and NDJSON import inputs at the same time is a configuration conflict and must fail clearly.

### Allure Lifecycle Boundary
- **D-06:** Rewrite the pytest output path around `allure-python-commons` objects/lifecycle. Use the Phase 20 mapper as a reference and golden semantic baseline, not as a wrapped JSON emitter.
- **D-07:** Treat the standalone `allure-cucumber` converter as deprecated legacy utility. Phase 21 focuses on the pytest-native path. It may remain temporarily for compatibility/reference, but docs and warnings should point users to the new pytest plugin path.
- **D-08:** Use `allure-python-commons` native presentation to maximum useful feature coverage. Preserve semantic equivalence with Phase 20, but visible output may improve when commons supports richer attachment, parameter, label, or detail APIs.
- **D-09:** Coexist with `allure-pytest` without coupling. The plugin must not import or depend on `allure-pytest`; detect duplicate Allure result risks and avoid duplicate BDD results.

### xdist Aggregation Ownership
- **D-10:** Consume the final consolidated controller stream from the existing message reporter/consolidation path.
- **D-11:** If consolidation diagnostics exist, default to generating a partial report with a warning. Provide an optional strict/fail mode for gate behavior.
- **D-12:** Attachment data/references are owned by the message stream. The controller resolves attachments from consolidated envelopes. Workers must not write shared final-truth Allure files.
- **D-13:** Do not wipe the Allure output directory by default. Create/append safely and warn when the target directory is non-empty.

### CLI/API Migration Shape
- **D-14:** Override the SPEC option names. New pytest-native options must start with `--allure-cucumber-*`; do not expose `--allure-bdd-*` as primary names.
- **D-15:** Use `--allure-cucumber-output` for output and `--allure-cucumber-messages-in` for NDJSON import.
- **D-16:** Remove the current `--allure-cucumber-messages` option immediately. Unknown option failure is acceptable.
- **D-17:** INI and CLI option must coexist and correspond to each other. CLI option wins when present; INI remains fallback configuration for the same output concept.

### Verification Surface
- **D-18:** Completion requires full layered proof: hook-level contract, NDJSON import, hook-vs-import golden equivalence, full e2e feature surface, xdist total report, and `allure-pytest` absent/present.
- **D-19:** Allure HTML rendering via Docker/Playwright is blocking verification, not optional smoke.
- **D-20:** Test both environments: one without `allure-pytest`, one with it installed. Assert no dependency and no duplicate BDD results.
- **D-21:** xdist proof must use real `pytest -n 2` with multiple BDD scenarios and attachments. Assert one total Allure report, no duplicate scenarios, and all attachments present.
- **D-22:** Include via/socket connection usage in distributed verification coverage.

### Hook-Based Interception Architecture (NEW — 2026-06-14)
- **D-23:** The plugin MUST intercept `pytest_bdd_message` calls and produce Allure results **in real-time** during test execution, not batch at session finish. Each envelope is deserialized, routed by `payload_kind`, and written through `AllureLifecycle` incrementally.
- **D-24:** Plugin architecture follows `allure-pytest` / `allure-pytest-bdd` patterns: `entrypoint.py` + `listener.py` + `api_hooks.py` + `message_adapter.py`. The `MessageDrivenListener` class replaces the current batch-collecting `AllureCucumberPlugin`.
- **D-25:** A separate `AllureCucumberApiHooks` class is registered with `allure_commons.plugin_manager` to implement allure-commons hooks (`start_step`, `stop_step`, `attach_data`, etc.), following the `AllurePytestBddApiHooks` pattern from `allure-pytest-bdd`.
- **D-26:** The `EnvelopeStateCache` (inspired by `allure-pytest`'s `ItemCache`) tracks `test_case_started_id → Allure uuid` mappings for step parenting and test result lifecycle management.
- **D-27:** Reference implementations used as architectural pattern source:
  - `allure-framework/allure-python/allure-pytest-bdd/src/pytest_bdd_listener.py` — listener pattern, step lifecycle
  - `allure-framework/allure-python/allure-pytest-bdd/src/allure_api_listener.py` — API hooks pattern
  - `allure-framework/allure-python/allure-pytest/src/listener.py` — cache pattern, hookwrapper approach
  - `allure-framework/allure-python/allure-pytest-bdd/src/plugin.py` — registration and cleanup patterns

### the agent's Discretion
- Exact `allure-python-commons` lifecycle/logger API shape, provided it writes through commons and preserves or improves Phase 20 semantics.
- Exact narrow mechanism for import-mode collection skip/no-op, provided running scenarios are not source of truth in import mode.
- Exact strict/fail flag name for consolidation diagnostics.
- Exact tests/files split, provided the blocking proof in D-18 through D-22 is satisfied.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition and Requirements
- `.planning/ROADMAP.md` - Phase 21 goal, dependency on Phase 20, and success criteria.
- `.planning/phases/21-adapt-plugin-system-of-allure-python-commons/21-SPEC.md` - Locked requirements, boundaries, constraints, and acceptance criteria. Also contains original `--allure-bdd-*` names that this context overrides.
- `.planning/PROJECT.md` - Project constraints: pytest-native plugin architecture, Cucumber reporting interoperability, `attrs`, `StashBound`, compatibility matrix.
- `.planning/REQUIREMENTS.md` - CCK and reporting requirement traceability.

### Prior Allure and Reporting Context
- `.planning/phases/20-docs-architecture-allure-md/20-CONTEXT.md` - Phase 20 Allure converter assets, CCK verification patterns, and existing Allure references.
- `docs/architecture/allure.md` - Architecture document created by Phase 20; should be updated to reflect pytest-native commons path and converter deprecation.

### Existing Allure Plugin and Converter
- `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` - Current pytest option registration and plugin registration.
- `src/pytest_bdd/plugin/allure_cucumber/plugin.py` - Current file-first pytest wrapper that converts NDJSON at session finish.
- `src/pytest_bdd/plugin/allure_cucumber/cli.py` - Standalone legacy converter entry point.
- `src/pytest_bdd/plugin/allure_cucumber/converter/converter.py` - Current NDJSON to Allure JSON conversion orchestration.
- `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py` - Phase 20 semantic mapping reference for scenario, step, status, tag, parameter, and attachment semantics.
- `src/pytest_bdd/plugin/allure_cucumber/converter/model.py` - Existing Allure JSON model reference.

### Message Runtime and xdist
- `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` - `pytest_bdd_message` and `pytest_bdd_xdist_message_batch` hook specs.
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py` - Live message emission, registry storage, session lifecycle, and controller finalization behavior.
- `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py` - Worker/controller message transport and final stream path behavior.
- `src/pytest_bdd/model/message_registry.py` - Existing `EnvelopeRegistry` to use first for live ingestion.
- `src/pytest_bdd/model/message_consolidation.py` - Existing xdist consolidation, diagnostics, ID namespacing, and total stream semantics.
- `src/pytest_bdd/model/execution_message_adapter.py` - Serialization/deserialization and ID namespace helpers.

### Verification Assets
- `tests/cases/contract/cck/conftest.py` - Existing CCK/Allure fixtures and report-generation helpers.
- `tests/cases/contract/cck/test_cck_allure_conversion.py` - Conversion contract test references.
- `tests/cases/contract/cck/test_cck_allure_rendering.py` - Docker/Playwright rendering test references.
- `tests/cases/contract/allure/test_allure_consumption_ui.py` - `_run_allure_docker()` pattern.
- `tests/cases/contract/messages/test_messages_feature_suite.py` - HTTP serving and Playwright browser path patterns.
- `tests/cases/integration/hook/test_gherkin_reporter_context_lifecycle.py` - Hook/runtime/xdist message behavior tests.
- `tests/cases/external/e2e/test_xdist_remote_message_aggregation.py` - Remote xdist via/socket style verification reference.
- `features/17 Allure Converter/` - Existing Allure-related executable feature docs location.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EnvelopeRegistry` stores emitted envelopes in `config.stash`; use this before inventing new hook-mode state.
- `message_consolidation.py` already provides xdist controller total stream semantics, diagnostics, ID namespacing, and deduplication.
- `LifecycleService.pytest_bdd_message` already serializes, validates, registers, emits live formatter lines, and queues message JSON.
- Phase 20 `allure_cucumber.converter` mapper is semantic reference for current Allure result shape.
- CCK/Docker/Playwright test helpers already exist and should be reused for blocking HTML verification.

### Established Patterns
- Plugin structure follows `entrypoint.py` plus `plugin.py`, with `attrs` classes for state.
- Runtime state should use `config.stash` and `StashBound` patterns, not direct ad hoc stash access.
- Cross-plugin communication should use pytest/pluggy hooks or public contracts, not deep direct imports when avoidable.
- xdist workers should forward/report message streams; controller owns final aggregation.
- Makefile and tox are the preferred verification command surfaces.

### Integration Points
- Update `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` for new option semantics.
- Replace file-first behavior in `src/pytest_bdd/plugin/allure_cucumber/plugin.py` with pytest-native hook/import orchestration.
- Add or update an adapter layer that converts consolidated Cucumber envelopes to `allure-python-commons` lifecycle/logger calls.
- Reuse message reporter finalization/consolidation for xdist rather than creating an Allure-specific worker merge path.
- Update `pyproject.toml` extras/entry points/docs if old converter CLI semantics change or deprecation needs packaging metadata.

</code_context>

<specifics>
## Specific Ideas

- New user-facing option names are `--allure-cucumber-output` and `--allure-cucumber-messages-in`.
- Existing `--allure-cucumber-messages` should be removed rather than kept as deprecated alias.
- Non-empty output directories should trigger a warning, not automatic cleanup.
- Consolidation warnings should still produce partial Allure output by default; strict/fail mode should be available.
- Verification must include via/socket distributed connection usage in addition to normal local `pytest -n 2`.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

### Reviewed Todos (not folded)
- **Improve library typing using best practices from awesome-python-typing** - generic typing improvement; not folded into Phase 21.
- **Integrate BDD/ATDD tests into development workflow and UAT phase** - broad process change; Phase 21 only needs its own acceptance and UAT coverage.
- **Vulture must be run not via pytest but as pre-commit hook** - unrelated and already handled by prior scope.
- **Split xdist-remote tests into separate parallel GHA executor job** - already Phase 18 scope; only distributed verification patterns carry forward.
- **Adapt GitHub CI to use make and validate with act** - prior CI workflow scope; only Makefile/test boundary patterns carry forward.
- **No TestClasses are allowed in tests** - style enforcement outside this phase.
- **Fix Makefile SHELL for cross-platform (Win/Mac/Linux)** - prior tooling scope; not folded.

</deferred>

---

*Phase: 21-adapt-plugin-system-of-allure-python-commons*
*Context gathered: 2026-06-13*
