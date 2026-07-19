# Phase 02: Code Quality Gates - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-12
**Phase:** 02-code-quality-gates
**Areas discussed:** Sentinel vs Exception strategy, Exception specificity, CI enforcement mechanism, Zero-matches UX

---

## Sentinel vs Exception Strategy

### returns Library

| Option | Description | Selected |
|--------|-------------|----------|
| Keep Optional[T] with None | Return type already communicates might-not-be-found | |
| Switch to _MISSING sentinel | Use object() sentinel everywhere | |
| Raise LookupError | Treat not-found as error | |
| Use returns library (Maybe/Result) | <https://pypi.org/project/returns/> | ✓ |

**User's choice:** Use returns library — `Maybe[T]` and `Result[T, E]`
**Notes:** Full Maybe + Result migration. Pytest hooks exempt. Per-module StrEnum for failure values. Per-file imports. Define canonical patterns.

### returns Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Maybe for all Optional returns | Convert all T\|None to Maybe[T] | |
| Full Maybe + Result migration | All Optional + error handling | ✓ |
| Maybe only for chain patterns | Only nested optional chains | |

**User's choice:** Full Maybe + Result migration
**Notes:** Aggressive — rewrites significant portion of codebase.

### Hook Exemption

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, hooks stay as-is | Framework contract requires None | ✓ |
| No, convert hooks too | Risk of breaking pytest | |

**User's choice:** Hooks exempt — consistent with AGENTS.md rule

### Error Types

| Option | Description | Selected |
|--------|-------------|----------|
| Domain-specific enums | Per-module StrEnum of failure reasons | ✓ |
| Strings | Plain string messages | |
| Custom exception classes | Exception instances as failure values | |

**User's choice:** Domain-specific per-module enums

### Import Style

| Option | Description | Selected |
|--------|-------------|----------|
| Per-file imports | Direct from returns in each file | ✓ |
| Central re-export | From `pytest_bdd.__init__` | |
| Convenience module | Internal re-export wrapper | |

**User's choice:** Per-file imports — explicit, no magic

### Pattern Documentation

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, define canonical patterns | Document which sigs use Maybe vs Result | ✓ |
| No, let executor decide | Per-instance judgment | |

**User's choice:** Define canonical patterns for consistency

---

## Exception Specificity

### Silent Swallowers

| Option | Description | Selected |
|--------|-------------|----------|
| logger.warning(exc_info=True) | Preserve catch-all, always log | ✓ |
| Replace with specific types | Audit each site for exact types | |
| Convert to Result.failure() | Consistent with returns migration | |

**User's choice:** Add logger.warning(exc_info=True) — minimum fix that preserves semantics

### parsers.py Exemption

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, exempt | Parser chain pattern is sound, roadmap says frozen | |
| No, convert to Result | Major change to frozen file | ✓ |

**User's choice:** Convert to Result — override roadmap freeze

### Freeze Override

| Option | Description | Selected |
|--------|-------------|----------|
| Respect freeze | Leave parsers.py as-is | |
| Override freeze | Convert anyway | ✓ |
| Wrap, don't modify | Thin adapter outside parsers.py | |

**User's choice:** Override freeze — explicitly authorized for this phase

---

## CI Enforcement Mechanism

### Lint Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Ruff AST-based lint rule | Custom rule, pre-commit + CI | ✓ |
| Pre-commit grep script | Simple, less precise | |
| pytest plugin assertion | Test-time AST inspection | |

**User's choice:** Ruff AST-based custom lint rule

### Transition Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Hard block — fix all | Zero tolerance after phase | ✓ |
| Warning-first | Allow existing, block new | |

**User's choice:** Hard block — all 95 violations must be fixed

---

## Zero-matches UX

### Error Format

| Option | Description | Selected |
|--------|-------------|----------|
| pytest.UsageError with step list | Lists unmatched steps with file:line | |
| Custom warning (non-fatal) | Shows as skipped with reason | |
| Collection error + skip marker | Error by default, opt-out flag | ✓ |

**User's choice:** Collection error + `--allow-empty-scenarios` escape hatch

### Transitional Period

| Option | Description | Selected |
|--------|-------------|----------|
| Direct enforcement | No transitional period | ✓ |
| One-release deprecation warning | Warning before error | |

**User's choice:** Direct enforcement — consistent with D-10 precedent

---

## the agent's Discretion

- Exact `StrEnum` member names per module
- Ruff rule implementation details (AST node types, hook detection heuristic)
- Error message formatting for zero-matches UsageError
- Migration ordering — which files/patterns to convert first

## Deferred Ideas

None — discussion stayed within phase scope.
