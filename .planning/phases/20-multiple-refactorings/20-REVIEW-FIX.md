---
phase: 20-multiple-refactorings
fixed_at: 2026-06-10T00:00:00Z
review_path: .planning/phases/20-multiple-refactorings/20-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

**Fixed at:** 2026-06-10
**Source review:** .planning/phases/20-multiple-refactorings/20-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (5 Critical, 5 Warning)
- Fixed: 10
- Skipped: 0

## Fixed Issues

### CR-01: Docker compose build context resolves to wrong directory

**Files modified:** `src/pytest_bdd/testing/assets/docker/remote_xdist/docker-compose.yml`
**Commit:** `d3dda262`
**Applied fix:** Updated `context:` from `../../../..` (4 levels → `src/pytest_bdd/`) to `../../../../..` (5 levels → repo root). Updated all `dockerfile:` paths from `tests/assets/docker/remote_xdist/*.Dockerfile` to `src/pytest_bdd/testing/assets/docker/remote_xdist/*.Dockerfile`. Used `>-` YAML block scalar for paths exceeding 80-char line limit to pass yamllint.

### CR-02: Dockerfiles at new location reference `tests/` paths that don't exist in build context

**Files modified:** None (resolved by CR-01)
**Commit:** N/A — implicitly resolved
**Applied fix:** With the build context fixed to repo root (CR-01), the Dockerfile COPY commands referencing `tests/` paths now work correctly because `tests/` exists at the repo root.

### CR-03: `[testing]` extra is empty — installs zero dependencies

**Files modified:** `pyproject.toml`
**Commit:** `435ea81e`
**Applied fix:** Removed the empty `testing = []` extra. It was dead configuration not referenced by any Makefile target or Dockerfile.

### CR-04: Makefile references old `tests/assets/docker/` path

**Files modified:** `Makefile`
**Commit:** `4a01781d`
**Applied fix:** Updated `test-external-docker-build` target from `tests/assets/docker/remote_xdist/docker-compose.yml` to `src/pytest_bdd/testing/assets/docker/remote_xdist/docker-compose.yml`.

### CR-05: Duplicate Docker asset directories exist — old and new locations diverge

**Files modified:** `src/pytest_bdd/testing/assets/docker/remote_xdist/controller.Dockerfile`, `src/pytest_bdd/testing/assets/docker/remote_xdist/worker.Dockerfile`
**Deleted:** `tests/assets/docker/remote_xdist/` (13 files)
**Commit:** `8c0bec95`
**Applied fix:** Updated Dockerfiles at the new location to use self-sufficient in-container paths (`src/pytest_bdd/testing/...` instead of `tests/...`). Updated ENTRYPOINT and SSH key copy paths. Removed the entire stale `tests/assets/docker/remote_xdist/` directory.

### WR-01: `docker_cluster.py` exec command references old `tests/` path inside container

**Files modified:** `src/pytest_bdd/testing/docker_cluster.py`
**Commit:** `b3881123`
**Applied fix:** Updated `docker compose exec` command from `tests/assets/docker/remote_xdist/controller_entrypoint.py` to `src/pytest_bdd/testing/assets/docker/remote_xdist/controller_entrypoint.py`.

### WR-02: `controller_entrypoint.py` references `tests.assets.docker...` Python module paths

**Files modified:** `src/pytest_bdd/testing/assets/docker/remote_xdist/controller_entrypoint.py`
**Commit:** `bcd8188c`
**Applied fix:** Updated `_build_pytest_cmd` and `_build_verify_cmd` to use `pytest_bdd.testing.assets.docker.remote_xdist.*` module paths instead of `tests.assets.docker.remote_xdist.*`.

### WR-03: Makefile `custom-rules` target may now analyze testing code unintentionally

**Files modified:** `src/pytest_bdd/_ruff/rules/init_rules.py`, `src/pytest_bdd/_ruff/rules/layer_rules.py`, `src/pytest_bdd/_ruff/rules/typing_rules.py`, `src/pytest_bdd/_ruff/rules/quality_gates.py`
**Commit:** `3e46a575`
**Applied fix:** Added `if "testing" in py_file.parts: continue` skip logic to 4 custom rule scanners, consistent with the existing pattern in `file_size_rules.py`.

### WR-04: `conftest.py` stale copy at old location invites confusion

**Files modified:** `tests/cases/e2e/conftest.py` (deleted)
**Commit:** `5bb0f899`
**Applied fix:** Removed the stale `tests/cases/e2e/conftest.py`. The active conftest is at `src/pytest_bdd/testing/cases/e2e/conftest.py` (configured via `testpaths = ["src/pytest_bdd/testing/cases"]` in pyproject.toml).

### WR-05: `parsers/__init__.py` and `scenario_locator/__init__.py` use wildcard re-exports

**Files modified:** `src/pytest_bdd/parsers/__init__.py`, `src/pytest_bdd/scenario_locator/__init__.py`
**Commit:** `8a19b5ad`
**Applied fix:** Replaced wildcard imports (`from x.facade import *`) with explicit named imports matching the `__all__` lists.

---

_Fixed: 2026-06-10T00:00:00Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
