---
description: Perform a comprehensive BDD-first repository audit and write structured outputs under .codex/architecture.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

If the user input narrows scope, adds constraints, or requests emphasis areas, honor that while still producing the required outputs unless the user explicitly asks for a reduced output set.

You are performing a comprehensive repository audit of a codebase whose primary purpose is BDD documentation and execution in the pytest ecosystem.

Context:
- This project uses BDD as executable documentation.
- The repository may contain Gherkin feature files, step definitions, pytest fixtures, pytest plugins/hooks, parsers, collectors, execution/runtime components, reporting/integration layers, docs, examples, compatibility shims, and internal extension points.
- The audit must evaluate:
  1. technology/tooling usage,
  2. implemented architecture,
  3. BDD-specific architecture and execution model,
  4. specification quality,
  5. coverage and traceability completeness,
  6. reliability, determinism, and scalability,
  7. public API and extension-surface integrity,
  8. rule enforceability and preventive controls.

Primary objectives:
1. Traverse the full repository tree.
2. Identify the implementation stack, libraries, tooling, and utilities actually in use.
3. Identify which architectural patterns are actually implemented in the codebase.
4. Identify which BDD-specific and pytest-specific architectural patterns and boundaries are present.
5. Evaluate the semantic quality of the executable specifications themselves, not just the code.
6. Infer explicit and implicit architecture rules from observed design and runtime wiring.
7. Validate the repository file-by-file against those rules.
8. Detect architectural drift, specification drift, and documentation drift.
9. Use parallel agents where possible.
10. Aggregate findings by rule, subsystem, module, file, and concern.
11. Produce both machine-readable and human-readable outputs.
12. Distinguish facts, hypotheses, inferred rules, and recommendations.

General operating rules:
- Do not invent patterns, practices, or guarantees without evidence.
- Do not infer architecture solely from folder names.
- Confirm conclusions with imports, call flows, registrations, runtime wiring, configuration, documentation, and actual usage.
- If a conclusion is inferred rather than explicit, label it as inferred.
- If confidence is limited, mark it low confidence and explain why.
- Treat feature files, documentation, examples, and config as first-class architecture evidence where relevant.
- Support polyglot or mixed config/docs assets if present.
- Prefer evidence-backed precision over broad but weak claims.

==================================================
Phase A. Build a repository map
==================================================

Walk the entire repository tree.

Exclude noise directories such as:
- .git
- node_modules
- dist
- build
- coverage
- .tox
- .nox
- .pytest_cache
- htmlcov
- site-packages
- vendor
- tmp
- cache
- generated artifacts
- __pycache__

Inspect all relevant files, including but not limited to:
- pyproject.toml
- poetry.lock
- requirements*.txt
- setup.py
- setup.cfg
- tox.ini
- pytest.ini
- noxfile.py
- conftest.py
- package.json
- lockfiles
- CI configs
- Dockerfiles / compose files
- Makefiles / task runners
- Ruff / Flake8 / mypy / coverage configs
- docs/*
- README*
- CONTRIBUTING*
- examples/*
- feature files
- source code modules
- test modules
- internal scripts
- plugin registration points

Build a repository map of:
- packages and modules
- public APIs
- internal/private modules
- parser components
- lexer/tokenization/AST components if any
- Gherkin / feature loading components
- step binding components
- pytest integration points
- fixtures
- hooks and plugin registration
- execution/runtime layers
- reporting/output/integration components
- test suites
- documentation/specification assets
- examples and demos
- compatibility layers
- CLI/configuration layers
- extension points
- custom utilities and internal scripts

Detect the implementation stack:
- Python version assumptions
- pytest plugin architecture
- parser libraries
- AST/tokenization layers
- reporting integrations
- CLI/configuration layers
- compatibility layers
- static analysis and lint tooling
- typing strategy
- packaging/distribution strategy
- CI/CD tooling
- developer experience tooling

Build dependency maps between modules and subsystems:
- import dependency map
- runtime wiring map
- plugin registration map
- fixture dependency map
- feature -> step -> runtime -> reporting traceability map

For each detected technology or tool, report:
- name
- role
- evidence_files[]
- confidence: exact|probable|possible

==================================================
Phase B. Detect architectural patterns
==================================================

Identify only patterns supported by evidence. For each pattern provide evidence.

Check for generic patterns including:
- Layered Architecture
- Clean Architecture
- Hexagonal / Ports and Adapters
- Modular Monolith
- Plugin Architecture
- Service Layer
- Adapter
- Facade
- Strategy
- Factory
- Visitor
- Observer / Event-driven interaction
- Dependency Injection
- Anti-corruption layer
- Compatibility boundary
- Public API / internal boundary model

Check for BDD / pytest-specific patterns including:
- Executable Specification architecture
- Gherkin-to-runtime translation pipeline
- Thin step-definition / glue-layer pattern
- Fixture-mediated dependency flow
- Parser / compiler style separation
- Plugin extension architecture for pytest
- Separation between specification, binding, execution, and reporting
- Hook-based extensibility boundaries
- Scenario-to-test-case mapping architecture
- Declarative specification with imperative adapter layer
- Compatibility shims for pytest internals or versions
- Step registration abstraction
- Feature/scenario/step traceability preservation model

For each detected pattern output:
- pattern_id
- pattern_name
- category: generic|bdd|pytest|hybrid
- confidence: high|medium|low
- evidence_files[]
- rationale
- implied_rules[]
- inferred_or_explicit: inferred|explicit

==================================================
Phase C. Audit executable-specification semantics
==================================================

Evaluate the semantic quality of the BDD assets themselves, not just the surrounding code.

Inspect for:
- domain language consistency
- ubiquitous language alignment across docs, feature files, step text, and public APIs
- procedural vs behavioral scenario style
- overly implementation-centric step wording
- UI-script style scenarios disguised as business specifications
- weak or vague Then outcomes
- multi-concern scenarios
- low readability for non-technical stakeholders
- duplication in scenario meaning expressed with inconsistent wording
- ambiguous step phrases
- hidden business assumptions encoded in fixtures instead of specs
- examples/docs/specs diverging in terminology
- executable documentation integrity

Classify specification smells including:
- procedural_specification
- implementation_leakage
- vague_assertion
- multi_concern_scenario
- low_business_signal
- duplicated_behavior_expression
- ambiguous_language
- fixture_hidden_behavior
- unreadable_executable_doc

For each semantic finding output:
- finding_id
- smell_type
- severity: critical|high|medium|low
- confidence: high|medium|low
- evidence_files[]
- impacted_scenarios[]
- summary
- why_it_matters
- suggested_fix

==================================================
Phase D. Infer architecture and quality rules
==================================================

Infer strict architecture rules from observed implementation patterns, repository structure, and specification model.

Each rule must include:
- rule_id
- title
- category: generic|bdd|pytest|hybrid|tooling|quality|reliability|api
- rule_type: invariant|policy|convention|heuristic
- inferred_or_explicit: inferred|explicit
- description
- applies_to
- allowed
- forbidden
- severity: critical|high|medium|low
- enforcement_level: blocking|advisory
- detection_heuristics
- false_positive_risks
- exception_policy
- legacy_tolerance
- automation_candidates[]
- evidence_basis[]

Infer both generic and BDD-specific rules.

Examples of generic rules:
- internal_modules_must_not_be_imported_from_public_api_consumers
- lower_level_parsing_components_must_not_depend_on_reporting
- runtime_execution_must_not_depend_on_test_assertion_helpers_in_reverse_direction
- public_api_must_not_depend_on_test_only_modules
- compatibility_layer_must_be_isolated
- accidental_public_api_must_be_detected_and_minimized
- extension_points_must_be_explicitly_bounded

Examples of BDD / pytest-specific rules:
- feature_files_are_specification_assets_not_runtime_logic_containers
- step_definitions_must_not_contain_core_business_or_runtime_orchestration_logic
- step_definitions_should_delegate_to_domain_or_runtime_services
- step_definitions_must_not_duplicate_parser_or_execution_logic
- gherkin_parsing_must_be_separate_from_pytest_execution_binding
- pytest_hooks_must_not_embed_domain_specific_step_logic
- fixture_setup_must_not_become_hidden_business_workflow
- fixtures_must_have_clear_scope_and_not_smuggle_cross_scenario_state
- scenario_binding_must_not_bypass_public_step_registration_mechanisms_without_reason
- reporting_components_must_not_control_execution_flow
- parser_components_must_not_depend_on_pytest_terminal_reporting
- compatibility_shims_must_not_leak_into_core_domain_model
- executable_spec_mapping_must_preserve_traceability_between_feature_scenario_step_and_test_node
- documentation_examples_and_real_executable_specs_must_be_clearly_separated_if_both_exist
- feature_step_text_parsing_rules_must_not_be_scattered_inconsistently_across_unrelated_modules
- executable_specs_should_use_domain_language_over_internal_implementation_terms
- feature_behavior_coverage_should_not_be_happy_path_only_for_critical_capabilities
- fixture_behavior_must_not_hide_required_specification_context
- failure_diagnostics_must_preserve_actionable_traceability

==================================================
Phase E. Validate the repository against rules
==================================================

Inspect the codebase file-by-file and subsystem-by-subsystem.

For each rule, determine status:
- PASS
- FAIL
- PARTIAL
- NOT_APPLICABLE
- UNKNOWN

For each rule result include:
- rule_id
- status
- confidence: high|medium|low
- evidence
- explanation
- impacted_files[]
- impacted_symbols[]
- exception_status: none|justified|legacy|unclear
- remediation
- automation_recommendation

If a check cannot be completed without execution, external systems, or unavailable context:
- do not invent a result
- mark UNKNOWN
- explain what would be required to verify it

==================================================
Phase F. Coverage and traceability completeness audit
==================================================

Audit whether executable specifications comprehensively and coherently map to the implemented behavior.

Check for:
- orphan feature files
- scenarios with missing bindings
- unused step definitions
- dead fixtures/helpers only reachable from legacy paths
- critical public behaviors without feature coverage
- happy-path-only behavior coverage
- missing negative/error-path coverage
- duplicated scenario coverage expressed with inconsistent vocabulary
- fragmented traceability from feature -> scenario -> step -> executable binding -> runtime node -> report
- runtime paths never exercised through specs where specs claim support
- examples/docs describing workflows that executable specs do not actually cover

For each coverage finding include:
- coverage_finding_id
- category: orphan_asset|unused_binding|missing_coverage|traceability_gap|duplication|drift
- severity
- confidence
- evidence_files[]
- summary
- impacted_capabilities[]
- suggested_fix

==================================================
Phase G. Reliability, determinism, and scalability audit
==================================================

Explicitly inspect for:
- order dependence between scenarios/tests
- fixture scope leaks
- shared mutable state across scenarios
- autouse fixtures introducing hidden behavior
- time/date/random/environment coupling
- external-system coupling without clear contracts
- flaky hooks or plugin registration side effects
- nondeterministic reporting paths
- collection/discovery instability
- parser performance bottlenecks
- repeated expensive parsing/loading
- runtime scaling issues across large feature suites
- xdist / parallel execution hazards
- memory retention due to session/module-scoped structures
- concrete signs of slow or fragile execution architecture

For each finding include:
- reliability_finding_id
- category: determinism|state_leak|parallelism|performance|scalability|flakiness
- severity
- confidence
- evidence_files[]
- summary
- why_it_is_risky
- suggested_fix
- verification_method

==================================================
Phase H. Public API and extension-surface audit
==================================================

Inspect the public and de facto public surface of the project.

Determine:
- what is intentionally public
- what is accidentally public
- what is internal but imported externally within the repo
- what extension points exist
- whether extension points are documented and stable
- whether plugin APIs depend on private internals
- whether re-export structure is coherent
- whether compatibility and deprecation mechanisms exist
- whether API boundaries are cleanly testable
- whether examples use supported extension points or private shortcuts

Detect:
- private import leakage
- accidental public API
- unstable extension contracts
- undocumented extension points
- re-export confusion
- compatibility shims leaking into normal user paths
- migration scaffolding left in production surface

For each API finding include:
- api_finding_id
- category: public_surface|private_leakage|extension_point|compatibility|deprecation
- severity
- confidence
- evidence_files[]
- summary
- suggested_fix

==================================================
Phase I. BDD-specific checks you must perform
==================================================

You must explicitly inspect for the following risks:

1. Step-definition abuse
- step functions containing substantial orchestration/business logic
- parsing and normalization logic duplicated inside step files
- direct low-level manipulation that should live in reusable runtime/services/helpers

2. Fixture misuse
- fixtures used as hidden control flow
- fixtures with unclear scope causing cross-scenario coupling
- autouse fixtures leaking implicit behavior into executable specifications
- fixtures mutating shared global state without clear isolation

3. Specification-to-execution leakage
- feature text tightly coupled to internal implementation details
- scenario binding that depends on private module structures
- step regex/parser logic duplicated across files
- brittle coupling between Gherkin text and internal function names

4. Plugin-boundary violations
- pytest hooks containing domain logic or step logic
- hook implementations depending on unrelated reporting or parsing internals
- plugin registration side effects spread across modules
- internal pytest integration details leaking into public API

5. Parser / runtime / reporting entanglement
- parser layer depending on reporting/UI/output concerns
- reporting layer controlling execution rather than observing it
- runtime layer tightly coupled to concrete parser internals where a boundary should exist

6. Traceability failures
- weak mapping from feature -> scenario -> step -> executable binding
- missing or fragmented code paths that make executable specs hard to trace
- architecture that makes debugging failed scenarios unnecessarily opaque

7. Documentation consistency failures
- docs claiming BDD workflow that the runtime architecture does not actually support
- examples diverging from actual public extension points
- architectural drift between docs, feature specs, and plugin behavior

8. Specification semantics failures
- procedural, implementation-driven, or low-signal feature/scenario design
- domain language drift between docs and executable specs
- hidden assumptions encoded outside the scenarios

==================================================
Phase J. Multi-agent analysis model
==================================================

Use parallel agents where possible.

Use at least these agent types:
1. Module agents
   - each agent analyzes one package/module/subsystem
2. Rule agents
   - each agent evaluates one inferred rule across the repository
3. Specification agents
   - each agent analyzes one feature/specification area for semantic quality and traceability
4. API agents
   - each agent analyzes one public surface / extension boundary
5. Reliability agents
   - each agent analyzes one reliability concern class

If the platform supports fan-out parallel execution, use it.
If not, emulate a multi-agent pipeline while still producing isolated outputs per agent.

Each agent must emit findings in normalized JSONL format.

One finding record must use this schema:
```json
{
  "rule_id": "...",
  "rule_title": "...",
  "pattern_id": "...",
  "severity": "critical|high|medium|low",
  "confidence": "high|medium|low",
  "category": "generic|bdd|pytest|hybrid|tooling|quality|reliability|api",
  "module": "...",
  "file": "relative/path",
  "line_start": 0,
  "line_end": 0,
  "symbol": "class/function/module if known",
  "violation_type": "dependency|layering|boundary|placement|coupling|state|traceability|plugin_boundary|fixture_misuse|step_glue_abuse|reporting_leakage|api_leakage|spec_semantics|coverage_gap|flakiness|performance|other",
  "summary": "...",
  "why_it_is_a_violation": "...",
  "evidence": ["..."],
  "suggested_fix": "...",
  "duplicate_key": "rule_id::file::line_start::symbol"
}
```

==================================================
Phase K. Aggregate findings
==================================================

After all agents finish, run a reducer:
- deduplicate by duplicate_key
- group by:
  - rule_id
  - category
  - subsystem
  - module
  - file
  - violation_type
- compute:
  - violations_total
  - unique_locations_total
  - modules_affected
  - severity_distribution
  - confidence_distribution

Identify hotspots:
- files with highest violation density
- most frequently violated rules
- subsystems with highest architecture drift
- BDD-specific hotspots
- pytest-plugin-boundary hotspots
- specification-semantics hotspots
- coverage-gap hotspots
- reliability/flakiness hotspots
- public-surface hotspots

Also identify:
- high-impact low-effort fixes
- risky but strategic refactors
- rules with poor enforceability
- rules likely to generate noise if automated
- areas requiring manual review

==================================================
Phase L. Preventive controls and enforcement strategy
==================================================

For each important rule, propose how it could be enforced and whether it should be enforced.

Possible enforcement mechanisms include:
- import-linter
- pytest architectural tests
- custom AST checks
- Ruff/Flake8 plugins
- mypy boundaries
- CI checks
- plugin registration tests
- traceability tests between feature/scenario/step/runtime
- fixture isolation tests
- API surface snapshot tests
- public-vs-private import checks
- spec-semantic lint rules
- documentation drift checks

For each control include:
- rule_id
- control_type
- enforceability: high|medium|low
- expected_noise: high|medium|low
- implementation_cost: low|medium|high
- maintenance_cost: low|medium|high
- recommended: yes|no
- rationale

==================================================
Phase M. Outputs
==================================================

Create:
1. .codex/architecture/stack_inventory.md
2. .codex/architecture/architecture_inventory.md
3. .codex/architecture/patterns.json
4. .codex/architecture/rules.json
5. .codex/architecture/findings.jsonl
6. .codex/architecture/violations_by_rule.md
7. .codex/architecture/violations_by_module.md
8. .codex/architecture/bdd_violations.md
9. .codex/architecture/pytest_integration_violations.md
10. .codex/architecture/specification_semantics.md
11. .codex/architecture/coverage_traceability.md
12. .codex/architecture/reliability_and_scalability.md
13. .codex/architecture/api_surface.md
14. .codex/architecture/hotspots.md
15. .codex/architecture/executive_summary.md
16. .codex/architecture/preventive_controls.md
17. .codex/architecture/audit_summary.json

Requirements for executive_summary.md:
- what technologies and tooling were detected
- what architecture patterns were detected
- what BDD-specific patterns were detected
- what the intended architecture appears to be
- the main architectural invariants
- the main specification-quality invariants
- whether executable-specification integrity is preserved
- the top 10 violations by importance
- quick wins
- risky refactors
- coverage blind spots
- reliability/flakiness risks
- API/extension-surface risks
- areas of low confidence

Requirements for audit_summary.json:
```json
{
  "project_summary": {
    "type": "",
    "languages": [],
    "frameworks": [],
    "libraries": [],
    "tooling": [],
    "public_surfaces": [],
    "extension_points": []
  },
  "patterns": [
    {
      "pattern_id": "",
      "pattern_name": "",
      "category": "",
      "confidence": "",
      "evidence_files": []
    }
  ],
  "rules": [
    {
      "id": "",
      "title": "",
      "category": "",
      "rule_type": "",
      "severity": "",
      "enforcement_level": "",
      "status": "",
      "evidence": [],
      "remediation": []
    }
  ],
  "semantic_findings": [
    {
      "finding_id": "",
      "smell_type": "",
      "severity": "",
      "evidence": [],
      "recommendation": ""
    }
  ],
  "coverage_findings": [
    {
      "coverage_finding_id": "",
      "category": "",
      "severity": "",
      "evidence": [],
      "recommendation": ""
    }
  ],
  "reliability_findings": [
    {
      "reliability_finding_id": "",
      "category": "",
      "severity": "",
      "evidence": [],
      "recommendation": ""
    }
  ],
  "api_findings": [
    {
      "api_finding_id": "",
      "category": "",
      "severity": "",
      "evidence": [],
      "recommendation": ""
    }
  ],
  "scores": {
    "repository_hygiene": 0,
    "dependency_management": 0,
    "architecture_integrity": 0,
    "bdd_architecture_integrity": 0,
    "specification_quality": 0,
    "coverage_traceability": 0,
    "reliability": 0,
    "api_surface_integrity": 0,
    "security": 0,
    "maintainability": 0,
    "overall": 0
  }
}
```

Requirements for preventive_controls.md:
- For each important rule, propose whether and how it should be enforced.
- Explicitly separate:
  - hard blocking controls
  - advisory controls
  - manual-review-only controls
- Identify controls that are likely too noisy or too expensive.
- Recommend a staged adoption path:
  - immediate
  - next iteration
  - long-term

==================================================
Phase N. Final concise console summary
==================================================

At the end, print a concise summary:
- technologies/tooling detected
- patterns detected
- BDD-specific patterns detected
- rules inferred
- total violations
- critical/high violations
- semantic-quality findings
- coverage/traceability findings
- reliability findings
- API-surface findings
- top hotspot files
- output paths

==================================================
Quality requirements
==================================================

- Do not invent patterns without evidence.
- Do not infer architecture only from folder names.
- Confirm with imports, call flows, registrations, runtime wiring, and actual usage.
- If a rule is inferred rather than explicit, label it as inferred.
- Mark low confidence where appropriate.
- Support polyglot or mixed config/docs assets if present.
- Treat feature files and documentation as first-class architecture evidence when relevant.
- Separate facts, hypotheses, inferred rules, and recommendations.
- Separate architectural violations from specification-quality problems.
- Separate reliability risks from ordinary code smells.
- Separate public API problems from internal structure problems.
- Identify justified exceptions and legacy zones when evidence supports that interpretation.
- Prefer practical, evidence-backed findings that a real engineering team can act on.
