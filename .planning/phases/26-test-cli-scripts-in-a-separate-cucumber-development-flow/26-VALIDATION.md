# Phase 26 Validation

**Phase:** Test CLI scripts in a separate Cucumber Development flow
**Status:** Planned validation artifact added during revision iteration 1
**Sources:** `26-RESEARCH.md` Validation Architecture, `26-SPEC.md`, `26-CONTEXT.md`, `26-01-PLAN.md`, `26-02-PLAN.md`

## Validation Objective

Prove that Phase 26 has executable Development BDD coverage for every locked requirement while preserving D-01 through D-04.

## Automated Gates

| Gate | Command | Covers |
|------|---------|--------|
| Plan 26-01 frontmatter | `rtk gsd-tools query frontmatter.validate .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-01-PLAN.md --schema plan` | Required plan metadata, requirements frontmatter |
| Plan 26-01 structure | `rtk gsd-tools query verify.plan-structure .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-01-PLAN.md` | Structured `<task>` blocks with `<files>`, `<action>`, `<verify>`, `<done>` |
| Plan 26-02 frontmatter | `rtk gsd-tools query frontmatter.validate .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-02-PLAN.md --schema plan` | Existing structured gap-closure plan metadata |
| Plan 26-02 structure | `rtk gsd-tools query verify.plan-structure .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-02-PLAN.md` | Existing gap-closure task structure |
| Focused Development E2E | `rtk powershell -NoProfile -Command "python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q"` | All seven Development feature files |
| Lint gate | `rtk powershell -NoProfile -Command "make lint"` | Project lint/format/type quality gate |
| Custom rules gate | `rtk powershell -NoProfile -Command "make custom-rules"` | Project architecture/custom lint rules |
| D-04 no-shell gate | `rtk powershell -NoProfile -Command "python -c \"from pathlib import Path; import re, sys; text='\\n'.join(p.read_text(encoding='utf-8') for p in Path('features/18 Development').glob('*.feature.md')); sys.exit(1 if re.search(r'run `(?:bash|sh)\\s+scripts/run_messages_coverage_audit\\.sh', text) else 0)\""` | Locked D-04 shell boundary |

## Requirement-to-Gate Map

| Requirement | Primary Plan | Validation |
|-------------|--------------|------------|
| P26-DEV-01 | 26-01 | Focused Development E2E collects and runs feature files under `features/18 Development/`. |
| P26-DEV-02 | 26-01 | Focused Development E2E exercises `src/pytest_bdd_testing/step/development.py` and shared harness steps. |
| P26-DEV-03 | 26-01 | Plan structure plus focused E2E verify the conftest registration and `test_18_development.py` loader. |
| P26-DEV-04 | 26-01 | Focused Development E2E runs Allure converter success and missing-input scenarios. |
| P26-DEV-05 | 26-01 | Focused Development E2E runs heading validator clean and failing scenarios. |
| P26-DEV-06 | 26-01, 26-02 | Focused Development E2E runs architecture tooling scenarios; 26-02 adds explicit `python scripts/arch.py analyze-gaps` coverage. |
| P26-DEV-07 | 26-01, 26-02 | Focused Development E2E runs compatibility matrix scenarios; 26-02 adds explicit `--report-e2e-migration-threshold` coverage. |
| P26-DEV-08 | 26-01 | Focused Development E2E runs schema sync clean and drift scenarios. |
| P26-DEV-09 | 26-01 | Focused Development E2E runs standalone Cucumber formatter rendering. |
| P26-DEV-10 | 26-01, 26-02 | Focused Development E2E documents the shell audit gap, and the D-04 static gate forbids direct bash/sh execution. |
| P26-DEV-11 | 26-01, 26-02 | Plan validation, this file, ROADMAP, and REQUIREMENTS provide traceability and verification commands. |

## Decision Gates

| Decision | Required Truth | Validation |
|----------|----------------|------------|
| D-01 | Entrypoint scripts are invoked through Python. | Feature text and focused E2E use `python -m pytest_bdd.script...` or direct Python script paths. |
| D-02 | Non-entrypoint scripts are invoked through Python relative paths. | 26-02 requires `python scripts/arch.py analyze-gaps`. |
| D-03 | Output assertions use fragments/regex style. | Feature scenarios assert output fragments, not full stdout snapshots. |
| D-04 | Shell scripts are not directly executed in E2E. | D-04 no-shell gate scans `features/18 Development/*.feature.md`; messages audit remains gap documentation. |

## Nyquist Compliance

- `26-01-PLAN.md` has structured `<task>` elements with automated verification commands.
- `26-02-PLAN.md` already has structured `<task>` elements with automated verification commands.
- This validation artifact resolves the research Validation Architecture artifact gap.
- No unresolved research open questions remain; resolutions are recorded in `26-RESEARCH.md` and implemented by 26-02 plus D-04 preservation.
