# Agent 6 Report: py313 windows (job 79104204768)

**Status:** Fixed at root cause (consolidated into single commit `7f3276af`).

## Reproduction

This host IS a Windows 11 / Python 3.14.2 machine. Reproduction of
the failing test directly:

```
$ uv run --extra test python -m pytest \
    tests/cases/integration/hook/test_live_formatter_terminal_layout.py \
    -v --tb=long

tests/cases/integration/hook/test_live_formatter_terminal_layout.py:183:
>       normalized_stdout = _strip_ansi(result.stdout)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^

text = None
    def _strip_ansi(text: str) -> str:
>       return _ANSI_ESCAPE_RE.sub("", text).replace("\r", "")
E       TypeError: expected string or bytes-like object, got 'NoneType'

==================== 1 failed, 1 passed, 1 error in 12.94s ====================
```

A second thread trace, from the same session:

```
File "C:\Users\bulky\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\Lib\subprocess.py", line 1613, in _readerthread
    buffer.append(fh.read())
File "C:\Users\bulky\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\Lib\encodings\cp1251.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
UnicodeDecodeError: 'charmap' codec can't decode byte 0x98 in position 2175
```

The 3.13 cell runs the same tox env shape (`py313-pytest{83,82,81,80,latest}-coverage-win`) and the same code path. The TypeError
manifestation is identical.

## Root Cause

`subprocess.run(..., capture_output=True, text=True)` defaults to
`locale.getpreferredencoding(False)` (cp1251/cp1252 on Windows for
non-CJK locales). The cucumber live-formatter bridge writes raw
UTF-8 bytes via `fs.writeSync(process.stdout.fd, ...)` (see
`live_formatter_bridge.mjs.j2:49, 55`). The reader thread in
`subprocess.py` fails on the first non-ASCII byte, sets
`result.stdout = None`, and the test crashes at
`_strip_ansi(None)`.

## Fix Applied

Added `encoding="utf-8"` and `errors="replace"` to four
`subprocess.run` call sites:

- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:32`
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:62`
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:159`
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py:263`

## Verification

After fix, the same test passes:

```
$ uv run --extra test python -m pytest \
    tests/cases/integration/hook/test_live_formatter_terminal_layout.py \
    -v
... 2 passed in 5.78s
```

Full integration suite: **268 passed, 1 skipped** (was 267 passed,
1 skipped, 1 failed, 1 error).

## Commit Reference

`7f3276af fix(live-formatter): force UTF-8 decoding for node subprocess output`

## Confidence

**HIGH**. Verified natively on the same host family (Windows 11 /
Python 3.14.2). The same test is run on Python 3.13 in the failing
cell, and the fix is Python-version independent (the
`locale.getpreferredencoding(False)` behaviour is identical).
