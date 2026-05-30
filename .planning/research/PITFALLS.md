# Pitfalls Research

**Domain:** Python BDD testing library (pytest plugin)
**Researched:** 2026-05-12
**Confidence:** MEDIUM (derived from issue trackers, codebase analysis, and ecosystem patterns; some findings from WebSearch only)

## Critical Pitfalls

### Pitfall 1: Silent Execution When No Steps Match

**What goes wrong:**
A scenario whose steps all start with an undefined keyword (or whose step definitions are all missing) passes silently without executing any actual test logic. Users get false confidence — green build, but nothing was tested. The pytest-bdd original had exactly this bug: scenarios starting with "And" silently passed (#403).

**Why it happens:**
BDD frameworks treat step-to-function binding as a separate lifecycle from test assertion. When the binding layer returns "no match" without propagating an error, the framework reports "scenario passed" because no assertion failed. This is especially insidious when step matching is dynamically resolved at test time rather than validated at collection time.

**How to avoid:**
- Validate step binding at **collection time**, not execution time. A scenario with zero matched steps should be an error, not a pass.
- Never let a `StepMatchResult` with `matched=False` propagate without an explicit failure signal.
- Add a pre-execution assertion: if `len(matched_steps) == 0`, raise `pytest.UsageError` or mark the test as `xfail("no step definitions found")`.
- The `steps.py` step manager must distinguish "no steps registered at all" from "specific step not found but others exist."

**Warning signs:**
- Any issue report where "tests pass but they shouldn't"
- `return None` in the step-matching hot path (96 instances exist in this codebase)
- Scenarios that have zero step definitions registered but appear in test output as `PASSED`

**Phase to address:**
STAB-02 phase. Eliminating `return None` in the step-matching path directly prevents this class of bug. Also TEST-03 for edge-case coverage.

---

### Pitfall 2: Breaking Step Matching Semantics During Refactoring

**What goes wrong:**
When cleaning up code (splitting modules, extracting classes, renaming), the step matching priority order changes. A "specific" step that previously overrode a "generic" step no longer does. Tests silently pass with the wrong step definition — no error, just wrong behavior. This killed pytest-bdd 6.0.0 (#542): reusable step functions regression broke the override chain.

**Why it happens:**
Step matching relies on an implicit priority order: more-specific steps should match before less-specific ones. When refactoring splits step manager logic across modules, that ordering can be lost if priority is determined by import order, registration order, or hash ordering rather than an explicit priority value.

**How to avoid:**
- **Never** rely on import order for step priority. Use explicit priority values or deterministic ordering rules.
- Add contract tests that verify: "given a specific step `@given('I have 3 apples')` and a generic step `@given(re.compile(r'I have \d+ apples'))`, the specific step matches first."
- After any refactoring of `steps.py` (627 lines), run the full test suite including `tests/feature/` integration tests.
- Maintain the 7 parser types' priority ordering as an explicit testable list, not as incidental implementation detail.

**Warning signs:**
- Code review where `steps.py` is split or step registration moves between modules
- Any change to how the step registry stores/orders step definitions
- Test failures where the wrong step implementation is called (not missing — wrong)

**Phase to address:**
REF-02 (code generator refactor) and REF-03 (large file reduction). `steps.py` at 627 lines is a refactoring target — any split MUST include step priority contract tests.

---

### Pitfall 3: Monolithic Module Splits That Break Implicit State Coupling

**What goes wrong:**
A 1422-line module (`scenario_run.py`) is split into separate `run.py`, `scenario_run.py`, and `feature_binding.py`. The split compiles, tests pass locally, but in production with xdist distributed execution, the state machine breaks because `ScenarioRun` and `FeatureRuntimeBinding` shared implicit state via the `StashBound` base class that wasn't explicitly passed post-split.

**Why it happens:**
Large modules accumulate implicit coupling: private methods access instance variables that were set by "distant" methods, circular-ish attribute access, `StashBound.find_in_stash()` patterns that assume co-location. When you split, the coupling becomes cross-module and breaks silently — no import error, just wrong runtime behavior.

pytest-bdd-ng's `scenario_run.py` is particularly dangerous because it combines:
1. State machine transitions (RunStage enum: idle → setup → running → step → teardown → finished)
2. pytest hook lifecycle callbacks (hook phases interleave with state transitions)
3. Stash read/write access (shared mutable state via pytest.config.stash)
4. Cucumber Messages protocol serialization

**How to avoid:**
- **Before splitting**, write characterization tests that capture current behavior of state transitions. Test every state in the RunStage enum.
- Define explicit interfaces between the split modules. The `Run`, `ScenarioRun`, and `FeatureRuntimeBinding` classes should communicate through well-defined method calls, not through stash side effects.
- Move enums (`HookPhase`, `RunStage`, `LifecycleKind`, `RunStatus`) to a dedicated `enums.py` **first** — this is safe and reduces the split's surface area.
- Add assertions or logging at every state transition point during the split. If `ScenarioRun` enters `step_running` without first entering `scenario_running`, detect it.
- Keep the stash key constants centralized in one place; never duplicate stash key string literals across modules.

**Warning signs:**
- Any `StashBound.from_stash()` call in one module that reads state set by another module
- State machine transitions triggered by pytest hooks (implicit transitions, not explicit method calls)
- Cross-module `return None` (indicates "I don't know the state but won't tell you")

**Phase to address:**
REF-01 (split scenario_run.py). This is the highest-risk refactoring. Do it first in the refactoring phase, before other large file reductions, to maximize time for stabilization.

---

### Pitfall 4: Dead Plugin Code That Deceives Users

**What goes wrong:**
A plugin is registered in `pyproject.toml` (`pytest-bdd-allure-logger`) and has an optional dependency (`[allure]` extra), but its `entrypoint.py` has all implementation commented out behind `# TODO: refactor/reimplement`. Users install the dependency, see the plugin registered, but get zero functionality. There's no error, no warning — just nothing happens. This is the exact state of the Allure logger plugin in this codebase.

**Why it happens:**
Feature development rushed for a release, then deprioritized. The plugin was stubbed out but never removed from the registration list. Over time, maintainers forget it's dead, and users discover it by installing the `[allure]` extra and getting no Allure reports.

**How to avoid:**
- **Remove dead plugins from `pyproject.toml` entry points immediately.** A non-functional plugin is worse than no plugin.
- If reimplementation is planned, leave the plugin directory but remove it from `pyproject.toml` `[project.entry-points."pytest11"]` until it's functional. Add a README or TODO file in the plugin directory.
- Add an audit step to every release: for each registered `pytest11` entry point, verify the plugin's `pytest_configure` or equivalent hook actually does something observable.
- The `tests/allure_/` directory exists but has zero test files — this is a second indicator of dead code. Either add tests or remove the directory.

**Warning signs:**
- Commented-out code in `entrypoint.py` (check: lines 26-39 are entirely commented)
- Plugin directories with `plugin.py` (289 lines of logic) but `entrypoint.py` that never instantiates the class
- `__pycache__/` directories in test directories with no corresponding `.py` files
- TODOs older than 6 months referencing "refactor/reimplement"

**Phase to address:**
STAB-01 (first stabilization phase). Remove or reimplement before any refactoring work begins.

---

### Pitfall 5: Broad Exception Handlers That Mask Real Failures

**What goes wrong:**
A `except Exception:` catch-all swallows a new error type introduced by a dependency upgrade. The error propagates nowhere, no log is written, and the system degrades silently. Users report "feature X stopped working" with no actionable traceback. This codebase has 22 bare `except Exception:` clauses, some marked `# noqa: BLE001 intentional`, including one in `collector.py` that swallows ALL parse failures during collection.

**Why it happens:**
During rapid feature development, catch-all handlers are added to prevent "annoying" tracebacks from breaking collection or execution. The reasoning: "If parsing fails, just skip that file and continue." But when parsing fails for a NEW reason (not the expected "invalid feature file"), that failure is invisible.

**Prevalence in this codebase:**

| Location | Risk | What it swallows |
|----------|------|-----------------|
| `collector.py:107` | **CRITICAL** | All feature file parse failures during collection |
| `code_generator/plugin.py:116` | HIGH | All ruff formatting failures |
| `hook_catalog_runtime.py:160` | MEDIUM | Hook catalog read failures |
| `gherkin_message_reporter/transport_runtime.py` | MEDIUM | Transport failures during live reporting |
| `util/url.py:24` | LOW | URL availability check |
| `parsers.py:652-672` (4 instances) | **ACCEPTABLE** | Parser cascade with explicit exception chaining |

**How to avoid:**
- Classify each bare except: **acceptable** (parser cascade with chaining), **needs logging** (transport/hook failures), or **must be specific** (collection failures).
- For "needs logging" cases: add `logger.warning("...", exc_info=True)` before the `pass` or `continue`.
- For "must be specific" cases (`collector.py:107`): catch `ParserError`, `OSError`, `UnicodeDecodeError` explicitly. Any other exception type should propagate.
- Add a ruff rule to flag new `except Exception:` unless accompanied by a specific `# noqa: BLE001` comment that explains WHY the catch-all is necessary.

**Warning signs:**
- `# noqa: BLE001` without a comment explaining WHY
- Any `except Exception:` followed by `pass` or `...` (three of these exist: `code_generator/plugin.py:117`, etc.)
- New bare excepts added during refactoring (refactoring should REDUCE, not increase)

**Phase to address:**
STAB-03 phase. This is the third stabilization priority after dead plugin removal and return-None elimination.

---

### Pitfall 6: `return None` Antipattern Propagation During Refactoring

**What goes wrong:**
When refactoring (splitting modules, extracting functions), developers copy the existing `return None` pattern because "that's how the codebase works." The 96 existing instances become 150. The refactoring effort that was supposed to clean up the codebase instead entrenches the antipattern.

**Why it happens:**
- Developers see `return None` in adjacent code and assume it's the project convention
- Functions that should raise exceptions (or return sentinels) instead return None because "the caller checks for it"
- `StashBound.find_in_stash()` returns `None` when not found, and every caller must handle it — creating cascading None checks

**How to avoid:**
- **Do not add new `return None` in non-hook code.** This must be enforced in code review.
- For stash access: use `StashBound.from_stash()` (raises on missing) or `find_in_stash()` (returns Optional). Document the contract.
- For lookups that can fail: raise `LookupError`, `KeyError`, or return a named sentinel like `MISSING = object()`.
- Convert the most-used "not found" returns to explicit exceptions in the Stabilization phase BEFORE large refactoring begins. This prevents copying the old pattern.

**Priority by density:**
1. `scenario_run.py` (11 instances) — highest impact, block before REF-01
2. `feature_locator.py` (6 instances) — medium, handle during SIM-01
3. `message_validation.py` (5 instances) — medium, handle during SIM-01

**Warning signs:**
- Code review: "this returns None like the surrounding code" — REJECT
- New functions with `-> None` return type that could fail (lookups, parses, builds)
- `Optional[X]` return types that never return `None` but also never document when they do

**Phase to address:**
STAB-02 phase (must complete before any REF phase). This is a gate: no refactoring of modules with active `return None` patterns until those patterns are resolved.

---

### Pitfall 7: Gherkin Parser Edge Cases Accumulating During Stabilization

**What goes wrong:**
During stabilization, parser code is cleaned up (renamed, restructured, simplified), but corner cases are accidentally removed or broken: escaped pipe characters in Scenario Outlines (#333), datatable parsing with examples (#741), step definitions with "/" characters (#655). Users discover these regressions months later because edge case test coverage is thin.

**Why it happens:**
The Gherkin parser (and its Python fallback via `gherkin-official`) handles dozens of edge cases accumulated over years of Cucumber specification work. When cleaning up "verbose" or "ugly" parser code, developers remove what looks like redundant logic but was actually handling a spec edge case. The existing tests pass because they test the happy path.

**How to avoid:**
- **Do not modify parser logic during a stabilization phase.** Stabilization should focus on structure (splitting modules, removing dead code, fixing antipatterns), not on changing parsing behavior.
- If parser changes are unavoidable, run the full Cucumber Messages test suite (`tests/messages/` and `tests/messages_coverage/`) AND add at least one test for each Gherkin keyword edge case (pipe characters, table escaping, docstrings, comments in tables, Unicode in examples).
- The `parsers.py` cascade logic (lines 648-678) with exception chaining is known fragile — do not touch this code during stabilization. The `# pragma: no cover` on line 678 means the total-failure fallback is untested. **Fix that test gap before modifying the cascade.**

**Warning signs:**
- Any diff touching `src/pytest_bdd/parsers.py` or `src/pytest_bdd/collector_batch.py`
- Changes to how `GherkinParser` or `MarkdownGherkinParser` interact with `gherkin-official`
- PR descriptions that say "simplified parser logic" or "removed unused parser code"

**Phase to address:**
None — parser behavior changes are OUT OF SCOPE for stabilization. Add test coverage gaps (TEST-03) without changing behavior.

---

### Pitfall 8: Missing Deprecation Path for Legacy Features

**What goes wrong:**
Legacy features (`--cucumberjson`, old step matching APIs, deprecated plugins) are removed without a deprecation cycle. Users who depend on these features get hard failures on upgrade with no migration path. The pytest-bdd original had this with the 6.0.0 release — breaking step aliases without warning (#528).

**Why it happens:**
Stabilization phases create pressure to "clean house." Maintainers see legacy code and remove it because it's "obviously" deprecated. But "obvious to maintainers" ≠ "obvious to users who haven't read the changelog."

**How to avoid:**
- **Every removal must be preceded by a `DeprecationWarning` in the previous release.** This rule is inviolable.
- Add `warnings.warn("--cucumberjson is deprecated, use --cucumber-json instead", DeprecationWarning)` when the legacy flag is used (STAB-04).
- Maintain a `DEPRECATIONS.md` file (or section in CHANGELOG) that lists all deprecated features, the version they were deprecated in, and the version they will be removed in.
- For this stabilization phase: ADD deprecation warnings, do NOT remove features. Removal happens in the NEXT major version.

**Warning signs:**
- PRs that remove a CLI flag, function, or plugin without adding a deprecation warning
- "We don't need legacy support for this option anymore" (literal comment in `cucumber_json/entrypoint.py:31`)
- Code removal that deletes more than 50 lines without a deprecation decorator or warning

**Phase to address:**
STAB-04 phase. Add deprecation warnings for `--cucumberjson`. Audit all CLI flags and public APIs for undocumented legacy paths.

---

### Pitfall 9: Inconsistent Plugin Patterns Causing Maintenance Burden

**What goes wrong:**
Plugins follow different architectural patterns within the same codebase. New contributors don't know which pattern to follow. Bug fixes in one plugin don't translate to similar fixes in others. The code generator plugin (`code_generator/plugin.py`) uses standalone functions and a `ruff` subprocess, while Struct BDD uses a plugin class pattern. This inconsistency is a recognized TODO (#64-65 in `code_generator/plugin.py`).

**Why it happens:**
Plugins were developed at different times by different contributors. Some were ported from the original pytest-bdd (which used function-based hooks). Others were built new with class-based patterns. Over time, the inconsistency became "how it is."

**How to avoid:**
- **Define the canonical plugin pattern** before refactoring plugins. Choose ONE pattern: class-based with `StashBound` inheritance (recommended, matches `StructBDDPlugin`, `PickleRunnerPlugin`) or function-based with explicit state passing.
- Document the pattern in `DEVELOPMENT.rst` so new contributors can follow it.
- Convert `code_generator` to the class-based pattern (REF-02) as the reference implementation.
- Add a linting rule or checklist item: "New plugins must follow the canonical pattern."

**Warning signs:**
- Mixed `@pytest.hookimpl` decorators on module-level functions vs instance methods
- Some plugins using `StashBound`, others accessing `config.stash` directly
- TODOs referencing "Rework into plugin class" (currently 2 in code_generator)

**Phase to address:**
REF-02 (code generator refactor into class-based pattern). This should happen before SIM-02 (unify programming approaches).

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `return None` on lookup failure | Avoids exception handling at call site | Silent None propagation, `AttributeError` 5 stack frames later | Pytest hook implementations only (protocol requires None for non-participation) |
| `except Exception: pass` | Prevents collection/execution crashes | Masks real bugs; users report "suddenly stopped working" | Only with `logger.warning(..., exc_info=True)` AND comment explaining why specific types can't be caught |
| Subprocess `shell=True` for npm | Works on all npm installations | Command injection if `package_name` contains metacharacters | Never. Use list-based `subprocess.run()` |
| `pickle` for test data serialization | Easy object dumping in tests | Arbitrary code execution if test output is intercepted | Never in CI-accessible code. Use JSON or cbor2 |
| Jinja2 `autoescape=False` | Simpler template syntax | XSS if template input includes untrusted content | Only for non-HTML output (Python/RST) with explicit safe annotations |
| Eager in-memory parsing of all features | Simple architecture | O(n) memory growth with feature count; breaks at 1000+ features | Projects with <100 feature files |
| `# pragma: no cover` on error paths | Cleaner coverage reports | Untested error handling; fails in production under edge cases | Only for `TYPE_CHECKING`, `NotImplementedError`, and `__name__ == "__main__"` |
| Implicit state via pytest.config.stash | Avoids parameter plumbing | Tight coupling, hard to test, state machine desync | Only for cross-plugin communication that can't go through pytest fixtures |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| cucumber-messages protocol | Assuming message field ordering is stable | Deserialize by field name, not position. Validate against schema. |
| gherkin-official (Python parser) | Not testing both Go and Python parser backends | Run CI matrix: one job with `PYTEST_BDD_GO_PARSER=1`, one without. The fallback parser must work. |
| pytest-xdist (distributed) | Assuming shared in-memory state across workers | All cross-worker state must go through `execnet` channels or pytest.config.stash. Never assume a `dict` set in worker 1 is visible in worker 2. |
| ruff (code formatting) | Using subprocess.invoke() instead of Python API | Use `ruff.format_str(code)` directly. The `ruff` package is already a dependency. |
| npm/Node.js (live reporter) | Using `shell=True` with f-strings for npm | Use list-based args: `subprocess.run(["npm", "list", "-g", package_name])`. Validate package_name against a whitelist. |
| PyYAML (struct BDD) | Using `yaml.load(..., Loader=FullLoader)` | Use `yaml.safe_load()` unless Python object tags are explicitly needed. The struct BDD pydantic validation provides a second defense layer but isn't a substitute. |
| Allure (reporting) | Registering a plugin that does nothing | Remove non-functional plugins from `pyproject.toml` entry points. Dead plugins are worse than absent plugins. |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Eager feature document map in stash | Memory grows linearly with feature count; `{Path: GherkinDocument}` dict in config.stash | Lazy parsing with LRU cache; parse features on-demand during collection | ~500+ feature files |
| Per-message JSON schema validation | Slow test collection and execution with large suites | Skip detailed validation in production/test mode; keep only in CI/dev | ~1000+ scenarios |
| Subprocess per code generation | 50-200ms overhead per file when generating step stubs | Use `ruff.format_str()` Python API (ruff already a dependency) | Any code generation invocation |
| ctypes version check on every parse | Go parser bridge calls `gherkin_go_version()` via ctypes FFI | Already mitigated: guarded by `_go_version_logged` flag (once per process) | N/A (already fixed) |
| Message validation for every envelope | CPU bottleneck on worker-to-controller communication with many xdist workers | Lazy validation; validate only on the reporting/consumption side | ~20+ xdist workers |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| `subprocess.run(..., shell=True)` with user-supplied `package_name` in f-string (npm_resource.py) | Command injection if package_name contains shell metacharacters (`; rm -rf /`) | Use list-based args. Whitelist package names against a known set or validate with regex `^[a-zA-Z0-9_\-@/]+$` |
| `pickle.loads()` on regex-extracted test stdout (toolz_test.py) | Arbitrary code execution if a crafted payload appears in test output | Replace with JSON serialization. If pickle must be used, add HMAC signature verification |
| `yaml.load(..., Loader=FullLoader)` in struct BDD parser | Python object deserialization from YAML files | Switch to `yaml.safe_load()`. FullLoader resolves Python tags in older PyYAML |
| `Environment(autoescape=False)` in Jinja2 templates (code generator, bdd_tree_to_rst) | HTML injection if template input includes untrusted feature file content | Use `autoescape=True`. For RST output (which can embed raw HTML), this is particularly important |
| No input validation on formatter arguments (live_formatter_runtime.py) | If attacker controls `pyproject.toml`, arbitrary Node.js arguments could be injected | Validate formatter names against whitelist. Add input sanitization for all user-supplied arguments |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent scenario pass on undefined steps (Pitfall 1 variant) | User thinks tests cover behavior; production bug goes undetected | Mark scenarios with zero step matches as `FAILED` or `ERROR`, never `PASSED` |
| Legacy CLI flag without deprecation warning | User upgrades library, flag disappears, CI pipeline breaks with no warning | `DeprecationWarning` for one major version before removal |
| Plugin installed but does nothing | User installs `[allure]` extra, gets no Allure reports, assumes library is buggy | Remove non-functional plugins from entry points. A missing plugin is better than a dead one |
| Confusing error messages from broad exception handlers | User gets generic "something went wrong" instead of actionable "feature file X has invalid syntax at line Y" | Specific exception types with helpful messages; wrap only at the outermost layer |
| Inconsistent step matching priorities across parser types | Same step text matches different implementations depending on parser backend | Document priority order. Add `--verbose` output showing which parser matched which step |
| No migration guide from original pytest-bdd | Users migrating from pytest-bdd hit breaking changes (aliases, step matching) with no guidance | DOC-03: Migration guide before any breaking change release |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Allure plugin tests:** `tests/allure_/` directory exists with `__pycache__/` but zero test files. Either add tests or remove the directory.
- [ ] **Parser total-failure fallback:** `ParserBuildValueError` at `parsers.py:678` is marked `# pragma: no cover`. No test exercises the case where ALL four parsers fail.
- [ ] **RST script CLI:** `bdd_tree_to_rst.py` `main()` function (lines 531-567) marked `# pragma: no cover`. CLI entrypoint is untested.
- [ ] **Test group configuration:** `pyproject.toml` maps `tests/allure_/** = slow` but no Python test files exist there. Test group ordering is misleading.
- [ ] **Deprecation warnings:** No `DeprecationWarning` in `cucumber_json/entrypoint.py` for `--cucumberjson`. Users have zero signal of impending removal.
- [ ] **Code generator plugin class:** Two TODOs at `code_generator/plugin.py:64-65` reference an incomplete refactor. Plugin does not follow the codebase's canonical pattern.
- [ ] **npm detection edge cases:** `npm_resource.py` raises `CalledProcessError` if npm is not on PATH. `get_npm_root()` can still raise; only `check_npm` and `check_npm_package` are guarded.
- [ ] **Struct BDD conditional tests:** All 4 test files in `tests/struct_bdd/` use `pytest.mark.skipif(not STRUCT_BDD_INSTALLED, ...)`. When struct-bdd optional deps are missing, zero tests run.
- [ ] **# pragma: no cover audit:** 37 instances; some may mask genuinely untested production code (not just `TYPE_CHECKING`/`__main__` guards).

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Silent step execution (Pitfall 1) | LOW | Add collection-time validation. Run existing test suites through the fix; any newly-failing tests were silently passing before — that's a feature, not a bug. |
| Step matching regression (Pitfall 2) | MEDIUM | Git bisect to the refactoring commit. Revert only the step registry changes; keep the structural improvements. Add contract tests before re-applying. |
| Module split breaks state machine (Pitfall 3) | HIGH | Revert to monolithic module. Write characterization tests capturing ALL state transitions. Re-split with characterization tests as gate. |
| Dead plugin (Pitfall 4) | LOW | Remove from entry points in patch release. Announce deprecation if reimplementation is planned. |
| Broad exception mask (Pitfall 5) | MEDIUM | Review crash logs. Replace catch-all with specific types + logging. Run full test suite with `--strict-markers` and `-W error` to surface hidden warnings. |
| Parser edge case regression (Pitfall 7) | HIGH | Revert parser changes. Add Cucumber Messages compliance tests. If Go parser was unaffected, suggest affected users use `PYTEST_BDD_GO_PARSER=1` as temporary workaround. |
| Missing deprecation (Pitfall 8) | HIGH | Restore removed feature in patch release. Add deprecation warning. Announce removal timeline in CHANGELOG. This damages user trust the most. |
| Security issue in subprocess (Pitfall 9 variant) | LOW | Patch release with fix. These are in npm_resource.py and code_generator/plugin.py — both go through subprocess with known-safe inputs, but fix proactively. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Silent step execution (Pitfall 1) | STAB-02 (return None elimination) | Zero scenarios with zero matched steps pass. Add `tests/feature/test_empty_step_validation.py`. |
| Step matching regression (Pitfall 2) | REF-02 (code generator), REF-03 (large files) | Contract tests for step priority ordering. Run `tests/feature/` integration tests before/after. |
| Module split breaks state (Pitfall 3) | REF-01 (split scenario_run.py) | Characterization tests for all RunStage transitions. Run with xdist (`-n 2`). |
| Dead plugin (Pitfall 4) | STAB-01 (allure plugin) | Plugin removed from `pyproject.toml` entry points OR reimplemented with passing tests. |
| Broad exception catch (Pitfall 5) | STAB-03 (exception cleanup) | `except Exception:` count reduced by 60%+. All remaining instances have `exc_info=True` logging. |
| Return None propagation (Pitfall 6) | STAB-02 (BEFORE any refactoring) | 96 instances reduced by 50%+ in non-hook code. No new instances added during refactoring. |
| Parser edge case regression (Pitfall 7) | OUT OF SCOPE for stabilization | Parser behavior unchanged. TEST-03 adds edge case coverage without behavior changes. |
| Missing deprecation (Pitfall 8) | STAB-04 (deprecation warnings) | `DeprecationWarning` emitted for `--cucumberjson`. DEPRECATIONS.md created. |
| Inconsistent plugin patterns (Pitfall 9) | REF-02 → SIM-02 | All plugins follow class-based pattern. DEVELOPMENT.rst documents the canonical pattern. |

## Sources

- **pytest-bdd issue tracker** (GitHub): Bug label closed issues — revealed step matching regression (#542), parser edge cases (#741, #655, #333), silent pass (#403), fixture lifecycle (#689). MEDIUM confidence (observations, not post-mortems).
- **behave/behave issue tracker** (GitHub): Bug label closed issues — revealed ResourceWarning (#1313), Python version breakage (#1270, #1255), PyPI install errors (#1225), config handling (#1202), formatter coupling (#1231, #935), build tooling drift (#994). MEDIUM confidence.
- **behave documentation** (behave.readthedocs.io): Philosophy, comparison, and appendix sections. HIGH confidence for documented behaviors, LOW for what's NOT documented.
- **pytest-bdd-ng codebase analysis** (`.planning/codebase/CONCERNS.md`, 2026-05-12): Direct analysis of current tech debt. HIGH confidence (verified in source code).
- **Cucumber best practices skill**: Scenario design, step definition patterns, anti-patterns. HIGH confidence (derived from Cucumber project documentation).
- **AGENTS.md** (project constitution): `return None` antipattern rule, `attrs` over dataclass requirement, `StashBound` pattern requirement. HIGH confidence (project-defined).

---

*Pitfalls research for: pytest-bdd-ng stabilization*
*Researched: 2026-05-12*
