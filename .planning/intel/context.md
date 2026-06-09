# Context Intel

Running notes keyed by topic, extracted from classified documents.

---

## Topic: CCK Allure Compatibility Pipeline Architecture

**Source:** specs/045-cck-allure-compatibility/spec.md

The pipeline validates that pytest-bdd-ng's allure-cucumber converter correctly renders all 45 CCK sample NDJSON files as Allure HTML reports. Architecture flow:

```
cucumber/compatibility-kit v29.2.2
  └─ devkit/samples/*.ndjson
        │ (session-scoped fixture, gh api / raw.githubusercontent.com)
        ▼
  tests/cases/contract/cck/fixtures/
        │ (per-sample conversion)
  pytest-bdd-ng allure-cucumber converter
        │ (ndjson → allure-results/)
        ▼
  Docker: frankescobar/allure-docker-service:2.27.0
        │ (allure-results → allure-report/)
        ▼
  _serve_directory() HTTP server
        │
  Playwright Chromium browser
        │ (assert visible elements)
        ▼
  PASS/FAIL per sample
```

---

## Topic: Conversion Strategy

**Source:** specs/045-cck-allure-compatibility/spec.md

- Use existing `convert()` function from `allure_cucumber.converter.converter`
- Each sample gets its own `allure-results/` directory
- Validate that `*-result.json` and `*-container.json` files are created
- Schema validation of output against Allure3 Events JSONSchema

---

## Topic: Implementation Phases

**Source:** specs/045-cck-allure-compatibility/plan.md

Execution order:
1. **Phase 1: Infrastructure** — CCK download utility, session-scoped fixtures, Docker helper, Playwright helpers
2. **Phase 2: Contract Tests** — Conversion edge cases (empty, single-line, failed, attachments, data tables, doc strings, rules, examples tables, hooks, retry)
3. **Phase 4.1-4.2: Parameterized Playwright** — Browser validation for all 45 samples
4. **Phase 3: BDD Feature** — Feature file with Given/When/Then scenarios
5. **Phase 5: Integration** — Wire into E2E test entry point, update markers, documentation

Note: The plan.md references "Phase 4" before "Phase 3" in execution order — this is intentional (Playwright tests before BDD feature).

---

## Topic: Existing Patterns to Reuse

**Source:** specs/045-cck-allure-compatibility/plan.md

- `_run_allure_docker()` from `test_allure_consumption_ui.py`
- `_serve_directory()` context manager from `test_messages_feature_suite.py`
- `_resolve_playwright_browsers_path()` from `test_messages_feature_suite.py`
- `convert()` from `allure_cucumber.converter.converter`
- Class-based test pattern (`TestCCKAllure*` with pytest markers)

---

## Topic: Dependencies

**Source:** specs/045-cck-allure-compatibility/spec.md

Existing: `allure_cucumber.converter`, `testing.docker`, `playwright`
New: `gh` CLI or `raw.githubusercontent.com` for CCK download
Docker image: `frankescobar/allure-docker-service:2.27.0`

---

## Topic: Project Phase Alignment

**Source:** .planning/ROADMAP.md (merge mode context)

This feature aligns with Phase 20, Wave 6: "CCK Allure compatibility pipeline: download utility, contract tests, Playwright validation" (20-06-PLAN.md, currently unchecked). The feature builds on Phase 20's Allure converter work (Waves 1-5 complete).

---

## Topic: Risk Mitigation

**Source:** specs/045-cck-allure-compatibility/spec.md

1. CCK download failure — Cache downloads, skip tests if unavailable
2. Docker unavailable — Skip with clear message, run conversion-only tests
3. Playwright unavailable — Skip with clear message, run Docker-only tests
4. Allure converter incompatibility — Log warnings, don't fail entire suite
5. Large NDJSON files — Set timeout limits, process incrementally
