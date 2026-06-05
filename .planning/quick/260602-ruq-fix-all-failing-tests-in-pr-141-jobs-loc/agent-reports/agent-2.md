# Agent 2 Report: py313 ubuntu (job 79104204425)

**Status:** Fixed at root cause (consolidated into single commit `7f3276af`).

## Reproduction

Same as agent 1 (Linux host unavailable; cross-referenced with locally
reproducible Windows failure and passing pypy3.11/3.10/3.11 ubuntu jobs).

## Root Cause

Same as agent 1: `subprocess.run(..., text=True)` defaults to system
encoding; the cucumber live-formatter bridge writes raw bytes via
`fs.writeSync(process.stdout.fd, ...)`; the Python reader thread fails
on non-ASCII bytes and sets `result.stdout = None`; the test then
crashes in `_strip_ansi(None)`.

## Fix Applied

Same as agent 1: `encoding="utf-8"` + `errors="replace"` in four
`subprocess.run` call sites (see agent-1.md for the full list).

## Verification

Confirmed locally on Windows / Python 3.14.2: the test that was
failing in 3.13 ubuntu CI (and identically in 3.14 Windows) now
passes. Full integration suite: **268 passed, 1 skipped**.

## Commit Reference

`7f3276af fix(live-formatter): force UTF-8 decoding for node subprocess output`

## Confidence

**HIGH** for the production code path. **MEDIUM** for the 3.13
Linux cell: not exercised in this session. Recommend re-verification
on a real Linux/3.13 runner.
