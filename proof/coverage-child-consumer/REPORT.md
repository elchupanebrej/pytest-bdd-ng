# Observed proof: child-exclusive and installed-consumer coverage (#340)

Branch: `proof/coverage-child-consumer-340`, created from
`integration/restore-parity-2026-10-29` at
`dee40c1a898b960587128b476617c8d7a59c5617`.

This branch is disposable and must not be merged. The proof adds only
`proof/coverage-child-consumer/`; it changes no product code, configuration, or
test suite.

## Environment

| Item | Observed |
|---|---|
| Host | WSL2 Ubuntu, Linux |
| Python | CPython 3.15.2 |
| coverage | 7.17.1 (`coverage>=7.17,<8`) |
| pytest | 9.2.0 |
| uv | 0.11.23 |
| Wheel | `pytest_cuke-2.3.1-py3-none-any.whl`, `sha256 c6d2380ab3c159ffa1a70fc385b6ce1d526d90ed0d7db7cc861526c05cf14b63` |
| Build | `PYTEST_CUKE_BUILD_GO=off uv build --wheel` |

The run happened under `/tmp/opencode/coverage-child-consumer-lyf7jx91/`.
`observed-output.txt` is the full captured output. Raw coverage databases and
temporary venvs are not committed.

## Command

```bash
nohup env PROOF_TMP=/tmp/opencode \
  python3 proof/coverage-child-consumer/proof.py \
  > proof/coverage-child-consumer/observed-output.txt 2>&1 &
```

The script performs these steps with real subprocesses:

1. Build the wheel from this branch.
2. Create a fresh instrumented venv with the wheel, `pytest`, and
   `coverage==7.17.1`.
3. Create a second fresh venv with the wheel and `pytest` but no `coverage`.
4. Verify `pytest_cuke.__file__` resolves inside the instrumented venv.
5. Run a parent pytest process under `coverage run` with
   `patch = subprocess`, `parallel = true`, `source = pytest_cuke`, and a
   token-carrying data-file base.
6. The parent launches one passing child pytest process and one deliberately
   failing child pytest process.
7. Copy fragments, combine them, and probe the parent fragment and the passing
   child fragment separately.
8. Run the same consumer from the uninstrumented venv under an instrumented
   driver and look for the child's fragment.

## Coverage configuration used

```ini
[run]
patch = subprocess
parallel = true
branch = true
source = pytest_cuke
data_file = /tmp/opencode/.../consumer/.coverage.dee40c1a898b-installed-child-dd462947e066

[report]
precision = 2
```

The proof does not set or apply `fail_under = 85`; it is not a gate acceptance
run.

## Observed results

| Check | Result |
|---|---|
| Installed import source | `/tmp/.../venv-instrumented/lib/python3.15/site-packages/pytest_cuke/__init__.py` |
| Checkout shadowing | None; the checkout is not on the consumer path |
| Parent process pid | `106967` |
| Passing child pid | `106968` |
| Failing child pid | `106981` |
| Fragments after the run | `3` (parent, passing child, failing child) |
| `coverage combine` | `Combined 3 files` |
| Child-exclusive product line | `pytest_cuke/parsers/parse_parser.py:61` (`res = dict(match.named)`) |
| Child line in combined evidence | `True` |
| Child line in the passing child fragment | `True` |
| Child line in the parent fragment | `False` |
| Failing child exit | `1` (`1 failed`), observed by the parent as `1` |
| Parent test outcome after child failure | `2 passed`; instrumentation and cleanup did not relabel the child failure |

The parent imports the installed plugin but never executes the chosen
`parse_arguments` line; only the child executes it. That line is present in the
combined evidence.

## Missing-instrumentation diagnosis

The uninstrumented venv has no `coverage` distribution:

```text
UNINSTRUMENTED_COVERAGE_SPEC=None
```

Its passing child still runs (`1 passed`), but the child writes no fragment.
Only the instrumented driver fragment exists:

```text
UNINSTRUMENTED_FRAGMENT=...pid107075...
UNINSTRUMENTED_CHILD_PID=107076
UNINSTRUMENTED_CHILD_FRAGMENT=None
UNINSTRUMENTED_JSON_EXIT=1
UNINSTRUMENTED_PRODUCT_EVIDENCE=False
DIAGNOSIS=measurement_gap
GATE_EXIT_IF_ENFORCED=2
```

`coverage json` reports `No data to report.` The proof therefore diagnoses a
`measurement_gap` and records the gate exit that must follow (`2`) instead of
accepting the passing child as coverage evidence.

## Limits

- Linux CPython 3.15 only in this run. Windows and the rest of the matrix were
  not exercised here.
- The proof uses a token in the data-file base name; it does not prove the
  product-owned gate wrapper, receipt schema, or `fail_under` enforcement.
- The proof establishes that the mechanism works; it does not choose the final
  child-declaration or gap-detection contract.
