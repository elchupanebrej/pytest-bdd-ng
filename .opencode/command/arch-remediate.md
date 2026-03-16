---
description: Generate a BDD-first remediation spec package from .codex/architecture audit outputs.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

If the user input narrows scope, adjusts priorities, or requests focus on selected modules or rules, honor that while still producing the required outputs unless the user explicitly asks for a reduced output set.

Architecture interpretation rule:
When evaluating this repository, treat BDD executable specification as a primary architectural concern, not just a testing style.
This means:
- feature files are specification artifacts with architectural importance
- step definitions are adapters/glue and should stay thin
- fixtures are dependency/state management tools and must not become hidden workflow engines
- pytest hooks are extension/integration points and must not absorb business or step logic
- parser, binding, execution, and reporting should remain conceptually separable
- traceability from feature text to executable behavior is an architectural quality attribute
- documentation, examples, and executable behavior must not drift apart

You are preparing a remediation specification package for a repository that implements BDD in the pytest ecosystem.

Inputs:
- .codex/architecture/architecture_inventory.md
- .codex/architecture/patterns.json
- .codex/architecture/rules.json
- .codex/architecture/findings.jsonl
- .codex/architecture/violations_by_rule.md
- .codex/architecture/violations_by_module.md
- .codex/architecture/bdd_violations.md
- .codex/architecture/pytest_integration_violations.md
- .codex/architecture/hotspots.md
- .codex/architecture/executive_summary.md
- .codex/architecture/preventive_controls.md

Objective:
Generate a requirements package that can be used in a GitHub Spec Kit flow to fix the architecture problems incrementally, safely, and in a way that preserves executable-specification behavior.

Core constraints:
- The project is a BDD implementation in the pytest ecosystem.
- Feature files and executable specifications are first-class assets and must remain trustworthy.
- Fixes must preserve or improve traceability between feature files, scenarios, steps, runtime execution, and reporting.
- Avoid big-bang refactors whenever incremental remediation is possible.
- Prefer guardrails early if violations are systemic.

Operate as follows.

Phase A. Normalize the problem space
Read findings and rules.
Group violations into remediation themes such as:
- step-definition abuse
- fixture misuse and hidden state flow
- parser/runtime/reporting entanglement
- plugin-boundary leakage
- public API vs internal pytest integration leakage
- weak executable-spec traceability
- duplicated step parsing/binding logic
- compatibility-layer contamination
- documentation/runtime drift
- dependency direction violations
- layering violations
- misplaced responsibility
- extension-point inconsistency

For each remediation theme identify:
- affected modules
- affected rules
- root cause
- technical risk
- user-facing risk
- BDD integrity risk
- likely remediation strategy

Phase B. Decompose into change increments
Break the remediation into small, reviewable, testable increments suitable for spec-driven execution.

Each increment must be:
- atomic
- testable
- safe for code review
- suitable for a dedicated PR
- respectful of pytest plugin and BDD runtime compatibility

For each increment produce:
- increment_id
- title
- goal
- scope
- in_scope
- out_of_scope
- dependencies
- risks
- acceptance_criteria
- required_tests
- rollback_notes
- bdd_impact
- pytest_impact
- compatibility_notes

Phase C. Prioritization model
Use this priority model:
- P0: architecture boundary violations that can break correctness, scenario isolation, plugin behavior, or future evolution
- P1: major dependency/layering problems and severe step/fixture/plugin misuse
- P2: localized responsibility/placement problems
- P3: naming, consistency, cleanup, documentation alignment

Prioritize earlier:
- violations that undermine executable specification trustworthiness
- violations that create hidden state across scenarios
- violations that entangle parser, runtime, and reporting
- violations that leak pytest internals into public extension surfaces
- missing guardrails that allow repeated drift

Phase D. Generate the spec package
Create these files:

1. .codex/spec-kit/repair_overview.md
2. .codex/spec-kit/remediation_backlog.json
3. .codex/spec-kit/spec.md
4. .codex/spec-kit/plan.md
5. .codex/spec-kit/tasks.md
6. .codex/spec-kit/acceptance_criteria.md
7. .codex/spec-kit/risk_register.md
8. .codex/spec-kit/validation_checklist.md
9. .codex/spec-kit/bdd_regression_strategy.md
10. .codex/spec-kit/architecture_guardrails.md

Requirements for each file:

repair_overview.md
- summarize the current architecture state
- explain what BDD and pytest-specific architecture the project appears to intend
- explain where the architecture is drifting
- propose a staged remediation strategy
- rank work by risk reduction and value
- explicitly state how executable specification fidelity will be preserved

remediation_backlog.json
Array of objects:
```json
{
  "increment_id": "...",
  "title": "...",
  "priority": "P0|P1|P2|P3",
  "rules_addressed": ["..."],
  "modules": ["..."],
  "goal": "...",
  "scope": ["..."],
  "non_goals": ["..."],
  "acceptance_criteria": ["..."],
  "tests": ["..."],
  "risks": ["..."],
  "depends_on": ["..."],
  "bdd_impact": "...",
  "pytest_impact": "...",
  "compatibility_notes": ["..."]
}
```

spec.md
Write this as a change specification with sections:
- Context
- Problem Statement
- Goals
- Non-Goals
- BDD Architecture Constraints
- pytest Integration Constraints
- Functional Requirements
- Non-Functional Requirements
- Migration Constraints
- Acceptance Criteria
- Success Metrics

plan.md
Include:
- implementation strategy
- sequencing
- dependency order
- risk-managed PR slicing strategy
- validation approach
- rollout notes
- rollback notes
- compatibility strategy for feature files, step registration, fixtures, hooks, and public APIs

tasks.md
List tasks in execution order.
For each task include:
- task_id
- description
- owner_hint: core|plugin|parser|runtime|reporting|qa|docs
- related_increment_id
- related_rules
- done_definition

acceptance_criteria.md
For each increment_id define acceptance criteria.
Must include where relevant:
- architectural boundaries are preserved
- forbidden dependencies are removed
- public extension points remain stable or are intentionally versioned
- feature/scenario/step traceability is preserved or improved
- scenario isolation is maintained
- fixture scope and state flow are explicit
- reporting behavior is not broken
- parser/runtime/reporting boundaries are cleaner after the change
- architecture tests / guardrails are added or updated

risk_register.md
For each risk include:
- risk
- likelihood
- impact
- mitigation
- detection_signal
- rollback_trigger

validation_checklist.md
Create a reviewer checklist that includes:
- dependency direction verified
- no forbidden imports
- step definitions remain thin
- fixtures do not introduce hidden state flow
- pytest hooks do not contain domain or step logic
- parser/runtime/reporting boundaries are preserved
- public API compatibility reviewed
- executable specification traceability verified
- feature files still map cleanly to runtime behavior
- tests added/updated
- docs/specs updated if needed
- no new cross-module coupling

bdd_regression_strategy.md
Define a regression strategy that protects BDD behavior:
- feature execution regression coverage
- scenario isolation checks
- step binding resolution checks
- fixture scope regression checks
- plugin hook behavior checks
- traceability checks
- reporting regression checks
- compatibility checks for public extension points

architecture_guardrails.md
Recommend preventive controls such as:
- import-linter contracts
- custom architecture tests
- pytest plugin integration tests
- fixture isolation tests
- step-definition thinness checks
- AST checks for forbidden imports/usages
- CI checks for public-vs-internal API leakage
- docs/runtime consistency checks

Phase E. Rules for generating remediation requirements
- Do not recommend a giant refactor if incremental remediation is possible
- Address P0 and P1 first
- Group violations into one increment only if they share a root cause
- Where violations are widespread, propose guardrails before mass code churn
- Clearly distinguish:
  - immediate fixes
  - structural fixes
  - preventive controls
- Preserve user-facing BDD behavior unless intentional change is explicitly specified
- Prefer refactors that improve traceability and debuggability of executable specs
- Treat feature files, step definitions, fixtures, pytest hooks, and plugin registration as architecture-sensitive surfaces

Phase F. Final summary
At the end print:
- number of remediation increments created
- the first 3 increments that should be executed
- the guardrails that should be implemented before broad remediation
- paths to all generated files
