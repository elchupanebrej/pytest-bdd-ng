# Phase 32: Implement Unbound Feature Detection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-09
**Phase:** 32-implement-unbound-feature-detection
**Areas discussed:** Detection mechanism, Severity & configurability, Skip item representation, File types to scan

---

## Detection Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Compare file paths | Scan features_base_dir for feature files, extract URIs from collected item metafunc params, diff the two sets. Simple, reliable. | ✓ |
| Track via Run model | Walk Run.feature_bindings_by_uri which already tracks all parsed features. Compare against filesystem. | |
| Hybrid both | Use Run model for parsed features + filesystem scan for completeness. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Resolve to absolute | Use Path.resolve() on both sides — collected URIs and filesystem scan results. | |
| Use relative from rootpath | Compute relative paths from pytest rootpath. Cleaner output. | ✓ |
| Match by stem/suffix only | Just compare filenames. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Parse from metafunc params | Items parametrized via scenarios() carry 'gherkin_document' with a .uri field. | ✓ |
| Use item.fspath and item.nodeid | Extract from pytest's built-in node attributes. | |
| Track during collection | Add a hook tracking dict during pytest_collection_modifyitems. | |

| Option | Description | Selected |
|--------|-------------|----------|
| In pytest_collection_modifyitems | Same hook that calls _validate_zero_match_scenarios. | |
| In pytest_collection_finish | Runs after collection is complete. Access to session object. | ✓ |
| In conftest.py pytest_configure | Runs before collection. Too early. | |

**User's choice:** Path comparison with relative-from-rootpath normalization, metafunc param extraction, `pytest_collection_finish` hook.

---

## Severity & Configurability

| Option | Description | Selected |
|--------|-------------|----------|
| Always skip | Design note's approach. Non-disruptive. | |
| Configurable skip/warn/error | INI + CLI option. Users get control. | ✓ |
| Always error | Strictest but could be too aggressive. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Tag-based exclusion | Feature files with @unbound tag are excluded. Exclusion in the feature file itself. | ✓ |
| Path-based allowlist | INI config option listing paths/globs. | |
| No exclusions | Design note's original stance. | |

| Option | Description | Selected |
|--------|-------------|----------|
| skip | Non-breaking default. | ✓ |
| warn | Show warnings but don't add skip items. | |
| error | Break by default. | |

| Option | Description | Selected |
|--------|-------------|----------|
| INI option with CLI override | bdd_unbound_features = skip|warn|error. CLI: --unbound-features. | ✓ |
| CLI flag only | Just --unbound-features. | |
| Include --allow-unbound-features | Additional boolean flag to suppress detection. | |

**User's choice:** Configurable severity with INI + CLI, default skip, tag-based exclusion (`@unbound`), config model alongside existing ScenarioCollection options.

---

## Skip Item Representation

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic pytest.Item subclass | Custom UnboundFeatureItem with runtest() calling pytest.skip(). | ✓ |
| pytest.Function with skip body | Build Function node via _pytest.python.Function.from_parent(). | |
| Modify session.items directly | Append plain pytest.Skipped marker items. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Feature path in nodeid | FEATURE_DIR::unbound::features/login.feature.md. Clear, grep-friendly. | ✓ |
| Just feature name | unbound::login.feature.md. Shorter. | |
| Indexed unbound items | unbound-001, unbound-002. Lean but not actionable. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Session | Simple, always available in pytest_collection_finish. | ✓ |
| Virtual module per directory | Nicer organization but more complex. | |
| Inline with collected items | Most contextual but hardest. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Just file path | Faster, simpler, no I/O overhead. | |
| Parse and include Feature name | Richer output but parsing adds latency. | |
| Parse lazily (try/fallback) | Try to parse, fall back to filename. Best UX when possible. | ✓ |

**User's choice:** Synthetic `pytest.Item` subclass, path-based nodeid, session parent, lazy parsing with fallback.

---

## File Types to Scan

| Option | Description | Selected |
|--------|-------------|----------|
| Both .feature and .feature.md | Scan for both Gherkin formats. | |
| Only .feature.md | Design note's original scope. | |
| All collectible formats | .feature, .feature.md, .url, .desktop, .webloc. Full coverage. | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Check if target is collected | Resolve shortcut to target, check if target feature is bound. | ✓ |
| Skip shortcut files entirely | Don't scan shortcuts. | |
| Treat shortcuts as unbound always | Always flag them. Strict but noisy. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Follow symlinks (True) | Standard rglob behavior. | ✓ |
| Don't follow symlinks | Safer against infinite loops. | |

**User's choice:** All collectible formats, shortcut resolution to target, follow symlinks.

---

## the agent's Discretion

- Exact `UnboundFeatureItem` class location and module name
- Implementation approach for shortcut file resolution during scan (reuse existing `FeatureFileModule` methods or new logic)
- Lazy parsing implementation (existing parser infrastructure vs lightweight regex extraction)

## Deferred Ideas

None — discussion stayed within phase scope.
