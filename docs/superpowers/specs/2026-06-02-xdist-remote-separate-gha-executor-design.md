# Split xdist-remote Tests Into a Separate GHA Executor

Date: 2026-06-02

## Goal

Reduce the wall-clock time of the `pytest-bdd-ng` CI pipeline by running the
six long-running xdist-remote tox environments in a dedicated GitHub Actions
job that executes in parallel with the main test job, instead of
sequentially inside it.

The six environments are:

- `py314-pytestlatest-xdist-remote-socket-lin`
- `py314-pytestlatest-xdist-remote-via-lin`
- `py314-pytestlatest-xdist-remote-ssh-lin`
- `py314-pytestlatest-xdist-remote-socket-win`
- `py314-pytestlatest-xdist-remote-via-win`
- `py314-pytestlatest-xdist-remote-ssh-win`

Each spins up a Docker compose cluster (`tests/assets/docker/remote_xdist/`)
and a pytest-xdist remote gateway (socket / via / ssh), so each is the
slowest env in the current matrix. Today they run inside the existing
`test` job on the `python-version=3.14, os={ubuntu-latest,windows-latest}`
matrix cells, serialized behind the rest of the tox envs in those cells.

The design changes only `.github/workflows/main.yml`. `tox.ini`, the
`Makefile`, `pyproject.toml`, and the test suite itself stay unchanged, so
`make tox` and `uvx --with tox-uv tox` (no arguments) still run the full
matrix locally.

## Approach

1. Add a new `test-xdist-remote` job in `.github/workflows/main.yml` with a
   six-cell matrix: `os ∈ {ubuntu-latest, windows-latest}` ×
   `mode ∈ {socket, via, ssh}`. The job runs in parallel with the existing
   `test` job (no `needs:` dependency).
2. In the existing `test` job, replace `make tox` with
   `uvx --with tox-uv tox --skip-env "xdist-remote-.*"` so the six envs are
   not run twice.
3. Provision Docker on the new job's runner through a declared GHA
   configuration step (`docker/setup-docker-action@v5`) rather than relying
   on the implicit preinstalled daemon. This makes Docker availability a
   first-class, auditable part of the workflow.

The new job invokes the existing `[testenv:py314-pytestlatest-xdist-remote-*]`
blocks from `tox.ini` unchanged. No new tox envs are introduced.

## Design

### Files touched

- `.github/workflows/main.yml` — modified only.
  - Modify the existing `test` job to skip the xdist-remote envs.
  - Add the new `test-xdist-remote` job.

No other files are touched. `tox.ini`, `Makefile`, `pyproject.toml`, and all
test files are out of scope.

### Existing `test` job change

Replace the current `make tox` step:

```yaml
- name: Test with tox
  run: |
    make tox
```

with:

```yaml
- name: Test with tox
  run: |
    uvx --with tox-uv tox --skip-env "xdist-remote-.*"
```

`make tox` resolves to `uvx --with tox-uv tox` on GHA via the `TOX ?=`
definition in the `Makefile` (`Makefile:47-49`), so the only behavioral
change is the appended `--skip-env` flag. All other steps in the `test`
job (checkout, setup-python, setup-node, setup-pandoc, setup-uv,
`env-install-npm`, coverage upload, build checking) stay exactly as they
are.

### New `test-xdist-remote` job

```yaml
test-xdist-remote:
  runs-on: ${{ matrix.os }}
  strategy:
    fail-fast: false
    matrix:
      os: [ubuntu-latest, windows-latest]
      mode: [socket, via, ssh]
  steps:
    - uses: actions/checkout@v4
      with:
        submodules: 'recursive'

    - name: Set up Python 3.14
      uses: actions/setup-python@v5
      with:
        python-version: "3.14"

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: "*"

    - name: Install pandoc
      uses: r-lib/actions/setup-pandoc@v2

    - name: Install uv
      uses: astral-sh/setup-uv@v6

    - name: Set up Docker
      uses: docker/setup-docker-action@v5
      with:
        version: 29.1.5

    - name: Verify Docker toolchain
      run: |
        docker --version
        docker compose version
        docker info --format 'server={{.Server.Version}} os={{.OSType}}'

    - name: Install npm dependencies
      run: |
        make env-install-npm

    - name: Run xdist-remote tox env
      env:
        PYTEST_REMOTE_MODE: ${{ matrix.mode }}
      run: |
        platform=${{ matrix.os == 'ubuntu-latest' && 'lin' || 'win' }}
        uvx --with tox-uv tox -e "py314-pytestlatest-xdist-remote-${{ matrix.mode }}-${platform}"
```

### Why `docker/setup-docker-action@v5`

`docker/setup-docker-action` is the official, multi-OS action for declaring
Docker as a workflow dependency. On GitHub-hosted Linux and Windows runners
the action is mostly a no-op for the daemon (it is already preinstalled and
running), but it:

- Pins the client version explicitly via `version:`.
- Establishes the precondition that other `docker/*` actions
  (`setup-buildx-action`, `build-push-action`, `login-action`) assume, so
  later optimizations (layer caching, buildx) compose cleanly.
- Makes Docker availability visible in the GHA job graph, so a future
  regression in the runner image (or a switch to `windows-2022` with a
  different Docker version) is detectable from the workflow file.

### Why standard runners, not larger / self-hosted

Per the user decision, each matrix cell runs on the standard
`ubuntu-latest` or `windows-latest` runner. Six parallel cells fit inside
the free concurrent-job quota for public repositories. No new infra is
required.

### Why no `needs: test`

The xdist-remote envs are independent of the main test job's outcome.
Making the new job depend on `test` would serialize them, defeating the
speedup. With no `needs:` they start at the same time as `test`.

### What is deliberately not added

- No `services: docker:` DinD container. The host daemon is what the test
  fixtures (in `tests/assets/docker/remote_xdist/docker-compose.yml` and
  `src/pytest_bdd/testing/docker.py`) expect.
- No `docker/login-action`. Images are local (`pytest-bdd-remote-xdist-*:
  local`); no registry is touched.
- No `docker/setup-buildx-action` or `docker/build-push-action` with
  `cache-from: type=gha`. The project's `docker compose build` is invoked
  from inside pytest, not from a GHA step, so wiring layer caching would
  require restructuring the test fixture. Out of scope.
- No `docker/setup-qemu-action`. Single-arch builds only.
- No macOS in the matrix. `tox.ini` defines only `lin` and `win` factors
  for the xdist-remote envs; macOS was never in scope.

## Data Flow

```text
PR / push / schedule
  └── workflow run
        ├── job: test                       (existing, 12 cells: 6 pythons × 3 OSes, minus 6 excludes)
        │     └── runs: uvx --with tox-uv tox --skip-env "xdist-remote-.*"
        │           (the 6 xdist-remote envs are skipped)
        │
        └── job: test-xdist-remote          (new, 6 cells: 2 OSes × 3 modes)
              ├── Set up Docker             (docker/setup-docker-action@v5)
              ├── Verify Docker toolchain   (docker --version / compose / info)
              ├── Install npm dependencies  (make env-install-npm)
              └── Run xdist-remote tox env  (uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-{mode}-{platform})
```

No shared state between `test` and `test-xdist-remote`; the barrier
coordination in `src/pytest_bdd/util/tests_group_ordering.py` is intra-xdist
and only relevant within a single tox env, so it is unaffected.

## Error Handling

- The new job's matrix uses `fail-fast: false` (same as the existing `test`
  job), so a single mode/platform failure does not cancel the others.
- The `Verify Docker toolchain` step surfaces a clear "docker missing" or
  "compose missing" error in the GHA log if the runner image ever regresses
  on Docker availability, before the slow tox step starts.
- The `Set up Docker` step itself fails fast (and with a clear error
  message) if the requested version pin cannot be satisfied.
- The original `test` job's skip regex (`"xdist-remote-.*"`) is the exact
  substring shared by all six env names; it cannot accidentally match any
  other env in `env_list` (verified by `uvx --with tox-uv tox -l | rg
  xdist-remote` returning 6 lines and nothing else containing that
  substring).

## Testing

Verification is via the GitHub Actions UI, plus a local pre-flight check:

1. Pre-flight on the local machine:
   - `uvx --with ruamel.yaml python -c "import yaml; yaml.safe_load(open('.github/workflows/main.yml'))"`
     (or `make validate-github-actions` if `act` is installed).
   - `uvx --with tox-uv tox -l | rg xdist-remote` returns exactly 6 lines,
     confirming no env was renamed.
2. Push to a feature branch and observe in the Actions UI:
   - The `test` job matrix still produces 18 cells; each finishes faster
     than before because the 6 xdist-remote envs are skipped.
   - 6 new `test-xdist-remote` jobs appear in parallel with the `test` job
     (not after it). Each shows a `Set up Docker` step, a `Verify Docker
     toolchain` step, and a `Run xdist-remote tox env` step.
   - No env is run twice: `tox -l` run inside the `test` job's log shows
     the xdist-remote envs as `skipped` or absent.
3. After merge, observe the GHA run time for the default branch. The
   `3.14 × ubuntu-latest` and `3.14 × windows-latest` cells should each
   finish strictly sooner; the xdist-remote envs run in parallel rather
   than sequentially inside the cell.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `tox --skip-env` regex matches the wrong envs | Pre-flight: `uvx --with tox-uv tox -l` piped through `rg xdist-remote` shows exactly 6 hits. No other env name contains `xdist-remote-`. |
| Windows runner Docker regression (Docker Desktop not running) | `Verify Docker toolchain` step surfaces `docker info` failure before the slow tox step. If it ever fires, the fix is to add `docker/setup-docker-action` options to enable a fallback path, not to silence the check. |
| GHA Windows runner is mid-migration (e.g., `windows-2025` vs `windows-2022`) and Docker is missing | `Set up Docker` step will install/configure Docker explicitly. Action supports all three target OSes. |
| `py314-pytestlatest-xdist-remote-ssh-{lin,win}` per-test timeout is 1500s (SSH mode is the slowest) | The new job runs in parallel with the main test, so its 1500s does not extend the wall-clock time of the main test job. GHA job timeout is 360 minutes by default, well above this. |
| Coverage upload (`codecov-action`) on the new job | The new job does not run the coverage envs, so it intentionally does not include the `Upload coverage to Codecov` step. Coverage of the xdist-remote envs is captured by the existing `py314-pytestlatest-gherkinlatest-xdist-coverage-lin` env in the main test job. |

## Out of Scope (Deliberately)

- Local `tox` / `make tox` speedup. Would require moving the 6 envs out
  of `[tox].env_list` and adding a `test-xdist-remote` Make target.
- Adding a `test-xdist-remote` Makefile target.
- Switching any runner to a larger (`ubuntu-latest-8-cores`) or self-hosted
  variant.
- Wiring Docker layer caching via `docker/build-push-action` +
  `cache-from: type=gha`. Requires restructuring the pytest fixture's
  compose invocation; revisit if Docker layer build becomes the dominant
  cost.
- Adding the 6 cells to `release.yaml` or any other workflow.
