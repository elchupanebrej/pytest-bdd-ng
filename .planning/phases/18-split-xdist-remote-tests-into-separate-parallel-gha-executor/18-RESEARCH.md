# Phase 18 Research: Split xdist-remote Tests Into Separate Parallel GHA Executor Job

## 1. Executive Summary

The objective of Phase 18 is to reduce the wall-clock execution time of the `pytest-bdd-ng` CI pipeline by isolating the six slow, resource-heavy, and Docker-backed `xdist-remote` tox environments from the main `test` job. Currently, these six environments execute sequentially inside the main job matrix, adding significant serialization overhead.

By splitting these tests into a dedicated, parallel GitHub Actions job (`test-xdist-remote`) and configuring the main `test` job to skip them:
- The main test suite cells (specifically Python 3.14 on Linux and Windows) will finish significantly faster.
- The six remote environments will run concurrently in 6 separate matrix cells.
- The project's Makefile command boundary established in Phase 17 is preserved.
- Default local execution behavior (e.g., running `make tox` or `tox` locally) remains completely unaffected, preserving full local matrix verification.

---

## 2. Detailed Analysis of the Six xdist-remote Environments

The six target tox environments are defined in `tox.ini` as:
- `py314-pytestlatest-xdist-remote-socket-lin`
- `py314-pytestlatest-xdist-remote-via-lin`
- `py314-pytestlatest-xdist-remote-ssh-lin`
- `py314-pytestlatest-xdist-remote-socket-win`
- `py314-pytestlatest-xdist-remote-via-win`
- `py314-pytestlatest-xdist-remote-ssh-win`

### Transport Modes Profile and Dependencies

| Mode | Local/Docker | Host Dependencies | Description |
|---|---|---|---|
| **socket** | Local | None | Runs remote processes locally. Uses `execnet.script.socketserver` on localhost ports `8888` and `8889`. Does not require Docker. |
| **via** | Local | None | Runs remote processes locally. Uses a proxy process and popen transport over localhost. Does not require Docker. |
| **ssh** | Docker Compose | Docker Daemon & Compose CLI | Spins up the Docker compose cluster under `tests/assets/docker/remote_xdist/docker-compose.yml`. Builds local images using the repository root as build context, starts containers acting as SSH hosts, and executes tests targeting container worker nodes. **Requires a running Docker host.** |

### Platform and OS Mapping
The environments use two platform factors:
- `lin`: Intended to run on `ubuntu-latest`.
- `win`: Intended to run on `windows-latest`.

---

## 3. Main Test Job Skip Mechanism & Makefile Command Boundary Preservation

To prevent the main `test` job from executing the six environments twice, it must skip them. However, per decision **D-02**, we must preserve the Makefile command boundary rather than bypassing it with raw `tox` calls.

### Proposed Makefile Modification
We introduce an optional parameter `TOX_ARGS` to the `Makefile` with a default empty value. This allows passing CLI arguments through the Makefile to `tox` without changing the default local behavior.

```diff
# Makefile:412-414
+TOX_ARGS ?=
 tox: env-check-tox
-	$(TOX)
+	$(TOX) $(TOX_ARGS)
```

### Main Job Skip Expression
In `.github/workflows/main.yml`, the main `test` job's step is updated to:
```yaml
      - name: Test with tox
        run: |
          make tox TOX_ARGS='--skip-env "xdist-remote-.*"'
```
- **Tox CLI match**: Tox 4.2+ supports `--skip-env <regex>`. The pattern `"xdist-remote-.*"` is highly specific. Since no other environments in `tox.ini` contain the `xdist-remote-` substring, this pattern skips exactly the six target environments.
- **Local Consistency**: Running `make tox` locally without `TOX_ARGS` continues to run the full matrix including the `xdist-remote` tests, preserving standard local testing.
- **Contract Compliance**: The contract test `tests/cases/contract/test_makefile_test_api.py` checks that `tox` is a target in the Makefile and that the `TOX` variable is conditionally declared. The proposed change preserves these characteristics exactly, ensuring contract tests pass.

---

## 4. Dedicated Parallel Executor Job Design (`test-xdist-remote`)

We introduce the `test-xdist-remote` job in `.github/workflows/main.yml`. It runs in parallel with the main `test` job.

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

### Rationale for Configuration
1. **Parallel Execution**: Since no `needs:` statement is specified, `test-xdist-remote` runs concurrently with `test`.
2. **Platform Mapping**: The GHA inline expression `platform="${{ matrix.os == 'ubuntu-latest' && 'lin' || 'win' }}"` maps the runner OS to the `tox` platform factor.
3. **Makefile Boundary**: Using `make tox TOX_ARGS="-e ..."` instead of direct `uvx` execution complies with D-02, routing execution through the Makefile's validation checks (e.g., `env-check-tox`).
4. **Environment Isolation**: No coverage upload or wheel building steps are included since coverage collection is handled by `py314-pytestlatest-gherkinlatest-xdist-coverage-lin` in the main job.

---

## 5. Docker Runner Setup and Verification

### GHA Provisioning
To satisfy D-09, Docker provisioning is decoupled from the test suite and declared directly in the workflow using `docker/setup-docker-action@v5` with version `29.1.5` pinned.

### Verification Step
A explicit `Verify Docker toolchain` step executes before tox:
```bash
docker --version
docker compose version
docker info --format 'server={{.Server.Version}} os={{.OSType}}' || docker info
```
If Docker or the Compose engine is unavailable, the step fails loudly immediately, avoiding long hangs during the main test execution.

### Hypervisor / Nested Virtualization Limitation on Windows Runners
> [!WARNING]
> **Windows GHA Virtualization Limitation**
> GitHub-hosted `windows-latest` runners are executed inside VMs that do not support nested virtualization.
> - While Docker Desktop is preinstalled and started on Windows GHA runners, it defaults to Windows Container mode.
> - Because nested virtualization is disabled, it is impossible to enable the WSL2 backend or run Linux containers on these runners.
> - Since the `ssh` mode (`py314-pytestlatest-xdist-remote-ssh-win`) relies on building and running Linux containers (`python:3.14-slim`), this specific matrix cell will fail to build the cluster on standard Windows GHA runners.
> - `socket` and `via` modes on Windows do not use Docker and will succeed.
> - To resolve this limitation in the future, self-hosted Windows agents with nested virtualization enabled or Windows-native SSH container worker configurations would be required.

---

## 6. Validation and Verification Strategy

### A. Local Pre-flight Checks
Before pushing to GitHub, developers should run:
1. **YAML Syntax Verification**: Validate the workflow file compiles correctly:
   ```bash
   uvx --with ruamel.yaml python -c "import yaml; yaml.safe_load(open('.github/workflows/main.yml'))"
   ```
2. **Target Matching Validation**: Verify that exactly six environments match the skip pattern and no other environments are skipped:
   ```bash
   uvx --with tox-uv tox -l | rg xdist-remote
   ```
3. **Local Action Simulation (Optional)**: If `act` is installed locally, validate the GHA setup:
   ```bash
   make validate-github-actions
   ```

### B. Post-Push GHA UI Checks
After pushing the implementation branch, verify the run in the GitHub Actions UI:
1. **Concurrency**: Confirm that the `test` and `test-xdist-remote` jobs run in parallel (no serialization line between them).
2. **Skip Verification**: Search the `test` job step logs (under `Test with tox`) for `xdist-remote-.*`. Verify that none of the six environments were run.
3. **Execution Verification**: Verify that the `test-xdist-remote` job executes exactly 6 matrix cells, and that the `Verify Docker toolchain` step successfully output version information for each OS.
