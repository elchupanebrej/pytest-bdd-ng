# Stack Research: pytest-bdd-ng Modernization

**Domain:** Python BDD testing library (pytest plugin)
**Researched:** 2026-05-12
**Confidence:** HIGH

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10–3.14 | Runtime | Project constraint. 3.10 EOL Oct 2026 — plan to drop after stabilization. |
| pytest | >=8.0.0 (<10) | Test framework host | Current is 9.0.3 (Apr 2026). `config.stash` pattern is stable since 6.x. The `>=7.0.0` pin in pyproject.toml is too loose — 7.x lacks stash improvements and modern hook ordering. Bump minimum to 8.0.0. |
| pluggy | 1.6.0 (implied via pytest) | Hook dispatch engine | Core of pytest plugin architecture. 1.6.0 (May 2025) adds performance improvements for hook call chains. No direct dependency needed — comes with pytest. |

### Gherkin Parsing Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| gherkin-official (Python) | >=39.1.0, <40 | Primary Gherkin parser | **CRITICAL UPDATE NEEDED.** Project pins `>=33` but latest is 39.1.0 (May 2026). That's 6 major versions behind. Newer versions align with cucumber-messages 32.x protocol. Requires Python >=3.10 — matches our range. |
| gherkin/go (Go backend) | v39 | High-performance parser via ctypes | Must match gherkin-official version. Currently at v28 — needs bump to v39. Import path: `github.com/cucumber/gherkin/go/v39` |
| cucumber/messages/go | v32 | Go messages library | Must match cucumber-messages Python version. Import path: `github.com/cucumber/messages/go/v32` |

**Rationale for Go parser backend:** The ctypes-based Go parser provides 50-100x faster parsing than pure Python for large feature suites. It's compiled at build time via `setuptools` custom command (`build_go`). Keep this as optional acceleration — always fall back to Python parser.

### Cucumber Protocol Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| cucumber-messages | >=32.3.1, <33 | Protocol message definitions | Current version 32.3.1 (Apr 2026). Protocol version string is `"32.3.1"`. This is the canonical Cucumber message protocol — all formatters and the live reporter depend on it. Pin upper bound to prevent silent breaking changes. |
| cucumber-tag-expressions | >=9.1.0 | Boolean tag filtering | Current version 9.1.0 (Feb 2026). Actively maintained by cucumber org. Supports Python 3.10-3.14 + PyPy. |
| cucumber-expressions | (verify current version) | Official Cucumber step expressions | One of 7 supported step parser types. This is the Cucumber-standard expression syntax. Verify current PyPI version matches protocol. |
| jsonschema | Latest stable | Message validation | Validates cucumber-messages against JSON schemas. Already in dependencies. |

**Message lifecycle:** Source → GherkinDocument → Pickle → TestCase → TestRunStarted → TestCaseStarted → TestStepStarted → TestStepFinished → TestCaseFinished → TestRunFinished. The `gherkin_message_reporter` plugin emits these as NDJSON for the live formatter bridge.

### Step Matching Engine

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| parse | >=1.22.0 | Format-string pattern matching | Default parser type. Actively maintained (v1.22.0, May 2026). Maps Python format() syntax in reverse. Use for simple parameter extraction like `{value:d}`. |
| parse_type | >=0.6.6 | Extended type converters for parse | Cardinality support (0..1, 0..*, 1..*), enum mappings, choice types. v0.6.6 (Aug 2025). Maintained but note: classifiers only list through Python 3.11 in metadata — verify 3.12-3.14 compatibility. |
| cucumber-expressions | Latest | Cucumber-standard expression syntax | Official Cucumber expression parser. Supports `{int}`, `{float}`, `{word}`, `{string}`, custom parameter types. Preferred over `re` and `parse` for Cucumber interoperability. |
| re (stdlib) | — | Regex-based step matching | Built-in. Use only when regex patterns are truly needed; prefer cucumber-expressions for readability. |
| cfparse | (via parse_type) | Cardinality-field parse variant | Extended parse with cardinality support in field names. Used when steps need `{items:Item+}` patterns. |

**Parser type hierarchy (7 total):** `re` → `parse` → `cfparse` → `cucumber_expression` → `string` → `step_func` → `step_func_async`. The modern priority order for users should be: cucumber-expressions first, then parse for format-string fans, then re for complex patterns.

### Plugin Architecture

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest (hook system) | >=8.0.0 | Plugin registration via `pytest11` entry points | 17 plugins registered in `[project.entry-points.pytest11]`. This is the canonical pytest plugin pattern — no alternatives exist. |
| StashKey / config.stash | (pytest built-in) | Thread-safe plugin state | Official pytest pattern since 6.x. Current codebase already follows `StashBound` pattern. No changes needed. |
| attrs | Latest | Data classes without boilerplate | Already used. `@attrs.define` is the modern API (not legacy `@attr.s`). Provides `__init__`, `__repr__`, `__eq__` generation + slots by default. Use over stdlib `dataclass`. |

**Plugin architecture best practices (pytest 8.x/9.x):**
- **Entry points:** Use `pytest11` namespace in `pyproject.toml` — already done.
- **State:** `config.stash` with typed `StashKey` — already done.
- **Hook ordering:** Use `tryfirst=True`/`trylast=True` on `@pytest.hookimpl` — already done.
- **Config:** Access via `pytest_configure(config)` hook — standard pattern.
- **Collection:** Use `pytest_collect_file` for custom file types (`.feature`, `.feature.md`) — already done.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.0.3 | Data validation/serialization | Used for config models and message validation. v2 is the current major with Rust-core performance. |
| Jinja2 | Latest | Template rendering | Feature doc generation, code generation templates. Stable, no concerns. |
| PyYAML | Latest | YAML struct BDD support | Required by `struct-bdd` extra for YAML feature definitions. |
| aiofiles | Latest (optional) | Async file I/O | Required by `async` extra. Only needed for async step implementations. |
| filelock | Latest | Distributed test locking | Used with pytest-xdist for test group ordering barriers. |
| ordered_set | Latest | Ordered set collection | Used in tag expression evaluation and scenario collection ordering. |
| packaging | Latest | Version parsing | Used for Python version detection in compatibility modules. |
| chevron | Latest | Mustache template rendering | Used for code generation templates. Minimal, well-maintained Mustache implementation. |

### Libraries to Re-Evaluate

| Library | Current Usage | Concern | Recommendation |
|---------|---------------|---------|----------------|
| decopatch | Decorator utilities | PyPI page requires JS — cannot verify health. Possibly unmaintained in 2026. | Audit usage. If only used for simple decorator patterns, replace with `functools.wraps` + manual decorator factories. If used for complex signature-preserving decorators, keep but pin version. |
| makefun | Dynamic function creation | Maintained (v1.16.0, May 2025) but niche. Tied to `decopatch` ecosystem. | Only needed if `decopatch` is kept. |
| ci-environment | CI detection | Lightweight utility. Last release unknown. | Low risk — simple detection logic. Could be inlined if unmaintained. |
| docopt-ng | CLI argument parsing | Legacy. No one uses docopt for new projects in 2026. | Replace with argparse (stdlib) or click for CLI scripts. Remove from core dependencies if only used in scripts. |
| pathlib2 | Path backport for older Python | Project requires Python >=3.10 — pathlib is built-in. | Remove entirely. pathlib2 was a Python 2/3.5 backport. Dead weight. |

### Development Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| ruff | 0.15.12 | Linting + formatting | Latest. Currently pinned to v0.12.0 in pre-commit config — update to 0.15.x. `preview = true` already set. |
| mypy | Latest | Static type checking | Configured with `pydantic.mypy` plugin. `check_untyped_defs = true`. |
| tox | >=4.2 | Test matrix runner | Current standard. Runs Python 3.10-3.14 × pytest versions matrix. |
| uv | Latest | Package management | Standard Python tooling for 2026. Used by cucumber org for publishing. Use `uv run`, `uv sync`, `uv pip compile` for deterministic deps. |
| pre-commit | Latest | Git hook framework | Runs ruff, mypy, and other checks before commit. |
| setuptools | Latest | Build backend | Keep as-is. While `hatchling` is more modern, switching build backends is out of scope for stabilization. |
| coverage.py | Latest | Test coverage | Used with Codecov/Coveralls for coverage reporting. |

### Infrastructure (unchanged, low priority)

| Technology | Version | Purpose |
|------------|---------|---------|
| pytest-xdist | >=3.8.0 | Distributed test execution |
| execnet | >=2.1.2 | Inter-process communication for xdist |
| Node.js (PATH) | Current LTS | Live formatter bridge (renders Cucumber JS formatters) |
| Go | 1.21+ | Build-time only, for cgo shared library compilation |
| ctypes | stdlib | Go parser bridge (no alternatives) |

## Installation

```bash
# Core (with Go parser support built at install time)
pip install pytest-bdd-ng

# Or with uv
uv add pytest-bdd-ng

# Extras
uv add "pytest-bdd-ng[struct-bdd]"    # YAML/JSON/TOML/HOCON feature definitions
uv add "pytest-bdd-ng[async]"          # Async step support
uv add "pytest-bdd-ng[allure]"         # Allure reporting (after STAB-01 fix)
uv add "pytest-bdd-ng[test]"           # Test dependencies
```

## Version Compatibility Matrix

| Package | Current Pin | Recommended Pin | Breaking Change? | Notes |
|---------|-------------|-----------------|------------------|-------|
| pytest | `>=7.0.0` | `>=8.0.0,<10` | Yes (drops 7.x) | 7.x lacks stash improvements, 9.x is current. Bump minimum. |
| gherkin-official | `>=33` | `>=39.1.0,<40` | Possible | 6 major versions of protocol changes. Test GherkinDocument/Pickle compatibility. |
| cucumber-messages | (unspecified) | `>=32.3.1,<33` | Possible | Add upper bound. Protocol is version-sensitive. |
| python | `>=3.10` | `>=3.10` | No | Keep as-is. Drop 3.10 after EOL (Oct 2026). |
| parse | (unspecified) | `>=1.20.0` | Low risk | Add minimum. parse is stable and backward-compatible. |
| parse_type | `>=0.6.0` | `>=0.6.0` | No | Already adequately pinned. |
| ruff | (unspecified) | `>=0.15.0` | No | Dev dep. Pre-commit hook should use `rev: v0.15.12`. |
| mypy | (unspecified) | `>=1.11` | No | Dev dep. Current is 1.11+. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Older gherkin-official (<39) | Out of sync with cucumber-messages 32.x protocol. Misses bug fixes and new Gherkin syntax support added between v33-v39. | gherkin-official >=39.1.0 |
| pytest <8.0.0 | Lacks `config.stash` improvements and modern hook ordering. pytest 8.x dropped Python 3.8, 9.x dropped 3.9. We target 3.10+ — no reason to support EOL pytest. | pytest >=8.0.0 |
| pathlib2 | Python 2/3.5 backport. Dead weight since project requires >=3.10. | stdlib pathlib |
| docopt-ng for new CLI work | docopt is a historical curiosity. No project starts with it in 2026. | argparse (stdlib) or click |
| bare `except Exception:` | Silently swallows errors — masks bugs. 22 instances in codebase (STAB-03). | Specific exception types or logged warnings |
| `return None` in non-hook code | Antipattern per AGENTS.md. 96 instances (STAB-02). | Explicit values or deterministic exceptions |
| Python dataclass over attrs | attrs is project standard per AGENTS.md. `@attrs.define` provides slots by default, better validation hooks. | attrs |
| Unpinned cucumber-messages | Breaking protocol changes between major versions. Without upper bound, a future v33 could silently break the message bridge. | Pin `<33` |
| Old Go parser (v28) | Doesn't match gherkin-official v39 output format. Protocol misalignment between Python and Go backends would cause subtle bugs. | Go v39 parser + v32 messages |

## Stack Patterns by Variant

**If using Go parser backend (production/high-volume):**
- Use `gherkin-official>=39.1.0` + Go parser compiled with `go/v39` imports
- Go messages library at `go/v32`
- Fall back to pure Python parser when Go shared library unavailable
- Build-time: `python setup.py build_go` or `pip install` triggers `BuildGoCommand`

**If using pure Python (CI/quick runs):**
- gherkin-official alone, no Go toolchain needed
- Slightly slower parsing — acceptable for small suites (<100 scenarios)
- No build-time dependencies beyond pip

**If extending with new step parser types:**
- Follow existing parser registration pattern in `steps.py`
- Prefer cucumber-expressions for Cucumber interoperability
- Only add new parsers if there's a clear user need (not during stabilization)

## Sources

- `/cucumber/messages` (Context7) — Protocol version 32.3.1, message types, lifecycle sequence. **HIGH confidence.**
- `/cucumber/gherkin` (Context7) — Go parser v39 import paths, Python parser usage. **HIGH confidence.**
- PyPI: `gherkin-official` — Latest version 39.1.0 (May 6, 2026), release history, Python >=3.10 requirement. **HIGH confidence.**
- PyPI: `cucumber-messages` — Latest version 32.3.1 (Apr 13, 2026), published via uv. **HIGH confidence.**
- PyPI: `cucumber-tag-expressions` — Latest version 9.1.0 (Feb 17, 2026), supports Python 3.10-3.14. **HIGH confidence.**
- PyPI: `pytest` — Latest version 9.0.3 (Apr 7, 2026), requires Python >=3.10. **HIGH confidence.**
- PyPI: `pluggy` — Latest version 1.6.0 (May 15, 2025), hook dispatch engine. **HIGH confidence.**
- PyPI: `parse` — Latest version 1.22.0 (May 2, 2026), actively maintained. **HIGH confidence.**
- PyPI: `parse_type` — Latest version 0.6.6 (Aug 11, 2025), maintained but classifier metadata only lists through 3.11. **MEDIUM confidence.**
- PyPI: `makefun` — Latest version 1.16.0 (May 9, 2025), actively maintained. **HIGH confidence.**
- PyPI: `ruff` — Latest version 0.15.12 (Apr 24, 2026), active weekly releases. **HIGH confidence.**
- `/websites/pytest_en_stable` (Context7) — Plugin architecture, StashKey pattern, hook specifications, `pytest_configure`. **HIGH confidence.**
- `/python-attrs/attrs` (Context7) — Modern `@attrs.define` API, comparison with dataclasses. **HIGH confidence.**
- `pyproject.toml` (project file) — Current dependency pins, entry points, tool configuration. **HIGH confidence.**
- `AGENTS.md` (project file) — Go parser versions (v28 → needs v39), attrs requirement, StashBound pattern. **HIGH confidence.**
- PyPI: `decopatch` — Could not verify (JS-rendered page). **LOW confidence.** Needs manual audit.

---

*Stack research for: pytest-bdd-ng stabilization milestone*
*Researched: 2026-05-12*
