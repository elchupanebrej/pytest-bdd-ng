<!-- markdownlint-disable MD013 -->

# Quickstart: Validate Template-Driven Feature Documentation Ordering

## 1. Prepare the environment

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testtypes,doc-gen]'
```

Expected:
- Editable install is ready for documentation-generation, contract, and strict docs-build validation.

## 2. Validate ordered feature-doc generation behavior

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 tox -e py313-pytestlatest-coverage-lin -- tests/doc/test_doc.py
```

Expected:
- Generated navigation follows numeric sibling prefixes.
- Reader-facing section headings and topic labels omit numeric prefixes.
- Generated page paths retain numeric prefixes.
- Manual prefix/suffix content outside the generated block remains unchanged.

## 3. Validate deterministic ordering errors

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/doc/test_doc.py \
  tests/contract/test_feature_doc_ordering_contract.py
```

Expected:
- Missing sibling prefixes fail with a deterministic validation error.
- Duplicate sibling prefixes fail with a deterministic validation error.
- Contract-level ordering schemas and validation paths stay aligned with implementation behavior.

## 4. Regenerate docs through the real script entry point

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python src/pytest_bdd/script/bdd_tree_to_rst.py features docs/features
```

Expected:
- `docs/features/features.rst` is regenerated from ordered sources.
- Generated index output stays deterministic across repeated runs.
- Prefix-free labels are rendered via templates while path names remain source-derived.

## 5. Validate template packaging and docs-generation contracts

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/contract/test_jinja2_doc_generation_contract.py \
  tests/contract/test_feature_doc_ordering_contract.py \
  tests/generation/test_template_packaging.py
```

Expected:
- Documentation template assets remain packaged and discoverable.
- The feature-ordering contract and existing docs-generation contract both pass.

## 6. Validate strict docs rendering

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 sphinx-build -W --keep-going -b html -c docs -D master_doc=features docs/features docs/_build/features-only-strict
```

Expected:
- Feature documentation renders without warnings promoted to errors.
- Prefix-free reader labels and generated include paths remain valid in the docs build.

## 7. Run contributor workflow gates

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
bash .codex/skills/precommit-runner/scripts/run_precommit.sh --all-files
```

Expected:
- Pre-commit passes when feature docs are regenerated and consistent.
- Stale generated docs or broken ordering validation are blocked before commit.

## Validation Record: 2026-03-08

### Executed commands

1. Ordered doc-generation pytest suite on the current host:

   ```bash
   cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
   conda run -n pytest-bdd-ng-py314 python -m pytest -q \
     tests/doc/test_doc.py \
     tests/contract/test_jinja2_doc_generation_contract.py \
     tests/contract/test_feature_doc_ordering_contract.py \
     tests/generation/test_template_packaging.py
   ```

   Result:
   - `15 passed, 7 skipped in 0.33s`
   - The skipped doc tests are expected on this Darwin/non-Python-3.13 host because `tests/doc/test_doc.py` is intentionally Linux/Python-3.13 gated.

2. Real generator entry point:

   ```bash
   cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
   conda run -n pytest-bdd-ng-py314 python src/pytest_bdd/script/bdd_tree_to_rst.py features docs/features
   ```

   Result:
   - First run rewrote stale generated output and exited with the expected stale-doc failure message.
   - Second run completed with exit code `0`, confirming deterministic no-diff regeneration.

3. Strict standalone feature-doc build:

   ```bash
   cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
   conda run -n pytest-bdd-ng-py314 sphinx-build -W --keep-going -b html -c docs -D master_doc=features docs/features docs/_build/features-only-strict
   ```

   Result:
   - Build succeeded with warnings treated as errors.

4. Repository-wide pre-commit gate:

   ```bash
   cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
   bash .codex/skills/precommit-runner/scripts/run_precommit.sh --all-files
   ```

   Result:
   - The gate failed because of pre-existing repository-wide issues outside this feature scope.
   - Reported failures were in `ruff-check`, `ruff-format`, `tox-ini-fmt`, `yamllint`, and `markdownlint`.
   - The unrelated violations were reported in existing probe/testenv files plus Markdown and YAML artifacts under `specs/`, `.opencode/command/`, `AGENTS.md`, and `GEMINI.md`.

5. Feature-scope lint verification after the implementation fixes:

   ```bash
   cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
   conda run -n pytest-bdd-ng-py314 ruff check \
     src/pytest_bdd/script/bdd_tree_to_rst.py \
     tests/contract/test_feature_doc_ordering_contract.py \
     tests/doc/test_doc.py \
     tests/generation/test_template_packaging.py
   conda run -n pytest-bdd-ng-py314 ruff format --check \
     src/pytest_bdd/script/bdd_tree_to_rst.py \
     tests/contract/test_feature_doc_ordering_contract.py \
     tests/doc/test_doc.py \
     tests/generation/test_template_packaging.py
   ```

   Result:
   - `ruff check`: all checks passed
   - `ruff format --check`: 4 files already formatted

### Platform note

- The Linux-specific tox slice from this feature plan could not be executed on this host because Docker is unavailable in `PATH`. The host-local pytest command above was used instead, and the platform-gated doc tests skipped as designed.
