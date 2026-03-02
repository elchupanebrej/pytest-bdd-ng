# Feature Specification: Maximize Messages Capability Coverage

**Feature Branch**: `[008-maximize-messages-coverage]`
**Created**: 2026-03-01
**Status**: Draft
**Input**: User description: "Ensure `pytest-bdd-ng` uses `messages` library capabilities as fully as possible, with no blind spots."

## Clarifications

### Session 2026-03-02

- Q: Which controlled status vocabulary and release-blocker policy should be canonical? → A: `Implemented`, `Pending`, `Non-Implementable`, `Not-Applicable`, `Not-Acceptable`; release blockers are `Pending` and `Not-Acceptable`.
- Q: Which out-of-scope boundary should apply for this release? → A: Capabilities outside the mandatory list may remain out of scope and must be explicitly governed if not implemented.
- Q: What deterministic mapping target should the readiness matrix enforce? → A: 100% of observed outcomes in the fixed readiness matrix must map deterministically to capability entries.
- Q: What recency rule should apply to `reviewed_at` for release readiness? → A: `reviewed_at` must be within the current release cycle; otherwise the capability is treated as `Pending` until re-reviewed.
- Q: How should conflicting decisions for the same `capability_id` in one release cycle be handled? → A: They are forbidden and treated as validation errors and release blockers.
- Q: Which capability fields are mandatory for hook-based reporting population in this release? → A: The full list provided by stakeholders is in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt`, and every listed capability is in scope for implementation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete capability inventory (Priority: P1)

As a maintainer, I need a complete catalog of relevant `messages` capabilities so I can see exactly what is supported, deferred, or intentionally excluded.

**Why this priority**: A trustworthy inventory is the foundation for all later coverage and release decisions.

**Independent Test**: Review the catalog and confirm each relevant capability appears exactly once with a status and, when not implemented, a documented reason and owner.

**Acceptance Scenarios**:

1. **Given** an approved upstream baseline, **When** the maintainer generates the catalog, **Then** every relevant capability is listed exactly once.
2. **Given** a capability that is not implemented, **When** a reviewer inspects the catalog, **Then** the entry includes status, rationale, decision owner, review date, and evidence reference.

---

### User Story 2 - Make coverage gaps visible (Priority: P2)

As a report consumer, I need runtime outcomes to map to cataloged capabilities so missing coverage is visible and cannot be silently ignored.

**Why this priority**: Coverage only improves when gaps are surfaced clearly and consistently.

**Independent Test**: Run a fixed readiness matrix (pass, fail, skipped, undefined, interrupted, retry, and parallel execution) and verify outcomes map to catalog entries with no ambiguous terminology.

**Acceptance Scenarios**:

1. **Given** the fixed readiness matrix, **When** reporting outputs are reviewed, **Then** each outcome maps to a cataloged capability entry.
2. **Given** two reporting views of the same run, **When** results are compared, **Then** they use the same status terms and mapping decisions.

---

### User Story 3 - Govern release readiness (Priority: P3)

As a release reviewer, I need a governance checklist that summarizes capability decisions and unresolved gaps so I can make a go/no-go decision quickly.

**Why this priority**: Formal governance prevents late surprises and undocumented risk acceptance.

**Independent Test**: Use only the governance checklist to determine supported capabilities, deferred work, and release blockers.

**Acceptance Scenarios**:

1. **Given** a release candidate, **When** the reviewer opens the governance checklist, **Then** all capabilities are present with one current status.
2. **Given** unresolved capabilities, **When** readiness is evaluated, **Then** each unresolved item is explicitly marked as blocker or approved deferral.

---

### Edge Cases

- A capability exists upstream but cannot be represented in current runtime outputs.
- A single runtime outcome could reasonably map to more than one capability.
- Execution is interrupted mid-run, producing partial evidence.
- Baseline capability definitions change during an active release cycle.
- Different teams use equivalent but differently named status terms.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a canonical inventory of all relevant `messages` capabilities from an approved upstream baseline.
- **FR-002**: Each capability entry MUST have exactly one status from this controlled vocabulary: `Implemented`, `Pending`, `Non-Implementable`, `Not-Applicable`, or `Not-Acceptable`, and exactly one active decision per `capability_id` per release cycle.
- **FR-003**: Any capability not marked as implemented MUST include rationale, decision owner, evidence reference, and review date.
- **FR-004**: The system MUST define deterministic mapping rules from runtime outcomes to capability entries.
- **FR-005**: The same runtime outcome MUST map to the same capability and status terminology across all reporting views.
- **FR-006**: The system MUST provide a governance artifact that lists every capability entry and its current disposition.
- **FR-007**: The governance artifact MUST flag unresolved entries as either blockers or approved deferrals, where blockers are `Pending` or `Not-Acceptable` and approved deferrals are `Non-Implementable` or `Not-Applicable`.
- **FR-008**: The system MUST detect and report capability additions, removals, and definition changes against the prior approved baseline at least once per week.
- **FR-009**: The system MUST require explicit evidence scenarios for state-dependent capabilities before those capabilities can be counted as covered.
- **FR-010**: Release readiness evaluation MUST fail when required capability evidence is missing, inconsistent, unreviewed, or reviewed outside the current release cycle (treated as `Pending` until re-reviewed).
- **FR-011**: The specification MUST treat capabilities listed in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt` as explicitly in scope for this release.
- **FR-012**: The system MUST keep capability status terminology consistent across specification, planning, and governance artifacts.
- **FR-013**: The system MUST treat multiple decisions for the same `capability_id` within one release cycle as a validation error and a release blocker.
- **FR-014**: Reporting hooks MUST populate every capability identifier listed in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt` when executing the dedicated coverage audit suite.
- **FR-015**: Any capability listed in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt` MUST NOT be classified as `Non-Implementable`, `Not-Applicable`, or `Not-Acceptable` for release readiness.

### Mandatory Hook-Populated Capability Set

- Normative source: `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt`
- Cardinality: 323 capability identifiers.
- Rule: each listed identifier is mandatory implementation scope for hook-based reporting emission and governance coverage in this release.

### Key Entities *(include if feature involves data)*

- **Message Capability**: A cataloged upstream capability with identifier, relevance, and baseline reference.
- **Capability Decision**: A status decision for one capability, including rationale, owner, evidence, and review timestamp.
- **Outcome Mapping Rule**: A deterministic rule linking one runtime outcome class to one or more capability identifiers.
- **Coverage Evidence Scenario**: A named execution scenario used to prove state-dependent capability coverage.
- **Governance Checklist Entry**: A release-facing record containing capability status, open risk, and disposition.

## Assumptions

- The upstream baseline is fixed per release cycle and approved by maintainers before evaluation begins.
- "Relevant capability" means any capability that can influence emitted message content, lifecycle linkage, status interpretation, or release governance.
- Stakeholders prefer explicit unsupported/deferred visibility over implicit omission.
- Weekly review cadence is acceptable for baseline change detection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of relevant baseline capabilities are present in the canonical inventory with exactly one status.
- **SC-002**: 100% of non-implemented capability entries include rationale, decision owner, evidence reference, and review date.
- **SC-003**: In the fixed readiness matrix, 100% of observed outcomes are automatically and deterministically mapped to cataloged capabilities with no ambiguous status terms.
- **SC-004**: Release reviewers can determine go/no-go status using only the governance artifact in 10 minutes or less.
- **SC-005**: Pre-release review finds zero undocumented capability gaps in two consecutive release cycles.
- **SC-006**: In dedicated coverage audit runs, 100% of capability identifiers listed in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt` are reported as `Implemented`.
