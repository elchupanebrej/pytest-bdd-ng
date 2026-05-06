# Quickstart: Cucumber Formatter Support

## Preconditions

- Repository root: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng`
- Branch: `012-cucumber-formatters-support`
- Python environment: `conda` env `pytest-bdd-ng-py314`

> Current workflow:
> - Python environment: repository synced with `uv sync --extra test --extra testenv --extra testtypes`

- `node` and `npm` available on `PATH`

## 1. Run one terminal formatter

```bash
# Legacy workflow:
# conda run --no-capture-output -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_cucumber_formatters.py -q --cucumber-progress
uv run python -m pytest \
  tests/e2e/test_cucumber_formatters.py -q --cucumber-progress
```

Expected:
- pytest completes successfully;
- one formatter writes terminal output after the canonical NDJSON stream is
  finalized;
- if `@cucumber/cucumber` is missing, the run may first print a global npm
  installation message.

## 2. Run multiple file-based formatters together

Create the output directory first because the reporter must not create it
automatically:

```bash
# Legacy workflow:
# mkdir -p /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.tmp-cucumber-reports
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_cucumber_formatters.py -q \
#   --cucumber-json=.tmp-cucumber-reports/report.json \
#   --cucumber-junit=.tmp-cucumber-reports/report.xml \
#   --cucumber-usage-json=.tmp-cucumber-reports/usage.json
uv run python -m pytest \
  tests/e2e/test_cucumber_formatters.py -q \
  --cucumber-json=.tmp-cucumber-reports/report.json \
  --cucumber-junit=.tmp-cucumber-reports/report.xml \
  --cucumber-usage-json=.tmp-cucumber-reports/usage.json
```

Expected:
- all requested file artifacts are created;
- JSON and XML payloads are non-empty and parseable by downstream tooling;
- file-based formatters may coexist in one run because they do not compete for
  terminal output.

## 3. Validate terminal formatter conflict handling

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_cucumber_formatters.py -q \
#   --cucumber-summary --cucumber-progress
uv run python -m pytest \
  tests/e2e/test_cucumber_formatters.py -q \
  --cucumber-summary --cucumber-progress
```

Expected:
- pytest fails before test execution;
- the error clearly states that only one terminal-output formatter may be
  active in a run.

## 4. Validate missing directory handling for file outputs

```bash
# Legacy workflow:
# rm -rf /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.tmp-missing-dir
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_cucumber_formatters.py -q \
#   --cucumber-json=.tmp-missing-dir/report.json
uv run python -m pytest \
  tests/e2e/test_cucumber_formatters.py -q \
  --cucumber-json=.tmp-missing-dir/report.json
```

Expected:
- pytest fails with a clear filesystem error;
- `.tmp-missing-dir/` is not created automatically.

## 5. Validate xdist-compatible post-run rendering

```bash
# Legacy workflow:
# mkdir -p /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.tmp-cucumber-reports
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_e2e.py -q -n 2 \
#   -m "not slow and not xdist and not docker" \
#   --cucumber-json=.tmp-cucumber-reports/xdist-report.json
uv run python -m pytest \
  tests/e2e/test_e2e.py -q -n 2 \
  -m "not slow and not xdist and not docker" \
  --cucumber-json=.tmp-cucumber-reports/xdist-report.json
```

Expected:
- xdist execution still produces one canonical report file;
- formatter rendering happens after worker output has been consolidated into the
  final NDJSON stream;
- the resulting formatter file reflects the full logical run, not one worker.

## 6. Validate the focused repository test slices

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_cucumber_formatters.py \
#   tests/e2e/test_cucumber_formatters_feature.py \
#   tests/compatibility/test_render_cucumber_formatters.py \
#   tests/hook/test_gherkin_reporter_context_lifecycle.py -q
uv run python -m pytest \
  tests/e2e/test_cucumber_formatters.py \
  tests/e2e/test_cucumber_formatters_feature.py \
  tests/compatibility/test_render_cucumber_formatters.py \
  tests/hook/test_gherkin_reporter_context_lifecycle.py -q
```

Expected:
- formatter flag registration, execution planning, auto-provisioning, and
  user-visible acceptance flows remain covered;
- regression coverage verifies the reporter lifecycle around session finish and
  NDJSON finalization.
