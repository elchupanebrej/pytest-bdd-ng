# coverage.py subprocess and installed-consumer capabilities

Research ticket: [elchupanebrej/pytest-bdd-ng#334](https://github.com/elchupanebrej/pytest-bdd-ng/issues/334)

Status: research complete. This report records facts, commands, and observed behavior only.
It does not choose policy and does not change product code.

Scope: the pinned implementation `coverage>=7.17,<8`, tested with `coverage==7.17.1`
(released 2026-11-03) [S12], on the supported interpreter matrix.

## Executive answers

| # | Question | Short answer | Evidence |
|---|----------|--------------|----------|
| 1 | Do `[run] patch = subprocess`, `parallel = true`, and `COVERAGE_PROCESS_START` instrument children and grandchildren launched by a pytest child process? | **Yes**, provided the coverage distribution (including its `a1_coverage.pth`) is installed in every interpreter that runs a descendant. A three-level chain (pytest -> child -> grandchild) produced one fragment per process and the installed package's lines from every level. `patch = subprocess` does not create the `.pth`; it publishes `COVERAGE_PROCESS_CONFIG` and forces `parallel = true`. | [D1] [D2] [S1] [S2] [S3] [P1] [P2] |
| 2 | Is a fresh venv created after installing the built wheel measured once coverage is explicitly provisioned, without shadowing the installed product? | **Yes**, when coverage is installed into that venv and the consumer is run from a directory that does not contain a same-named source package. The measured file was the venv's `site-packages/...` file. Without coverage in the fresh venv, descendants produced no fragments at all even though the outer venv had coverage. | [P3] [P4] [P10] |
| 3 | Can per-process fragments carry a run token that `combine` accepts selectively? | **Not as a dedicated token in the fragment suffix.** The suffix is fixed (`host.pid.random[.hash]`). A run token can be carried in the *base data file name* via `[run] data_file` or `COVERAGE_FILE`; `combine` then selects by that base prefix, by explicit file paths, or by directories. A literal custom suffix exists only through the Python `Coverage(data_suffix=...)` API, which `process_startup()` does not expose. | [D4] [D5] [S6] [S7] [S8] [S10] [P5] [P6] |
| 4 | Observed behavior on CPython 3.11-3.15, PyPy 3.12, GraalPy 25.3 | All Linux/Windows CPython cells and Linux PyPy 3.12 produced 3 fragments and an 88% report. GraalPy 25.4.4.1.1 also passed the simple probe, but it is not an officially supported implementation, has no C tracer and no `sys.monitoring`, and ran roughly 10x slower. Exact GraalPy 25.3 was not available on the host. | [S9] [P7] [P8] |
| 5 | Exact cases that produce no fragment at all | Missing coverage in the descendant interpreter, `-S`, scrubbed environment, `os._exit()` without `patch = _exit`, SIGKILL, SIGTERM without `sigterm = true`, `execv` without `patch = execv` (parent only), bad/missing config, and `parallel = false`. Details and observed counts below. | [D1] [D7] [D8] [S11] [P8] [P9] [P11] [P12] |

## Mechanism at 7.17.1

The pieces that matter for this ticket are small and can be read directly:

1. `process_startup()` starts coverage when `COVERAGE_PROCESS_CONFIG` or
   `COVERAGE_PROCESS_START` is present. `COVERAGE_PROCESS_CONFIG` wins if both are set.
   The config string is a serialized `CoverageConfig` prefixed with `:data:` [D6] [S3].
2. The coverage wheel ships `a1_coverage.pth` at the top level. That `.pth` imports
   `coverage` and calls `coverage.process_startup(slug="pth")` only when one of the two
   environment variables is set [S4] [S5]. This is why the *coverage distribution must be
   installed in the interpreter that runs the descendant*; it is not enough for an outer
   environment to have coverage.
3. `[run] patch = subprocess` sets `COVERAGE_PROCESS_CONFIG` in `os.environ` to the
   parent's serialized config. It does not write a `.pth` at runtime despite the helper's
   docstring [S2].
4. `[run] patch = subprocess` forces `parallel = true` during config post-processing [S1].
   Because the serialized config includes `patch = ["subprocess"]` and `parallel = true`,
   an auto-started child re-applies the patch and republishes the config for its own
   children. That is the grandchild path. The 7.10.3 changelog explicitly fixed missed
   data when subprocesses spawned more subprocesses simultaneously and when subprocesses
   ran in other directories [S13].
5. `serialize()` makes `data_file` and existing `source` paths absolute; this is what keeps
   child fragments in the parent's data directory even when a child changes `cwd` [S8] [P13].

`COVERAGE_PROCESS_START` alone also works for descendants when it points at a config with
`parallel = true`, because the variable is inherited. In that mode the parent does not need
`patch = subprocess`; the `.pth` still starts coverage in each descendant. We observed 4
fragments (driver, pytest, child, grandchild) with this setup [P2] [P14].

## 1. Children and grandchildren of a pytest child

Probe shape: a disposable installed package `spawnlib` was built as
`spawnlib-1.0.0-py3-none-any.whl`, installed into a fresh venv, and exercised from a
separate consumer directory. `pytest` called `top_main()`, which spawned a child process
calling `child_main()`, which spawned a grandchild process calling `grandchild_main()`.
Every process imported the installed `spawnlib`. The run used:

```ini
[run]
patch = subprocess
parallel = true
source = spawnlib
data_file = .coverage
```

With `coverage run --rcfile=cov.ini -m pytest -q`, three fragments appeared. Decoding the
line data showed the expected split:

| Process | Fragment line numbers in `site-packages/spawnlib/__init__.py` |
|---------|----------------------------------------------------------------|
| pytest process (`top_main`) | 26, 27, 28, 29, 30, 32, 34 |
| child process (`child_main`) | 15-23 |
| grandchild process (`grandchild_main`) | 11, 12 |

The combined report measured the installed file, not a source tree:

```text
/tmp/opencode/covresearch/probe/venv315/lib/python3.15/site-packages/spawnlib/__init__.py
16 statements, 2 missed, 88% (missing 22, 33)
```

A second shape put an outer `coverage run` around a driver that spawned
`python -m pytest`; pytest then spawned a child and a grandchild. This produced **four**
fragments: the driver (empty, because it did not import `spawnlib`), the pytest process,
the child, and the grandchild. The pytest process was auto-started, not explicitly run
under `coverage run -m pytest`, which confirms the child path as well [P1] [P2].

`os.system()` was also observed to work (2 fragments: parent and child), matching the
documented scope of `patch = subprocess` [D1] [P18].

Caveats:

- `patch = subprocess` uses `COVERAGE_PROCESS_CONFIG`, not `COVERAGE_PROCESS_START`
  [S2] [S3]. Both are accepted by the shipped `.pth` [S4]. The public "Managing
  processes" page documents `COVERAGE_PROCESS_START`; `COVERAGE_PROCESS_CONFIG` appears in
  the `process_startup()` docstring instead [D1] [D6].
- `execv`/`spawnv` with an explicit new environment still needs the coverage variable in
  that environment. `patch = execv` saves the parent's data and injects
  `COVERAGE_PROCESS_CONFIG` into `exec*e`/`spawn*e`; without it the parent's fragment is
  lost when the process image is replaced [D1] [S2] [P9].
- `patch = execv` is explicitly rejected on Windows in 7.17.1 [S11] [P15].

## 2. Fresh venv and the installed consumer

Probe: build `spawnlib` wheel, create a fresh venv, install only
`spawnlib`, `pytest`, and `coverage==7.17.1`, then run from a consumer directory that is
not the source tree.

Results:

- `spawnlib.__file__` resolved to
  `<venv>/lib/python3.15/site-packages/spawnlib/__init__.py`.
- 3 fragments were produced; `coverage combine` consumed all 3; the report measured the
  site-packages file and reported 88% [P3].
- A control venv with `spawnlib` and `pytest` but **no coverage** produced no descendant
  fragments. Only the outer driver fragment existed. Installing `coverage==7.17.1` into
  that venv created `a1_coverage.pth`; the same run then produced the descendant fragment
  and measured the installed package [P4].

This is the practical meaning of "explicitly provisioned": the fresh consumer venv needs
the coverage distribution so its `.pth` is present. An outer coverage installation cannot
instrument a descendant interpreter that cannot import coverage.

Shadowing observation: when the consumer working directory contained a local
`spawnlib/__init__.py`, Python imported that local package first and coverage measured the
local file (`spawnlib/__init__.py`, 8 statements, 75%), not the installed product [P10].
This is normal `sys.path` behavior [D10], and it is the concrete shadowing failure to avoid.

## 3. Run tokens and selective `combine`

The parallel fragment suffix is generated by `filename_suffix()` and matched by a fixed
pattern: `.host.pid<pid>.X<6 chars>x` plus an optional `.H<hash>h` content hash used for
deduplication [S6]. There is no user-controlled token field in that suffix.

What works instead:

- Set a distinct **base** data file name per run with `[run] data_file` or `COVERAGE_FILE`,
  for example `COVERAGE_FILE=.coverage.runA`. Fragments become
  `.coverage.runA.<host>.pid<pid>.X...`. `coverage combine --data-file=.coverage.runA`
  (or `COVERAGE_FILE=.coverage.runA coverage combine`) combines only that prefix [D4] [D5].
- Put fragments in a per-run directory and pass that directory to `coverage combine`.
- Pass explicit fragment file paths to `coverage combine`; the command accepts files and
  directories [D5] [S7].

Observed: two runs wrote `.coverage.runA.*` and `.coverage.runB.*`. Combining with
`COVERAGE_FILE=.coverage.runA` reported "Combined 3 files" and left all three
`.coverage.runB.*` files untouched. Combining one explicit `.coverage.runB.*` file into
a separate base combined exactly one file and deleted that input (no `--keep`) [P5].

The Python API can set a literal suffix: `Coverage(data_file=".coverage.x",
data_suffix="runA")` writes `.coverage.x.runA`. That literal suffix can be combined by
naming the file explicitly, but `process_startup()` calls `Coverage(config_file=...)`
without `data_suffix`, so auto-started children cannot receive a token suffix through
configuration or environment [S3] [S10] [P6].

`combine` deletes the matched input fragments unless `--keep` is passed; selective
combining is therefore destructive for the selected fragments [D5].

## 4. Supported matrix results

Each cell ran the same three-level probe from Section 1: `coverage run -m pytest -q`,
3 expected fragments, then `coverage combine` and `coverage report`.

| Platform | Interpreter | coverage | Tracer / core | Fragments | Report |
|----------|-------------|----------|---------------|-----------|--------|
| Linux (WSL2 Ubuntu 22.04) | CPython 3.11.17 | 7.17.1 | C tracer | 3 | 88% |
| Linux | CPython 3.12.15 | 7.17.1 | C tracer | 3 | 88% |
| Linux | CPython 3.13.15 | 7.17.1 | C tracer | 3 | 88% |
| Linux | CPython 3.14.7 | 7.17.1 | C tracer | 3 | 88% |
| Linux | CPython 3.15.2 | 7.17.1 | C tracer | 3 | 88% |
| Linux | PyPy 3.12.15 (PyPy 8.0.1) | 7.17.1 | pure Python (no C tracer) | 3 | 88% |
| Linux | GraalPy 3.13.14 (GraalVM 25.4.4.1.1) | 7.17.1 | pure Python; no `sys.monitoring` | 3 | 88% |
| Windows 10.0.26300 | CPython 3.11.0 | 7.17.1 | C tracer | 3 | 88% |
| Windows | CPython 3.12.10 | 7.17.1 | C tracer | 3 | 88% |
| Windows | CPython 3.13.11 | 7.17.1 | C tracer | 3 | 88% |
| Windows | CPython 3.14.2 | 7.17.1 | C tracer | 3 | 88% |
| Windows | CPython 3.15.0b1 | 7.17.1 | C tracer | 3 | 88% |

Notes:

- `coverage==7.17.1` requires Python `>=3.11` and lists CPython and PyPy as supported
  implementations. Its classifiers cover 3.11-3.16 [S9].
- The coverage README at this tag says "PyPy3 version 3.11" [S14]; PyPy 3.12.15 worked
  empirically with the pure-Python tracer. No PyPy C tracer existed in the tested venv
  [P7].
- GraalPy is not listed as a supported implementation [S9]. The host had GraalPy
  25.4.4.1.1, not exactly 25.3. It passed the simple probe with the pure-Python tracer
  because there is no C extension and no `sys.monitoring`; requesting
  `COVERAGE_CORE=sysmon` emitted
  `CoverageWarning: Can't use core=sysmon: sys.monitoring isn't available in this version,
  using default core (no-sysmon)` and fell back [P7] [P16]. The simple pytest probe took
  about 10.7 s on GraalPy versus roughly 0.7-1.4 s on CPython in the same probe, consistent
  with the missing C tracer. This is "observed to work in the simple case", not a support
  claim.
- Windows 3.15 was only available as `3.15.0b1` on this host. Linux 3.15.2 final was
  tested. All Windows cells used the same synthetic wheel and the same config.
- Free-threaded builds were not tested; the ticket did not request them.

## 5. Cases that produce no fragment at all

A fragment is written only if coverage started in that process and the process ended in a
way that runs coverage's save path. The following were observed with the pinned version,
unless marked "documented only". Counts below are for a driver that spawns exactly one
Python child, so "1 fragment" means the driver's fragment only.

| Case | Observed | Source / knob |
|------|----------|---------------|
| Descendant interpreter has no `coverage` installed (fresh venv) | 1 fragment; no child fragment. Installing coverage into that venv made the child fragment appear. | [S4] [S5] [P4] |
| Child started with `python -S` | Child ran (`ran without site`) but produced no fragment. `-S` skips `site`, so the `.pth` is not processed. | [D7] [D10] [P8] |
| Environment scrubbed; `COVERAGE_PROCESS_CONFIG`/`START` absent | Child ran but produced no fragment. | [D1] [P8] |
| Child ends with `os._exit()` and `patch = _exit` is not enabled | 1 fragment. Adding `_exit` to `patch` produced the child fragment. | [D1] [D8] [P8] [P17] |
| Child killed with SIGKILL | 1 fragment; no save path ran. | [D1] [P8] |
| Child receives SIGTERM without `sigterm = true` | 1 fragment. With `sigterm = true`, the child fragment appeared. | [D1] [D9] [P8] |
| Parent replaces itself with `execve` without `patch = execv` | 1 fragment: the parent's data was lost; the child fragment remained because the copied environment still had the coverage token. | [D1] [S2] [P9] |
| Bad or missing `COVERAGE_PROCESS_START` file, or malformed `COVERAGE_PROCESS_CONFIG` | Startup traceback (e.g. `ConfigError: Couldn't read ... as a config file` or a base64 decode error), child continued running, 1 fragment. Coverage did not start. | [S3] [P12] |
| `parallel = false` with manual `COVERAGE_PROCESS_START` (no `patch = subprocess`) | No parallel fragments; all processes wrote the same base file. The last writer won, and an empty parent save clobbered the child's data. `coverage combine` reported "No data to combine". | [D3] [S1] [P11] |
| Non-Python descendant (documented only) | No fragment; `patch = subprocess` is documented for Python processes. | [D1] |
| Descendant crashes before clean exit (documented only, e.g. segfault) | No fragment; coverage needs a chance to write at process end. | [D1] |

For contrast, these interpreter flags did **not** suppress the child fragment in the probe:
`-I` (isolated), `-E` (ignore `PYTHON*` environment variables), and `-s` (no user site).
They do not disable the venv `site` directory or the `COVERAGE_*` variables [D7] [P19].

## 6. Reproduction

The probe lived entirely under `/tmp/opencode/covresearch` on the Linux side and
`C:/Users/bulky/Projects/covprobe-win` on the Windows side. No product checkout was
modified. The essential commands were:

```bash
python3 -m pip wheel --no-deps -w dist .
python3 -m venv venv
venv/bin/python -m pip install dist/spawnlib-1.0.0-py3-none-any.whl \
    "coverage==7.17.1" pytest
venv/bin/python -m coverage run --rcfile=cov.ini -m pytest -q
venv/bin/python -m coverage combine --rcfile=cov.ini
venv/bin/python -m coverage report --rcfile=cov.ini -m
```

The probe package had three call levels:

```python
def grandchild_main():
    return leaf(21)

def child_main():
    subprocess.run([sys.executable, "-c",
        "import spawnlib; raise SystemExit(0 if spawnlib.grandchild_main() == 42 else 3)"])
    return leaf(21)

def top_main():
    subprocess.run([sys.executable, "-c",
        "import spawnlib; raise SystemExit(0 if spawnlib.child_main() == 42 else 3)"])
    return leaf(21)
```

For the run-token case, the same run was repeated with
`COVERAGE_FILE=.coverage.runA` and `COVERAGE_FILE=.coverage.runB`, then combined with
`COVERAGE_FILE=.coverage.runA` and with a per-run `--data-file`.

## References

Primary documentation:

- [D1] coverage.py 7.17.1, "Managing processes": <https://coverage.readthedocs.io/en/7.17.1/subprocess.html>
- [D2] coverage.py 7.17.1, `[run] patch`: <https://coverage.readthedocs.io/en/7.17.1/config.html#config-run-patch>
- [D3] coverage.py 7.17.1, `[run] parallel`: <https://coverage.readthedocs.io/en/7.17.1/config.html#config-run-parallel>
- [D4] coverage.py 7.17.1, `[run] data_file`: <https://coverage.readthedocs.io/en/7.17.1/config.html#config-run-data-file>
- [D5] coverage.py 7.17.1, "Combining data files": <https://coverage.readthedocs.io/en/7.17.1/commands/cmd_combine.html>
- [D6] coverage.py 7.17.1, `coverage.process_startup`: <https://coverage.readthedocs.io/en/7.17.1/api_module.html#coverage.process_startup>
- [D7] Python 3 command line options [<https://docs.python.org/3/using/cmdline.html#cmdoption-S> `-S`], [<https://docs.python.org/3/using/cmdline.html#cmdoption-E> `-E`], [<https://docs.python.org/3/using/cmdline.html#cmdoption-I> `-I`]
- [D8] Python `os._exit()`: <https://docs.python.org/3/library/os.html#os._exit>
- [D9] Python `signal` / SIGTERM: <https://docs.python.org/3/library/signal.html>
- [D10] Python `site` and `.pth` files: <https://docs.python.org/3/library/site.html>

Pinned source (coverage.py tag `7.17.1`, commit `13bc5f6144e1cdda9fb202ac1ea45e386683dcb9`):

- [S1] `coverage/config.py`, `post_process()` forces `parallel` for `patch = subprocess`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/config.py#L566-L574>
- [S2] `coverage/patch.py`, `_patch_subprocess()` publishes `COVERAGE_PROCESS_CONFIG`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/patch.py#L114-L118>
- [S3] `coverage/control.py`, `process_startup()`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/control.py#L1445-L1502>
- [S4] `coverage/pth_file.py`, the `.pth` entry point: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/pth_file.py#L10-L16>
- [S5] `setup.py`, packaging of `a1_coverage.pth`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/setup.py#L77-L102>
- [S6] `coverage/sqldata.py`, `filename_suffix()` and `SUFFIX_PATTERN`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/sqldata.py#L1233-L1266>
- [S7] `coverage/data.py`, `combinable_files()`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/data.py#L70-L98>
- [S8] `coverage/config.py`, `serialize()` and absolute paths: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/config.py#L591-L607>
- [S9] `setup.py`, classifiers and `python_requires`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/setup.py#L56-L66> and <https://github.com/coveragepy/coveragepy/blob/7.17.1/setup.py#L216>
- [S10] `coverage/control.py`, `data_suffix` vs `parallel`: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/control.py#L609-L622>
- [S11] `coverage/patch.py`, `patch = execv` rejected on Windows: <https://github.com/coveragepy/coveragepy/blob/7.17.1/coverage/patch.py#L63-L66>
- [S12] `CHANGES.rst`, 7.17.1 release date: <https://github.com/coveragepy/coveragepy/blob/7.17.1/CHANGES.rst#L27-L33>
- [S13] `CHANGES.rst`, 7.10.3 fixes for nested and out-of-directory subprocesses: <https://github.com/coveragepy/coveragepy/blob/7.17.1/CHANGES.rst#L822-L840>
- [S14] `README.rst`, supported Python and PyPy versions: <https://github.com/coveragepy/coveragepy/blob/7.17.1/README.rst#L28-L29>

Probe evidence (disposable environments; no product code):

- [P1] Linux CPython 3.15.2, `coverage run -m pytest`, 3-level chain: 3 fragments, lines
  split by process, combined 88%.
- [P2] Linux CPython 3.15.2, outer driver -> `python -m pytest` -> child -> grandchild:
  4 fragments (driver empty, pytest, child, grandchild).
- [P3] Fresh venv with wheel + coverage: measured
  `site-packages/spawnlib/__init__.py`, 3 fragments, 88%.
- [P4] Fresh venv without coverage: 1 fragment; after installing coverage: 2 fragments and
  the installed package measured.
- [P5] `.coverage.runA` / `.coverage.runB` selective combine; explicit file combine.
- [P6] `Coverage(data_suffix="runA")` writes `.coverage.x.runA`; explicit-file combine
  works; no env/config path to set this suffix.
- [P7] Matrix table in Section 4 (Linux CPython 3.11-3.15, PyPy 3.12, GraalPy 25.4.4.1.1;
  Windows CPython 3.11-3.15.0b1).
- [P8] No-fragment cases in Section 5 (`-S`, scrubbed env, `os._exit`, SIGKILL, SIGTERM).
- [P9] `execve` with and without `patch = execv`: 2 fragments vs 1 fragment.
- [P10] Local `spawnlib/` in the consumer cwd shadows the installed package; report measured
  the local 8-line file.
- [P11] `parallel = false` + manual `COVERAGE_PROCESS_START`: no fragments, single
  `.coverage_nopar`, empty last writer, `combine` reported "No data to combine".
- [P12] Bad `COVERAGE_PROCESS_START` and malformed `COVERAGE_PROCESS_CONFIG`: startup
  traceback, child continued, no fragment.
- [P13] Child with `cwd="/tmp"` still wrote its fragment in the parent's data directory
  because `data_file` was serialized as an absolute path.
- [P14] `COVERAGE_PROCESS_START` alone with `parallel = true` produced 4 fragments across
  driver/pytest/child/grandchild.
- [P15] Windows CPython 3.14: `patch = execv` exits with
  `patch=execv isn't supported yet on Windows.`
- [P16] GraalPy `COVERAGE_CORE=sysmon` warning and fallback text.
- [P17] `patch = subprocess, _exit` recovered the child fragment after `os._exit()`.
- [P18] `os.system()` child measured (2 fragments).
- [P19] `-I`, `-E`, and `-s` children still produced fragments.

## Limits

- The probe package is synthetic. It isolates coverage.py mechanics and avoids modifying or
  depending on the product's test suite. Product-specific import layouts, plugins, and
  installed-package metadata could add behavior not covered here.
- One probe run per matrix cell is enough to establish whether fragments and measurement
  exist, not to benchmark performance. The GraalPy timing is indicative only.
- The host did not offer GraalPy 25.3 exactly; the tested build was GraalPy 25.4.4.1.1
  (Python 3.13.14).
- The Windows host did not offer a final CPython 3.15; the tested build was 3.15.0b1.
  Linux used final CPython 3.15.2.
- No policy recommendation is made here. In particular, this report does not decide which
  provisioning strategy, token scheme, or support matrix the repair should adopt.
