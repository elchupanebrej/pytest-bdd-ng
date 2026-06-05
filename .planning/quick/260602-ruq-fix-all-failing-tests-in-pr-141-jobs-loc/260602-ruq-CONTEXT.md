# Quick Task 260602-ruq: Fix all failing tests in PR #141 jobs locally. Launch agent per issue - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning
**PR:** https://github.com/elchupanebrej/pytest-bdd-ng/pull/141
**Branch:** unify-run-context-to-go-gherkin-parser-restructure-tests-and-makefile-ci-stabilization
**Run:** 26828896530 (commit 81cfb860)

## Task Boundary

Fix all failing tests in the PR's CI jobs locally. Each failing CI job is a separate issue that gets a dedicated agent.

## Source of Truth

7 of 12 CI jobs in run 26828896530 fail at the "Test with tox" step with exit code 2. The pre-commit.ci status also fails.

### Failing jobs

| Job ID | Name | Conclusion | Started | Duration |
|--------|------|------------|---------|----------|
| 79104204423 | test (3.12, ubuntu-latest) | failure | 2026-06-02T15:08:33Z | 1h 1m 4s |
| 79104204425 | test (3.13, ubuntu-latest) | failure | 2026-06-02T15:08:33Z | 54m 55s |
| 79104204681 | test (3.14, ubuntu-latest) | failure | 2026-06-02T15:08:33Z | 43m 25s |
| 79104204396 | test (3.13, macos-latest) | failure | 2026-06-02T15:08:33Z | 38m 43s |
| 79104204474 | test (3.14, macos-latest) | failure | 2026-06-02T15:08:33Z | 32m 7s |
| 79104204768 | test (3.13, windows-latest) | failure | 2026-06-02T15:08:33Z | 1h 0m 23s |
| 79104204453 | test (3.14, windows-latest) | failure | 2026-06-02T15:08:33Z | 37m 42s |

### Passing jobs

- 79104204391: test (pypy3.11, windows-latest) - success
- 79104204591: test (pypy3.11, macos-latest) - success
- 79104204433: test (3.11, ubuntu-latest) - success
- 79104204593: test (3.10, ubuntu-latest) - success
- 79104204840: test (pypy3.11, ubuntu-latest) - success

### Step that fails in every cell

`Test with tox` (step 8 of each cell). Runs `make tox` which is `uvx --with tox-uv --with tox-gh-actions tox`.

## Matrix overview (from tox.ini)

`env_list` covers: pre-commit, feature-docs, mypy, playwright-report, mypy-messages, xdist-remote-{socket,via,ssh}-{lin,win}, coverage-{lin,mac,win} on multiple pytest versions per Python, gherkin versions, ruff, and xdist-coverage. Each cell runs:

```
{env:_PYTEST_CMD:pytest} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson -vvl
```

with `coverage: _PYTEST_CMD = coverage run --append -m pytest -m "not docker"` for coverage envs and `pypy311: _PYTEST_CMD = pytest -m "not docker"`.

`test_group_default = "integration"` plus `test_group_paths` map `tests/cases/<group>/**` to each group. `testpaths = ["tests/cases"]`.

## Local reproduction snapshot (Windows 11, Python 3.14.2)

Running `uv run --extra test python -m pytest tests/cases/integration -q`:
- 267 passed, 1 skipped
- 1 failure: `tests/cases/integration/hook/test_live_formatter_terminal_layout.py::test_usage_formatter_wraps_to_terminal_width`
- 1 error: same test
- TypeError in `_strip_ansi(result.stdout)`: `expected string or bytes-like object, got 'NoneType'`
- The test shells out to node and asserts on stdout; stdout is None

The `test_find_crossover_threshold` slow benchmark in `tests/cases/unit/unit/test_threshold_finder.py` was excluded by the integration marker but should be excluded for `pytest -m "not docker"` runs too — it's marked `pytest.mark.slow` and would dominate runtime in full tox.

## Implementation Decisions

### Agent dispatch strategy
- One parallel agent per failing CI job (7 agents)
- Each agent's scope is the single failing job's test execution path
- Each agent must reproduce locally, identify the failure, fix it, and verify
- Agents that cannot run their platform (e.g., macOS agent on Windows host) must use Docker/WSL where available and otherwise reason from code + cross-reference with passing jobs

### Fix scope
- Address the root cause, not symptoms
- Do not bypass or skip tests
- Do not refactor unrelated code
- Reuse local virtualenv at `.venv`; do not recreate tox envs unless the cell demands it

### Platform constraints on the orchestrator host
- Host is Windows 11 with Python 3.14.2 and `uv 0.11.15`
- Linux tox backend available via WSL2 if set up; Docker available for some
- macOS tox backend cannot run on this host — the macOS agent must rely on Docker (`python:3.14-windowsservercore-ltsc2022` is Windows, not macOS; the project has a `Makefile` `test-all` target that handles this, but per project AGENTS.md Docker is required for non-native)

### Pre-commit status
- pre-commit.ci is also failing — separate from tox
- Last spec commit `a21b4cd6 Run env-heavy pre-commit checks via tox` moved pre-commit into tox (`py{313,314}-pre-commit`); a passing pre-commit locally does not guarantee pre-commit.ci passes

### the agent's Discretion
- Whether to dispatch exactly 7 agents (one per failing job) or fewer grouped agents (e.g., 3 platform-based)
- Whether to fix pre-commit.ci in the same task or defer
- How to verify Linux/macOS fixes when the host cannot run those backends

## Specific Ideas

- Investigate `_strip_ansi(result.stdout)` TypeError first — it's reproducible on this Windows host and may be the root cause for one or more cells
- The recent `fix(scenario_locator): sort resolved feature paths to preserve file order` is a suspect for order-dependent failures
- The recent `Refactor: Move private pytest and sys imports to compatibility package` is a suspect for import-related failures
- The recent `Run env-heavy pre-commit checks via tox` adds new tox envs that may fail on 3.12+
- Look at `.planning/quick/260602-lhn-seems-file-locator-doesn-t-preserve-file/SUMMARY.md` for context on the last quick task that touched CI

## Canonical References

- PR: https://github.com/elchupanebrej/pytest-bdd-ng/pull/141
- Run: https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/26828896530
- AGENTS.md project rules
- tox.ini, pyproject.toml, Makefile, .github/workflows/main.yml
- `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` (future spec for log artifacts)
- `docs/superpowers/specs/2026-06-02-xdist-remote-separate-gha-executor-design.md` (future spec for splitting xdist-remote)

## Open items for the planner

- Confirm: dispatch exactly 7 parallel agents (one per failing job) vs fewer grouped agents
- Confirm: pre-commit.ci fix in scope or deferred
- Confirm: agents commit per fix or batch at end
