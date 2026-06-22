# Development Scripts Exploration

This document identifies all scripts, custom linter rule checkers, and command-line interfaces (CLIs) used for development and CI/CD operations in the `pytest-bdd-ng` repository, evaluating them as candidates for ATDD/BDD E2E tests in the new "Development" space (`features/18 Development/` or similar).

---

## 1. Custom Pylint Rules & Architecture Tooling (`scripts/`)

The architecture scoring and docstring-injection subsystem consists of several Python scripts coordinated by a single facade CLI.

### 1.1. Unified Architecture CLI Facade (`scripts/arch.py`)
- **What it does**: Provides a unified CLI entry point (`python scripts/arch.py <command>`) for all architectural score collection, gap analysis, and template injections.
- **Commands coordinated**:
  - `inject-source` &rarr; `scripts/inject_responsibility_docstrings.py`
  - `inject-tests` &rarr; `scripts/inject_test_docstrings.py`
  - `fill-tests` &rarr; `scripts/fill_test_docstrings.py`
  - `collect-scores` &rarr; `scripts/collect_arch_scores.py`
  - `collect-test-scores` &rarr; `scripts/collect_test_scores.py`
  - `analyze-gaps` &rarr; `scripts/analyze_responsibility_zones.py`
- **Location**: [scripts/arch.py](file:///c:/Users/bulky/Projects/pytest-bdd/scripts/arch.py)
- **Current testing state**: Individual Pylint checkers (e.g., `TypingRulesChecker`, `FileSizeRulesChecker`) are unit-tested under `src/pytest_bdd_testing/case/unit/test_pylint_checkers.py`. However, the CLI commands, automatic injections, docstring re-formatting, and gap analysis reports are completely untested at the E2E level.
- **Proposed ATDD/BDD Scenario**:
  - Verify that running `python scripts/arch.py inject-source` on a mockup Python module with no docstring creates the correct structural responsibility template.
  - Verify that running `python scripts/arch.py collect-scores` collects scores from source files and writes a valid JSON structure.
  - Verify that running `python scripts/arch.py analyze-gaps` generates the gaps report markdown file matching expected warning zones.

### 1.2. Auxiliary Formatting & Cleanup Scripts
- **`scripts/fix_long_lines.py`**: Formats docstrings to adhere to PEP 8/Ruff line limits while ignoring rule tags (e.g. `#arch-eval:`).
- **`scripts/fix_incomplete_scores.py`**: Auto-fills missing evaluation keys in docstrings with configured default values.
- **Location**: [scripts/fix_long_lines.py](file:///c:/Users/bulky/Projects/pytest-bdd/scripts/fix_long_lines.py) and [scripts/fix_incomplete_scores.py](file:///c:/Users/bulky/Projects/pytest-bdd/scripts/fix_incomplete_scores.py).
- **Proposed ATDD/BDD Scenario**:
  - Verify that `fix-long-lines` splits oversized sentences but does not touch lines matching `#arch-eval:` patterns.
  - Verify that `fix-incomplete-scores` identifies incomplete blocks and populates the remaining scores with defaults.

---

## 2. Codebase Verification & Sync CLI Tools (`src/pytest_bdd/script/`)

These CLI tools are registered as package console scripts or run directly as hooks.

### 2.1. Feature Headings Validator (`src/pytest_bdd/script/validate_feature_headings.py`)
- **What it does**: Scans a path for Gherkin/Markdown feature documents to detect violations of the heading policy (e.g., empty headings). Used in a local pre-commit hook.
- **Location**: [validate_feature_headings.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/script/validate_feature_headings.py)
- **Current testing state**: Heading parser behavior is tested indirectly through features runtime collection (`features/10 Heading Validation/`), but the standalone pre-commit CLI tool wrapper is untested.
- **Proposed ATDD/BDD Scenario**:
  - Given a mock folder with a feature file containing `# Feature: ` (empty name)
  - When running `python src/pytest_bdd/script/validate_feature_headings.py --root-path <mock-folder>`
  - Then the command exits with code `1` and emits violations to stderr.

### 2.2. Compatibility Matrix CLI (`src/pytest_bdd/script/compatibility_matrix.py`)
- **What it does**: Registered as `compatibility_matrix` entrypoint. Extracts Python and pytest test factors from `tox.ini` and computes tox environment lists, checks pair compatibility, and reports E2E migration status.
- **Location**: [compatibility_matrix.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/script/compatibility_matrix.py)
- **Current testing state**: Untested.
- **Proposed ATDD/BDD Scenario**:
  - Verify that running `compatibility_matrix` with `--python 3.14 --pytest latest` outputs compatibility validation results (e.g., "compatible pair").
  - Verify that running with `--report-e2e-migration-threshold` compares tests and features directories and reports coverage metric status.

### 2.3. Messages Contract Schema Sync Tool (`src/pytest_bdd/script/sync_messages_contract_schemas.py`)
- **What it does**: Validates and synchronizes local Cucumber Messages schemas against the upstream contract version (runs in pre-commit as `--check`).
- **Location**: [sync_messages_contract_schemas.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/script/sync_messages_contract_schemas.py)
- **Current testing state**: Untested.
- **Proposed ATDD/BDD Scenario**:
  - Given a copy of the schemas directory where one schema file is modified to simulate schema drift.
  - When running `sync_messages_contract_schemas --check --schema-path <mock-dir>`
  - Then the CLI exits with code `1` and prints drift details.

### 2.4. Standalone Cucumber Formatter Renderer (`src/pytest_bdd/script/render_cucumber_formatters.py`)
- **What it does**: Registered as `render_cucumber_formatters` entrypoint. Renders a Cucumber NDJSON messages file into any terminal or file-based formatter reports (e.g. pretty, summary, usage).
- **Location**: [render_cucumber_formatters.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/script/render_cucumber_formatters.py)
- **Current testing state**: Formatters are tested via pytest plugin hooks, but this standalone formatter renderer CLI has no tests.
- **Proposed ATDD/BDD Scenario**:
  - Given a valid Cucumber NDJSON messages file.
  - When running `render_cucumber_formatters --messages-ndjson <file> --cucumber-summary`
  - Then the summary is written to standard output, matching expected formats.

---

## 3. Messages Coverage Audit Script (`scripts/run_messages_coverage_audit.sh`)

- **What it does**: Coordinates the captured runtime NDJSON audit against baseline decisions and schemas to ensure no messages coverage drift.
- **Location**: [run_messages_coverage_audit.sh](file:///c:/Users/bulky/Projects/pytest-bdd/scripts/run_messages_coverage_audit.sh)
- **Current testing state**: Governed in CI workflow, but the shell orchestration script itself is untested.
- **Proposed ATDD/BDD Scenario**:
  - Run the audit script and check that the generated JSON report is valid against `governance-report.schema.json`.

---

## Summary of Candidates

| Candidate / Script | Location | Type | Purpose | Test Priority |
| :--- | :--- | :--- | :--- | :--- |
| **`allure-cucumber`** | `src/pytest_bdd/plugin/allure_formatter/cli.py` | Registered CLI | NDJSON to Allure results | **High** (user-facing tool) |
| **`validate_feature_headings`** | `src/pytest_bdd/script/validate_feature_headings.py` | Script / Pre-commit | Pre-commit empty headings gate | **High** (pre-commit quality gate) |
| **`arch.py`** (facade) | `scripts/arch.py` | CLI Facade | Source code/tests scoring and template injection | **Medium** (architecture utility) |
| **`render_cucumber_formatters`** | `src/pytest_bdd/script/render_cucumber_formatters.py` | Registered CLI | Standalone NDJSON rendering | **Medium** (reporting CLI) |
| **`compatibility_matrix`** | `src/pytest_bdd/script/compatibility_matrix.py` | Registered CLI | Tox matrices & migration report | **Medium** (matrix tool) |
| **`sync_messages_contract_schemas`** | `src/pytest_bdd/script/sync_messages_contract_schemas.py` | Script / Pre-commit | Message schema drift verification | **Low** (internal sync checker) |
| **`run_messages_coverage_audit`** | `scripts/run_messages_coverage_audit.sh` | Shell Script | Messages audit orchestration | **Low** (CI runner script) |
