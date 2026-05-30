# Phase 3: Core Runtime Refactor - Discussion Log

**Date:** 2026-05-12
**Phase:** 03-core-runtime-refactor
**Mode:** discuss (interactive)

## Areas Discussed

### 1. Module Boundary Placement
**Options presented:** Lock specific class→module mapping vs let planner optimize
**User decision:** Let planner optimize
**Notes:** User trusts the planner to determine optimal grouping based on dependency analysis. ROADMAP module names are the target but class placement is flexible.

### 2. Import Migration Strategy
**Options presented:** Re-export compat layer vs update all importers directly vs hybrid with deprecation
**User decision:** Update all 18 importers to new paths directly
**Notes:** No backward compat re-exports. Clean break.

### 3. Characterization Test Scope
**Options presented:**
- A: Existing tests are the gate (faster, less work)
- B: Write explicit characterization tests before split (safer, more work)
**User decision:** Option B — explicit characterization tests
**Notes:** User requested deeper explanation of RunStage state machine before deciding. After understanding the lifecycle (idle→setup→running⇄step→teardown→finished) and the 6 existing hook/model tests, user chose the safer approach. Tests must snapshot `ActiveObjectSet` states, `as_dict()` outputs, and transition chains.

### 4. Circular Import Resolution
**Options presented:** TYPE_CHECKING imports vs restructure references
**User decision:** Restructure references
**Notes:** Do not use TYPE_CHECKING as a workaround. Properly restructure the Run↔FeatureRuntimeBinding↔ScenarioRun dependency triangle.

## Deferred Ideas

None.

## The Agent's Discretion Items

- Helper function placement
- Type alias placement
- Characterization test file organization
- Order of operations within the split

---
Discussion completed: 2026-05-12
