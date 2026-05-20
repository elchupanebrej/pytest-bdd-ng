# Phase 13: Unify cucumber-json plugins INI/CLI options - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-20
**Phase:** 13-unify-cucumber-json-plugins-ini-cli-options
**Areas discussed:** Consolidation strategy, Entry point fate, Config precedence, Output parity + xdist worker behavior

---

## Consolidation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Single entry point | One plugin handles both INI and CLI; remove second pytest11 registration | |
| Shared config layer | Keep both entry points, extract shared config parsing into common module | |
| Thin wrapper | One plugin becomes thin adapter delegating to the other's implementation | |
| New dispatcher (freeform) | New plugin that understands both INI and CLI options, delegates to existing plugins | ✓ |

**User's choice:** Add a new dispatcher that delegates work to one of the existing plugins; dispatcher understands both INI and CLI options.
**Notes:** User described this as a freeform answer — not one of the presented options. The dispatcher is additive; existing plugins are not modified.

---

### Entry Point Structure (sub-area)

| Option | Description | Selected |
|--------|-------------|----------|
| Replace both | Dispatcher is sole pytest11 entry point; existing plugins deregistered | |
| Add alongside | Dispatcher is a third entry point; existing two remain active (risk: duplicate registration) | ✓ |
| Replace only INI one | cucumber_json becomes the dispatcher; cucumber_json_formatter stays as-is | |

**User's choice:** Add alongside — dispatcher is a third entry point; existing two remain active.
**Notes:** User acknowledged duplicate registration risk explicitly. Guard responsibility assigned to dispatcher.

---

### Duplicate Registration Guard (sub-area)

| Option | Description | Selected |
|--------|-------------|----------|
| Guard in dispatcher | Dispatcher checks pluginmanager before delegating; skips if already registered | ✓ |
| Guard in existing plugins | Backends detect if dispatcher is active and defer | |
| No guard | Rely on pytest's duplicate-plugin detection | |

**User's choice:** Guard in dispatcher.
**Notes:** Existing plugins remain unmodified.

---

## Entry Point Fate

| Option | Description | Selected |
|--------|-------------|----------|
| Both stay permanently | Independent plugins; dispatcher is additive | |
| Both eventually deprecated | Dispatcher becomes canonical; existing deprecated in future phase | |
| No change for now | Phase 13 only adds dispatcher; deprecation out of scope | ✓ |

**User's choice:** No change for now — Phase 13 is strictly additive.

---

### Dispatcher Location (sub-area)

| Option | Description | Selected |
|--------|-------------|----------|
| New top-level module | src/pytest_bdd/plugin/cucumber_json_dispatcher/ | ✓ |
| Inside cucumber_json package | src/pytest_bdd/plugin/cucumber_json/dispatcher.py | |
| Inside cucumber_json_formatter package | src/pytest_bdd/plugin/cucumber_json_formatter/dispatcher.py | |

**User's choice:** New top-level module — `src/pytest_bdd/plugin/cucumber_json_dispatcher/`

---

## Config Precedence

| Option | Description | Selected |
|--------|-------------|----------|
| CLI wins | --cucumber-json overrides INI cucumber_json_path when both set | ✓ |
| INI wins | cucumber_json_path takes precedence over CLI flag | |
| Both run independently | Both backends activate; two output files produced | |
| Error / mutual exclusion | Raise if both set simultaneously | |

**User's choice:** CLI wins — `--cucumber-json` overrides `cucumber_json_path` INI.

---

### Override Notification (sub-area)

| Option | Description | Selected |
|--------|-------------|----------|
| Silent | INI option silently ignored; only CLI output produced | ✓ |
| Warning | Emit pytest warning that INI was overridden by CLI | |

**User's choice:** Silent override.

---

## Output Parity

| Option | Description | Selected |
|--------|-------------|----------|
| Intentionally different | INI = Python JSON; CLI = Node.js JSON. No convergence needed. | |
| Converge on CLI format | Make INI path produce identical output to Node.js formatter | |
| Converge on INI format | Make CLI path produce identical output to Python writer | |
| Document the difference | Note format differences; users choose knowingly | ✓ |

**User's choice:** Document the difference — add note explaining both formats.

---

### xdist Worker Behavior (sub-area, user-raised)

| Option | Description | Selected |
|--------|-------------|----------|
| Dispatcher suppresses itself on workers | Check 'workerinput' before delegating; no-op on worker nodes | ✓ |
| Delegate unconditionally | Let each backend handle its own worker suppression | |

**User's choice:** Dispatcher suppresses itself — apply `workerinput` guard in `pytest_configure`.

---

## Agent's Discretion

None — all significant decisions were explicit user choices.

## Deferred Ideas

- Deprecation of existing individual entry points — noted for a future cleanup phase
- Format convergence between Python writer and Node.js formatter — out of scope; formats intentionally differ
