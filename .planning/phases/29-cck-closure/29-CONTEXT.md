# Phase 29: CCK Closure - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Close CCK-01 through CCK-07 documentation gaps from v1.0 milestone audit — reconcile requirements, specs, and verification artifacts with actual implementation state.

This is a documentation reconciliation phase. The implementation already exists; the plan (29-01-PLAN.md) is already complete.

</domain>

<decisions>
## Implementation Decisions

### Documentation Reconciliation
- **D-01:** CCK-01 through CCK-07 requirements are already marked [x] in REQUIREMENTS.md with accurate implementation notes (44 samples not 45, allure3-local:latest Docker image, feature file at `features/12 Formatters/08` not `features/17 Allure Converter/3`)
- **D-02:** Spec 045 success criteria are all marked [x] — the spec goal text was updated to reflect 44 samples
- **D-03:** VERIFICATION.md exists at `.planning/phases/29-cck-closure/VERIFICATION.md`
- **D-04:** ROADMAP.md includes Phase 29 in the progress table with status "Complete"

### Reconciliation Gaps Identified
- **D-05:** Traceability table in REQUIREMENTS.md (lines 137-143) still shows CCK-01..07 as "Pending" and mapped to "Phase 20 — Allure Converter Wave 6" — needs update to "Complete" and "Phase 29 — CCK Closure"
- **D-06:** Spec 045 architecture section (line 48) still references `frankescobar/allure-docker-service:2.27.0` — actual image is `allure3-local:latest` (upgraded in quick task 260611)
- **D-07:** Spec 045 architecture section (line 65) still references `features/17 Allure Converter/3 CCK Allure compatibility.feature.md` — actual path is `features/12 Formatters/08 CCK Allure compatibility.feature.md`
- **D-08:** Spec 045 Section 4 (line 107) says "45 CCK samples" — should be "44 CCK samples" (CCK v29.2.2)

### CCK-05 Partial Implementation
- **D-09:** CCK-05 contract tests: 3 of 10 edge cases implemented (empty NDJSON, single-line, failed scenarios); remaining 7 deferred as low-priority — this is an intentional scope decision, not a gap

### the agent's Discretion
- Traceability table updates, spec 045 stale references, and sample count correction are straightforward edits that downstream agents can apply without further discussion

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCK Compatibility
- `specs/045-cck-allure-compatibility/spec.md` — CCK pipeline spec with stale Docker image and feature file path references
- `specs/045-cck-allure-compatibility/plan.md` — CCK pipeline implementation plan
- `.planning/REQUIREMENTS.md` lines 43-51 — CCK-01 through CCK-07 requirement definitions
- `.planning/REQUIREMENTS.md` lines 137-143 — CCK traceability table (needs Phase/Status update)

### Implementation Evidence
- `src/pytest_bdd/testing/cck.py` — CCK download utility (session-scoped, gh api with fallback)
- `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py` — Playwright validation tests (parameterized for all 44 samples)
- `features/12 Formatters/08 CCK Allure compatibility.feature.md` — BDD feature file for the pipeline
- `.planning/phases/29-cck-closure/VERIFICATION.md` — Phase 29 verification report
- `.planning/phases/29-cck-closure/29-01-PLAN.md` — Phase 29 plan (complete)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- CCK download fixture: `src/pytest_bdd/testing/cck.py` — session-scoped, handles gh api + raw.githubusercontent.com fallback
- Allure converter: `allure_cucumber.converter.converter.convert()` — existing NDJSON-to-Allure conversion
- Docker Allure rendering: `allure3-local:latest` — custom image (upgraded from frankescobar)
- Playwright validation: `TestCCKAllureUIValidation` — parameterized browser checks for scenario names, step names, statuses

### Established Patterns
- CCK tests are marked with `@pytest.mark.docker`, `@pytest.mark.browser`, `@pytest.mark.slow`, `@pytest.mark.contract`
- Feature file uses background steps for CCK sample availability
- Step definitions in `tests/cases/e2e/steps_cck_allure.py` registered via `pytest_plugins`

### Integration Points
- CCK tests live at `src/pytest_bdd_toolchain/case/contract/cck/`
- Feature file at `features/12 Formatters/08 CCK Allure compatibility.feature.md`
- E2E loader at `src/pytest_bdd_toolchain/case/e2e/feature/test_12_formatters.py`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — the reconciliation edits are straightforward (traceability table update, spec 045 stale reference corrections).

</specifics>

<deferred>
## Deferred Ideas

### Strict Module API and Import Pylint Rules
- **Source:** Pending todo `2026-07-01-strict-module-api-import-rules.md`
- **Problem:** Project moving away from package facades; current pylint rules (BLQ1401-BLQ1404) forbid `__all__` in non-`__init__.py` files but a stricter contract is desired
- **Scope:** 12 new custom pylint rules enforcing module export discipline and import boundaries
- **Why deferred:** New capability requiring significant pylint rule implementation, module `__all__` additions to ~50+ files, and pre-commit updates — belongs in its own phase (candidate for Phase 30)

</deferred>

---

*Phase: 29-CCK Closure*
*Context gathered: 2026-07-02*
