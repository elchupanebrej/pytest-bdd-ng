---
created: 2026-06-02T19:42:51.125Z
title: Split xdist-remote tests into separate parallel GHA executor job
area: tooling
files:
  - .github/workflows/main.yml
  - docs/superpowers/specs/2026-06-02-xdist-remote-separate-gha-executor-design.md
  - tox.ini
  - Makefile:47-49
  - tests/assets/docker/remote_xdist/docker-compose.yml
  - src/pytest_bdd/testing/docker.py
  - src/pytest_bdd/util/tests_group_ordering.py
---

## Problem

Six long-running xdist-remote tox environments
(`py314-pytestlatest-xdist-remote-{socket,via,ssh}-{lin,win}`) currently
execute serially inside the existing `test` job on the
`python-version=3.14, os={ubuntu-latest, windows-latest}` matrix cells.
Each spins up a Docker compose cluster
(`tests/assets/docker/remote_xdist/`) and a pytest-xdist remote gateway
(socket / via / ssh), making them the slowest envs in the matrix and the
dominant contributor to CI wall-clock time on the 3.14 cells.

## Solution

Implement the design in
`docs/superpowers/specs/2026-06-02-xdist-remote-separate-gha-executor-design.md`.
Touches only `.github/workflows/main.yml`; `tox.ini`, `Makefile`,
`pyproject.toml`, and the test suite stay unchanged so
`make tox` / `uvx --with tox-uv tox` still run the full matrix locally.

Tasks:

- [ ] In the existing `test` job, replace `make tox` with
  `uvx --with tox-uv tox --skip-env "xdist-remote-.*"` so the six envs are
  not run twice.
- [ ] Add a new `test-xdist-remote` job with a six-cell matrix
  (`os ∈ {ubuntu-latest, windows-latest}` × `mode ∈ {socket, via, ssh}`),
  running in parallel with `test` (no `needs:` dependency).
- [ ] Provision Docker on the new job via `docker/setup-docker-action@v5`
  with pinned `version: 29.1.5`; add a `Verify Docker toolchain` step
  (`docker --version`, `docker compose version`, `docker info`).
- [ ] Wire standard preamble steps on the new job: `actions/checkout@v4`
  (with `submodules: 'recursive'`), `actions/setup-python@v5` for 3.14,
  `actions/setup-node@v4`, `r-lib/actions/setup-pandoc@v2`,
  `astral-sh/setup-uv@v6`, `make env-install-npm`.
- [ ] Invoke each env as
  `uvx --with tox-uv tox -e "py314-pytestlatest-xdist-remote-${mode}-${platform}"`
  with `PYTEST_REMOTE_MODE: ${{ matrix.mode }}` and
  `platform = matrix.os == 'ubuntu-latest' ? 'lin' : 'win'`.
- [ ] Use `fail-fast: false` on the new job's matrix (matches the existing
  `test` job).
- [ ] Pre-flight verification before pushing:
  `uvx --with tox-uv tox -l | rg xdist-remote` returns exactly 6 lines, and
  the workflow YAML parses (`yaml.safe_load` or `make validate-github-actions`).
- [ ] Verify in the Actions UI: 6 `test-xdist-remote` jobs run in parallel
  with `test` (not after), and no env is executed twice.

Deliberately out of scope (per spec): local `make tox` speedup, larger /
self-hosted runners, Docker layer caching via `docker/build-push-action`,
macOS in the matrix, changes to `release.yaml`.

Related todo: `2026-05-27-adapt-github-ci-to-use-make.md` also modifies
`.github/workflows/main.yml` and the `make tox` invocation. Resolve the
conflict when sequencing the two — if the make-based CI cleanup lands
first, the test-job change in this todo becomes
`make tox -- --skip-env "xdist-remote-.*"` (or an equivalent Make target
override).
