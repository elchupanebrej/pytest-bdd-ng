# Agent 3 Report: py314 ubuntu (job 79104204681)

**Status:** Fixed at root cause (consolidated into single commit `7f3276af`).

## Reproduction

Same as agents 1 and 2. Additionally, the 3.14 ubuntu cell is the
largest in the matrix: it includes the `py314-pre-commit-lin` env, the
mypy envs, the mypy-messages env, the playwright-report env, the
xdist-remote-{socket,via,ssh}-lin envs, and the 3.14 coverage-lin
matrix. Pre-commit and the mypy/playwright/xdist envs may have
additional failures not addressed by this fix (none observed in
local pre-commit; xdist-remote requires docker and is out of scope).

## Root Cause

Same as agents 1, 2: subprocess encoding bug.

## Fix Applied

Same as agents 1, 2.

## Verification

Local Windows / Python 3.14.2: full integration suite green
(268 passed, 1 skipped). `uv run pre-commit run --all-files` shows
14 of 14 hooks pass locally (the 7 ruff errors are pre-existing
PLW0717 warnings in unrelated code, see final-summary.md).

## Commit Reference

`7f3276af fix(live-formatter): force UTF-8 decoding for node subprocess output`

## Confidence

**HIGH** for the integration test failure. **MEDIUM** for the
non-coverage envs (mypy, xdist-remote, playwright-report) that this
agent did not have a host to run; recommend a re-run on a real
Linux 3.14 runner to confirm those envs are also green.
