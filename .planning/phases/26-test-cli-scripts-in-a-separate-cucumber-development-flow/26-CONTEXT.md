# Phase 26: Test CLI scripts in a separate Cucumber Development flow - Context

**Gathered:** 2026-06-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 26 documents and verifies repository development workflows through executable BDD coverage. Scope is the development-script surface used by contributors and CI: CLIs, helper scripts, and pre-commit quality gates that previously had indirect or ad hoc coverage.

In scope: `allure-cucumber`, `validate_feature_headings.py`, `scripts/arch.py`, `compatibility_matrix`, `sync_messages_contract_schemas.py`, `render_cucumber_formatters`, and `scripts/run_messages_coverage_audit.sh`.

Out of scope: changing production behavior except where required to make the Development feature scenarios pass, redesigning the E2E harness, or mutating global user environment during scenarios.
</domain>

<spec_lock>
## Requirements (locked via SPEC.md)

**11 requirements are locked.** See `26-SPEC.md` for full requirements, boundaries, and acceptance criteria.

Downstream agents MUST read `26-SPEC.md` before planning or implementing. Requirements are not duplicated here.

**In scope (from SPEC.md):**
- Add a Development BDD feature space covering repository-specific scripts, CLIs, and pre-commit quality gates.
- Add shared development step definitions for mock file setup, command execution in the test directory, exit-code checks, and stdout/stderr assertions.
- Register development steps in the E2E conftest and add an E2E loader for `features/18 Development/`.
- Cover the `allure-cucumber` converter CLI with success and missing-input scenarios.
- Cover `validate_feature_headings.py` clean and failing heading validation scenarios.
- Cover `scripts/arch.py` responsibility injection, score collection, and gap analysis scenarios.
- Cover the `compatibility_matrix` CLI compatibility, tox environment, and E2E migration-report scenarios.
- Cover `sync_messages_contract_schemas.py` clean and drift scenarios.
- Cover `render_cucumber_formatters` standalone NDJSON-to-summary rendering.
- Cover `scripts/run_messages_coverage_audit.sh` governance report orchestration.
- Update Phase 26 roadmap/planning artifacts.

**Out of scope (from SPEC.md):**
- Changing production behavior except where required to make the Development feature scenarios pass.
- Redesigning the E2E harness.
- Mutating global user environment during scenarios.
</spec_lock>

<decisions>
## Implementation Decisions

### CLI Invocation Strategy
- **D-01:** BDD scenarios will invoke the python interpreter directly for entrypoint scripts (e.g. using `python src/pytest_bdd/script/validate_feature_headings.py`).
- **D-02:** Non-entrypoint scripts (e.g. `scripts/arch.py`) will be invoked via python interpreter directly using relative paths from the repository root, with PYTHONPATH resolving to the repository root.
- **D-03:** Standard output and error output assertions in BDD scenarios will use substring/regex matching (e.g., `the renderer terminal output includes:` with tabular lines) to remain robust against minor output format updates.
- **D-04:** Scenarios must rely only on Python scripts for execution. The presence of any shell scripts (such as `scripts/run_messages_coverage_audit.sh`) will be reported/documented as an architectural gap/risk instead of running them directly in E2E tests.

### the agent's Discretion
- Whichever step names and file structures are cleanest for writing feature files and step mappings under `src/pytest_bdd_testing/step/development.py`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Feature Specs and Exploration
- `specs/026-dev-scripts-bdd/development_script_exploration.md` — candidates analysis
- `specs/026-dev-scripts-bdd/plan.md` — implementation plan
- `.planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-SPEC.md` — locked requirements

### Codebase Maps
- `.planning/codebase/TESTING.md` — testing patterns
- `.planning/codebase/CONVENTIONS.md` — coding conventions
- `.planning/codebase/STRUCTURE.md` — directory structure
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd_testing/step/harness.py`: contains `run '{command}'` and `the renderer terminal output includes:` steps which are reused.
- `src/pytest_bdd_testing/step/development.py`: provides mock file creation and exit code check steps.

### Established Patterns
- `testdir` based file setups and command runs in BDD integration/E2E test files.

### Integration Points
- `src/pytest_bdd_testing/case/e2e/conftest.py` imports step definitions.
- `src/pytest_bdd_testing/case/e2e/feature/test_18_development.py` loads features under `features/18 Development/`.
</code_context>

<specifics>
## Specific Ideas
- All BDD scenarios use the Python interpreter directly rather than relying on system path console scripts.
</specifics>

<deferred>
## Deferred Ideas
- Resolving the `test_undefined_parameter_runtime.py` probe warning issue is documented as a known risk/limitation rather than being fixed in this phase.
</deferred>

---

*Phase: 26-Test CLI scripts in a separate Cucumber Development flow*
*Context gathered: 2026-06-20*
