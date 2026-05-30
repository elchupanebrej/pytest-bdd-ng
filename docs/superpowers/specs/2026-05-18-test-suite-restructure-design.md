# Test Suite Restructure Design

Date: 2026-05-18

## Goal

Restructure the test suite so its project tree explains test purpose, while Makefile targets provide one clear entrypoint for local, full, environment-specific, and slow test runs.

The design separates three concerns:

- semantic group: where the test lives
- speed: whether the test is slow
- environment: which host or external capability the test needs

Tests that depend on uncontrolled real machine state are defects. They must be made hermetic, Docker-backed, browser-backed, or explicitly platform-gated.

## Target Test Tree

Collected tests live only under `tests/cases/`:

```text
tests/
  cases/
    unit/
    integration/
    contract/
    e2e/
    compat/
    perf/
    external/
  assets/
    fixtures/
    templates/
    golden/
    docker/
    feature_docs/
```

`tests/assets/` contains passive test data, templates, golden files, Docker assets, and feature-document fixtures. It does not contain collected tests.

Reusable active helper code must not live under `tests/support`. It moves into a project-owned package:

```text
src/pytest_bdd/testing/
  docker.py
  docker_cluster.py
  cucumber_formatters.py
  temp_paths.py
```

Fixture code that is local to one test group may remain in that group’s `conftest.py`.

## Semantic Groups

The canonical semantic groups are:

- `unit`: pure in-process module tests
- `integration`: local plugin, parser, runtime, pytester, and subprocess-light flows
- `contract`: golden files, boundary contracts, schema contracts, and formatter parity contracts
- `e2e`: full executable user workflows and feature-doc driven acceptance tests
- `compat`: Python, pytest, dependency, and platform compatibility checks
- `perf`: benchmarks and intentionally expensive performance probes
- `external`: Docker, browser, and host-platform harnesses or acceptance wrappers

Migration mapping:

- existing `tests/unit`, `tests/model`, and `tests/args` mostly move to `tests/cases/unit`
- existing `tests/feature`, `tests/hook`, `tests/library`, `tests/gherkin_integration`, and `tests/struct_bdd` mostly move to `tests/cases/integration`, except full workflow cases that move to `tests/cases/e2e`
- existing `tests/messages`, `tests/messages_coverage`, and formatter golden tests split between `tests/cases/contract` and `tests/cases/integration`
- existing `tests/doc`, `tests/generation`, and `tests/scripts` move to `tests/cases/integration` or `tests/cases/contract` based on whether they verify behavior or generated contract artifacts
- Docker-backed xdist remote work moves under `tests/cases/external/docker_xdist`
- long benchmark-style tests move to `tests/cases/perf`

E2E collection must be split per file, not by collecting a full directory through one scenario loader. Each E2E test module should bind only the feature file or files it owns, so failures, selection, and ownership stay file-local.

## Selection Model

Pytest keeps path-based semantic group resolution through `test_group_paths`:

```text
tests/cases/unit/** = unit
tests/cases/integration/** = integration
tests/cases/contract/** = contract
tests/cases/e2e/** = e2e
tests/cases/compat/** = compat
tests/cases/perf/** = perf
tests/cases/external/** = external
```

Semantic markers:

- `unit`
- `integration`
- `contract`
- `e2e`
- `compat`
- `perf`
- `external`

Speed marker:

- `slow`

Environment markers:

- `docker`
- `windows`
- `posix`
- `browser`

`windows` includes Windows host behavior and WSL2 bridge behavior where the test requires that bridge. There is no separate `wsl2` marker.

## Makefile API

Make is the human entrypoint. Tox remains the matrix engine.

Required test targets:

- `make test`: run the full feasible suite for the current machine without surprise provisioning
- `make test-all`: run every feasible local, Docker, and platform bridge target, then render reports
- `make test-unit`
- `make test-integration`
- `make test-contract`
- `make test-e2e`
- `make test-compat`
- `make test-perf`
- `make test-external`
- `make test-slow`
- `make test-docker`
- `make test-windows`
- `make test-posix`

Default test targets depend on validation checks only. They do not install prerequisites.

## Environment Behavior

Platform rules:

- `windows` tests run against native Windows behavior. On non-Windows hosts, they run through an explicit Docker or bridge target only when that harness exists.
- `posix` tests run natively on Linux, macOS, or WSL. On Windows hosts, they run through WSL2 or Docker where possible.
- `docker` tests require Docker and Docker Compose.
- `browser` tests require Playwright browser assets and run only through browser-specific targets.

Default behavior:

- `make test` excludes unavailable environment-specific tests by selector.
- explicit environment targets fail early with actionable setup errors.
- unsupported cross-platform bridge targets fail during environment validation before pytest starts.

## Environment Validation and Provisioning

Validation is read-only:

- `make env-check`
- `make env-check-docker`
- `make env-check-windows`
- `make env-check-browser`

Validation checks Docker daemon, Docker Compose, WSL2 Windows bridge capability, required Docker images, Playwright browser install, Python versions, and Node where needed. It reports missing prerequisites and exits nonzero. It does not install or mutate.

Provisioning is explicit:

- `make env-install`
- `make env-install-docker`
- `make env-install-windows`
- `make env-install-browser`

Provisioning may install or prepare supported prerequisites such as Playwright browsers, Docker images, WSL2 helper distro or image setup, Python 3.14 through `uv python install`, and Node package tools where the project owns the setup path.

Test targets depend on `env-check-*`, not `env-install-*`.

## Migration Safety

Validation for the restructure:

- add classification tests proving every file under `tests/cases/**` resolves to exactly one semantic group
- add Makefile smoke tests for target presence and command shape
- move tests mechanically first, then update imports, pytest config, Makefile, and tox
- preserve behavior by running representative old commands and new Make targets against equivalent slices

No marker hygiene test suite is required by this design.

## Development Guide

`DEVELOPMENT.rst` must gain a section that explains how to use the new test configuration. It should cover:

- semantic test groups and their directories
- speed and environment facets
- Makefile targets for normal, full, slow, Docker, Windows, POSIX, and browser runs
- environment validation versus explicit provisioning
- how to add a new test in the correct directory with the correct markers
- the E2E rule that scenario collection is per file, not through a whole feature directory

## Out of Scope

- changing product behavior
- changing SpecKit constitution or existing completed specs
- keeping `tests/support`
- adding `realenv`
- adding a separate `wsl2` marker
