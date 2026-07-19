# Phase 33: Gather Failed CI Logs into Workflow Artifact - Pattern Map

**Mapped:** 2026-07-10
**Files analyzed:** 1
**Analogs found:** 1 / 1

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.github/workflows/main.yml` — new `collect-failed-logs` job | config (GHA job) | event-driven (triggered by `if: failure()` + `needs`, queries REST API, downloads logs, uploads artifact) | `.github/workflows/main.yml` lines 87-124 (`test-xdist-remote` job) — same file, job block structure; `.github/workflows/messages-baseline-drift.yml` lines 83-88 — `upload-artifact@v4` step | same-file / exact |

## Pattern Assignments

### `.github/workflows/main.yml` — New `collect-failed-logs` job (config, event-driven)

The new job is added after the existing `test-xdist-remote` job definition (after line 124). Two existing files supply the patterns.

---

#### A. Job Block Structure

**Analog:** `.github/workflows/main.yml`, lines 87-124 (`test-xdist-remote` job)

**Job declaration pattern** (lines 87-98):
```yaml
  test-xdist-remote:
    runs-on: ubuntu-latest
    defaults:
      run:
        shell: bash
    strategy:
      fail-fast: false
      matrix:
        mode:
          - socket
          - via
          - ssh
    steps:
```

**Key conventions observed:**
- Two-space indentation for job key; four-space for properties inside the job
- `runs-on:` on the line immediately after the job name (no blank line)
- `steps:` precedes the list of steps
- Steps use `- name:` for human-readable labels, `uses:` for actions, `run:` for inline shell
- Action versions are always pinned with `@v<N>` (e.g., `actions/checkout@v5`, `actions/github-script@v7`, `actions/upload-artifact@v4`)

**Step naming convention** (from `test` job, lines 48-85):
```yaml
    steps:
      - uses: actions/checkout@v5
        with:
          submodules: 'recursive'
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
```
- Steps that use `uses:` can optionally also have a `name:` — both patterns appear
- `with:` block follows `uses:` for action inputs, indented deeper
- `if:` conditions (when used on steps) appear on the same line as `uses:` or `name:`

**New features needed (not present in any existing workflow):**
- `if: failure()` — no existing usage in this codebase. This is a standard GHA function that evaluates true when any job in `needs` has failed.
- `needs:` — no existing usage in this codebase. Standard GHA syntax for job dependency ordering.
- `permissions:` — no explicit per-job permissions block in any existing workflow. The design spec `permissions: { actions: read, contents: read }` follows least-privilege GHA conventions.

**Placement pattern:** The new job is added after the last job (`test-xdist-remote`) in `main.yml`, i.e., after line 124. Blank line before the new job declaration for readability.

---

#### B. `upload-artifact@v4` Step Pattern

**Analog:** `.github/workflows/messages-baseline-drift.yml`, lines 83-88

```yaml
      - name: Upload baseline diff artifact
        uses: actions/upload-artifact@v4
        with:
          name: messages-baseline-diff
          path: |
            specs/008-maximize-messages-coverage/contracts/baseline-diff.json
```

**Conventions to apply:**
- `uses: actions/upload-artifact@v4` — exact string, version-pinned
- `with:` block indented two spaces past `uses:`
- `name:` is a human-readable step label (kebab-case or natural language)
- `path:` can be a single line string or multiline `|` block

**New inputs needed (present in design spec, not in the analog):**
- `if-no-files-found: ignore` — prevents upload step failure when no log files were written (guard for D-08). Syntax: add under `with:` at same indentation as `name:` and `path:`.
- `if:` condition on the step for `hashFiles(...) != ''` — guards the upload from running when directory is empty. Syntax: `if: hashFiles('failed-job-logs/*.log') != ''` on the same line as `- name:` or `uses:`, same pattern as existing `if:` conditions in `test` job (line 70, 76, 80).

---

#### C. `actions/github-script@v7` Inline Script Pattern

**Analog:** None in this codebase (no existing `github-script` usage). However, `messages-baseline-drift.yml` lines 62-81 contain an inline Python script via `run: python - <<'PY'` that demonstrates the project's convention for multi-line inline scripts:

```yaml
      - name: Fail on capability deltas
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          ...
          PY
```

**Convention:** Multi-line inline scripts use heredoc-style delimiters (`<<'PY'`, `<<'EOF'`), consistent indentation, and a blank line before the closing delimiter.

**For `github-script` inline JS (new pattern):**
The `script:` input passes the code via the `with:` block:
```yaml
      - name: Download logs for failed matrix jobs
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('node:fs');
            const path = require('node:path');
            ...
```

---

## Shared Patterns

### YAML / Yamllint Conventions

**Source:** All workflow files in `.github/workflows/`

**Top-level `on:` comment** (line 8 of `main.yml`, line 7 of `messages-baseline-drift.yml`, line 7 of `release.yaml`):
```yaml
on:  # yamllint disable-line rule:truthy
```
Every workflow file in the project uses this disable comment. The new `collect-failed-logs` job is added to `main.yml` which already has this comment — no change needed.

**YAML document header:**
```yaml
---
# CI workflow: GitHub Actions runs the full compatibility and
# remote-test matrix on push/PR...
name: Main testing workflow
```
Triple-dash document start, followed by a comment block, then the workflow `name:`. The existing header comments do not need updating for this phase.

**No `.yamllint` config exists in the project root** — yamllint rules are observed via inline pragmas only.

### Error Handling Patterns

**Source:** Design spec at `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` § Error handling (lines 86-96)

No existing analog in the codebase — this is a new kind of error handling for the project:
- Per-job try/catch in the github-script body: individual `downloadJobLogsForWorkflowRun` failures are logged via `core.warning()` and the loop continues (D-07)
- Top-level `listJobsForWorkflowRun` failure is not caught — fails the step, which is acceptable
- Upload step guards: `if: hashFiles(...) != ''` on the step + `if-no-files-found: ignore` on the action (D-08)

### Permissions Pattern

**Analog:** None in existing workflows (all use GitHub Actions defaults). The design spec mandates:
```yaml
    permissions:
      actions: read
      contents: read
```
This is a standard GHA `permissions:` block at the job level. Indented four spaces under the job key.

## No Analog Found

The following patterns have no close match in the existing codebase. The planner should use the design spec (`docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md`) as the authoritative reference:

| Pattern | Reason |
|---------|--------|
| `if: failure()` job condition | No existing workflow uses failure-triggered downstream jobs |
| `needs: [test, test-xdist-remote]` | No existing workflow uses `needs` for job dependencies |
| `permissions:` per-job block | No existing workflow explicitly sets per-job permissions |
| `actions/github-script@v7` usage | No existing workflow uses github-script for API calls |
| `hashFiles(...)` in step condition | No existing workflow uses hashFiles as a guard |
| `if-no-files-found: ignore` on upload-artifact | Not used in the single existing upload-artifact call |

## Metadata

**Analog search scope:** `.github/workflows/` (all 8 files scanned)
**Design spec:** `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` (authoritative)
**Pattern extraction date:** 2026-07-10
