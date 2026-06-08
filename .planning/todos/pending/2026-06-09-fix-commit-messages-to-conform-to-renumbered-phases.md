---
created: "2026-06-09T17:19:30.112Z"
title: "Fix commit messages to conform to renumbered phases"
area: planning
files:
  - .planning/ (phase directories)
  - git history
---

## Problem

During development, phases were renumbered (inserted, removed, or reordered), but commit messages from those phases retain stale phase numbers. This creates confusion when reviewing git history — commits reference phase numbers that no longer match the current ROADMAP.md numbering. For example, a commit might say `feat(phase-15): ...` when the work actually belongs to Phase 20 in the current roadmap.

## Solution

1. Audit git log for commit messages referencing the old phase-number scheme
2. Identify which phase each commit belongs to in the current ROADMAP
3. Create a mapping document or decide whether to rewrite history (interactive rebase) or document the mapping
4. If rewriting: use `git rebase -i` to amend commit messages to match current phase numbering
5. If documenting: create a `docs/migration/phase-renumbering.md` that maps old → new phase numbers
