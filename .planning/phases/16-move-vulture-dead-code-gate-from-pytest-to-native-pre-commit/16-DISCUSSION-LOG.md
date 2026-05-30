# Phase 16: Move vulture dead-code gate from pytest to native pre-commit hook - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit
**Areas discussed:** Whitelist shape, stale false-positive cleanup, CI entrypoint, test removal boundary

---

## Whitelist Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Native whitelist file | Add `vulture_whitelist.py`; configure `[tool.vulture].paths = ["src/pytest_bdd", "vulture_whitelist.py"]`. Least custom code. | ✓ |
| Native whitelist + comments | Same native approach, but preserve current rationale comments from `KNOWN_FALSE_POSITIVES`. | |
| Keep exact file/line/message allowlist | Preserves current precision, but needs wrapper/custom code. | |
| Other | Freeform preference. | |

**User's choice:** Native whitelist file.
**Notes:** User selected native vulture config over wrapper support code.

---

## Stale False-Positive Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Accept native behavior | Simpler. Remove stale-entry pytest enforcement. Cleanup happens when vulture/Python whitelist check exposes stale code. | ✓ |
| Add lightweight whitelist validation | Keep small `python vulture_whitelist.py` or syntax-check step if practical. No custom vulture parser. | |
| Preserve exact stale-entry enforcement | Requires wrapper/custom script. Conflicts with native-first decision. | |
| Other | Freeform preference. | |

**User's choice:** Accept native behavior.
**Notes:** Exact stale-entry enforcement from the current pytest test is not required.

---

## CI Entrypoint

| Option | Description | Selected |
|--------|-------------|----------|
| Via existing pre-commit env | Add vulture hook to `.pre-commit-config.yaml`; existing tox/pre-commit path runs it. | ✓ |
| Dedicated tox env | Add a separate vulture tox environment. Clear gate, more config. | |
| Direct CI command only | Run `python -m vulture` directly in CI. Bypasses pre-commit standardization. | |
| Other | Freeform preference. | |

**User's choice:** Via existing pre-commit env.
**Notes:** Do not add a dedicated tox vulture env unless planning finds it necessary.

---

## Test Removal Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Delete it entirely | Dead-code gate lives in pre-commit/CI only. | ✓ |
| Replace with tiny config sanity test | Check `[tool.vulture]` paths include whitelist and source. Extra test, low value. | |
| Keep old test temporarily | Duplicate gate during migration, then remove later. More noise. | |
| Other | Freeform preference. | |

**User's choice:** Delete it entirely.
**Notes:** `tests/cases/unit/unit/test_dead_code.py` should be removed, not replaced.

---

## the agent's Discretion

None.

## Deferred Ideas

None from discussion. Weak todo matches were reviewed and left out of scope.
