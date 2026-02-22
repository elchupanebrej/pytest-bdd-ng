<!-- markdownlint-disable MD013 -->

# Research: Python/Pytest Compatibility Alignment (EOL Floor Update)

## Decision 1: Supported version floor policy

- Decision: Support Python 3.10-3.14 and pytest>=6.2.5; treat Python 3.9 and pytest<6.2.5 as explicitly unsupported.
- Rationale: This matches EOL policy, keeps support deterministic, and prevents accidental legacy matrix expansion.
- Alternatives considered:
  - Keep Python 3.9 as best-effort: rejected because it conflicts with explicit EOL deprecation.
  - Keep pytest 6.0/6.1/6.2.0-6.2.4 in matrix: rejected due to requested support floor and maintenance cost.

## Decision 2: Validation scope after deprecation

- Decision: Run full matrix validation only for supported pairs; add explicit negative checks for deprecated EOL pairs.
- Rationale: Provides complete confidence for supported surface while still asserting fail-fast behavior for unsupported combinations.
- Alternatives considered:
  - Validate all historical pairs: rejected as unnecessary and contradictory to deprecation scope.
  - Validate only a representative subset: rejected because it weakens deterministic coverage guarantees.

## Decision 3: Runtime and tooling representation

- Decision: Encode support floor in matrix logic, tox env selection, CI job matrix, and contributor docs.
- Rationale: Single policy reflected in all execution paths avoids drift between local runs, CI, and documentation.
- Alternatives considered:
  - Enforce floor only in docs: rejected because tooling drift would reintroduce unsupported execution paths.
  - Enforce floor only in CI: rejected because local and release workflows would remain inconsistent.

## Decision 4: Diagnostics for unsupported combinations

- Decision: Unsupported EOL pairs MUST fail fast with explicit reason code and actionable message.
- Rationale: Clear diagnostics reduce triage time and make deprecation behavior testable.
- Alternatives considered:
  - Silent skip behavior: rejected due to ambiguity and hidden failures.
  - Generic exception without reason code: rejected because it is weak for automation and contract testing.

## Decision 5: Cross-platform validation execution rule

- Decision: Use native execution for host-native targets; use Docker skill for non-native platform validation except Windows targets.
- Rationale: Satisfies constitution requirements while preserving practical execution for Windows-target exceptions.
- Alternatives considered:
  - Native-only validation for all targets: rejected due to constitution non-compliance.
  - Docker for all targets including Windows: rejected because constitution explicitly allows Windows exception.
