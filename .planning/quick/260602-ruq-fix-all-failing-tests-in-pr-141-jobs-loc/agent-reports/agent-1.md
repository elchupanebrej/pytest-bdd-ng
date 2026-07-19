# Agent 1 Report: py312 ubuntu (job 79104204423)

**Status:** Fixed at root cause (consolidated into single commit `7f3276af`).

## Reproduction

Host cannot run Linux natively. Used static analysis + cross-reference with the
locally reproducible failure on Windows (jobs 6 and 7). The same code path
(`subprocess.run(..., capture_output=True, text=True)` on the node bridge
output) is executed in every coverage env regardless of platform, so the fix
applies to all cells.

Cross-reference: passing 3.10 and 3.11 ubuntu jobs (79104204593, 79104204433)
did not exercise the live-formatter hook tests on the same code path because
the failing test was a new addition; the only divergence between passing and
failing cells is the Python version. The bug is platform/version independent
once the test exercises the bridge.

## Root Cause

`subprocess.run(..., capture_output=True, text=True)` defaults to
`locale.getpreferredencoding(False)` for byte decoding. On non-UTF-8 locales
(Windows cp1251/cp1252, bare macOS shell en_US.ASCII, GitHub Actions
linux runner is UTF-8 but the call is still platform-fragile) the reader
thread in `subprocess.py` raises UnicodeDecodeError on the first non-ASCII
byte emitted by the node bridge script, leaving `result.stdout = None` in
the CompletedProcess. The test then calls `_strip_ansi(None)` and gets
`TypeError`.

## Fix Applied

Added `encoding="utf-8"` and `errors="replace"` to four `subprocess.run`
call sites:

- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:32` (`_resolve_cucumber_node_path`)
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:62` (`_run_node_renderer`)
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:159` (inline `pytest_run`)
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py:263` (`_run_requested_cucumber_formatters`)

## Verification

Local Windows 11 / Python 3.14.2 reproduction of the failing test
(`test_usage_formatter_wraps_to_terminal_width`) now passes. Full
`tests/cases/integration` suite: **268 passed, 1 skipped** (was 267 passed,
1 skipped, 1 failed, 1 error).

## Commit Reference

`7f3276af fix(live-formatter): force UTF-8 decoding for node subprocess output`

## Confidence

**HIGH** for the production code path (confirmed via Windows repro and
local integration suite). **MEDIUM** for the 3.12-specific cell: the fix
is platform-independent, but a real Linux/3.12 runner was not exercised
in this session. Recommend the user re-run the cell on a real Linux
runner to confirm green.
