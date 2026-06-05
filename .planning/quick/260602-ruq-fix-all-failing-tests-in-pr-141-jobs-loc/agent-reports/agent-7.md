# Agent 7 Report: py314 windows (job 79104204453)

**Status:** Fixed at root cause (consolidated into single commit `7f3276af`).

## Reproduction

This cell was reproduced live on this host (Windows 11 / Python
3.14.2). Output captured in `triage-windows-3.14.txt` and
`verify-hook.txt`.

## Root Cause

Identical to agent 6: subprocess encoding defaults to cp1251/cp1252
on Windows; the bridge writes UTF-8; the reader thread crashes;
`result.stdout = None`; `_strip_ansi(None)` TypeError.

## Fix Applied

Same as agent 6.

## Verification

Confirmed locally: `test_usage_formatter_wraps_to_terminal_width`
passes after the fix. Full integration suite: **268 passed,
1 skipped**. The 3.14 cell includes additional envs (mypy-win,
ruff-win, mypy-messages, xdist-remote-win) that this agent did not
re-run on a native Windows runner; see final-summary.md for the
followup list.

## Commit Reference

`7f3276af fix(live-formatter): force UTF-8 decoding for node subprocess output`

## Confidence

**HIGH** for the coverage env (the failing test is in this env and
is now green). **MEDIUM** for the other 3.14 envs (mypy, ruff,
xdist-remote) that this host did not exercise end-to-end.
