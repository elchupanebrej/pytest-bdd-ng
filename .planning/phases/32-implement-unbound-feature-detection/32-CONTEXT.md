# Phase 32: Implement Unbound Feature Detection - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Detect `.feature` and `.feature.md` files (plus shortcut formats: `.url`, `.desktop`, `.webloc`) in `features_base_dir` that exist on disk but are NOT bound to any pytest test collection. Report them as `pytest.skipped` items so silently-ignored feature files become visible to contributors.

The detection runs at `pytest_collection_finish` — after all collection is complete, the batch parser is flushed, and the Run model is populated. It scans `features_base_dir` recursively (following symlinks), collects the set of feature files, extracts collected feature URIs from item metafunc params, diffs the sets, and injects synthetic skip items for any unbound features.

</domain>

<decisions>
## Implementation Decisions

### Detection Mechanism
- **D-01:** Use file path set comparison — scan `features_base_dir` for feature files (all collectible formats), extract collected URIs from item metafunc params (`gherkin_document.uri`), diff the two sets.
- **D-02:** Path normalization: compute relative paths from `pytest.rootpath` for comparison. Both the filesystem scan results and extracted item URIs should be normalized to the same relative form.
- **D-03:** Hook: `pytest_collection_finish`. All items are collected, batch parser is flushed, Run model is populated. Access items via `session.items`.
- **D-04:** Extract feature URIs from collected items by inspecting `item.callspec.params` for `gherkin_document.uri`. Covers both `scenarios()`-based collection and autoload-based collection.

### Severity & Configurability
- **D-05:** Configurable severity: INI option `bdd_unbound_features = skip|warn|error` with CLI override `--unbound-features=skip|warn|error`.
- **D-06:** Default severity: `skip` — non-breaking, raises awareness without blocking CI.
- **D-07:** Add to `ScenarioCollection` config model (alongside `FeatureAutoLoad`, `FeatureBaseLoad` in `src/pytest_bdd/model/scenario_collection.py`). Follows existing config patterns.
- **D-08:** Tag-based exclusion: feature files containing an `@unbound` tag in their Gherkin are excluded from detection. The exclusion lives in the feature file itself following BDD conventions.

### Skip Item Representation
- **D-09:** Synthetic `pytest.Item` subclass (`UnboundFeatureItem`) with `runtest()` that calls `pytest.skip("Feature not bound to any test module")`.
- **D-10:** Nodeid includes relative path from `features_base_dir`: `unbound::features/login.feature.md`. The `FEATURE_DIR` portion provides directory context.
- **D-11:** Parent node: `session`. Items appear at top level, clearly separated from real tests. Simpler than building virtual modules.
- **D-12:** Parse feature files lazily (try/fallback) to include the Feature name in the skip reason for richer output. Fall back to filename-only if parsing fails.

### File Types to Scan
- **D-13:** Scan all collectible formats: `.feature`, `.feature.md`, `.url`, `.desktop`, `.webloc`.
- **D-14:** For shortcut files (`.url`, `.desktop`, `.webloc`): resolve the shortcut to its target URL/path, then check whether the TARGET feature file is collected. The shortcut itself is a pointer — what matters is whether the pointed-to feature is bound.
- **D-15:** Follow symlinks during recursive scan of `features_base_dir`. Users who symlink feature directories expect them to be treated as if the files were physically there.

### the agent's Discretion
- The planner decides the exact `UnboundFeatureItem` class location and module name.
- The planner decides the exact implementation approach for the shortcut file resolution during scan (reuse existing `FeatureFileModule` static methods or write new resolution logic).
- The planner decides whether to implement lazy parsing via the existing Gherkin parser infrastructure or a lightweight regex-based extraction for the feature name.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements & Design
- `.planning/notes/unbound-feature-detection.md` — Design note with problem statement, detection timing, scope, and reporting approach. **Originating design document.**
- `.planning/todos/done/implement-unbound-feature-detection.md` — Todo item with 5 acceptance criteria for the phase.

### Feature Collection & Autoload
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` — `ScenarioTestCollector` plugin: `pytest_collection_modifyitems` (line 936), `_validate_zero_match_scenarios` (line 671), `pytest_collection_finish` hook where detection should integrate.
- `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` — Plugin entry: CLI/INI option registration pattern to follow for new `--unbound-features` flag.
- `src/pytest_bdd/plugin/scenario_test_collector/helpers.py` — `_is_feature_autoload_item` (line 412) — used to distinguish autoload items from explicit `scenarios()` items.
- `src/pytest_bdd/collector.py` — `FeatureFileModule` (line 231): virtual module synthesis from `.feature` files; shortcut resolution methods (`get_feature_pathlike_from_url_file`, `_from_desktop_file`, `_from_weblock_file`).
- `src/pytest_bdd/model/scenario_collection.py` — `FeatureBaseLoad`, `FeatureAutoLoad` config models; pattern to follow for new `UnboundFeatures` config model.
- `src/pytest_bdd/feature_locator.py` — `ScenarioLocatorBuilder.resolve_features_base_dir` (line 557): how `features_base_dir` is resolved from config.

### Existing Adjacent Mechanisms
- `src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py` — `IdeBindingService.pytest_sessionfinish` (line 657): emits `unbound-scenario` diagnostics for zero-hookup pickles in the Run model. Reference for existing unbound detection pattern.
- `src/pytest_bdd/types/failure_reasons.py` — `ScenarioRunFailure.FEATURE_NOT_BOUND` (line 159): existing enum value for feature-not-bound failures.

### Project Conventions
- `.planning/PROJECT.md` — Project constraints: ruff rules, attrs over dataclass, StashBound pattern, code style.
- `.planning/codebase/TESTING.md` — Test patterns: `testdir`-based integration tests, factory functions for model objects, pytest marker conventions.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScenarioTestCollector.pytest_collection_modifyitems` already calls `_validate_zero_match_scenarios(config, items)` at line 981. Same hook structure can be extended or mirrored in a new `pytest_collection_finish` method.
- `FeatureFileModule.get_feature_pathlike_from_*_file` static methods resolve shortcut files to target URLs. These or their underlying logic can be reused for shortcut resolution during the filesystem scan.
- `ScenarioLocatorBuilder.default_features_base_dir` (line 334) and `resolve_features_base_dir` (line 557) already resolve `features_base_dir` from config — reuse the same resolution path.
- `_is_feature_autoload_item` in `helpers.py` distinguishes autoload-collected items from explicit `scenarios()` items.
- `FeatureBaseLoad` config model in `model/scenario_collection.py` provides the pattern for adding new INI/CLI options.

### Established Patterns
- Plugin option registration: `entrypoint.py` uses `parser.addini()` for INI options and `parser.getgroup().addoption()` for CLI flags. New `--unbound-features` / `bdd_unbound_features` should follow this pattern.
- `ScenarioCollection` namespace pattern: config constants as nested classes (`Cli`, `Ini`) in `model/scenario_collection.py`.
- Post-collection validation: `_validate_zero_match_scenarios` is a module-level free function called from the plugin's hook method. The unbound detection should follow this same pattern — a separate function called from `pytest_collection_finish`.
- Item creation pattern: `FeatureFileModule` builds virtual modules via `importlib.machinery.ModuleSpec` and `module_from_spec`. The `UnboundFeatureItem` is simpler — a direct `pytest.Item` subclass.

### Integration Points
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` — Add a `pytest_collection_finish` hook method that calls the unbound detection function. This is the primary integration point.
- `src/pytest_bdd/model/scenario_collection.py` — Add `UnboundFeatures` config model class (following `FeatureAutoLoad`/`FeatureBaseLoad` pattern) defining INI option name, CLI flag, and default value.
- `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` — Register the `--unbound-features` CLI option and `bdd_unbound_features` INI option.
- `features_base_dir` resolution — reuse `ScenarioLocatorBuilder` resolution or the `FeatureBaseLoad` config accessors.
</code_context>

<specifics>
## Specific Ideas

### Acceptance Criteria (from todo)
1. Recursive scan of `features_base_dir` for feature files (all collectible formats)
2. Compare against collected features after pytest collection
3. Unbound features appear as `SKIPPED` in pytest output
4. Skip reason clearly states the feature is not bound
5. No regressions in existing test behavior

### User-Specified Behavior
- `@unbound` tag in a feature file marks it as intentionally unbound — excluded from detection
- Lazy parsing of feature files to include the Feature name in skip output when possible
- Shortcut files resolved to their targets before checking collection status
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 32-implement-unbound-feature-detection*
*Context gathered: 2026-07-09*
