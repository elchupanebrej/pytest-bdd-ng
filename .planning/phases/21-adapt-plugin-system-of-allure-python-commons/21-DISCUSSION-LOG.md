# Phase 21: adapt-plugin-system-of-allure-python-commons - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 21-adapt-plugin-system-of-allure-python-commons
**Areas discussed:** Ingestion state model, Allure lifecycle boundary, xdist aggregation ownership, CLI/API migration shape, Verification surface

---

## Ingestion State Model

| Question | Options | User's choice |
|----------|---------|---------------|
| How should live hook envelopes and NDJSON import feed shared adapter? | Stash-bound stream; Adapter-only iterator; Existing registry first; You decide | Existing registry first, with xdist awareness |
| For xdist, where should Allure conversion happen? | Controller only; Worker-local then merge files; Hybrid fallback; You decide | Controller only |
| NDJSON import mode should run inside pytest how? | Session-only import; Collection skip mode; Separate CLI only; You decide | Collection skip mode |
| What should happen if both live mode and NDJSON import inputs are supplied? | Reject conflict; Prefer NDJSON; Merge both; You decide | Reject conflict |

**Notes:** User explicitly reminded that xdist must be remembered. Final decision: live mode reads consolidated controller stream/registry, import mode feeds the same adapter from file, and mixed source-of-truth fails.

---

## Allure Lifecycle Boundary

| Question | Options | User's choice |
|----------|---------|---------------|
| How should Phase 20 converter map into allure-python-commons? | Semantic adapter over commons lifecycle; Rewrite around commons objects; Dual backend mapper; You decide | Rewrite around commons objects |
| What should happen to standalone allure-cucumber converter? | Keep standalone converter JSON-based; Migrate standalone converter too; Deprecate standalone converter; You decide | Deprecate standalone converter |
| How should attachments/doc strings/data tables map? | Preserve Phase 20 semantics exactly; Use commons-native presentation where better; Minimal first pass; You decide | Use commons-native presentation where better |
| Should plugin support allure-pytest installed at same time? | Coexist without coupling; Disable when allure-pytest active; Integrate with allure-pytest hooks; You decide | Coexist without coupling |

**Notes:** User wants maximum useful feature coverage from `allure-python-commons`, even when visible presentation improves beyond Phase 20 JSON output.

---

## xdist Aggregation Ownership

| Question | Options | User's choice |
|----------|---------|---------------|
| Which existing message reporter asset should Allure rely on? | Consolidated controller stream; EnvelopeRegistry snapshots per participant; Transport batches directly; You decide | Consolidated controller stream |
| What if consolidated stream has warnings? | Fail Allure generation; Generate partial report with warning; Configurable strictness; You decide | Default partial, optional fail |
| How should worker attachments move to controller for Allure? | Message stream owns attachment data/refs; Worker writes attachment files to shared temp dir; Hybrid; You decide | Message stream owns attachment data/refs |
| Should Allure output directory be wiped before writing? | Create/append safely, no wipe by default; Clean output dir by default; Add explicit clean option; You decide | No wipe; warn when non-empty |

**Notes:** Final truth belongs to controller-consolidated message stream, not worker filesystem writes.

---

## CLI/API Migration Shape

| Question | Options | User's choice |
|----------|---------|---------------|
| What should new user-facing options be? | Keep SPEC names; Override SPEC with new `--allure-cucumber-*` names only; Keep both; You decide | Override SPEC |
| Exact option names? | `--allure-cucumber-output` + `--allure-cucumber-messages-in`; `--allure-cucumber-results` + `--allure-cucumber-messages-in`; `--allure-cucumber-output` + `--allure-cucumber-input`; You decide | `--allure-cucumber-output` + `--allure-cucumber-messages-in` |
| What about current `--allure-cucumber-messages`? | Replace with deprecation alias; Remove immediately; Keep as equal alias forever; You decide | Remove immediately |
| How should output option interact with existing ini? | Keep ini as fallback; Rename ini to match new behavior; Remove ini; You decide | INI and CLI option must coexist and correspond |

**Notes:** This conflicts with `21-SPEC.md`, which locked `--allure-bdd-output` and `--allure-bdd-messages-in`. Context records user override; planner must reconcile.

---

## Verification Surface

| Question | Options | User's choice |
|----------|---------|---------------|
| What should be minimum blocking proof before phase done? | Full layered proof; Contract-heavy only; E2E-heavy only; You decide | Full layered proof |
| Should Allure HTML rendering with Docker/Playwright be blocking? | Raw results required, HTML smoke when tools available; HTML rendering blocking always; Raw results only; You decide | HTML rendering blocking always |
| How should allure-pytest coexistence be tested? | Two envs absent/present; Mock import presence; Manual note only; You decide | Two envs absent/present |
| xdist proof shape? | Real `pytest -n 2` with multiple BDD scenarios and attachments; Unit-level consolidation only; Remote xdist Docker too; You decide | Real `pytest -n 2`, plus via/socket connection usage |

**Notes:** Verification is intentionally heavy: generated Allure HTML must be rendered and inspected, not only raw result files.

---

## the agent's Discretion

- Exact `allure-python-commons` API wiring.
- Exact strict/fail option name for consolidation diagnostics.
- Exact import-mode collection skip/no-op mechanism.
- Exact test file split.

## Deferred Ideas

None.
