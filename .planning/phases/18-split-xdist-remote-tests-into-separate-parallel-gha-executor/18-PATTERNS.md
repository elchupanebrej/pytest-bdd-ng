# Phase 18: Split xdist-remote tests into separate parallel GHA executor - Pattern Map

**Mapped:** 2026-06-02
**Files analyzed:** 2 modified
**Analogs found:** 3 / 3

## File Classification

| New/Modified File or Target | Role | Data Flow | Closest Analog | Match Quality |
|-----------------------------|------|-----------|----------------|---------------|
| `Makefile` `tox` target | config | batch command-execution | `Makefile` lines 412-414 | exact |
| `.github/workflows/main.yml` (`test` job modification) | config | event-driven batch | `.github/workflows/main.yml` existing `Test with tox` step | exact |
| `.github/workflows/main.yml` (`test-xdist-remote` job) | config | event-driven batch | `.github/workflows/main.yml` existing `test` job | exact |

## Pattern Assignments

### `Makefile` `tox` target (config, batch command-execution)

**Analog:** Existing `tox` target.

**Current variable pattern** (`Makefile` lines 412-414):
```makefile
tox: env-check-tox
	$(TOX)
```

**Target pattern to copy:** Add a configurable `TOX_ARGS` parameter with conditional default (empty), and forward it to `$(TOX)` command. This preserves standard local run behavior.

```makefile
TOX_ARGS ?=
tox: env-check-tox
	$(TOX) $(TOX_ARGS)
```

**Planner note:** Keep the `.PHONY` and `env-check-tox` checks unchanged. This keeps it 100% compliant with existing Makefile contract checks (`tests/cases/contract/test_makefile_test_api.py`).

---

### `.github/workflows/main.yml` `test` job modification (config, event-driven batch)

**Analog:** Existing `Test with tox` step.

**Current step pattern** (`.github/workflows/main.yml` lines 63-65):
```yaml
      - name: Test with tox
        run: |
          make tox
```

**Target pattern to apply:** Modify the run command to pass `TOX_ARGS` to skip the six `xdist-remote` environments:

```yaml
      - name: Test with tox
        run: |
          make tox TOX_ARGS='--skip-env "xdist-remote-.*"'
```

**Planner note:** Ensure the regex `"xdist-remote-.*"` is quoted properly to survive both YAML and shell parsing.

---

### `.github/workflows/main.yml` `test-xdist-remote` parallel job (config, event-driven batch)

**Analog:** Existing `test` job structure (lines 12-82), but trimmed of coverage, build-checking, and schema verification steps. Also analog to existing Docker setup step patterns (such as standard action usage).

**Existing `test` job steps to reuse** (`.github/workflows/main.yml` lines 44-62):
- Checkout code
- Set up Python 3.14 (fixed, no need for matrix)
- Set up Node.js
- Setup pandoc
- Set up uv
- Install npm dependencies

**New patterns to introduce (from design):**
1. **Docker Setup & Verification**: A dedicated action to provision Docker (`docker/setup-docker-action@v5`) followed by a diagnostic step to confirm Docker daemon and Compose version.
2. **Matrix mapping**: `matrix.os` mapped to `lin` or `win` platforms inline using GitHub expression:
   `platform="${{ matrix.os == 'ubuntu-latest' && 'lin' || 'win' }}"`
3. **Environment variable passing**: `PYTEST_REMOTE_MODE: ${{ matrix.mode }}`.
4. **Targeted tox run**: `make tox TOX_ARGS="-e py314-pytestlatest-xdist-remote-${{ matrix.mode }}-${platform}"`.

**Target pattern structure:**
```yaml
  test-xdist-remote:
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        shell: bash
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

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "*"

      - name: Install pandoc
        uses: r-lib/actions/setup-pandoc@v2

      - name: Set up uv
        uses: astral-sh/setup-uv@v6

      - name: Set up Docker
        uses: docker/setup-docker-action@v5
        with:
          version: 29.1.5

      - name: Verify Docker toolchain
        run: |
          docker --version
          docker compose version
          docker info --format 'server={{.Server.Version}} os={{.OSType}}' || docker info

      - name: Install npm dependencies
        run: |
          make env-install-npm

      - name: Run xdist-remote tox env
        env:
          PYTEST_REMOTE_MODE: ${{ matrix.mode }}
        run: |
          platform="${{ matrix.os == 'ubuntu-latest' && 'lin' || 'win' }}"
          make tox TOX_ARGS="-e py314-pytestlatest-xdist-remote-${{ matrix.mode }}-${platform}"
```

**Planner note:** Keep `fail-fast: false` to ensure one slow/problematic matrix cell (e.g. `ssh` on Windows runner, as described in `18-RESEARCH.md`) does not abort the other running cells.

---

## Shared Patterns

### Makefile Argument Forwarding
Whenever command arguments must be customized in CI but default to full matrices or standard setups locally, pass them via Make variables (e.g. `TOX_ARGS ?=`) rather than bypassing Makefile targets.

### Toolchain Setup Consistency
Maintain identical order and version references for tool setup steps (checkout, setup-python, setup-node, setup-pandoc, setup-uv) across different GitHub Actions workflow jobs.

### Loud Preflight Checks
For integrations with external system services (such as Docker daemon), verify their existence and retrieve versions before running test execution frameworks.

---

## No Analog Found

- **Windows Runner Nested Virtualization Limitation**: The SSH Docker Compose tests require building/running Linux containers. Because nested virtualization is disabled on standard GitHub-hosted Windows runners, this specific runner cell is known to fail on standard GHA. No workaround analog exists in the current repository, but this is a documented runner/infra constraint rather than a code mapping discrepancy.

---

## Integration Points

| Point | Exact Change |
|-------|--------------|
| `Makefile` line 412 | Add `TOX_ARGS ?=` variable. |
| `Makefile` line 414 | Update `tox` target to use `$(TOX) $(TOX_ARGS)`. |
| `.github/workflows/main.yml` line 65 | Update `Test with tox` step to run `make tox TOX_ARGS='--skip-env "xdist-remote-.*"'`. |
| `.github/workflows/main.yml` after line 82 | Append the `test-xdist-remote` parallel matrix job definition. |

## Metadata

**Analog search scope:** `Makefile`, `.github/workflows/main.yml`, `tox.ini`, `tests/cases/contract/test_makefile_test_api.py`
**Files scanned:** 5
**Pattern extraction date:** 2026-06-02
