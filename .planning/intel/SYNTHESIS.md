# Synthesis Summary

**Generated:** 2026-06-11
**Mode:** merge
**Ingest set:** 2 documents

---

## Document Counts by Type

| Type | Count |
|------|-------|
| ADR | 0 |
| SPEC | 2 |
| PRD | 0 |
| DOC | 0 |
| **Total** | **2** |

---

## Decisions Locked

0 decisions locked. Both SPEC documents are `locked: false`. No ADRs in ingest set. No existing locked decisions found in merge context.

---

## Requirements Extracted

8 requirements extracted:

| ID | Source | Description |
|----|--------|-------------|
| REQ-cck-allure-45-samples | spec.md | Validate allure-cucumber converter against all 45 CCK NDJSON samples |
| REQ-cck-download-strategy | spec.md | CCK download via `gh api` with fallback, session-scoped caching |
| REQ-cck-docker-allure | spec.md | Docker-based Allure HTML report generation |
| REQ-cck-playwright-validation | spec.md | Playwright browser validation of rendered reports |
| REQ-cck-edge-cases | spec.md | 10 contract test edge cases (empty, single-line, failed, attachments, etc.) |
| REQ-cck-bdd-feature | plan.md | BDD feature file with step definitions |
| REQ-cck-parameterized-rendering | plan.md | Parameterized Playwright tests for all 45 samples |

---

## Constraints

7 constraints extracted:

| ID | Type | Content |
|----|------|---------|
| CONSTRAINT-001 | api-contract | CCK release tag `v29.2.2`, GitHub API download |
| CONSTRAINT-002 | protocol | Docker image `frankescobar/allure-docker-service:2.27.0` |
| CONSTRAINT-003 | nfr | Test markers: `@docker`, `@browser`, `@slow`, `@contract` |
| CONSTRAINT-004 | nfr | Graceful degradation for Docker, Playwright, `gh` CLI |
| CONSTRAINT-005 | protocol | Must reuse existing patterns (`_run_allure_docker`, `_serve_directory`, etc.) |
| CONSTRAINT-006 | schema | Fixed file structure across 6 files |
| CONSTRAINT-007 | nfr | Out-of-scope boundaries (no snapshot comparison, no step execution) |

---

## Context Topics

6 context topics recorded:
1. CCK Allure Compatibility Pipeline Architecture
2. Conversion Strategy
3. Implementation Phases (5 phases)
4. Existing Patterns to Reuse
5. Dependencies
6. Risk Mitigation

---

## Conflicts

- **0** blockers
- **0** competing variants
- **2** auto-resolved (INFO level — classification note, no locked decisions)

---

## Pointers

- **Conflicts report:** `.planning/INGEST-CONFLICTS.md`
- **Decisions:** `.planning/intel/decisions.md`
- **Requirements:** `.planning/intel/requirements.md`
- **Constraints:** `.planning/intel/constraints.md`
- **Context:** `.planning/intel/context.md`
- **Target phase:** Phase 20, Wave 6 (20-06-PLAN.md) — already referenced in ROADMAP.md

---

*Synthesis complete. Ready for roadmapping.*
