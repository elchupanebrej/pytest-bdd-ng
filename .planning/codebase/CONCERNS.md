---
last_mapped_commit: c59470a9bc50f5ae0f628a572832a5b614d862a7
mapped_at: 2026-05-12
focus: concerns
---

# Codebase Concerns

**Analysis Date:** 2026-05-12

## Tech Debt

**Allure Logger Plugin — Dead/Stub Code:**
- Issue: Entire implementation is commented out in `src/pytest_bdd/plugin/allure_logger/entrypoint.py` (lines 26-39) behind `# TODO: refactor/reimplement Allure plugin`. The `pytest_configure` hook does nothing except check if allure is accessible, then returns. The `plugin.py` (289 lines) has full implementation code that can never be reached because the `entrypoint.py` never registers `AllureLogger`. The plugin entrypoint is registered in `pyproject.toml` at line 87 (`pytest-bdd-allure-logger`) but produces no observable behavior.
- Files: `src/pytest_bdd/plugin/allure_logger/entrypoint.py`, `src/pytest_bdd/plugin/allure_logger/plugin.py`
- Impact: Users who install `pytest-bdd-ng[allure]` get a non-functional plugin. Allure integration is dead code. Deceptive UX.
- Fix approach: Either delete the entire `allure_logger` plugin directory (and the `allure` optional dependency), or re-implement the hook registration in `entrypoint.py` to actually wire up `AllureLogger` and `PatchedAllureListener`.

**Code Generator — Unfinished Refactoring:**
- Issue: `src/pytest_bdd/plugin/code_generator/plugin.py` has two explicit TODOs at lines 64-65: `# TODO: Rework into plugin class` and `# TODO: Use wrapping around other plugins`. The code generator functions exist as standalone module-level functions rather than following the plugin class pattern used by other plugins in the codebase. Additionally, the `_format_code` function at line 86 uses a temporary file + `subprocess.run` to invoke `ruff` for formatting, which is fragile (file I/O races, subprocess overhead).
- Files: `src/pytest_bdd/plugin/code_generator/plugin.py`
- Impact: Inconsistent architecture with rest of plugin system. The `ruff` subprocess formatter adds startup latency and potential tempfile cleanup issues.
- Fix approach: Refactor into a `CodeGeneratorPlugin` class following the pattern of `StructBDDPlugin` or `AllureLogger`. Replace ruff subprocess with `ruff` Python API (`ruff.format_str()`), or use `io.StringIO` instead of tempfile.

**Legacy `--cucumberjson` Option:**
- Issue: `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` line 31 has `# TODO: we don't need legacy support for this option anymore`. The `--cucumberjson` CLI flag is registered as a legacy alias for `--cucumber-json` but has no deprecation warning and no removal plan.
- Files: `src/pytest_bdd/plugin/cucumber_json/entrypoint.py`
- Impact: CLI bloat, maintenance overhead, user confusion between two flag names.
- Fix approach: Add a `DeprecationWarning` when `--cucumberjson` is used. Remove after one major version cycle.

**Struct BDD — Private Loaders:**
- Issue: `src/pytest_bdd/plugin/struct_bdd/parser.py` line 100 has `# TODO: make loaders part of public API`. The `build_loader()` method constructs format-specific loaders (YAML, TOML, JSON, HOCON, HJSON, JSON5) but they are not accessible to external consumers who might want to parse struct BDD documents programmatically.
- Files: `src/pytest_bdd/plugin/struct_bdd/parser.py`
- Impact: Limitation for programmatic users. Cannot reuse format loaders outside the parser flow.
- Fix approach: Expose `build_loader()` as a public classmethod or module-level factory function.

**`return None` Antipattern — 96 Instances:**
- Issue: 96 occurrences of `return None` across the source codebase. The AGENTS.md explicitly states: "Outside pytest hook implementations, returning None is an antipattern; use explicit values or deterministic exceptions instead." While pytest hooks require `return None` for non-participation, many of these returns are in non-hook code paths (e.g., scenario lookups, stash access, model methods) where an explicit exception or sentinel would be clearer.
- Files: Widespread. Highest density in `src/pytest_bdd/model/scenario_run.py` (11 instances), `src/pytest_bdd/feature_locator.py` (6 instances), `src/pytest_bdd/model/message_validation.py` (5 instances).
- Impact: Callers must always check for `None` (or miss the check and get `AttributeError`/`TypeError` downstream). Debugging is harder because `None` silently propagates.
- Fix approach: Gradual refactoring. For lookup failures, raise `LookupError` or return a named sentinel. For "not found/not available" cases, use `Optional` return types consistently with explicit `None` checks at all call sites.

**Broad Exception Catchers — 22 Instances:**
- Issue: 22 uses of `except Exception:` (marked `# noqa: BLE001`) across the source. Some are genuinely intentional (e.g., `parsers.py` line 652 where trying multiple parser backends should gracefully degrade). However, several catch-all handlers silently swallow errors without logging, especially:
  - `src/pytest_bdd/plugin/code_generator/plugin.py` line 116: bare `except Exception: ...` — silently swallows all formatting failures
  - `src/pytest_bdd/collector.py` line 107: `except Exception: # noqa: BLE001 intentional` — swallows all parse failures during collection
  - `src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py` line 160: `except Exception: # noqa: BLE001` — swallows hook catalog read failures
- Files: `src/pytest_bdd/parsers.py`, `src/pytest_bdd/collector.py`, `src/pytest_bdd/plugin/code_generator/plugin.py`, `src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py`, `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`, `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py`, others.
- Impact: Silent failure can mask real bugs. The parsers.py pattern (try multiple parsers, chain exceptions) is sound. Others need at minimum a warning log.
- Fix approach: Replace bare `except Exception:` with specific exception types where possible. Where catch-all is necessary, add `logger.debug()` or `logger.warning()` with `exc_info=True` to preserve traceability.

**Massive File — `scenario_run.py` (1422 lines):**
- Issue: `src/pytest_bdd/model/scenario_run.py` is 1422 lines, well beyond the threshold where a single module becomes difficult to understand and modify. It contains the `Run`, `ScenarioRun`, and `FeatureRuntimeBinding` classes plus their inner state machines, lifecycle management, and stash integration.
- Files: `src/pytest_bdd/model/scenario_run.py`
- Impact: High risk of merge conflicts on multi-developer projects. Hard to locate specific logic. Test failures hard to trace. Coupling between classes.
- Fix approach: Split into separate modules: `src/pytest_bdd/model/run.py` (Run), `src/pytest_bdd/model/scenario_run.py` (ScenarioRun only), `src/pytest_bdd/model/feature_binding.py` (FeatureRuntimeBinding). Move `HookPhase`, `RunStage`, and `LifecycleKind` to a dedicated `enums.py`.

**Other Large Files (>400 lines):**
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` — 823 lines
- `src/pytest_bdd/script/message_capability_governance.py` — 748 lines
- `src/pytest_bdd/model/message_validation.py` — 672 lines
- `src/pytest_bdd/steps.py` — 627 lines
- `src/pytest_bdd/parsers.py` — 598 lines (762 total with wrappers)
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py` — 549 lines
- `src/pytest_bdd/plugin/struct_bdd/model.py` — 498 lines
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` — 473 lines
- `src/pytest_bdd/plugin/code_generator/plugin.py` — 412 lines (518 total)
- Impact: Accumulation of large modules increases onboarding time and defect rate.

## Known Bugs

**`_DUMP_START`/`_DUMP_END` Pattern in `toolz_test.py` — Pickle Security:**
- Symptoms: `src/pytest_bdd/util/toolz_test.py` uses `pickle.loads` (line 41) on data extracted via regex from test stdout. If any test output accidentally contains a specially crafted base64 pickle payload, arbitrary code execution is possible.
- Files: `src/pytest_bdd/util/toolz_test.py`
- Trigger: A test file writes data matching `_pytest_bdd_>>><<<_pytest_bdd_` pattern to stdout. The `collect_dumped_objects()` function picks it up.
- Workaround: This is test-only infrastructure and never runs in production. Low risk for end users but a risk for CI if malicious test output enters the pipeline.

## Security Considerations

**Subprocess with `shell=True` — `npm_resource.py`:**
- Risk: `src/pytest_bdd/util/npm_resource.py` uses `shell=True` in three functions: `get_npm_root()` (line 45), `check_npm()` (line 58), `check_npm_package()` (line 75 — uses f-string with `package_name`). While `package_name` is typically controlled by the library, the `shell=True` pattern is inherently risky and violates bandit rule S602.
- Files: `src/pytest_bdd/util/npm_resource.py`
- Current mitigation: Marked `# noqa:S602 intentional`. The `package_name` in `check_npm_package()` is passed through `f'npm list -g "{package_name}"'`, which means a malicious package name containing shell metacharacters (`; rm -rf /`) would be executed.
- Recommendations: Convert all `subprocess.check_output(..., shell=True)` calls to use list-based arguments without shell. Example: `subprocess.check_output(["npm", "list", "-g", package_name])`.

**Jinja2 Without Autoescape:**
- Risk: `Environment(autoescape=False, keep_trailing_newline=True)` in `src/pytest_bdd/plugin/code_generator/plugin.py` (line 48). If template input ever includes untrusted content, generated Python code could be affected.
- Files: `src/pytest_bdd/plugin/code_generator/plugin.py`
- Current mitigation: Marked `# noqa: S701`. The template generates Python code, not HTML.
- Recommendations: Document clearly why autoescape is not needed for code generation.

**Subprocess Argument Injection in `live_formatter_runtime.py`:**
- Risk: `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` spawns Node.js subprocesses with user-configurable formatter arguments. While these use list-based `subprocess.run()` (marked `# noqa: S603`), the formatter arguments are constructed from configuration values. If an attacker can control configuration (e.g., via a malicious `pyproject.toml` or `tox.ini`), arbitrary commands could be injected.
- Files: `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` (lines 203, 234, 336, 652, 765)
- Current mitigation: The NPM package name and formatter names come from the plugin's own constants, not user input. Low practical risk.
- Recommendations: Add input validation for any user-supplied formatter arguments.

**YAML Loading:**
- Risk: `src/pytest_bdd/plugin/struct_bdd/parser.py` line 112 uses `yaml.load(..., Loader=FullLoader)` from PyYAML. `FullLoader` is safer than the deprecated default loader but still resolves Python tags by default in older PyYAML versions. With PyYAML >= 5.1+, `FullLoader` is equivalent to `UnsafeLoader`.
- Files: `src/pytest_bdd/plugin/struct_bdd/parser.py`
- Current mitigation: Struct BDD YAML files are typically project-internal, not user-uploaded content. Low practical risk.
- Recommendations: Consider switching to `yaml.safe_load()` unless Python object deserialization is explicitly needed. The struct BDD model uses pydantic validation afterward, providing a second defense layer.

## Performance Bottlenecks

**Code Generator — Ruff via Subprocess:**
- Problem: `src/pytest_bdd/plugin/code_generator/plugin.py` function `_format_code()` (line 86) writes generated code to a temp file, runs `ruff format` as a subprocess, then reads the file back. This adds subprocess startup overhead (~50-200ms) on every code generation invocation.
- Files: `src/pytest_bdd/plugin/code_generator/plugin.py`
- Cause: Using `subprocess.run()` with `find_ruff_bin()` instead of the ruff Python API.
- Improvement path: Use `ruff.format_str(code)` directly via the `ruff` Python package (already a dependency, line 72 of `pyproject.toml`). Eliminates subprocess and tempfile I/O.

**Gherkin Go Bridge — Version Check on Every Parse:**
- Problem: `src/pytest_bdd/_gherkin_go/__init__.py` attempts to log the Go parser version on first successful parse via `_log_version()` (line 32). The `gherkin_go_version()` call goes through ctypes FFI, which may have non-trivial overhead. However, this is only done once per process (guarded by `_go_version_logged`), so it's not a hot path concern.
- Files: `src/pytest_bdd/_gherkin_go/__init__.py`

**Large Message Validation — `message_validation.py` (672 lines):**
- Problem: `src/pytest_bdd/model/message_validation.py` performs schema validation and cross-message consistency checks. During large test runs with many scenarios, message validation could become a bottleneck.
- Files: `src/pytest_bdd/model/message_validation.py`
- Cause: JSON schema validation via `jsonschema` is inherently slow compared to structural validation. Cross-message ID lookups use hash-based registries, which is efficient.
- Improvement path: Consider lazy validation (deferred until needed for reporting) or sampling-based validation for large runs.

## Fragile Areas

**`scenario_run.py` — Complex State Machine:**
- Files: `src/pytest_bdd/model/scenario_run.py`
- Why fragile: The `ScenarioRun` class manages a multi-phase lifecycle state machine (`RunStage`) interleaved with pytest hook execution. State transitions are implicit (set via hooks called by pytest, not via explicit transitions). Errors in hook registration, ordering, or cancellation can leave the state machine in an inconsistent state. The `StashBound` base class adds another dimension of complexity (stash read/write timing).
- Safe modification: Always add assertions or logging at state transition points. Write tests that exercise error paths (hook failures, cancellation, partial execution). Use the existing contract tests in `tests/contract/test_hook_lifecycle_non_null_contract.py` as a model.
- Test coverage: Partially covered by `tests/hook/` and `tests/feature/test_run_lifecycle.py`, but edge cases around hook error propagation and concurrent stash access are under-tested.

**`parsers.py` — Parser Cascade with Exception Chaining:**
- Files: `src/pytest_bdd/parsers.py` (lines 648-678)
- Why fragile: The `build_parsers()` method tries four different parsers (string, cucumber_expression, cfparse, re) and chains exceptions. If any parser raises an exception type the code doesn't expect, the exception chain logic (`e.__cause__, e_cause = e_cause, e`) can fail or produce confusing tracebacks. The code has a comment: "Rework to exception groups after python 3.10 end of support".
- Safe modification: This pattern is stable but opaque. Tests must exercise each parser failure independently.
- Test coverage: Individual parser failures may not have dedicated tests. The `# pragma: no cover` on line 678 suggests the `ParserBuildValueError` fallback path is only exercised implicitly.

**`npm_resource.py` — Fragile NPM Detection:**
- Files: `src/pytest_bdd/util/npm_resource.py`
- Why fragile: Uses `subprocess.check_output` with `shell=True` to detect npm availability. If npm is not on PATH, it raises `CalledProcessError`. The `@_check_subprocess` decorator converts this to `False`, but only for `check_npm` and `check_npm_package` — `get_npm_root` can still raise.
- Safe modification: Add a `--no-npm` flag or environment variable to skip npm-dependent features entirely.
- Test coverage: Likely not tested in CI (requires Node.js/npm on the PATH).

## Scaling Limits

**In-Memory Feature Document Map:**
- Current capacity: The 022 feature stores `{Path: GherkinDocument}` in `pytest.config.stash` (in-memory dict). For projects with hundreds of feature files, this grows linearly with total feature document size.
- Limit: Large-scale BDD suites (1000+ feature files, each with many scenarios) could consume hundreds of MB of memory. The current architecture has no paging or lazy-loading mechanism.
- Scaling path: If this becomes a bottleneck, implement lazy parsing with LRU caching in the stash access layer, or parse features on-demand during collection rather than eagerly.

**Subprocess Worker Architecture (xdist):**
- Current capacity: `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py` manages execnet channels for xdist worker communication. Each worker opens a transport channel.
- Limit: The serialization layer (`message_transport.py`, `message_validation.py`) does per-message JSON schema validation. With large numbers of workers and high message volume, this could become a CPU bottleneck.
- Scaling path: Skip detailed validation on worker-to-controller messages in production mode; keep validation only in test/development.

## Dependencies at Risk

**`gherkin-official>=33` — Version Lock:**
- Risk: Pinned minimum version `>=33` in `pyproject.toml` line 58. This dependency wraps the canonical Gherkin parser. The Go gherkin bridge (`src/pytest_bdd/_gherkin_go/`) provides a ctypes alternative, but the Python fallback parser depends on gherkin-official. The version constraint (`>=33`) is forward-looking, but if future versions introduce breaking API changes, the fallback breaks.
- Impact: All parsing falls back to Go parser, which requires a compiled shared library. On platforms without the shared library, parsing fails entirely.
- Migration plan: Maintain the Go parser as the primary backend with thorough platform compatibility testing. Keep the Python fallback for development environments.

**`py` Package (Deprecated):**
- Risk: `src/pytest_bdd/plugin/code_generator/plugin.py` imports `py` (line 13: `import py`). The `py` library has been deprecated in favor of `pathlib` and `pytest`'s own utilities.
- Impact: The `py` package may be removed from future Python or pytest environments.
- Migration plan: Identify and replace all `py` usage with `pathlib` equivalents. Check for other `py` imports across the codebase.

**`pickle` Usage in Test Utilities:**
- Risk: `src/pytest_bdd/util/toolz_test.py` uses `pickle` (imported at line 6 with `# noqa:S403`). This is test-only infrastructure but still represents a vector for pickle-based deserialization attacks if test output is ever intercepted.
- Impact: Only relevant in CI/test environments. Low risk.
- Migration plan: Replace pickle with JSON serialization for test object dumping, or use a safer serialization format like `cbor2` or plain `json` with type hints.

## Missing Critical Features

**No Deprecation Warning System:**
- Problem: Legacy features like `--cucumberjson` lack deprecation warnings. Users have no signal that the option is being phased out.
- Blocks: Clean removal of legacy CLI options.
- Recommendation: Add a consistent deprecation pattern (e.g., `warnings.warn("...", DeprecationWarning)` or `pytest.deprecated_call()`).

## Test Coverage Gaps

**Allure Logger Plugin — Zero Tests:**
- What's not tested: The entire `allure_logger` plugin. `tests/allure_/` directory exists (and is referenced in `pyproject.toml` `test_group_paths` at line 264) but contains no Python test files — only `__pycache__/`.
- Files: `src/pytest_bdd/plugin/allure_logger/entrypoint.py`, `src/pytest_bdd/plugin/allure_logger/plugin.py`
- Risk: Any reactivation of the allure plugin would introduce untested code. The existing plugin code may have rotted and contain bugs.
- Priority: High (if allure support is intended to be maintained); Low (if allure support is being dropped).

**Struct BDD Plugin — Conditional Testing:**
- What's not tested: Struct BDD functionality when `STRUCT_BDD_INSTALLED=False`. All 4 test files in `tests/struct_bdd/` use `pytest.mark.skipif(not STRUCT_BDD_INSTALLED, ...)`.
- Files: `tests/struct_bdd/test_steps.py`, `tests/struct_bdd/test_deserialization.py`, `tests/struct_bdd/test_gherkin_document_model_compat.py`
- Risk: If struct-bdd optional dependencies are not installed, the entire test suite for this plugin is skipped. This means CI must run with struct-bdd installed to get coverage, but that's an optional dependency.
- Priority: Medium.

**`parsers.py` — Parser Build Fallback:**
- What's not tested: The `ParserBuildValueError` raise at line 678 is marked `# pragma: no cover`. This means no test exercises the case where ALL four parsers fail to build.
- Files: `src/pytest_bdd/parsers.py`
- Risk: The error handling for total parser failure is assumed correct but never validated.
- Priority: Low.

**`# pragma: no cover` — 37 Instances:**
- What's not tested: 37 code branches marked `# pragma: no cover` across the source, including `TYPE_CHECKING` blocks, `__name__ == "__main__"` guards, `NotImplementedError` raises in abstract methods, and CLI entrypoint functions.
- Files: See full list in analysis above. Highlights: `src/pytest_bdd/parsers.py` (9 instances), `src/pytest_bdd/scenario_locator.py` (5 instances), `src/pytest_bdd/tag_expression.py` (2 instances).
- Risk: Some `# pragma: no cover` may mask genuinely untested production code (not just `TYPE_CHECKING`/`__main__` guards). Each should be reviewed.
- Priority: Medium.

**Test Group Configuration Drifted:**
- What's not matching: `pyproject.toml` line 264 maps `tests/allure_/** = slow` but that directory has no Python test files. Line 253 lists `test_group_order = ["instant", "fast", "medium", "slow", "external"]` but the `allure_` directory cannot contribute to the `slow` group.
- Files: `pyproject.toml`
- Risk: Test group ordering configuration is misleading. CI may skip a group that has no actual tests, masking configuration drift.
- Priority: Low.

---

*Concerns audit: 2026-05-12*
