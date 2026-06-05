# Phase 18: Split xdist-remote tests into separate parallel GHA executor job - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Split the six long-running Docker-backed xdist-remote tox environments out of the existing GitHub Actions `test` job into a dedicated parallel `test-xdist-remote` job. The main `test` job must skip those six environments so they are not executed twice, while local `make tox` and full tox behavior remain unchanged unless a minimal Makefile forwarding change is needed to preserve the Phase 17 Makefile boundary.

This phase owns `.github/workflows/main.yml` changes for the new executor job, main-job skip behavior, Docker runner setup/verification for remote xdist, and local workflow validation. It does not own broader CI logging artifacts, tox environment restructuring, local tox speedups, Docker fixture rewrites, release workflow changes, larger/self-hosted runners, or Docker layer caching.

</domain>

<decisions>
## Implementation Decisions

### Folded Scope
- **D-01:** Fold the todo "Split xdist-remote tests into separate parallel GHA executor job" into Phase 18. Its approved design spec is the baseline scope and must guide planning.

### Main Test Job Boundary
- **D-02:** Preserve Phase 17's Makefile command boundary in GitHub Actions. The main `test` job should not bypass Makefile with a raw tox command if a Makefile-compatible solution is practical.
- **D-03:** The implementation may use `make tox -- --skip-env "xdist-remote-.*"` or add minimal Makefile support for forwarding tox arguments, provided the six xdist-remote environments are not run in the main `test` job and local full-matrix behavior remains intact.
- **D-04:** Do not change `tox.ini` env definitions or remove the xdist-remote environments from the default tox env list as part of this phase.

### Remote Executor Job
- **D-05:** Add a dedicated `test-xdist-remote` GitHub Actions job with exactly six matrix cells: `os` in `ubuntu-latest`, `windows-latest`; `mode` in `socket`, `via`, `ssh`.
- **D-06:** `test-xdist-remote` must run in parallel with `test`; do not add `needs: test`.
- **D-07:** Use `fail-fast: false` on the `test-xdist-remote` matrix, matching the existing `test` job behavior.
- **D-08:** Each new matrix cell must run the matching existing tox env: `py314-pytestlatest-xdist-remote-${mode}-${platform}`, where platform is `lin` for Ubuntu and `win` for Windows.

### Docker Runner Setup
- **D-09:** The xdist-remote tests must run on a GitHub Actions runner where Docker has already been provisioned through GitHub CI setup capabilities. Test code and pytest fixtures must not own Docker environment setup or image-loading orchestration beyond their existing compose-based test behavior.
- **D-10:** The workflow must verify Docker availability before running tox. Verification should fail visibly before the slow tox step if Docker or Docker Compose is unavailable.
- **D-11:** The planner should choose the GitHub Actions Docker setup mechanism that best satisfies D-09, such as an explicit setup action or runner setup step. The design must avoid moving setup responsibility into tests.

### Verification
- **D-12:** Local verification should use `act` when feasible, with `make validate-github-actions` as the preferred project command if `act` is installed.
- **D-13:** Local preflight must also prove the workflow YAML parses and exactly six tox envs match `xdist-remote`.
- **D-14:** Because local validation cannot fully prove GitHub-hosted runner parallelism, the plan should include a post-push GitHub Actions UI check that confirms six `test-xdist-remote` cells run parallel with `test` and no xdist-remote env runs twice.

### the agent's Discretion
- Exact Makefile argument-forwarding syntax, if needed to support `make tox -- --skip-env ...`.
- Exact GitHub Actions expression syntax for mapping `matrix.os` to `lin` or `win`.
- Exact Docker setup action/version or runner setup step, provided setup is done by CI before tests and Docker verification is explicit.
- Exact workflow step names, provided the job graph remains readable and the Phase 17 Makefile boundary is preserved.

### Folded Todos
- **Split xdist-remote tests into separate parallel GHA executor job** (`.planning/todos/pending/2026-06-02-split-xdist-remote-tests-into-separate-parallel-gha-executor.md`): This todo is Phase 18 scope. It supplies the approved design, env list, workflow job shape, verification expectations, and out-of-scope constraints.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition and Folded Todo
- `.planning/ROADMAP.md` - Phase 18 entry and dependency on Phase 17.
- `.planning/todos/pending/2026-06-02-split-xdist-remote-tests-into-separate-parallel-gha-executor.md` - Folded todo and implementation checklist.
- `docs/superpowers/specs/2026-06-02-xdist-remote-separate-gha-executor-design.md` - Approved design baseline; overridden only where this context records newer user decisions.

### Prior Phase Decisions
- `.planning/phases/17-adapt-github-ci-to-use-make-and-validate-with-act/17-CONTEXT.md` - Makefile command boundary for CI and visible GitHub Actions setup responsibilities.
- `.planning/phases/17-adapt-github-ci-to-use-make-and-validate-with-act/17-01-SUMMARY.md` - Implemented Makefile CI command API.
- `.planning/phases/17-adapt-github-ci-to-use-make-and-validate-with-act/17-02-SUMMARY.md` - Implemented GitHub workflow migration to Makefile targets.
- `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md` - Makefile as cross-platform command API and loud environment checks.

### Codebase Maps
- `.planning/codebase/STACK.md` - CI tooling, tox, uv, Docker, GitHub Actions, and npm formatter dependencies.
- `.planning/codebase/ARCHITECTURE.md` - Test and plugin architecture, including xdist/runtime integration.
- `.planning/codebase/INTEGRATIONS.md` - GitHub Actions workflow, Docker remote xdist fixtures, and CI service integrations.
- `.planning/codebase/TESTING.md` - Test group layout, tox usage, Docker/external tests, and verification patterns.

### Source and Configuration
- `.github/workflows/main.yml` - Primary implementation target for main job skip behavior and new remote executor job.
- `Makefile` - Existing CI command surface; may need minimal tox argument forwarding to preserve Phase 17 boundary.
- `tox.ini` - Existing xdist-remote tox env definitions; must remain unchanged unless planner finds a hard blocker and documents why.
- `tests/assets/docker/remote_xdist/docker-compose.yml` - Existing compose cluster used by remote xdist tests.
- `src/pytest_bdd/testing/docker.py` - Docker test support and daemon checks.
- `src/pytest_bdd/util/tests_group_ordering.py` - Intra-test grouping/barrier logic; expected unaffected by job split.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Makefile` already defines `tox`, `env-install-npm`, `check-message-schemas`, and `validate-github-actions` targets from Phase 17.
- `.github/workflows/main.yml` already uses setup actions for checkout, Python, Node.js, pandoc, uv, npm dependencies, tox, message schema checks, Codecov, and build checking.
- `tox.ini` already defines exactly six xdist-remote envs through `py314-pytestlatest-xdist-remote-{socket, via, ssh}-{lin, win}`.
- `tests/assets/docker/remote_xdist/` already contains the Docker compose cluster and controller/worker Dockerfiles used by the remote tests.

### Established Patterns
- GitHub Actions owns runner/toolchain setup; Makefile owns project command internals.
- Makefile targets should fail loudly with actionable errors when tools are unavailable.
- CI behavior can differ from local behavior through explicit workflow invocation or CI-only command arguments, but local `make tox` should remain the full default matrix.
- Docker-backed tests are external/slow and should surface environment failures before deep pytest execution when possible.

### Integration Points
- `.github/workflows/main.yml`: modify the existing `Test with tox` step so it skips xdist-remote envs through the Makefile boundary.
- `.github/workflows/main.yml`: add `test-xdist-remote` with six matrix cells, standard setup preamble, Docker setup/verification, npm install, and one tox env per cell.
- `Makefile`: only touch if necessary to forward tox arguments cleanly from `make tox -- ...`; do not broaden Phase 18 into general Makefile redesign.
- `tox.ini`: read to compute env names, but avoid modifying.

</code_context>

<specifics>
## Specific Ideas

- Main job skip should be equivalent to `--skip-env "xdist-remote-.*"` while preserving the Makefile boundary.
- New job should not include Codecov upload or build checking because it runs only xdist-remote envs, not coverage/build envs.
- Docker verification should include `docker --version`, `docker compose version`, and `docker info` or equivalent.
- `PYTEST_REMOTE_MODE` should be set from `matrix.mode` for the remote job.
- Local verification should prefer `make validate-github-actions`/`act` when available, plus tox env listing checks.

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- **Gather failed CI logs into workflow artifact** (`.planning/todos/pending/2026-06-02-gather-failed-ci-logs-into-workflow-artifact.md`) - adjacent CI workflow improvement, but it adds a separate artifact collection capability and should stay outside Phase 18.
- **Integrate BDD/ATDD tests into development workflow and UAT phase** - broad process change; not part of remote xdist job split.
- **No TestClasses are allowed in tests** - testing style enforcement; unrelated to GitHub Actions remote xdist scheduling.
- **Vulture must be run not via pytest but as pre-commit hook** - completed prior scope; unrelated to this phase.
- **Fix Makefile SHELL for cross-platform (Win/Mac/Linux)** - completed prior scope; only the Makefile command-boundary decision carries forward.

</deferred>

---

*Phase: 18-split-xdist-remote-tests-into-separate-parallel-gha-executor*
*Context gathered: 2026-06-02*
