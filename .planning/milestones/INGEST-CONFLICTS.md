## Conflict Detection Report

### BLOCKERS (0)

No blockers found. All ADRs (001-011) align with existing locked decisions in PROJECT.md and CONTEXT.md files. All
feature specs align with existing requirements in REQUIREMENTS.md.

### WARNINGS (4)

[WARNING] Phase 27 validation currently accepts fake-tool BDD scenarios
  Found: `.planning/phases/27-replace-make-sh-with-act/27-VALIDATION.md` says `07 Messages Coverage Audit.feature.md` and `08 Docs Build Script.feature.md` execute scripts with fake external dependencies where needed.
  Impact: This conflicts with the ingested context that Phase 27 BDD/e2e scenarios must use real `act` jobs and no mock tools for Act acceptance coverage.
  → Update Phase 27 validation and implementation plan so `07` and `08` acquire artifacts from real Act jobs before marking validation complete.
  Resolution: Approved by user and applied to destination planning files on 2026-06-23; Phase 27 BDD validation is reopened.

[WARNING] Phase 27 Act BDD currently records exit/dry-run success as sufficient
  Found: Phase 27 validation records real `act --list` and `act -n` BDD success, but the ingested context says successful completion alone is insufficient.
  Impact: BDD executable documentation may pass while failing to prove artifact-producing Make replacement behavior.
  → Add an agreed artifact matrix and require host-side assertions over Act-produced artifacts for each relevant job.
  Resolution: Approved by user and applied to destination planning files on 2026-06-23; artifact matrix added to Phase 27 validation.

[WARNING] Design spec proposes renaming pytest_bdd_testing to pytest_bdd_toolchain
Found: `docs/superpowers/specs/2026-06-24-rename-pytest-bdd-testing-to-toolchain.md` proposes renaming the package and
moving scripts into it.
Impact: Conflicts with Phase 20 decisions (20-26, 20-27) that established `pytest_bdd_testing` as the independent test
package name. Would require updating ROADMAP.md, REQUIREMENTS.md (R1-R9), and all references in .planning/ files.
→ Resolve by either: (a) updating the design spec to preserve `pytest_bdd_testing` name, or (b) creating a new phase to
implement the rename with full impact analysis.

[WARNING] Design spec proposes moving scripts/ into the package
Found: The same design spec proposes moving all 11 scripts from `scripts/` into `src/pytest_bdd_toolchain/tool/`.
Impact: Phase 27 (Make→act migration) preserved or replaced scripts with Python equivalents. Moving scripts into the
package would change the distribution model and may conflict with Phase 27's D-05, D-06 decisions about script
locations.
→ Resolve by verifying Phase 27 script decisions and updating the design spec to align with established script
locations.

### INFO (4)

[INFO] ADR-001 (attrs over dataclass) aligns with PROJECT.md
Found: ADR-001 documents the decision to use `attrs` over `dataclass`.
Note: PROJECT.md already mandates "Must use `attrs` over `dataclass`" in Constraints section. No conflict.

[INFO] ADR-005 (Go parser) aligns with spec 023 and Phase 20
Found: ADR-005 documents Go parser as optional extra with Python fallback.
Note: Spec 023 and Phase 20 (A3) already locked this decision. No conflict.

[INFO] ADR-007 (no return None) aligns with PROJECT.md
Found: ADR-007 documents zero return None policy via BLQ901.
Note: PROJECT.md already mandates this in Constraints section. No conflict.

[INFO] No locked-decision conflict detected for incoming ADRs
Found: The incoming ADRs (001-011) are classified as ADR and no ADR-locked decision in the existing planning files
contradicts them.
  Note: Merge proceeded after explicit approval of the warnings and destination-file update plan.

### INGESTION COMPLETE

**Documents ingested:**

- 11 ADRs (001-011) → PROJECT.md Key Decisions table
- 24 feature specs → REQUIREMENTS.md Spec Requirements table
- 1 design spec (rename pytest_bdd_testing) → Pending resolution of warnings

**Updated planning files:**

- `.planning/PROJECT.md` — Added ADR references
- `.planning/REQUIREMENTS.md` — Added spec requirements
- `.planning/ROADMAP.md` — Added Phase 28 for feature specs implementation
- `.planning/INGEST-CONFLICTS.md` — Updated with current conflict detection
