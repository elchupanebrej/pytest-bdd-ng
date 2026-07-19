# Architectural Problem Report

## 1. Executive Summary
This report identifies current architectural problems, structural weaknesses, and technical debt in the `pytest-bdd-ng` project. Based on static analysis, configuration reviews, and pending state tracking, several areas require refactoring, particularly around code organization, typing, and quality gate unification.

## 2. Findings by Architectural Domain

### 2.1 Code Organization & Modularity
- **Incomplete Namespace Package Migration:**
  The project intends to use PEP 420 namespace packages for the `pytest_bdd_testing` tree (as noted in `pyproject.toml` where `INP001` is ignored with the comment "PEP 420 namespace packages: __init__.py files intentionally removed"). However, many `__init__.py` files still exist across `src/pytest_bdd_testing/**`, causing inconsistencies in the package layout.
- **Ruff Rules Project Layout Unification:**
  There is a pending action to unify ruff rules and completely remove `__init__.py` usage to properly solidify the namespace package approach.

### 2.2 Type Safety & Interfaces
- **Typing Gaps:**
  The project has pending improvements to adopt best practices from `awesome-python-typing`.
- **mypy Strictness:**
  While the `uv run mypy` environment passes for `src/pytest_bdd/` with current configurations, running `mypy` directly surfaces implementation gaps in custom pylint checkers (e.g., `Class cannot subclass "BaseChecker" (has type "Any")`) and strict typing enforcement in parts like `status_policy.py` and `message_schema_validation.py`.

### 2.3 Testing Architecture & Quality Gates
- **`TestClasses` Enforcement:**
  The project forbids the use of `TestClasses` in tests. While a custom `pylint` rule (`no-test-class`) is enabled, the architectural plan requires enforcing this via a faster `ruff` rule to provide immediate feedback during development.
- **Remote `xdist` Blockers:**
  Docker-backed remote SSH `xdist` tests require Docker Desktop, which blocks local non-Docker suites and creates friction for native environments. These tests need to be split into a separate parallel GitHub Actions executor job to unblock core test suites.
- **`noqa` Explanations:**
  A custom `pylint` rule is needed for enforcing `noqa` comments without reasons, to ensure all local lint overrides are explicitly justified (e.g., `# noqa: E501 - <reason>`).

### 2.4 Plugin System & Integrations
- **Allure Plugin Adaptation (Phase 25):**
  The `adapt-plugin-system-of-allure-python-commons` phase is actively executing but not completed. The architecture defines two modes (pytest-native real-time interception vs standalone format), and deferred tasks include "Layer 2 validation: Playwright-based HTML rendering validation of Allure reports".

## 3. Actionable Recommendations
1. **Sweep `__init__.py` files:** Execute a project-wide sweep to remove all `__init__.py` files within the `pytest_bdd_testing` tree to fully transition to PEP 420 namespace packages.
2. **Migrate Custom Lint Rules to Ruff:** Where possible, migrate custom `pylint` rules (like `no-test-class`) to custom `ruff` plugins or equivalent AST checks in a pre-commit hook to speed up the quality gates.
3. **Isolate Environment-Dependent Tests:** Complete the split of remote `xdist` tests into dedicated CI jobs to unblock local and native environment execution.
4. **Implement Missing Pylint Checkers:** Add the custom checker for enforcing `noqa` explanations to maintain strict oversight on ignored linting rules.
5. **Address Typing Debt:** Complete the rollout of `awesome-python-typing` practices, particularly focusing on generic type parameters and ensuring consistent return types in the core models and plugins.
