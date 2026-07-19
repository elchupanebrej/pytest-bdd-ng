# Phase 35: improve-library-typing-using-best-practices-from-awesome-pyt - Context

**Gathered:** 2026-07-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the complete `src/` production and toolchain codebase conform to strict static typing, without broad checker bypasses. Preserve Python 3.10-3.14 support, establish a non-regressing implementation gate, and validate the installed `pytest_bdd` distribution's documented public typing contract.

</domain>

<decisions>
## Implementation Decisions

### Typing Pass Scope
- **D-01:** Cover all production and toolchain source code, not merely `src/pytest_bdd` or selected high-risk paths.
- **D-02:** Completion means every source module passes its configured checker or checkers without module-wide `ignore_errors`.
- **D-03:** Treat static incompatibilities discovered during the pass as defects; do not preserve them solely because dynamic runtime use currently accepts them.
- **D-04:** Add a CI gate that reports no checker errors for both source packages.

### Checker Strategy
- **D-05:** Use strict mypy as the primary implementation gate, supplemented by public-distribution and consumer-contract validation.
- **D-06:** Require 100% public type completeness immediately; do not introduce a temporary ratchet or baseline.
- **D-07:** Run a discovery spike against upstream Pyright strict and Astral ty after the source pass. Promote neither to a whole-source blocking gate unless the results justify it under the no-broad-suppression policy.
- **D-08:** Run supplementary static validation for Python 3.10 and platform `All`, in addition to the primary mypy configuration's current newest-supported target.

### Suppressions and Third-Party Boundaries
- **D-09:** Do not use suppressions for unresolved typing issues. Resolve them in the code, in a local type boundary, or upstream where appropriate.
- **D-10:** Address inadequate dependency typing locally first; contribute upstream when the fix is reusable.
- **D-11:** Model dynamic pytest, pluggy, and attrs boundaries through direct public framework types plus project-owned protocols or adapters where those public types are insufficient.
- **D-12:** Put Python 3.10-3.14 typing compatibility logic in central compatibility modules rather than scattering version-specific imports at call sites.

### Scope Amendment — 2026-07-13

- **D-01A:** `src/pytest_bdd_toolchain/case/**` is the repository's test/case suite,
  not production or toolchain implementation. It is outside Phase 35's strict-mypy
  implementation gate.
- **D-02A:** The configured mypy gate excludes the test suite with the narrowly scoped
  `pytest_bdd_toolchain.case.*` override. All remaining in-scope `pytest_bdd` and
  `pytest_bdd_toolchain` implementation modules must pass without suppressions.
- **D-09A:** This exclusion is a documented test-scope boundary, not permission to
  suppress unresolved errors in any in-scope module.

### Public Typing Contracts
- **D-13:** Validate consumer contracts against an installed wheel in an isolated environment; source-tree fixture checks are not authoritative.
- **D-14:** Cover every documented public API family with representative fixtures: scenario binding, step decorators and fixture injection, parser types, hooks, reporters/configuration, and package re-exports.
- **D-15:** Each API-family fixture includes valid examples that must pass and deliberately invalid examples that must be rejected with the intended diagnostic category.
- **D-16:** Run both mypy and upstream Pyright against the public consumer fixtures.

### the agent's Discretion
- The planner determines the exact fixture layout, diagnostic matching mechanism, CI job boundaries, and the locally appropriate type constructs for each dynamic boundary.
- The planner classifies findings from the Pyright strict and ty discovery spike and records the evidence for any later gate decision.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements and Research
- `.planning/ROADMAP.md` — Phase 35's fixed roadmap boundary and dependency on Phase 34.
- `.planning/PROJECT.md` — supported Python versions, public-library compatibility constraints, and project conventions.
- `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-VALIDATION-RESEARCH.md` — baseline findings and the evaluated layered-validation approach; consult its primary-source links when implementing checker configuration.
- `docs/research/type-checker-comparison.md` — prior local Pyright/ty comparison; rerun it against the completed scope rather than treating its counts as current.

### Existing Typing and Packaging Configuration
- `pyproject.toml` — strict mypy configuration, source-package scope, current exceptions, package metadata, and `py.typed` packaging rules.
- `.pre-commit-config.yaml` — existing mypy hook and development-quality integration point.
- `.github/workflows/lint.yml` — CI lint/type-check integration point.
- `src/pytest_bdd/py.typed` — PEP 561 marker included in the published library distribution.
- `src/pytest_bdd/compatibility/typing.py` — centralized cross-version typing compatibility pattern.
- `stubs/` — local third-party dependency typing boundaries; not a public companion-stub package.

### Public API and Contract Test Targets
- `src/pytest_bdd/__init__.py` — top-level package boundary and package-export policy.
- `src/pytest_bdd/scenario.py` — scenario binding public API.
- `src/pytest_bdd/steps/` — public step-decorator and registration contracts.
- `tests/compatibility/` — existing public API and compatibility validation patterns.
- `tests/feature/` — `pytester` integration-test patterns for externally observable behavior.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Strict mypy is already configured in `pyproject.toml`, targeted at both source packages, and is invoked by pre-commit; Phase 35 hardens this rather than creating a separate primary checker.
- `src/pytest_bdd/compatibility/typing.py` centralizes version-gated typing imports and is the established location for Python 3.10 compatibility logic.
- `src/pytest_bdd/py.typed` provides the packaging marker that Pyright `--verifytypes` and installed-wheel consumers must validate.
- `tests/compatibility/` and `tests/feature/` provide existing public-surface and consumer-style test locations and patterns.

### Established Patterns
- Source uses future annotations, project-local compatibility facades, explicit type annotations, and narrow `TYPE_CHECKING` imports.
- The library is attrs-, pytest-, and pluggy-heavy; dynamic framework boundaries need typed adapters/protocols rather than broad suppressions or framework-internal imports.
- The supported runtime matrix is Python 3.10-3.14, while the current mypy target is newest-supported Python; supplementary validation must exercise the 3.10 contract.

### Integration Points
- `pyproject.toml`, `.pre-commit-config.yaml`, and `.github/workflows/lint.yml` are the primary configuration and CI entry points for the implementation gate.
- Wheel build/install flow is the integration point for Pyright `--verifytypes` and external consumer fixtures.
- Public owner modules and package re-exports are the inventory for the contract-fixture suite; the planner must derive the exact documented surface rather than assuming the top-level package alone defines it.

</code_context>

<specifics>
## Specific Ideas

- Public validation is deliberately layered: strict mypy validates implementation; Pyright `--verifytypes` validates the shipped `pytest_bdd` contract; installed-wheel fixtures validate user-facing inference and rejection behavior.
- Negative fixture assertions should match diagnostic categories or codes rather than brittle full diagnostic wording.
- `pytest_bdd_toolchain` is in scope for strict implementation typing but is not a published-distribution contract target.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt*
*Context gathered: 2026-07-12*
