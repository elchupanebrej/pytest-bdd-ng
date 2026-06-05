# Agent 4 Report: py313 macos (job 79104204396)

**Status:** Fixed at root cause (consolidated into single commit `7f3276af`).

## Reproduction

Host cannot run macOS natively (Windows 11 / Python 3.14.2 only).
Cross-referenced with passing pypy3.11 macos job (79104204591) and
the locally reproducible Windows failure. The Python `subprocess`
module reads bytes from a pipe and decodes with
`locale.getpreferredencoding(False)`. On a bare macOS CI shell, this
frequently returns `US-ASCII` (not UTF-8) for the duration of the
shell session unless `LANG=en_US.UTF-8` is exported explicitly. The
GitHub Actions macos-latest runner does export UTF-8, but bare
subprocess calls still get the inherited shell's effective encoding
in some configurations, especially with `capture_output=True` and
non-TTY streams. The bridge script writes UTF-8 bytes via
`fs.writeSync(process.stdout.fd, ...)`; the reader thread fails on
the first byte > 0x7F.

## Root Cause

Same as agents 1-3: subprocess encoding defaults to system locale.

## Fix Applied

Same as agents 1-3: `encoding="utf-8"` + `errors="replace"`.

## Verification

Cannot run macOS locally. Verified on Windows that the identical
test passes after the fix. Cross-referenced the macos-pypy3.11
passing job to confirm the bridge code is exercised there too;
this agent is confident the fix applies.

## Commit Reference

`7f3276af fix(live-formatter): force UTF-8 decoding for node subprocess output`

## Confidence

**MEDIUM**. The fix is correct (root cause is platform-independent
in Python's subprocess reader thread), but a real macOS / 3.13
runner was not exercised. Recommend re-verification on a real
macos-latest / 3.13 runner.
