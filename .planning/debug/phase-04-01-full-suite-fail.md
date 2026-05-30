---
status: resolved
trigger: "Phase 04-01 full-suite failures after environment unblocker"
created: 2026-05-13
updated: 2026-05-13
---

# Debug Session: Phase 04-01 Full Suite Failures

## Symptoms

### Expected Behavior

Full test suite should pass.

### Actual Behavior

All 29 failures from Phase 04-01 final verification should be investigated and fixed or correctly reclassified.

### Error Messages

Use `.planning/phases/04-plugin-refactoring/04-01-SUMMARY.md` Final Verification Gate as the current error corpus.

Known failure groups:

- cucumber expression parameter matching failures
- terminal reporter and missing-step output mismatches
- expected failing scenarios propagating as failed nested pytester runs in formatter/message coverage tests
- optional structured BDD dependency failures for `pyhocon`, `hjson`, and `json5`
- stale generated Cucumber message schema evidence: `Envelope.schema.json`
- e2e feature outcome mismatches under `tests/e2e/test_e2e.py`

### Timeline

Phase 3 verification previously had local environment blockers recorded in `.planning/phases/03-core-runtime-refactor/03-03-SUMMARY.md`.
Phase 04-01 fixed the pytester temp-root blocker, xdist bootstrap import blocker, and local pre-commit environment blocker.
After those fixes, full-suite execution reached product/test expectation failures instead of the original environment failures.

### Reproduction

Project documentation command:

```bash
uv run python -m pytest tests/ -q
```

Phase 04-01 local verification command:

```bash
UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/ -q
```

Most recent observed result:

```text
29 failed, 820 passed, 13 skipped in 2091.60s
```

## Current Focus

hypothesis: Phase 04-01 failures are a mix of WSL temp-root capture setup, validation side effects, optional extras gaps, stale acceptance docs, and missing Docker prerequisites.
test: local full suite excluding Docker-only tests, focused e2e gates, and representative previously failing slices.
expecting: non-Docker suite passes; Docker-marked tests remain environmental until Docker Desktop or WSL2 Alpine Docker backend is available.
next_action: pre-commit and commit fixes.
reasoning_checkpoint: root causes isolated by failure group, not treated as one broad regression.
tdd_checkpoint: focused failing cases were run before and after each fix.

## Evidence

- timestamp: 2026-05-13
  observation: Phase 04-01 final verification failed after environment blockers were fixed.
  source: .planning/phases/04-plugin-refactoring/04-01-SUMMARY.md
- timestamp: 2026-05-13
  observation: `uv run` still used `/mnt/c/...` temp paths before pytest loaded `tests/conftest.py`, so global capture could fail before test-local temp normalization ran.
  source: `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python - <<'PY' ...`
- timestamp: 2026-05-13
  observation: `src/sitecustomize.py` is loaded by editable `uv run`; stdlib-only temp normalization sets `TMPDIR`, `TEMP`, `TMP`, and `tempfile.gettempdir()` to `/tmp`.
  source: interpreter probe
- timestamp: 2026-05-13
  observation: zero-match validation invoked step matching as a probe, surfacing duplicate-match warnings as errors and blocking `--generate-missing`.
  source: focused tests for cucumber expression, missing generation, report, lifecycle, and message slices
- timestamp: 2026-05-13
  observation: `tests/struct_bdd/test_steps.py` requires `pyhocon`, `hjson`, and `json5`, but the `test` extra did not include the `struct-bdd` extra.
  source: struct BDD focused test
- timestamp: 2026-05-13
  observation: huge-suite performance benchmark cannot assert Go-parser speedup when the optional shared library is unavailable.
  source: `tests/unit/test_performance_batch.py::test_performance_huge_suite`
- timestamp: 2026-05-13
  observation: legacy Cucumber JSON reporter acceptance feature used removed CLI alias; `--cucumber-json` now targets the cucumber-js formatter, while legacy reporter uses `cucumber_json_path`.
  source: `tests/e2e/test_e2e.py -k 'Cucumber and JSON and mixed'`
- timestamp: 2026-05-13
  observation: Docker-marked remote xdist tests fail on this machine because Docker Desktop / WSL2 Docker backend is not installed. Spec 019 requires failure on missing Docker, so this is prerequisite failure, not product code failure.
  source: `tests/e2e/test_xdist_remote_message_aggregation.py`
- timestamp: 2026-05-13
  observation: focused regression slices passed after fixes.
  source: cucumber expression/report/missing-generation/messages slice, pytester env slice, reporter/message slice, struct BDD, performance, schema scripts
- timestamp: 2026-05-13
  observation: e2e feature entrypoint passed.
  source: `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/e2e/test_e2e.py -q` -> `104 passed in 963.57s`
- timestamp: 2026-05-13
  observation: local non-Docker full suite passed.
  source: `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/ -q -m 'not docker'` -> `835 passed, 14 skipped, 13 deselected in 2136.02s`

## Eliminated

- Parser/message schema staleness as active blocker: schema sync tests pass.
- Cucumber expression/runtime matching as active blocker: focused parameterized report/message slices pass.
- E2E feature corpus as active blocker: `tests/e2e/test_e2e.py` passes.
- Docker-marked tests as product regression: they are environmental by explicit spec requirement.

## Resolution

root_cause: Multiple independent blockers surfaced after Phase 04-01 unblocked collection: WSL temp-root capture setup happened too late, zero-match validation had side effects, test extras omitted structured BDD optional dependencies, optional Go benchmark assumed accelerator availability, one acceptance feature documented a removed legacy CLI alias, and Docker prerequisites are absent locally.
fix: Add early stdlib-only temp-root normalization, suppress duplicate step warnings only inside zero-match validation probes, skip zero-match validation for missing-step generation and filtered collections, include `struct-bdd` in the `test` extra, skip Go speed benchmark without the shared library, update legacy Cucumber JSON acceptance docs to use `cucumber_json_path`, and preserve Docker failures as prerequisite signal.
verification: Local non-Docker suite passes; full Docker-inclusive suite remains blocked by missing Docker Desktop / WSL2 Docker backend.
files_changed:
  - docs/features/07 Report/05 Cucumber JSON reporter.feature.rst
  - features/07 Report/05 Cucumber JSON reporter.feature.md
  - pyproject.toml
  - src/pytest_bdd/model/feature_binding.py
  - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py
  - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
  - src/pytest_bdd/util/temp_root.py
  - src/sitecustomize.py
  - tests/conftest.py
  - tests/unit/test_performance_batch.py
