<!-- markdownlint-disable MD013 -->

# Quickstart: Validate Jinja2 Documentation Generation Migration

## Prerequisites

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testtypes,doc-gen]'
uv sync --extra test --extra testtypes --extra doc-gen
```

## Scenario 1: Semantic parity for generation output (US1)

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/generation/test_generate.py \
#   tests/generation/test_generate_missing.py
uv run python -m pytest -q \
  tests/generation/test_generate.py \
  tests/generation/test_generate_missing.py
```

Expected:
- Generation tests pass with Jinja2 templates.
- Quote-heavy and unicode cases preserve semantic behavior.

## Scenario 2: Manual-content-safe documentation regeneration (US2)

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python src/pytest_bdd/script/bdd_tree_to_rst.py features docs/features
# conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/doc/test_doc.py
uv run python src/pytest_bdd/script/bdd_tree_to_rst.py features docs/features
uv run python -m pytest -q tests/doc/test_doc.py
```

Expected:
- Only generated sections are refreshed.
- Manual prefix/suffix content remains unchanged.

## Scenario 3: `features.rst` scope boundary enforcement (FR-011/FR-012)

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
rg -n "conversion|internal implementation|migration history|конвер" docs/features/features.rst || true
```

Expected:
- No internal implementation or conversion-history sections are present in `docs/features/features.rst`.
- Internal implementation notes, if needed, are located outside `docs/features/features.rst`.

## Scenario 4: Contract and packaging validation (US3)

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/contract/test_jinja2_doc_generation_contract.py \
#   tests/generation/test_template_packaging.py
uv run python -m pytest -q \
  tests/contract/test_jinja2_doc_generation_contract.py \
  tests/generation/test_template_packaging.py
```

Expected:
- Migration contract checks pass.
- Required `.jinja2` assets are available in package metadata.

## Scenario 5: Pre-commit stale-doc enforcement (US3)

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
bash .codex/skills/precommit-runner/scripts/run_precommit.sh --all-files
```

Expected:
- Pre-commit passes when generated documentation is in sync.
- Pre-commit fails when generated documentation is stale.

## Scenario 6: Features HTML build viability

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 sphinx-build -W --keep-going -b html -c docs -D master_doc=features docs/features docs/_build/features-only-strict
uv run sphinx-build -W --keep-going -b html -c docs -D master_doc=features docs/features docs/_build/features-only-strict
```

Expected:
- Build succeeds with warnings treated as errors.
- Generated output rooted at `docs/features/features.rst` is renderable as standalone HTML documentation.
