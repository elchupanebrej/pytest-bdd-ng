# Phase 35 Validation

## Sequenced automated checks

| Plan/task | Command | Expected result |
|---|---|---|
| 35-01/1 | configuration assertions plus `uv sync --all-extras` | No mypy source exclusion or `ignore_errors`; capture the expanded nonzero baseline in `35-TYPING-BASELINE.md`, never in the canonical inventory. |
| 35-01/2 | `uv run --all-extras pyright --project pyright.strict.json --version` | Actual upstream strict config with `typeCheckingMode=strict`, Python 3.10, platform All. |
| 35-02 through 35-137 | Each exact ledger task’s focused `mypy --config-file pyproject.toml <explicit paths>` command | Bounded batch clean; remediation plans write only their own evidence record. |
| 35-138/1 | `uv run --all-extras python scripts/verify_installed_types.py --assert-isolated --check-verifytypes` | Fresh external venv contains pinned mypy/upstream Pyright and wheel-only imports; verifytypes parses to 100%. |
| 35-138/2 | consumer fixture test | Both venv checker executables accept valid and reject invalid public API fixtures by category. |
| 35-138/3 | Focused mypy for `test_18_development.py` and `step/development.py`; `uv run --all-extras pytest src/pytest_bdd_toolchain/case/e2e/feature/test_18_development.py -q`; `uvx --with tox-uv tox -e py310-typing-contract` | The real Development BDD loader and registered steps execute the Python-3.10 isolated contract, with a sole-owner strict-mypy evidence record. |
| 35-139 | Run `uv run --all-extras pyright --project pyright.strict.json` and `uvx ty check src/pytest_bdd src/pytest_bdd_toolchain` independently, capturing each output and exit status before either is classified | Full-scope outcomes are classified; no promotion without zero-error localized evidence. A nonzero Pyright exit must not prevent ty discovery. |
| 35-140/1 | `python scripts/reconcile_typing_inventory.py` plus no-bypass configuration assertions | First and only canonical inventory aggregation; every source module has exactly one owner and isolated evidence. |
| 35-140/2 | Full-source mypy, reconciliation, and `py310-typing-contract` as separately asserted final gates | First and only required final full-source zero-error reconciliation and installed-wheel contract completion. |

## Manual evidence

- Compare ledger rows to the `git ls-files` command: every source module must have one owner, focused command, clean status, disposition, and evidence. Plan 140 is the sole writer of `35-TYPING-INVENTORY.md`; Plan 01’s baseline is in `35-TYPING-BASELINE.md`.
- Inspect the wheel runner: it builds a wheel, installs the wheel plus pinned mypy and upstream Pyright into a fresh venv, copies fixtures to an external cwd, invokes only venv checker paths, and asserts checker paths plus `pytest_bdd.__file__` are in that venv’s site-packages.
- Inspect valid/invalid fixtures for scenario binding, step decorators/fixture injection, parser types, hooks, reporters/configuration, and package re-exports; invalid checks assert a category/code, not wording.
- Inspect Plan 139’s `35-139-pyright.txt`, `35-139-ty.txt`, and `35-139-exit-statuses.txt`: both discovery commands must have run and been classified as actionable, checker/model limitation, or missing third-party stub before a promotion/no-promotion decision.

## Phase acceptance

Completion requires exact one-owner source coverage, no broad mypy bypasses, final zero-error full-source mypy, a 100% `pyright --verifytypes` installed-wheel result, six valid/negative public API families under venv-local mypy and upstream Pyright, a Python-3.10/platform-All contract, BDD acceptance coverage, and independently captured Pyright/ty discovery evidence.
