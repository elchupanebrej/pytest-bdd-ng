# Phase 35 Typing Validation Research

**Date:** 2026-07-12
**Question:** How should this project extend its existing strict mypy approach with additional type validation, while supporting Python 3.10-3.14?

## Current Baseline

- Mypy is the enforced checker: `pyproject.toml` checks `pytest_bdd` and `pytest_bdd_toolchain` with many strict flags, Python 3.14, local `stubs/`, and the Pydantic plugin. Tox runs it in `py314-pytest{90,latest}-mypy`; pre-commit runs it too.
- The configuration currently excludes `src/pytest_bdd_toolchain/(case|step)/` and has seven module groups with `ignore_errors = true`. Phase decisions require removing these broad bypasses and covering both packages.
- The library publishes `pytest_bdd/py.typed`. `src/pytest_bdd_toolchain/case/unit/test_mypy_strict.py` already asserts that `mypy --strict src/` exits zero, but it is itself currently outside the mypy scope.
- `docs/research/type-checker-comparison.md` (2026-06-08) previously evaluated pyright and ty on only `src/pytest_bdd`. It found complementary diagnostics but reported attrs-related pyright noise. Re-run any evaluation against the post-Phase-35 tree and the full chosen scope; do not treat those counts as a current baseline.

## Complementary Validation Options

### 1. Pyright or basedpyright: a second whole-source checker

**Value beyond mypy.** Pyright uses an independent analyzer and its strict mode has diagnostics for unknown types, missing generic arguments, invalid `__all__`, and other flow/API issues. Its configuration supports an explicit target `pythonVersion`, target platform, custom stub path, strict paths, and per-rule diagnostics. This makes it useful for checking the minimum supported Python version separately from the interpreter used to run CI. [Pyright configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md), [basedpyright configuration](https://docs.basedpyright.com/latest/configuration/config-files/)

**Fit and risk.** A strict whole-source Pyright gate would be useful only after a measured spike. The project is attrs- and plugin-heavy and relies on mypy's Pydantic plugin; neither extension is a mypy plugin contract. The existing local comparison found material attrs-related false positives. A second checker also duplicates a large amount of configuration and introduces divergent suppression syntax and semantics.

**basedpyright is not the default choice.** It adds stricter defaults, baselines, and configuration features, but it is a fork rather than the upstream checker. Its own documentation warns library authors to leave basedpyright-only language features disabled when users may use other type checkers. A baseline would also conflict with the phase decision to eliminate broad bypasses. Use upstream Pyright if the spike proves a whole-source second checker has an acceptable zero-error policy. [Basedpyright features and library compatibility note](https://docs.basedpyright.com/latest/configuration/config-files/)

**Effort:** high. Add a separate configuration, lock a Node/PyPI-delivered checker version, resolve source/import/stub differences, and maintain parity across source packages and Python target versions.

### 2. Pyright `--verifytypes`: validate the published package contract

**Value beyond mypy.** This is the best targeted complement. It assesses the completeness of a PEP 561 `py.typed` package's public interface rather than re-checking every implementation detail. The typing specification defines type completeness as public classes, methods, parameters, returns, aliases, and visible variables resolving to known types; private symbols are exempt. That maps directly to the library's distribution promise. [Typing Python Libraries: type completeness](https://typing.python.org/en/latest/guides/libraries.html#type-completeness), [Pyright CLI issue documenting `--verifytypes`](https://github.com/microsoft/pyright/issues/5802)

**Fit and implementation.** Build the wheel, install it into a clean environment, and run `pyright --verifytypes pytest_bdd --ignoreexternal` against the installed artifact. Set a policy after the initial report: ideally 100% type completeness for the public `pytest_bdd` API, with a versioned report available as CI output. This checks the built distribution, `py.typed` placement, and exported surface rather than merely the checkout.

**Limits.** It does not replace mypy: it does not validate internal implementation typing or runtime behavior, and it should not be applied to the internal `pytest_bdd_toolchain` package as a public distribution contract.

**Effort:** low to medium. It requires a release-style isolated environment and one explicit policy decision about an initial threshold versus a zero-defect/100% gate.

### 3. Checker contract fixtures for public APIs

**Value beyond mypy.** Add small consumer-style source fixtures that import the installed wheel and exercise the public decorators, step definitions, fixture injection, overloads, and protocols. Run mypy and Pyright against them: valid examples must pass, and intentionally invalid examples must emit a stable expected diagnostic. This protects inferred decorator signatures, which unit tests cannot observe. The typing guidance specifically recommends `ParamSpec`, `Concatenate`, and protocols for non-trivial decorators. [Typing Python Libraries: decorators](https://typing.python.org/en/latest/guides/libraries.html#decorators)

**Fit.** This is checker-agnostic validation of the user-facing contract. It avoids requiring two analyzers to agree over every dynamic internal pytest/plugin implementation. It can cover the public API now and expand as contracts become stable.

**Limits.** Fixtures require deliberate maintenance and must use only documented public APIs. Negative tests should assert diagnostic code/category rather than exact wording.

**Effort:** medium; high long-term value.

### 4. `stubtest`: runtime/stub shape validation

**Value.** Mypy's `stubtest` imports code, introspects it, and compares that runtime shape to `.pyi` stubs. It catches drift such as a stub omitting a defaulted parameter. [Mypy stubtest documentation](https://mypy.readthedocs.io/en/stable/stubtest.html)

**Fit.** Do not make it a Phase 35 gate for `pytest_bdd` as currently packaged: its public annotations are inline, not companion `.pyi` files. `stubs/` is a local third-party-boundary stub directory, not an installable public stub package. `stubtest` cannot verify source annotations' return types and explicitly does not type-check code.

**Later use.** Add it only if the project starts publishing maintained `.pyi` files or an explicit `pytest-bdd-ng-stubs` companion package. It could then be a release check with narrowly documented allowlists for optional dependencies.

**Effort now:** low to run, but low signal and wrong contract.

### 5. Astral `ty`: fast independent audit

**Value beyond mypy.** `ty` is an independent Rust checker with configurable rules, per-file overrides, GitHub Actions output, and explicit Python 3.10 through 3.15 targets. It can run with `uvx ty check` and has a `github` output format. [ty overview](https://docs.astral.sh/ty/), [ty CLI](https://docs.astral.sh/ty/reference/cli/), [ty configuration](https://docs.astral.sh/ty/reference/configuration/)

**Fit and risk.** It is valuable as a time-boxed audit and for editor feedback, particularly because the old local comparison found diagnostics mypy missed. It has a distinct configuration and no mypy-plugin compatibility, so a clean mypy result does not imply a clean ty result. Do not use `type: ignore` compatibility as a blanket solution: ty can respect those comments by default, but that conceals independent findings.

**Recommendation for this phase:** run ty in the discovery spike and record the unique, reproducible diagnostic classes. Do not make it a required CI gate unless the spike shows that every remaining finding is actionable or precisely and locally suppressible.

**Effort:** low for an audit, high for a zero-error gate.

## Cross-Version Validation

The current mypy configuration targets Python 3.14, whereas the distribution declares `requires-python = >=3.10`. Runtime tests cover the matrix, but static validators must also be told the minimum target to reject typing/runtime APIs unavailable in 3.10. Pyright and ty both support an explicit target version; ty otherwise derives the minimum from `project.requires-python`. [Pyright configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md), [ty Python version configuration](https://docs.astral.sh/ty/reference/configuration/#python-version)

Run the chosen supplementary static validation at Python 3.10 and platform `All` (or the project-supported OS targets where platform-sensitive imports matter). Keep the primary mypy command on its existing newest-supported interpreter unless investigation demonstrates a reason to add a second mypy target configuration.

## Recommendation

Adopt a layered model rather than immediately adding a strict second whole-repository checker:

1. **Primary implementation gate:** make `mypy --strict src` clean for both packages, remove broad excludes and `ignore_errors`, and retain only narrow coded/explained boundary suppressions.
2. **Required public-distribution gate:** add Pyright `--verifytypes pytest_bdd --ignoreexternal` against the built wheel in a clean environment, targeting Python 3.10. Make 100% public type completeness the desired completion standard; choose a temporary ratchet only if the baseline cannot be fixed in the phase.
3. **Required API regression checks:** add consumer fixtures checked by both mypy and upstream Pyright, beginning with the public scenario/step decorator contracts. This gives independent validation where users receive it without forcing all dynamic internals through Pyright immediately.
4. **Discovery before committing to a second implementation gate:** spike upstream Pyright strict and ty on the completed full source scope. Classify each diagnostic as actionable, a checker/model limitation, or a missing third-party stub. Promote a tool to blocking CI only if it reaches zero with localized documented exceptions and adds material unique findings.

This extends mypy with validation that is both externally meaningful and feasible for an attrs- and plugin-heavy library. It also makes a future second-checker decision evidence-based rather than permanent by assumption.

## Decisions Needed in the Follow-up Discussion

1. **Public completeness policy:** require 100% `pyright --verifytypes` coverage immediately, or set a temporary non-decreasing threshold with an explicit deadline to reach 100%?
2. **Contract-fixture scope:** cover only the stable decorators and public protocols in Phase 35, or also plugins/reporters and package re-exports?
3. **Second-checker spike outcome:** evaluate upstream Pyright strict only, Pyright strict plus ty, or Pyright strict plus ty and basedpyright for comparison (the latter adds fork maintenance and is not recommended absent a specific benefit)?
4. **Compatibility target:** run supplementary public validation at Python 3.10 with platform `All` only, or add per-platform static runs for Windows/macOS/Linux-sensitive imports?

## Sources

- [Python typing guidance for libraries](https://typing.python.org/en/latest/guides/libraries.html)
- [Mypy `stubtest` documentation](https://mypy.readthedocs.io/en/stable/stubtest.html)
- [Pyright configuration reference](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)
- [basedpyright configuration reference](https://docs.basedpyright.com/latest/configuration/config-files/)
- [ty documentation](https://docs.astral.sh/ty/)
