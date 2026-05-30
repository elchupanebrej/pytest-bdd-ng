# Phase 15: Cross-platform test suite entrypoint (Makefile + MinGW sh) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-21
**Phase:** 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
**Areas discussed:** Unsupported shell behavior, Docker target discovery, env-check depth, Documentation style

---

## Unsupported Shell Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Fail early with clear message | Guard at top of Makefile detects missing bash/sh and prints actionable error | ✓ |
| Attempt auto-invoke Git Bash | Makefile tries to shell out to Git Bash automatically | |
| You decide | Let the agent pick | |

**User's choice:** Fail early with clear message
**Notes:** Spike findings already prove the detection approach works with `uname -s`. The guard should print "ERROR: make requires Git Bash on Windows. Run from Git Bash terminal." and exit.

---

## Docker Target Discovery

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-attempt with - prefix (current) | Docker targets run if Docker available, silently skipped if not | ✓ |
| Separate opt-in target | Remove Docker from test-all, add explicit test-all-docker | |
| You decide | Let the agent decide | |

**User's choice:** Auto-attempt with - prefix (keep current behavior)
**Notes:** Matches Phase 12 D-10 (test-all should not fail on unavailable environments). Split `test-docker` into `test-docker-linux` and `test-docker-windows` per spike findings for platform routing.

---

## env-check Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Silent pass, loud fail (keep current) | @ prefix on success, clear ERROR on failure | ✓ |
| Verbose status report | Print what's available vs missing on every check | |
| You decide | Let the agent pick | |

**User's choice:** Silent pass, loud fail (keep current convention)
**Notes:** Matches Phase 12 D-08 read-only policy. No noise on repeated runs.

---

## Documentation Style

| Option | Description | Selected |
|--------|-------------|----------|
| Concise prerequisite table + common commands | Table of OS, tools, verify command, links to install pages | ✓ |
| Full step-by-step per platform | Detailed walkthroughs for each OS | |
| You decide | Let the agent decide | |

**User's choice:** Concise prerequisite table + common commands
**Notes:** Keeps DEVELOPMENT.rst maintainable. Avoids duplicating upstream install guides that change over time.

---

## the agent's Discretion

- Exact Makefile guard syntax and error message wording
- Docker target names and per-platform routing table structure
- env-check target internals
- DEVELOPMENT.rst section structure and prerequisite table format
- Whether to add a `test-docker` meta-target
- Exact `uname` filter patterns for MinGW/MSYS/Cygwin variants

## Deferred Ideas

- **"Integrate BDD/ATDD tests into development workflow and UAT phase"** — Workflow/process change, not a Makefile change
- **"No TestClasses are allowed in tests"** — Ruff rule enforcement, not Makefile-related
