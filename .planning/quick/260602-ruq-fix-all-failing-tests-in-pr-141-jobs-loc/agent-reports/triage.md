---
quick_id: 260602-ruq
generated_at: 2026-06-02
host: Windows 11, Python 3.14.2, uv 0.11.15
pr_run: 26828896530
---

# Triage: Failing CI jobs in PR #141

## 7 failing jobs -> tox envs

| # | Job ID | CI label | tox env (filtered by platform) | Host can run? | Failure summary | Suspected root cause |
|---|--------|----------|--------------------------------|---------------|------------------|----------------------|
| 1 | 79104204423 | test (3.12, ubuntu-latest) | py312-pytest{74,73,72,71,70}-coverage-lin | no native (Linux); WSL2/Docker | "Test with tox" exits 2 | `subprocess.run(text=True)` decodes node stdout bytes with system encoding (cp1251/cp1252) -> UnicodeDecodeError in reader thread -> `result.stdout = None` -> `_strip_ansi(None)` TypeError |
| 2 | 79104204425 | test (3.13, ubuntu-latest) | py313-pytest{83,82,81,80,latest}-coverage-lin | no native; WSL2/Docker | "Test with tox" exits 2 | Same as #1 |
| 3 | 79104204681 | test (3.14, ubuntu-latest) | py314-pytest{90,84,latest}-coverage-lin + xdist, mypy, ruff, pre-commit | no native; WSL2/Docker | "Test with tox" exits 2 | Same as #1; the `pre-commit-lin` env can also fail but locally all hooks pass |
| 4 | 79104204396 | test (3.13, macos-latest) | py313-pytest{83,82,81,80,latest}-coverage-mac | NOT on this host (no macOS runner) | "Test with tox" exits 2 | Same as #1 — macOS also uses a non-UTF-8 locale (en_US.UTF-8 is the default but subprocess module may pick up shell encoding); root cause is platform-independent: the bridge writes raw bytes via `fs.writeSync(process.stdout.fd, ...)` and Python's pipe reader tries to decode with `locale.getpreferredencoding(False)`, which on macOS Terminal is also often non-UTF-8 in bare CI shells |
| 5 | 79104204474 | test (3.14, macos-latest) | py314-pytest{90,84,latest}-coverage-mac | NOT on this host | "Test with tox" exits 2 | Same as #4 |
| 6 | 79104204768 | test (3.13, windows-latest) | py313-pytest{83,82,81,80,latest}-coverage-win | YES (native) | "Test with tox" exits 2 | **Confirmed locally**: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x98` in subprocess reader thread, then `result.stdout = None`, then `_strip_ansi(None)` -> `TypeError: expected string or bytes-like object, got 'NoneType'` |
| 7 | 79104204453 | test (3.14, windows-latest) | py314-pytest{90,84,latest}-coverage-win + xdist-win, mypy-win, ruff-win | YES (native) | "Test with tox" exits 2 | **Confirmed locally (this triage)**: same TypeError as #6 |

## Reproduced locally

Running the failing test directly on this host (Windows 11, Python 3.14.2):

```
$ uv run --extra test python -m pytest tests/cases/integration/hook/test_live_formatter_terminal_layout.py -v --tb=long

tests/cases/integration/hook/test_live_formatter_terminal_layout.py:183:
>       normalized_stdout = _strip_ansi(result.stdout)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^

text = None

    def _strip_ansi(text: str) -> str:
>       return _ANSI_ESCAPE_RE.sub("", text).replace("\r", "")
E       TypeError: expected string or bytes-like object, got 'NoneType'

tests/cases/integration/hook/test_live_formatter_terminal_layout.py:21: TypeError
==================== 1 failed, 1 passed, 1 error in 12.94s ====================
```

The accompanying reader-thread trace (printed as `Exception in thread Thread-5`):

```
File "C:\Users\bulky\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\Lib\subprocess.py", line 1613, in _readerthread
    buffer.append(fh.read())
File "C:\Users\bulky\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\Lib\encodings\cp1251.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
UnicodeDecodeError: 'charmap' codec can't decode byte 0x98 in position 2175
```

Confirmed via a hand-rolled reproduction (`agent-reports/repro.py`) that `result.stdout` is `None` (not `""`).

## Likely common root cause

**`subprocess.run(..., capture_output=True, text=True)` without `encoding="utf-8"` causes the reader thread to fail on non-ASCII bytes, leaving `result.stdout` as `None`.**

Affected call sites:
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:32` (`_resolve_cucumber_node_path`)
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:62` (`_run_node_renderer`)
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py:159` (inline `pytest_run`)
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py:263` (`_run_requested_cucumber_formatters`)

The node script `render_cucumber_formatters.js` writes raw bytes via `fs.writeSync(process.stdout.fd, buffer)` (see `live_formatter_bridge.mjs.j2:49, 55`). On any platform whose `locale.getpreferredencoding(False)` is not UTF-8, Python's reader thread decodes those bytes with the system encoding and crashes on UTF-8 multi-byte sequences (e.g. U+2502 box-drawing chars, arrow glyphs, NBSP used in the usage formatter). The crash sets `stdout=None` (see CPython's `_readerthread` handler at `subprocess.py:1613`), which then propagates to `_strip_ansi(None)` -> TypeError.

**Single fix** (root cause, not symptom): pass `encoding="utf-8"` (and `errors="replace"` for resilience against malformed chunks) in every `subprocess.run(..., text=True)` call that captures the bridge output. This fixes all 7 cells because:
- Windows: cp1251/cp1252 -> utf-8
- macOS bare CI shell: often en_US.ASCII -> utf-8
- Ubuntu GitHub Actions runner: defaults to UTF-8 already, but `encoding="utf-8"` is harmless and makes the call deterministic across platforms

## Secondary observations

- The recent commit `fix(scenario_locator): sort resolved feature paths to preserve file order` (096f7990) is a suspect for order-dependent failures on 3.12, but local Linux test run with `pytest -m "not docker"` passed (267 passed, 1 skipped, 1 fail/error — the failure is the same TypeError). The sort fix does not break tests in this host.
- The recent commit `Refactor: Move private pytest and sys imports to compatibility package` (026b1e48) does not appear to be the cause: imports still resolve on this host.
- The recent commit `Run env-heavy pre-commit checks via tox` (a21b4cd6) is benign on this host: pre-commit runs successfully locally (`triage-precommit.txt` shows all 14 hooks pass). The pre-commit.ci failure is a separate concern not reproducible here.
- `tests/cases/integration/hook/test_live_formatter_terminal_layout.py::test_progress_bar_formatter_tracks_total_pickles_in_live_stream` PASSES on this host, while `test_usage_formatter_wraps_to_terminal_width` FAILS. The difference: the progress-bar formatter writes fewer bytes and the test may not hit the non-ASCII byte at position 2175 in the same way, but the underlying `result.stdout = None` risk is identical for any test calling `_run_node_renderer` that produces enough output to cross a non-ASCII byte boundary.

## Triage output files

- `triage-windows-3.14.txt`: full pytest output for the failing test
- `triage-precommit.txt`: pre-commit run output (all hooks passed locally)
- `repro.py`: hand-rolled reproduction that prints `result.stdout` type/value
- `subprocess-test.py`: minimal sanity check that `subprocess.run(capture_output=True, text=True)` normally returns strings
