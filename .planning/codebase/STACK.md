---
last_mapped_commit: c59470a9bc50f5ae0f628a572832a5b614d862a7
mapped_at: 2026-05-12
focus: tech
---

# Technology Stack

**Analysis Date:** 2026-05-12

## Languages

**Primary:**
- Python 3.10-3.14 (project language) - All library source, tests, scripts, and tooling. Requires Python >=3.10 (`pyproject.toml:83`)

**Secondary:**
- Go 1.21+ (build-time only) - Compiled shared library for gherkin parsing via cgo. Source at `gherkin_go/`, build orchestrated by `src/pytest_bdd/_gherkin_go/_build.py`
- JavaScript (Node.js / ESM) - Cucumber formatter bridge and HTML reporting. `@cucumber/pretty-formatter` and `@cucumber/html-formatter` consumed at runtime via Node.js subprocess

**Infrastructure:**
- YAML - GitHub Actions workflows at `.github/workflows/main.yml` and `.github/workflows/messages-baseline-drift.yml`
- TOML - `pyproject.toml`, `.markdownlint.yaml`
- RST - Documentation and README (`README.rst`, `docs/`)
- Markdown - Gherkin feature specs in `features/` as `.feature.md` files

## Runtime

**Environment:**
- Python 3.10-3.14, with PyPy 3.11 also tested (`tox.ini:15`)
- Cross-platform: Linux, macOS, Windows (`pyproject.toml:33-35`)

**Package Manager:**
- pip (setup via `pyproject.toml` with setuptools build backend)
- uv (preferred dev tooling) — `uv run`, `uv sync`, `uvx` throughout Makefile and tox
- Lockfile: Missing (no `uv.lock` or `requirements.lock`; reproducibility via tox pinned versions)

## Frameworks

**Core:**
- `pytest>=7.0.0` - Test framework, plugin host. The library extends pytest via `pytest11` entry points
- `pluggy` - pytest plugin architecture (implicit via pytest)
- `cucumber-messages` - Python bindings for Cucumber Messages protocol (NDJSON serialization of test results)
- `gherkin-official>=33` - Python gherkin parser (fallback parser)
- `attrs` - Data class decorator library, used throughout for model types (convention over stdlib `dataclass`)

**Testing:**
- `pytest>=7.0.0` - All tests (unit, feature, e2e) run via pytest
- `pytest-xdist>=3.8.0` - Distributed test execution and remote worker reporting
- `pytest-httpserver` - HTTP server fixture for integration tests
- `pytest-order` - Test ordering plugin
- `coverage` - Code coverage measurement (via tox `coverage` factor)
- `tox>=4.2` with `tox-uv` - Multi-environment test runner and CI orchestrator
- `codecov` - Coverage upload to Codecov (CI only)
- `python-coveralls` - Coverage upload to Coveralls (optional, `pyproject.toml:149`)
- `playwright` - Browser-based acceptance testing (optional, `pyproject.toml:153`)

**Build/Dev:**
- `setuptools` - Build system (`pyproject.toml:1-3`)
- `ruff` (v0.12.0 in pre-commit) - Linting and formatting (replaces flake8/isort/black)
- `pre-commit` (v5.0.0 hooks) - Git pre-commit hook runner, configured at `.pre-commit-config.yaml`
- `mypy` - Static type checking with `pydantic.mypy` plugin
- `tox-ini-fmt` - tox.ini formatter
- `yamllint` - YAML lint
- `markdownlint` - Markdown lint (via Node.js v22.0.0 in pre-commit)
- `GitPython` - Git operations in scripts

## Key Dependencies

**Critical (hard runtime dependencies, from `pyproject.toml:46-74`):**

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.0.0 | Plugin host framework |
| `gherkin-official` | >=33 | Python gherkin parser (fallback) |
| `cucumber-messages` | latest | Cucumber Messages protocol Python bindings |
| `cucumber-expressions` | latest | Cucumber expression engine |
| `cucumber-tag-expressions` | latest | Tag expression evaluation |
| `attrs` | latest | Data classes with validation |
| `parse` | latest | Parse-based step argument extraction |
| `parse_type` | >=0.6.0 | Type parsing for parse expressions |
| `pydantic` | >=2.0.3 | Data validation models |
| `jsonschema` | latest | JSON Schema validation for message contracts |
| `PyYAML` | latest | YAML support (struct-bdd optional) |
| `Jinja2` | latest | Template rendering (docs, formatter bridge, code gen) |
| `filelock` | latest | Cross-process file locking for parallel formatter output |
| `certifi` | latest | TLS certificate bundle |
| `aiohttp` | latest | Async HTTP (URL-based scenario locator) |
| `packaging` | latest | Version parsing |
| `ruff` | latest | Programmatic lint invocation |
| `chevron` | latest | Mustache template engine |
| `ci-environment` | latest | CI environment detection |
| `decopatch` | latest | Decorator utilities |
| `docopt-ng` | latest | CLI argument parsing (scripts) |
| `makefun` | latest | Function creation utilities |
| `ordered_set` | latest | Ordered set data structure |
| `pathvalidate` | latest | Path validation |
| `py` | latest | Stdlib shim (pytest dependency) |
| `importlib-metadata` | latest (Python <3.10) | Backport for importlib.metadata |
| `importlib-resources` | latest | Resource file access |
| `StrEnum` | latest (Python <3.11) | Backport for StrEnum |
| `typing-extensions` | latest (Python <3.11) | Backport for typing features |

**Infrastructure (optional extras, from `pyproject.toml:106-171`):**

| Extra | Packages | Purpose |
|-------|----------|---------|
| `allure` | `allure-python-commons`, `allure-pytest` | Allure reporting integration |
| `async` | `aiofiles` | Async file I/O |
| `doc-gen` | `pandoc`, `panflute`, `pathlib2`, `pypandoc` | Feature documentation generation to RST |
| `struct-bdd` | `hjson`, `json5`, `pyhocon`, `tomli`, `PyYAML`, `types-PyYAML` | YAML/JSON/HOCON/TOML BDD support |
| `test` | `deepdiff`, `execnet`, `GitPython`, `PyHamcrest`, `pytest-httpserver`, `pytest-order`, `pytest-xdist`, `python-coveralls`, `jq` | Test suite dependencies |
| `test-playwright` | `playwright` | Browser acceptance tests |
| `testenv` | `tox`, `codecov` | CI environment |
| `testtypes` | `mypy`, type stubs (`types-*`) | Type checking |
| `full` | All of the above | Complete install |

**Go (build-time only):**

Go dependencies defined in `gherkin_go/go.mod`:
- `github.com/cucumber/gherkin/go/v28` v28.0.0 — Gherkin parser
- `github.com/gofrs/uuid` v4.4.0+incompatible — UUID generation (indirect, via cucumber/messages)
- `github.com/cucumber/messages/go/v24` v24.0.1 — Messages protocol (indirect)
- `github.com/stretchr/testify` v1.10.0 — Test utilities (indirect)

**JavaScript (runtime):**

Consumer at runtime via Node.js subprocess (not npm-managed in repo, installed via CI/pre-commit):
- `@cucumber/pretty-formatter` — Terminal formatter output (summary, progress, progress-bar, snippets, pretty, usage)
- `@cucumber/html-formatter` — HTML report generation
- `cucumber-html-reporter` — Alternative HTML reporter

## Configuration

**Project Configuration:**
- `pyproject.toml` — Single source of truth for build config, project metadata, tool settings (mypy, pytest, ruff, setuptools). 454 lines.
- `tox.ini` — Multi-environment test matrix: Python 3.10-3.14 × pytest 7.0-9.x/latest × coverage/mypy/messages/xdist/ruff/formatters × OS (linux, macos, windows). 120 lines.
- `.pre-commit-config.yaml` — Pre-commit hooks: ruff, trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files, check-toml, tox-ini-fmt, yamllint, markdownlint, pretty-format-toml, generate-feature-doc, validate-feature-headings. 64 lines.

**Tool Configuration (all in `pyproject.toml`):**
- `[tool.mypy]` — Lines 182-226. `check_untyped_defs=true`, `pydantic.mypy` plugin, per-module type checking overrides.
- `[tool.pytest.ini_options]` — Lines 228-274. Test group ordering (instant→fast→medium→slow→external), markers, testpaths, filterwarnings.
- `[tool.ruff]` — Lines 276-411. Comprehensive lint select (50+ rule sets, line length 120, Python 3.10+).
- `[tool.setuptools]` — Lines 413-453. Package directory, package data includes (`.so`/`.dll`/`.dylib`, JS files, JSON schemas, Jinja2 templates).

**Environment Variables (not read from any file):**
- `PYTEST_BDD_GHERKIN_BACKEND` (`auto`, `go`, `python`) — Select gherkin parser backend (`src/pytest_bdd/_gherkin_go/__init__.py:24`)
- `PYTEST_BDD_LIVE_FORMATTER_STDOUT_ISATTY` / `STDOUT_COLUMNS` / `STDOUT_ROWS` — Formatter terminal dimensions
- `PYTEST_BDD_TRANSPORT_FAIL_WORKERS` — Force xdist transport failure by worker ID (testing)
- `PYTEST_REMOTE_MODE` (`socket`, `ssh`, `via`) — xdist remote execution mode (Docker tests)
- `PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT` — Activate message coverage audit gate

**.env file present** (`C:\Users\bulky\Projects\pytest-bdd\.env`) — Contains environment configuration (contents not inspected per security policy).

**CI Configuration:**
- `.github/workflows/main.yml` — Main test matrix: Python 3.10-3.14 × pypy3.11 × ubuntu/windows/macos. Installs tox, uv, pandoc, Node.js, npm packages. Runs tox, codecov, build check with twine.
- `.github/workflows/messages-baseline-drift.yml` — Weekly cron (Mondays 4AM) checking message capability baseline for drift.

## Build System

**Build Backend:** setuptools (`pyproject.toml:2`)

**Build Commands:**
```bash
uvx --with build python -m build    # Build wheel and sdist
uvx --with twine twine check dist/*  # Validate built packages
```

**Custom Build Command:**
- `build_go` — `pytest_bdd._gherkin_go._build.BuildGoCommand` runs `go build -buildmode=c-shared` to produce `libgherkin_go.so`/`gherkin_go.dll`/`libgherkin_go.dylib` (`pyproject.toml:418`)

**Package Data (shipped with wheel):**
- Markdown parser JavaScript: `src/pytest_bdd/markdown_parser.js`
- Go shared libraries: `src/pytest_bdd/_gherkin_go/*.so`, `*.dll`, `*.dylib`
- JSON schemas: `src/pytest_bdd/model/message_jsonschema/*.json`
- Jinja2 templates: `src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/*.j2`
- Feature templates: `src/pytest_bdd/template/*.jinja2`

## CLI Entry Points

Defined in `pyproject.toml:173-176` under `[project.scripts]`:
- `bdd_tree_to_rst` — Converts feature files to RST documentation
- `compatibility_matrix` — Lists/checks compatibility matrix
- `render_cucumber_formatters` — Renders Cucumber formatter output from NDJSON

## Plugin Entry Points (pytest11)

Registered in `pyproject.toml:86-104` under `[project.entry-points.pytest11]`:
- `pytest-bdd-scenario-test-collector` — Feature file collection and scenario test generation
- `pytest-bdd-scenario-runner` (pickle_runner) — Scenario execution runtime
- `pytest-bdd-gherkin-message-reporter` — Live formatter bridge and message reporting
- `pytest-bdd-gherkin-terminal-reporter` — Terminal output reporter
- `pytest-bdd-gherkin-scenario-reporter` — Scenario result reporter
- `pytest-bdd-cucumber-json` — Cucumber JSON output
- `pytest-bdd-cucumber-formatter-{json,junit,pretty,progress,progress-bar,snippets,summary,usage,usage-json}` — Formatter plugins
- `pytest-bdd-allure-logger` — Allure reporting integration
- `pytest-bdd-code-generator` — Test code generation from feature files
- `pytest-bdd-struct-bdd` — YAML/JSON/HOCON/TOML BDD support

## Platform Requirements

**Development:**
- Python 3.10+ (3.14 recommended for active development, `Makefile:17`)
- uv package manager
- Node.js with npm (for formatter bridge and HTML reports)
- pandoc (for documentation generation)
- Go 1.21+ (only if building Go gherkin parser from source)
- Git (for GitPython scripts and pre-commit hooks)
- Docker/Compose (optional, for xdist remote acceptance tests)

**Production:**
- Python 3.10-3.14 on Linux, macOS, or Windows
- pip-installable wheel with pre-compiled Go shared library for Linux/macOS/Windows
  (falls back to Python `gherkin-official` parser if Go library unavailable)
- Optional `@cucumber/pretty-formatter` and `@cucumber/html-formatter` npm packages
  for live formatter output and HTML reports

---

*Stack analysis: 2026-05-12*
