# Phase 20: codegen-step-binding-and-tolerant-steps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-03
**Phase:** 20-codegen-step-binding-and-tolerant-steps
**Areas discussed:** Command/API shape, file rewriting safety, runtime/reporting semantics

---

## Command/API Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Add new flags, keep old flags | Preserve `--generate`, `--generate-missing`, and `--feature`; add spec flags. | |
| Rename old flags into new spec flags | Cleaner CLI with breaking behavior change. | yes |
| Compatibility aliases | New flags canonical, old flags hidden or deprecated aliases. | |

**User's choice:** Rename old flags into new spec flags.
**Notes:** Breaking cleanup is acceptable for this phase.

| Option | Description | Selected |
|--------|-------------|----------|
| Human terminal report only | Current style, easy for users, weak for automation. | |
| Cucumber Messages events | Machine-readable and aligned with reporting model. | |
| JSON output | Structured output for missing data. | yes |

**User's choice:** JSON output.
**Notes:** Follow-up clarified NDJSON as the concrete JSON output shape.

| Option | Description | Selected |
|--------|-------------|----------|
| Cucumber-message-shaped JSON | Envelopes or step-definition diagnostics where possible. | |
| Project-specific JSON | Stable direct schema such as `{features, scenarios, missing_steps}`. | |
| NDJSON stream | One JSON object per event. | yes |

**User's choice:** NDJSON stream.
**Notes:** One JSON object per missing scenario binding or missing step definition event.

| Option | Description | Selected |
|--------|-------------|----------|
| Idempotent no-op | Detect existing equivalent binding and leave file unchanged. | yes |
| Error | Fail loud on duplicate bind intent. | |
| Append anyway | Simpler but risks duplicate tests. | |

**User's choice:** Idempotent no-op.
**Notes:** Existing equivalent `scenarios(...)` for the same feature means no change.

---

## File Rewriting Safety

| Option | Description | Selected |
|--------|-------------|----------|
| AST-aware imports and append scenario/steps | Safer imports and existing binding/decorator detection. | yes |
| Append-only with simple import prepend | Less code but more duplicate/import risk. | |
| Generate patch/diff only | Safest, but less streamlined. | |

**User's choice:** AST-aware rewriting.
**Notes:** Append generated blocks only after structural checks.

| Option | Description | Selected |
|--------|-------------|----------|
| `raise NotImplementedError` | Normal Python signal and default failed WIP behavior. | yes |
| `pytest.skip(...)` | Friendlier for in-progress suites but hides default failure intent. | |
| Empty body under `@not_implemented` | Relies entirely on runtime status. | |

**User's choice:** `raise NotImplementedError`.
**Notes:** Generated missing-step skeletons use this body.

| Option | Description | Selected |
|--------|-------------|----------|
| Deterministic unique suffix | Base slug from text, append `_2`, `_3` on collision. | |
| Hash suffix | Stable but ugly. | |
| Error on collision | User resolves manually. | |
| Use `_` | Function names are not important and not gathered. | yes |

**User's choice:** Use `_`.
**Notes:** Generated step skeleton functions should be named `_`.

| Option | Description | Selected |
|--------|-------------|----------|
| Roll back write and fail | No partially broken target file by default. | yes |
| Keep file and fail | User can inspect/fix generated content. | conditional |
| Write `.bak`, keep generated file, fail | Safer but creates extra files. | |

**User's choice:** Roll back by default; keep file only with special option.
**Notes:** Option name selected as `--keep-generated-on-error`.

---

## Runtime/Reporting Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Step function bodies only | Still match steps, parse args, and run before/after step hooks. | |
| Step calls plus before/after step hooks | Faster, less realistic. | |
| Entire scenario execution after collection | Verify binding only, skip lifecycle. | yes |

**User's choice:** Entire scenario execution after collection.
**Notes:** `--mock-run` verifies collection/binding only and must not run step hooks or step bodies.

| Option | Description | Selected |
|--------|-------------|----------|
| Both orders | `@not_implemented` before or after step decorator works. | yes |
| Spec order only | Simpler, stricter. | |
| Step decorator inner only | Require `@not_implemented` outermost. | |

**User's choice:** Both orders.
**Notes:** Applies to `@given`, `@when`, `@then`, and `@step`.

| Option | Description | Selected |
|--------|-------------|----------|
| Step reported failed, scenario passed | Exposes soft failure in step-level reports. | yes |
| Step reported passed with attachment/log | Less red noise. | |
| Step reported skipped | Signals ignored but semantically odd. | |

**User's choice:** Step reported failed, scenario may pass.
**Notes:** When tolerant status resolves to `ignored`, step-level failure remains visible.

| Option | Description | Selected |
|--------|-------------|----------|
| First priority wins silently | No warning or error on lower-priority conflicts. | yes |
| First priority wins with warning | Warn when lower-priority config conflicts. | |
| Conflict is error | Strict but noisier. | |

**User's choice:** First priority wins silently.
**Notes:** Priority remains pytest marker > Gherkin tag > CLI option > default.

## the agent's Discretion

- Internal module boundaries, helper types, and test split.
- Exact NDJSON field names, with deterministic machine-readable output required.
- Specific migration tests for removed/replaced old codegen flags.

## Deferred Ideas

None.
