# Phase 32: Implement Unbound Feature Detection - Research

**Researched:** 2026-07-09
**Domain:** pytest plugin development, BDD test collection lifecycle
**Confidence:** HIGH

## Summary

This phase adds post-collection detection of `.feature`/`.feature.md` files (plus shortcut formats: `.url`, `.desktop`, `.webloc`) in `features_base_dir` that exist on disk but are NOT bound to any pytest test collection. The detection runs at `pytest_collection_finish` — after all collection is complete, the batch parser is flushed, and the Run model is populated. It scans `features_base_dir` recursively (following symlinks), collects the set of feature files, extracts collected feature URIs from item metafunc params (`gherkin_document.uri`), diffs the two sets, and injects synthetic skip items for any unbound features.

All 15 implementation decisions from CONTEXT.md (D-01 through D-15) are technically feasible. The primary implementation strategy is: a new free function `_detect_unbound_features()` following the established `_validate_zero_match_scenarios` pattern, called from a new `pytest_collection_finish` hook on `ScenarioTestCollectorPlugin`, with config driven by a new `UnboundFeatures` model class in `scenario_collection.py`.

**Primary recommendation:** Implement as a module-level free function in a new `unbound.py` module within `scenario_test_collector/`, following the established pattern of `_validate_zero_match_scenarios`. Gating on xdist worker nodes is critical — detection must only run on the controller node.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use file path set comparison — scan `features_base_dir` for feature files (all collectible formats), extract collected URIs from item metafunc params (`gherkin_document.uri`), diff the two sets.
- **D-02:** Path normalization: compute relative paths from `pytest.rootpath` for comparison. Both the filesystem scan results and extracted item URIs should be normalized to the same relative form.
- **D-03:** Hook: `pytest_collection_finish`. All items are collected, batch parser is flushed, Run model is populated. Access items via `session.items`.
- **D-04:** Extract feature URIs from collected items by inspecting `item.callspec.params` for `gherkin_document.uri`. Covers both `scenarios()`-based collection and autoload-based collection.
- **D-05:** Configurable severity: INI option `bdd_unbound_features = skip|warn|error` with CLI override `--unbound-features=skip|warn|error`.
- **D-06:** Default severity: `skip` — non-breaking, raises awareness without blocking CI.
- **D-07:** Add to `ScenarioCollection` config model (alongside `FeatureAutoLoad`, `FeatureBaseLoad` in `src/pytest_bdd/model/scenario_collection.py`). Follows existing config patterns.
- **D-08:** Tag-based exclusion: feature files containing an `@unbound` tag in their Gherkin are excluded from detection. The exclusion lives in the feature file itself following BDD conventions.
- **D-09:** Synthetic `pytest.Item` subclass (`UnboundFeatureItem`) with `runtest()` that calls `pytest.skip("Feature not bound to any test module")`.
- **D-10:** Nodeid includes relative path from `features_base_dir`: `unbound::features/login.feature.md`. The `FEATURE_DIR` portion provides directory context.
- **D-11:** Parent node: `session`. Items appear at top level, clearly separated from real tests. Simpler than building virtual modules.
- **D-12:** Parse feature files lazily (try/fallback) to include the Feature name in the skip reason for richer output. Fall back to filename-only if parsing fails.
- **D-13:** Scan all collectible formats: `.feature`, `.feature.md`, `.url`, `.desktop`, `.webloc`.
- **D-14:** For shortcut files (`.url`, `.desktop`, `.webloc`): resolve the shortcut to its target URL/path, then check whether the TARGET feature file is collected. The shortcut itself is a pointer — what matters is whether the pointed-to feature is bound.
- **D-15:** Follow symlinks during recursive scan of `features_base_dir`. Users who symlink feature directories expect them to be treated as if the files were physically there.

### the agent's Discretion
- The planner decides the exact `UnboundFeatureItem` class location and module name.
- The planner decides the exact implementation approach for the shortcut file resolution during scan (reuse existing `FeatureFileModule` static methods or write new resolution logic).
- The planner decides whether to implement lazy parsing via the existing Gherkin parser infrastructure or a lightweight regex-based extraction for the feature name.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Feature file scanning | API / Backend | — | Filesystem I/O at `pytest_collection_finish` time |
| URI extraction from items | API / Backend | — | Reads `item.callspec.params` populated during collection |
| Set comparison & diff | API / Backend | — | Pure in-memory computation |
| Config option parsing | API / Backend | — | CLI/INI config read via pytest config API |
| Skip item injection | API / Backend | — | Modifies `session.items` in plugin hook |
| `@unbound` tag detection | API / Backend | — | File read + regex during scan |
| Shortcut file resolution | API / Backend | — | Delegates to existing `FeatureFileModule` static methods |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0.0 (existing) | Test runner; `pytest_collection_finish` hook | Already project dependency; hook is built-in |
| pathlib (stdlib) | — | Filesystem scanning, path normalization | Standard library, no dependency needed |
| `pytest_bdd.mimetype` | existing | `gherkin_suffixes`, `link_suffixes` for file type detection | Already canonically defined; single source of truth |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `re` (stdlib) | — | Regex-based `@unbound` tag and Feature name extraction | Lightweight alternative to full Gherkin parse for tag/name detection |
| `pytest_bdd.parser.GherkinParser` | existing | Full Gherkin parse for feature name extraction (if regex insufficient) | Planners' discretion per D-12 |
| `pytest_bdd.collector.FeatureFileModule` | existing | Shortcut resolution static methods | For D-14 shortcut-to-target resolution |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `re` for @unbound tag detection | Full `GherkinParser` parse | Parser is more correct but heavier; `@unbound` is a simple tag pattern — regex is sufficient and avoids importing parser machinery in a post-collection hook |
| `re` for Feature name extraction | Full `GherkinParser` parse | Parser handles all Gherkin edge cases; regex `Feature:\s*(.+)$` covers 99% of real-world feature files |

**Installation:**
```bash
# No new dependencies — all functionality uses existing stdlib + pytest-bdd internals
```

**Version verification:** Not applicable — no external packages required beyond existing project dependencies.

## Package Legitimacy Audit

> No external packages are installed for this phase. All functionality uses stdlib (`pathlib`, `re`) and existing `pytest-bdd` internals (`mimetype`, `collector`, `model`, `parser`).

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    pytest collection lifecycle               │
│                                                             │
│  pytest_collect_file → FeatureFileModule → scenarios()      │
│       │                         │                           │
│       │                    [items collected]                │
│       │                         │                           │
│       ▼                         ▼                           │
│  pytest_collection_modifyitems  │                           │
│  (_validate_zero_match_         │                           │
│   scenarios)                    │                           │
│       │                         │                           │
│       └─────────────────────────┘                           │
│                    │                                        │
│                    ▼                                        │
│          pytest_collection_finish  ◄── NEW HOOK             │
│                    │                                        │
│    ┌───────────────┼───────────────┐                        │
│    │               │               │                        │
│    ▼               ▼               ▼                        │
│  [1] Scan      [2] Extract    [3] Diff &                   │
│  features_     collected      inject skip                   │
│  base_dir      URIs from      items into                    │
│  for feature   session.items  session.items                 │
│  files                                                        │
│    │                                                        │
│    ├─ Check @unbound tag → exclude                          │
│    ├─ Resolve shortcuts → target URI                        │
│    └─ Normalize paths → "file:relpath"                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. **Scan phase:** `Path(features_base_dir).rglob('*')` → filter by `path.suffixes` matching `gherkin_suffixes ∪ link_suffixes` → for each file: check `@unbound` tag (regex), normalize to `"file:" + relpath(path, features_base_dir).as_posix()` → produce set of `{normalized_uri, ...}`
2. **Extract phase:** iterate `session.items` → `getattr(item, "callspec", None)` → `callspec.params.get("gherkin_document")` → `str(gherkin_document.uri)` → produce set of collected URIs
3. **Diff phase:** `unbound_uris = scanned_set - collected_set` → for each unbound URI: create `UnboundFeatureItem(parent=session)` with `runtest()` calling `pytest.skip()`
4. **Severity dispatch:** `warn` → `pytest.warns()`; `error` → `pytest.fail()`; `skip` (default) → `pytest.skip()`

### Recommended Project Structure
```
src/pytest_bdd/plugin/scenario_test_collector/
├── unbound.py              # NEW: _detect_unbound_features() + UnboundFeatureItem class
├── plugin.py               # MODIFIED: add pytest_collection_finish hook
├── entrypoint.py           # MODIFIED: register --unbound-features CLI/INI options
├── helpers.py              # No changes (or add URI extraction helper)
├── hook.py                 # No changes
src/pytest_bdd/model/
├── scenario_collection.py  # MODIFIED: add UnboundFeatures config class
tests/
├── feature/
│   └── test_unbound_features.py   # NEW: testdir-based integration tests
├── unit/
│   └── test_unbound_features.py   # NEW: unit tests for detection logic
```

### Pattern 1: Config Model (UnboundFeatures)
**What:** Namespaced config constants for CLI and INI options, following `FeatureAutoLoad`/`FeatureBaseLoad`/`EmptyScenarios` pattern.
**When to use:** Every new configurable option in the scenario_test_collector plugin.
**Example:**
```python
# Source: existing pattern in src/pytest_bdd/model/scenario_collection.py
class UnboundFeatures:
    class Ini(StrEnum):
        SEVERITY_OPTION = "bdd_unbound_features"

    class Cli(StrEnum):
        SEVERITY_OPTION = "unbound_features"
```

### Pattern 2: Post-Collection Validation Function
**What:** A module-level free function called from a plugin hook method, following `_validate_zero_match_scenarios` pattern.
**When to use:** Any validation that runs after all items are collected.
**Example:**
```python
# Source: existing pattern in src/pytest_bdd/plugin/scenario_test_collector/plugin.py (lines 671-754)
def _detect_unbound_features(session: Session) -> None:
    """Detect feature files in features_base_dir not bound to any pytest test."""
    # ... detection logic ...
```

### Pattern 3: Synthetic Skip Item
**What:** A `pytest.Item` subclass with `runtest()` that calls `pytest.skip()`, parented to session.
**When to use:** Injecting virtual test items that don't correspond to real test functions.
**Example:**
```python
# Source: existing pattern in tests (test_hooks.py line 119)
class UnboundFeatureItem(pytest.Item):
    def __init__(self, *, name: str, parent, feature_path: str, feature_name: str | None = None):
        super().__init__(name=name, parent=parent)
        self._feature_path = feature_path
        self._feature_name = feature_name

    def runtest(self):
        reason = f"Feature not bound to any test module: {self._feature_name or self._feature_path}"
        pytest.skip(reason)
```

### Pattern 4: Plugin CLI/INI Registration
**What:** Register options via `parser.getgroup().addoption()` for CLI and `parser.addini()` for INI, using config model constants.
**When to use:** Every new pytest option.
**Example:**
```python
# Source: existing pattern in entrypoint.py (lines 146-210)
unbound_hlp = "Action for unbound feature files: skip (default), warn, or error"
group.addoption(
    "--unbound-features",
    action="store",
    dest=str(UnboundFeatures.Cli.SEVERITY_OPTION),
    choices=["skip", "warn", "error"],
    default="skip",
    help=unbound_hlp,
)
parser.addini(
    str(UnboundFeatures.Ini.SEVERITY_OPTION),
    default="skip",
    help=unbound_hlp,
)
```

### Anti-Patterns to Avoid
- **Duplicating URI format logic:** The `"file:" + relpath.as_posix()` format must match between scan and extraction. Do NOT create a separate normalization — use a single helper function.
- **Running detection on xdist workers:** `pytest_collection_finish` fires on every worker node. Gate with `if hasattr(session.config, "workerinput"): return`.
- **Parsing every file with full GherkinParser:** For `@unbound` tag detection, a simple regex scan of the file content is sufficient. Full parse is overkill for tag detection. However, the Feature name extraction may benefit from the parser — planner decides.
- **Blocking on parse failures:** If a feature file can't be parsed (malformed Gherkin), it should still be reported as unbound with filename-only reason. Don't silently skip it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Feature file suffix detection | Custom suffix list | `pytest_bdd.mimetype.gherkin_suffixes ∪ link_suffixes` | Canonical source of truth already used by `pytest_bdd_is_collectible` |
| Shortcut file resolution | Custom `.url`/`.desktop`/`.webloc` parsers | `FeatureFileModule.get_feature_pathlike_from_*_file()` static methods | Already handle all three formats, edge cases, and cross-platform differences |
| Gherkin parsing (if needed) | Custom parser | `pytest_bdd.parser.GherkinParser` or `MarkdownGherkinParser` | Existing parser infrastructure handles encodings, batch caching, error recovery |
| features_base_dir resolution | Custom resolution logic | `ScenarioLocatorBuilder.resolve_features_base_dir` pattern or direct `FeatureBaseLoad` config reads | Must match collection-time resolution to get correct comparison |

**Key insight:** The correctness of this feature hinges on path normalization matching the existing URI format (`"file:" + relpath(path, features_base_dir).as_posix()`). Any discrepancy between scan normalization and collection URI format will produce false positives/negatives.

## Common Pitfalls

### Pitfall 1: URI Format Mismatch
**What goes wrong:** Filesystem scan normalizes paths differently from how collected URIs are formatted, causing false positives (collected features marked as unbound) or false negatives (unbound features not detected).
**Why it happens:** The collected URI format is `"file:" + relpath(feature_path, features_base_dir).as_posix()`. If the scan computes relative to `session.config.rootpath` instead of `features_base_dir`, paths won't match.
**How to avoid:** Resolve `features_base_dir` using the exact same algorithm as `ScenarioLocatorBuilder.resolve_features_base_dir`. Compute relative paths from `features_base_dir`, not `rootpath`. D-02 mentions `rootpath` but only as the base for resolving `features_base_dir` when it's relative — not for computing per-file relative paths.
**Warning signs:** All feature files reported as unbound when some are actually collected. Debug: print collected URIs and scanned paths side by side.

### Pitfall 2: xdist Duplicate Items
**What goes wrong:** In `pytest-xdist` distributed mode, each worker runs `pytest_collection_finish` independently and injects its own skip items, causing duplicate output.
**Why it happens:** `pytest_collection_finish` is a session-scoped hook that fires on every worker node.
**How to avoid:** Add early return at top of detection function: `if hasattr(session.config, "workerinput"): return`. Workers have a `workerinput` attribute; the controller does not.
**Warning signs:** Duplicate "SKIPPED" lines in xdist output for the same feature file.

### Pitfall 3: Non-BDD Items Breaking URI Extraction
**What goes wrong:** `AttributeError` when accessing `item.callspec.params` on non-BDD items (regular pytest test functions).
**Why it happens:** Not all items in `session.items` are BDD scenario items. Some may be regular test functions or items from other plugins.
**How to avoid:** Use defensive access pattern (already established in `_validate_zero_match_scenarios` lines 725-734):
```python
callspec = getattr(item, "callspec", None)
params = getattr(callspec, "params", {})
gherkin_document = params.get("gherkin_document")
if not isinstance(gherkin_document, GherkinDocument):
    continue
```
**Warning signs:** `AttributeError: 'Function' object has no attribute 'callspec'` during collection.

### Pitfall 4: Symlink Loops
**What goes wrong:** Infinite recursion when `features_base_dir` contains symlink cycles.
**Why it happens:** D-15 explicitly requires following symlinks. `Path.rglob` follows symlinks in Python 3.12+.
**How to avoid:** Maintain a `set` of resolved (real) paths and skip already-seen paths:
```python
seen: set[Path] = set()
for p in features_base_dir.rglob("*"):
    real = p.resolve()
    if real in seen:
        continue
    seen.add(real)
```
**Warning signs:** Hangs during collection, infinite loop in scan.

### Pitfall 5: Missing features_base_dir
**What goes wrong:** `FileNotFoundError` if `features_base_dir` doesn't exist.
**Why it happens:** Projects may configure a `features_base_dir` that hasn't been created yet, or the default `"."` resolved against `rootpath`.
**How to avoid:** Check `features_base_dir.is_dir()` before scanning. If not a directory, return early (no files to detect).
**Warning signs:** Crash during `pytest_collection_finish` with `FileNotFoundError`.

### Pitfall 6: Feature name extraction failure masking detection
**What goes wrong:** If lazy parsing for Feature name (`Feature: ...`) fails with an exception, the entire detection might abort.
**Why it happens:** Uncontrolled exceptions in the try/fallback pattern.
**How to avoid:** Wrap the parse attempt in a broad `except Exception` with a logged warning (following STAB-03: use specific exception types or `exc_info=True`). For regex-based approach: fall back to filename-only if regex doesn't match.
**Warning signs:** Some unbound features silently not reported when parsing fails.

## Code Examples

Verified patterns from official sources:

### Extracting Feature URIs from Collected Items
```python
# Source: src/pytest_bdd/plugin/scenario_test_collector/plugin.py lines 725-734
# [VERIFIED: codebase source]
def _extract_collected_feature_uris(items: Sequence[Item]) -> set[str]:
    """Extract the set of feature URIs from collected pytest items."""
    uris: set[str] = set()
    for item in items:
        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", {})
        gherkin_document = params.get("gherkin_document")
        if isinstance(gherkin_document, GherkinDocument):
            uris.add(str(gherkin_document.uri))
    return uris
```

### URI Format (How Collected URIs Are Built)
```python
# Source: src/pytest_bdd/scenario_locator/file_locator.py line 599
# [VERIFIED: codebase source]
# URI format is: "file:" + relative_path.as_posix()
# Where relative_path = Path(relpath(feature_path, features_base_dir))
uri = "file:" + rel_feature_path.as_posix()
```

### Shortcut File Resolution (Reuse Pattern)
```python
# Source: src/pytest_bdd/collector.py lines 564-619
# [VERIFIED: codebase source]
# FeatureFileModule.get_feature_pathlike_from_url_file returns (path, pathType, working_dir)
# FeatureFileModule.get_feature_pathlike_from_desktop_file returns (path, pathType, None)
# FeatureFileModule.get_feature_pathlike_from_weblock_file returns (path, pathType, None)
# All use cls.detect_uri_pathtype() for scheme classification
```

### Scan-Collectible Check Pattern
```python
# Source: src/pytest_bdd/plugin/scenario_test_collector/plugin.py lines 1363-1375
# [VERIFIED: codebase source]
def _is_collectible_feature_file(path: Path) -> bool:
    """Check if a file is a collectible feature file (Gherkin or link shortcut)."""
    from functools import partial
    from operator import contains
    from pytest_bdd.mimetype import gherkin_suffixes, link_suffixes
    return any(
        map(
            partial(contains, gherkin_suffixes.union(link_suffixes)),
            path.suffixes,
        )
    )
```

### Default features_base_dir Resolution
```python
# Source: src/pytest_bdd/feature_locator.py lines 333-386, 557-613
# [VERIFIED: codebase source]
# Build a ScenarioLocatorBuilder and call resolve_features_base_dir(None)
builder = ScenarioLocatorBuilder(config=config)
features_base_dir = builder.resolve_features_base_dir(None)
# Or read directly from config:
# cli_dir = config.getoption("features_base_dir", default=None)
# ini_dir = config.getini("bdd_features_base_dir")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Silently ignored unbound features | Post-collection detection with skip items | Phase 32 (new) | Contributors can see which feature files are not wired into test collection |
| No visibility into orphaned `.feature.md` files | Explicit SKIPPED items in pytest output | Phase 32 (new) | CI pipelines can detect accidentally-unbound features |
| IDE-only unbound detection (via `IdeBindingService.pytest_sessionfinish`) | Dual detection: IDE diagnostics + pytest output | Phase 32 (new) | Both IDE users and CLI/CI users get unbound feedback |

**Deprecated/outdated:**
- None — this is a new capability, not a replacement.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `item.callspec.params["gherkin_document"]` is the correct and only way to extract feature URIs across both `scenarios()` and autoload collection paths | Common Pitfalls #3 | Low — this pattern is already validated in `_validate_zero_match_scenarios` and confirmed in the codebase |
| A2 | `@unbound` tag can be reliably detected with regex `@unbound\b` without full Gherkin parse | D-08 | Low — Gherkin tags follow a simple `@tagname` format on dedicated lines; regex covers all standard cases |
| A3 | `features_base_dir` resolution using `ScenarioLocatorBuilder` matches what the collector uses at collection time | Architecture Patterns | Medium — if autoload uses a different resolution path than `scenarios()`, the scan base could diverge |
| A4 | `hasattr(session.config, "workerinput")` reliably distinguishes xdist controller from workers | Common Pitfalls #2 | Low — this is the standard pytest-xdist worker detection pattern |
| A5 | `Path.rglob('*')` with symlink-loop protection via `seen` set is sufficient for file scanning | Common Pitfalls #4 | Low — this is a standard recursive scan pattern |

## Open Questions (RESOLVED)

1. **Shortcut file handling when target is a URL** — RESOLVED: For URL-type shortcuts, always consider the shortcut "bound" if the target URL resolves successfully during collection. The `.url` file is just a pointer — what matters is whether the pointed-to feature content made it into the collection. If `FeatureFileModule` successfully resolved and collected it, the shortcut is bound. Otherwise (no item found with matching URI), it's unbound.
   - What we know: `FeatureFileModule.get_feature_pathlike_from_url_file` returns `(url, FeaturePathType.URL, working_dir)`. The collected item's `gherkin_document.uri` would be the URL string.
   - Recommendation: Already resolved as stated above.

2. **Interaction with `--collect-only` mode** — RESOLVED: Detection should run regardless. The goal is visibility into which features are bound. `--collect-only` is a natural time to surface this information.
   - What we know: In `--collect-only`, test execution never happens. Skip items would appear in the collected items list.
   - Recommendation: Already resolved as stated above.

3. **Performance impact on large feature directories** — RESOLVED: Use `os.scandir`-based iteration (which `Path.rglob` wraps) for efficiency. The regex `@unbound` check per file adds minimal overhead (single regex on file content). If performance becomes an issue, add a config option to disable detection (`--disable-unbound-detection`).
   - What we know: Scanning with `rglob` and checking each file's `.suffixes` is O(n) in the number of files. For projects with 1000+ feature files, this adds measurable overhead at `pytest_collection_finish`.
   - Recommendation: Already resolved as stated above.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All code | ✓ | (project standard) | — |
| pytest >= 7.0.0 | `pytest_collection_finish` hook | ✓ | (project standard) | — |
| `pathlib` | Filesystem scanning | ✓ | stdlib | — |
| `re` | `@unbound` tag detection | ✓ | stdlib | — |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

*Step 2.6: All dependencies are stdlib or existing project dependencies — no new external tools needed.*

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 7.0.0 (existing) |
| Config file | `pyproject.toml` under `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/feature/test_unbound_features.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AC-01 | Recursive scan of `features_base_dir` for feature files | unit | `pytest tests/unit/test_unbound_features.py -x -k "test_scans_features_base_dir"` | ❌ Wave 0 |
| AC-02 | Compare against collected features after pytest collection | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_compares_against_collected"` | ❌ Wave 0 |
| AC-03 | Unbound features appear as SKIPPED in pytest output | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_unbound_appears_skipped"` | ❌ Wave 0 |
| AC-04 | Skip reason clearly states the feature is not bound | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_skip_reason_clear"` | ❌ Wave 0 |
| AC-05 | No regressions in existing test behavior | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_no_regression"` | ❌ Wave 0 |
| D-05 | Configurable severity (skip/warn/error) | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_severity"` | ❌ Wave 0 |
| D-08 | `@unbound` tag exclusion | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_unbound_tag_exclusion"` | ❌ Wave 0 |
| D-14 | Shortcut file resolution | integration | `pytest tests/feature/test_unbound_features.py -x -k "test_shortcut_resolution"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/feature/test_unbound_features.py tests/unit/test_unbound_features.py -x`
- **Per wave merge:** `uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_unbound_features.py` — unit tests for `_detect_unbound_features`, `_extract_collected_feature_uris`, `_scan_feature_files`, `_resolve_shortcut_target`
- [ ] `tests/feature/test_unbound_features.py` — testdir-based integration tests covering all acceptance criteria
- [ ] `tests/feature/test_unbound_features.py` — `conftest.py` setup for shared fixtures (feature file creation helpers)
- [ ] `tests/unit/test_unbound_features.py` — `test_unbound_config.py` for config model validation

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | File path validation: ensure scanned paths are within `features_base_dir`, prevent path traversal during symlink resolution |
| V6 Cryptography | no | — |

### Known Threat Patterns for pytest plugin post-collection hooks

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via symlinks outside `features_base_dir` | Tampering / Elevation of Privilege | Resolve symlinks with `Path.resolve()` and verify resolved path is still within `features_base_dir` tree before including in results |
| Malformed Gherkin causing parse crashes that hide unbound features | Denial of Service | Wrap parse calls in try/except; fall back to filename-only reporting; never let a parse failure prevent other features from being detected |
| Very large feature file causing regex DoS (if regex used) | Denial of Service | Use bounded regex patterns (no nested quantifiers); `@unbound\b` and `Feature:\s*(.+)$` are safe patterns |
| Config injection via `bdd_unbound_features` INI option | Tampering | Use `choices=["skip", "warn", "error"]` in CLI `addoption()` to restrict valid values |

## Sources

### Primary (HIGH confidence)
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` — `_validate_zero_match_scenarios` (lines 671-754), `pytest_collection_modifyitems` (line 936), `pytest_bdd_is_collectible` (lines 1363-1375), `ScenarioTestCollector` class hierarchy (lines 893-1465) [VERIFIED: codebase source]
- `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` — CLI/INI option registration pattern (lines 146-210) [VERIFIED: codebase source]
- `src/pytest_bdd/plugin/scenario_test_collector/helpers.py` — `_is_feature_autoload_item` (lines 412-460) [VERIFIED: codebase source]
- `src/pytest_bdd/collector.py` — `FeatureFileModule` class (lines 231-721), shortcut resolution methods [VERIFIED: codebase source]
- `src/pytest_bdd/model/scenario_collection.py` — Config model pattern: `FeatureAutoLoad`, `FeatureBaseLoad`, `EmptyScenarios` [VERIFIED: codebase source]
- `src/pytest_bdd/feature_locator.py` — `ScenarioLocatorBuilder.resolve_features_base_dir` (lines 557-613), `default_features_base_dir` (lines 333-386) [VERIFIED: codebase source]
- `src/pytest_bdd/scenario_locator/file_locator.py` — URI format `"file:" + relpath.as_posix()` (line 599) [VERIFIED: codebase source]
- `src/pytest_bdd/mimetype.py` — `gherkin_suffixes`, `link_suffixes`, `Suffix` enum [VERIFIED: codebase source]
- `src/pytest_bdd/types/failure_reasons.py` — `ScenarioRunFailure.FEATURE_NOT_BOUND` (line 159) [VERIFIED: codebase source]
- `.planning/notes/unbound-feature-detection.md` — Design note with problem statement and scope [CITED: planning artifact]
- `.planning/todos/done/implement-unbound-feature-detection.md` — 5 acceptance criteria [CITED: planning artifact]
- `.planning/PROJECT.md` — Project constraints: ruff rules, attrs over dataclass, `__tracebackhide__` convention [CITED: planning artifact]
- `.planning/codebase/TESTING.md` — Test patterns: testdir-based integration tests, factory functions [CITED: planning artifact]

### Secondary (MEDIUM confidence)
- `src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py` — Existing `IdeBindingService.pytest_sessionfinish` unbound detection pattern (lines 657-719) [CITED: codebase source — adjacent mechanism, not directly reused]

### Tertiary (LOW confidence)
- None — all research is from primary codebase sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new external dependencies; all libraries are existing project internals or stdlib
- Architecture: HIGH — pattern directly mirrors `_validate_zero_match_scenarios` with known codebase integration points
- Pitfalls: HIGH — identified from reading source code and understanding the collection lifecycle; xdist gating confirmed as necessary via analysis of hook execution model

**Research date:** 2026-07-09
**Valid until:** 2026-08-09 — stable domain, 30-day validity

## Project Constraints (from AGENTS.md)

Extracted from `./AGENTS.md` and `PROJECT.md`:
- Use `attrs` library over builtin `dataclass`es — but `UnboundFeatureItem` is a `pytest.Item` subclass, not an attrs candidate
- `__tracebackhide__ = True` must be set at module level in all `src/pytest_bdd/` modules (Phase 31)
- Follow repository linting/formatting via `ruff` and pre-commit hooks
- No `return None` antipattern — use explicit values or deterministic exceptions
- Three-file plugin structure (`entrypoint.py` + `hook.py` + `plugin.py`) from ADR-003
- `StashBound` pattern for `pytest.config.stash` access from ADR-002 (not needed for this phase — no new stash access)
