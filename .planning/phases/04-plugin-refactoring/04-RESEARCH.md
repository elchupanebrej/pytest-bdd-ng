---
phase: 04-plugin-refactoring
status: complete
created: 2026-05-13
requirements: [REF-02, REF-03]
---

# Phase 04 Research: Plugin Refactoring

## Research Complete

Phase 4 is a structural refactor with behavior parity requirements. Planning must preserve Phase 3's direct-owning-module rule while raising the plugin boundary from convention to enforceable contract.

## Current State

- `pyproject.toml` registers 17 `pytest11` plugins.
- Eight cucumber formatter plugins are single-file modules (`cucumber_pretty.py`, `cucumber_progress.py`, etc.) and are the main outliers from package-style plugin structure.
- `src/pytest_bdd/plugin/code_generator/plugin.py` is 522 lines and still exposes function-style entrypoint callbacks; `entrypoint.py` imports `check_existence`, `generate_and_print_code`, and `generate_and_print_missing_code` directly.
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` is 900 lines. It mixes live process lifecycle, node/npm package resolution, formatter support payload construction, runtime asset rendering, formatter subprocess startup, formatter invocation, HTML rendering, and npm checks.
- `src/pytest_bdd/model/message_validation.py` is 791 lines. It mixes schema loading, schema validation, xdist compatibility, observed outcome mapping, implementation status governance, stream validation, and dict-to-message parsing.
- Direct plugin-internal imports currently exist between formatter modules, formatter support, reporter runtime modules, collector plugins, scenario reporter plugins, and pickle runner helpers.

## Recommended Plan Shape

Use six plans:

1. Verification environment unblocker. Required before refactor work because D-10 says Phase 4 cannot close on environmental blockers.
2. Contract and golden baseline tests. Locks plugin registry shape, plugin boundary import rule, large-file line targets, and formatter parity before moving code.
3. Code generator class refactor. Covers REF-02 and reduces one large plugin file without touching formatter behavior.
4. Plugin package and boundary normalization. Converts single-file formatter entrypoints to package-style plugins and moves stable cross-plugin contracts into `model/`.
5. Live formatter runtime split. Split by process, package/session, payload/render responsibilities and keep `LiveFormatterService` under 400 lines.
6. Message validation split and final verification. Split model validation responsibilities and run the full gate.

This order keeps tests and contracts ahead of behavior-preserving moves.

## Implementation Findings

### Code generator

Target shape:
- `src/pytest_bdd/plugin/code_generator/entrypoint.py` should instantiate/register or delegate to `CodeGeneratorPlugin` methods.
- `src/pytest_bdd/plugin/code_generator/plugin.py` should expose `CodeGeneratorPlugin`.
- Pure helpers can move to focused modules such as `rendering.py`, `collection.py`, and `request.py` if that is needed to keep `plugin.py` maintainable.
- Existing public command behavior must remain:
  - `--generate-missing`
  - `--generate`
  - `--feature`
  - missing-code exit status `100`

### Formatter package migration

Formatter modules are small but structurally inconsistent. A low-risk migration is:
- Create package directories for each single-file formatter plugin.
- Preserve plugin names and CLI flags.
- Move shared request/adapter contracts out of reporter internals into model-level stable contracts before rewiring imports.
- Update `pyproject.toml` entrypoints from `pytest_bdd.plugin.cucumber_pretty:pretty_plugin` style to `pytest_bdd.plugin.cucumber_pretty.entrypoint`.

### Cross-plugin boundaries

Allowed:
- Imports within the same plugin package.
- Imports from `pytest_bdd.model.*`, `pytest_bdd.util.*`, and `pytest_bdd.compatibility.*`.
- Pytest hooks and hook specs.

Blocked:
- A plugin package importing another plugin package's implementation modules.
- Formatter plugins importing `pytest_bdd.plugin.gherkin_message_reporter.session` directly.
- Reporter plugins importing scenario reporter or pickle runner internals when a model contract or hook is the stable surface.

Stable model contracts should stay narrow:
- formatter requests/results
- validation results
- codegen requests

### Large file split targets

`live_formatter_runtime.py` split by responsibility:
- process lifecycle: `LiveFormatterProcess`, finalize/wait/join/failure/write helpers
- node package/session resolution: node executable lookup, package discovery, npm root, env building
- support payload/rendering: formatter expression/source reference payload construction
- runner/render entrypoints: start live formatters, run requested formatters, HTML generation, npm check

`message_validation.py` split by responsibility:
- schema loading/building/cache
- schema validation API and violations
- xdist compatibility validation
- observed outcome/capability collection
- stream validation loop
- dict parsing

## Validation Architecture

Automated validation must include:

- Source contract for all 17 `pytest11` plugins:
  - each entrypoint resolves to a package-style module path ending in `.entrypoint`
  - each package has `entrypoint.py`, `plugin.py`, and `hook.py`
  - each `plugin.py` exposes at least one canonical plugin class for the registered plugin
- Boundary contract:
  - no file under `src/pytest_bdd/plugin/**` imports another plugin package's internals
  - same-package plugin imports are allowed
  - model/util/compatibility imports are allowed
- Large-file contract:
  - `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` has fewer than 400 lines
  - `src/pytest_bdd/model/message_validation.py` has fewer than 400 lines
- Golden formatter parity:
  - capture representative formatter output before refactor
  - assert byte-identical or normalized-identical output after refactor for JSON/JUnit/pretty/progress/progress-bar/snippets/summary/usage/usage-json
- Full verification gate:
  - full suite green
  - xdist smoke green
  - pre-commit green without relying on skipped hooks for Phase 4 closure

## Risks

- Plugin package migration can break entrypoint loading if `pyproject.toml` and import paths drift.
- Moving formatter request/result types too late keeps plugin boundary tests red for too long.
- Moving them too broadly creates a new service layer. Keep model contracts narrow.
- Golden outputs can be noisy if terminal/color/path data is not normalized. Prefer existing formatter support helpers and fixture projects.
- Full-suite environment fixes must be isolated from refactor changes so regressions are attributable.

## Planning Guidance

- Every plan must cite the relevant D-IDs from `04-CONTEXT.md`.
- Do not add private-path compatibility shims.
- Do not split `steps.py` in Phase 4.
- Do not change parser behavior.
- Prefer source contracts and focused tests before large moves.
