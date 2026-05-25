---
phase: 16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit
plan: "01"
subsystem: testing
tags: [pre-commit, vulture, dead-code, quality-gate]

requires:
  - phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
    provides: Stable test command surface and pre-commit workflow context
provides:
  - Native vulture pre-commit hook configuration
  - Root vulture whitelist using vulture's native format
  - Removal of pytest-based vulture wrapper tests and direct test/tox vulture dependency
affects: [quality-gates, pre-commit, audit-prune, SIM-03]

tech-stack:
  added: [jendrikseipp/vulture pre-commit hook]
  patterns: [native tool configuration, native whitelist]

key-files:
  created:
    - vulture_whitelist.py
    - .planning/phases/16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit/16-VERIFICATION.md
  modified:
    - .pre-commit-config.yaml
    - pyproject.toml
    - tox.ini
    - tests/cases/unit/unit/test_dead_code.py

key-decisions:
  - "Use native vulture configuration and whitelist instead of a custom pytest wrapper."
  - "Let pre-commit own the dead-code gate; unit tests no longer execute vulture."
  - "Keep stale whitelist behavior native to vulture rather than maintaining exact file/line assertions."

patterns-established:
  - "Dead-code audit tools run as pre-commit hooks, not pytest tests."
  - "Tool false positives use native allowlist files unless a wrapper becomes unavoidable."

requirements-completed: [SIM-03]

duration: 45min
completed: 2026-05-25
---

# Phase 16: Vulture Pre-commit Hook Summary

**Vulture dead-code checking now runs through native pre-commit configuration with a native whitelist.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-05-25T22:25:00+03:00
- **Completed:** 2026-05-25T23:11:11+03:00
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Added `jendrikseipp/vulture` `v2.16` as a native pre-commit hook.
- Added `[tool.vulture]` in `pyproject.toml` with `min_confidence = 80` and native paths.
- Added `vulture_whitelist.py` from current findings.
- Deleted the pytest wrapper test and removed direct `vulture` dependencies from test extras and tox deps.

## Task Commits

1. **Move vulture gate to native pre-commit** - `4e4ac1f0` (chore)

## Files Created/Modified

- `vulture_whitelist.py` - Native vulture whitelist for current false positives.
- `.pre-commit-config.yaml` - Adds native vulture hook.
- `pyproject.toml` - Adds `[tool.vulture]`; removes `vulture` from test extra.
- `tox.ini` - Removes direct vulture dependency from default tox env.
- `tests/cases/unit/unit/test_dead_code.py` - Removed pytest wrapper gate.

## Decisions Made

Followed phase context decisions D-01 through D-08. The only execution adjustment was adding file-level Ruff ignores in `vulture_whitelist.py` so the native whitelist remains compatible with the existing `ruff-check` pre-commit hook.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- `pretty-format-toml` reformatted `pyproject.toml`; rerun passed.
- Initial `ruff-check` on `vulture_whitelist.py` failed on native whitelist expressions; resolved with `# ruff: noqa: B018, D100, F821`.

## User Setup Required

None - pre-commit installs the vulture hook environment automatically.

## Next Phase Readiness

Phase 16 is complete. Future SIM-03 audit work can rely on `pre-commit run vulture --all-files` as the dead-code gate.

---
*Phase: 16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit*
*Completed: 2026-05-25*
