# Phase 15: Validation Architecture

**Created:** 2026-05-23
**Scope:** Makefile cross-platform entrypoint and DEVELOPMENT.rst documentation
**Source of truth:** `ROADMAP.md` Phase 15 success criteria + `15-CONTEXT.md` locked decisions. `15-SPEC.md` tox-backed expansion is deferred unless promoted to a later phase.

## Validation Goals

- Prove Makefile OS detection and Git Bash guard are present.
- Prove `test-docker` remains a compatibility/meta target and split Docker targets exist.
- Prove `test-external` runs only through non-fatal Docker/external routing in `test-all`.
- Prove current-host dry-runs resolve without Makefile syntax errors.
- Prove DEVELOPMENT.rst documents concise cross-platform prerequisites and canonical Make commands.

## Requirement Map

| ID | Source | Behavior | Validation |
|----|--------|----------|------------|
| P15-01 | ROADMAP #1-3, D-01 | `UNAME_S` detection, unsupported PowerShell/cmd guard, Windows shell/path behavior | Static grep + PowerShell guard smoke |
| P15-02 | ROADMAP #4, D-02 | `test-docker` compatibility/meta target plus `test-docker-linux` and `test-docker-windows` split targets | Static grep + dry-run |
| P15-03 | ROADMAP #5, Phase 12 D-10 | `test-all` routes native targets fatally, Docker/external/report targets non-fatally | Static grep + `rtk make -n test-all` |
| P15-04 | ROADMAP #6 | `test-windows` and `test-posix` preserve pytest exit code 5 handling | Static grep |
| P15-05 | ROADMAP #7, D-04 | DEVELOPMENT.rst has Cross-Platform Setup prerequisite table | Static grep + pre-commit |
| P15-06 | ROADMAP #8 | Existing Makefile targets continue to resolve | Dry-runs + feasible smoke tests |

## Automated Commands

Run from repository root.

```powershell
rtk rg -c "UNAME_S :=.*uname -s" Makefile
rtk rg -c "^test-docker:" Makefile
rtk rg -c "^test-docker-linux:" Makefile
rtk rg -c "^test-docker-windows:" Makefile
rtk rg -c "DOCKER_TARGETS.*test-external|test-external.*DOCKER_TARGETS" Makefile
rtk make -n test-all
rtk make -n test-docker
rtk make -n test-docker-linux
rtk make -n test-docker-windows
rtk rg -c "Cross-Platform Setup" DEVELOPMENT.rst
rtk uv run pre-commit run --files Makefile DEVELOPMENT.rst
```

## Expected Results

- `UNAME_S` grep returns at least 1.
- `test-docker`, `test-docker-linux`, and `test-docker-windows` target greps each return 1.
- `rtk make -n test-all` shows native route first and non-fatal Docker/external/report route with ignored-error prefix.
- `test-external` is not listed in fatal native target routing.
- DEVELOPMENT.rst contains Cross-Platform Setup and canonical Make command documentation.
- Pre-commit exits 0 or reports only pre-existing unrelated hook environment issues; file content issues must be fixed.

## Manual Check

On Windows, run `rtk make test-all` from Git Bash. If run from PowerShell/cmd, Makefile must fail early with: `ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.`
