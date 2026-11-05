# Coverage child/consumer proof (ticket #340)

Disposable, merge-never proof for the decisions in
[Wayfinder map #333](https://github.com/elchupanebrej/pytest-bdd-ng/issues/333)
and [ADR 0004](https://github.com/elchupanebrej/pytest-bdd-ng-harness/blob/main/docs/adr/0004-subprocess-and-installed-consumer-coverage.md).

The script builds the wheel from this branch, installs it into two fresh
`uv` environments, runs a parent pytest process that launches real child
pytest processes, combines coverage fragments, and reports the observed
fragment split and the missing-instrumentation diagnosis.

## Run

```bash
PYTEST_CUKE_BUILD_GO=off uv run --no-project python proof/coverage-child-consumer/proof.py
```

Or with a Python 3.11+ interpreter that has `uv` on `PATH`:

```bash
python3 proof/coverage-child-consumer/proof.py
```

All work happens under a temporary directory (`/tmp/opencode/...` by default,
override with `PROOF_TMP`). Nothing is installed into this checkout or the
active environment. `observed-output.txt` records the output from the run on
this branch.

## What it proves

1. The built wheel is installed into a fresh instrumented venv; the imported
   `pytest_cuke` is the venv's `site-packages` copy, not this checkout.
2. A parent pytest process launches real child pytest processes.
3. A line in `pytest_cuke/parsers/parse_parser.py` executed only by the child
   appears in the combined evidence; the parent fragment does not execute it.
4. A deliberately failing child keeps exit code `1` through coverage start and
   cleanup; the parent observes that code and continues.
5. A second fresh venv without `coverage` runs the same consumer successfully
   but produces no child fragment and no product evidence. The proof reports
   `DIAGNOSIS=measurement_gap` with the gate exit that must follow (`2`), not a
   silent pass.

This proof does not apply `fail_under = 85`, does not land product code, and
does not claim full-suite or CI acceptance.
