# Phase 35: improve-library-typing-using-best-practices-from-awesome-pyt - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-12
**Phase:** 35-improve-library-typing-using-best-practices-from-awesome-pyt
**Areas discussed:** Typing pass scope, Checker strategy, Suppressions and third-party boundaries, Public typing contracts

---

## Typing pass scope

| Decision | Selected |
|---|---|
| Scope | All production and toolchain code |
| Completion standard | Every source module passes configured checkers without module-wide `ignore_errors` |
| Static incompatibilities | Treat as defects |
| Regression prevention | CI gate with no checker errors for both source packages |

## Checker strategy

| Decision | Selected |
|---|---|
| Primary arrangement | Strict mypy implementation gate plus layered public-distribution and consumer-contract validation |
| Public completeness | 100% immediately |
| Consumer-contract surface | Entire documented public surface |
| Discovery spike | Upstream Pyright strict and ty |
| Supplementary target | Python 3.10, platform All |

## Suppressions and third-party boundaries

| Decision | Selected |
|---|---|
| Checker suppressions | None |
| Inadequate dependency typing | Local first, upstream when reusable |
| Dynamic framework boundaries | Public framework types plus project-owned protocols/adapters |
| Cross-version typing | Central compatibility modules |

## Public typing contracts

| Decision | Selected |
|---|---|
| Consumer model | Isolated installed-wheel fixtures |
| Fixture coverage | Representative fixture per documented API family |
| Assertions | Valid and negative cases |
| Contract checkers | Mypy and upstream Pyright |

## the agent's Discretion

- Exact fixture organization, diagnostic matching, CI composition, and per-boundary type modeling.
- Classification and follow-up policy for Pyright strict and ty spike findings.

## Deferred Ideas

None.
