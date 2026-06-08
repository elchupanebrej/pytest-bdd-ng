# Contributing

pytest-bdd-ng is a Python library and pytest plugin. Contributions should keep
behavior aligned with pytest, Cucumber/Gherkin semantics, and the executable
feature documentation in this repository.

## Development Setup

Use the project-managed environment:

```bash
uv python install 3.14
uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd
```

The package supports Python 3.10 through 3.14. Python 3.14 is the primary local
development target in current tooling.

## Source Layout

- `src/pytest_bdd/` contains library code and pytest plugins.
- `src/pytest_bdd_testing/cases/` contains grouped pytest suites.
- `features/` contains executable BDD documentation.
- `docs/features/` contains generated documentation; do not edit generated
  feature docs by hand.
- `docs/adr/` records architectural decisions.
- `DEVELOPMENT.rst` contains detailed development guidance.

## Before Changing Code

Read the relevant architecture or guide docs before touching shared runtime
areas:

- `docs/architecture/index.md`
- `docs/guides/configuration.md`
- `docs/guides/testing.md`
- `DEVELOPMENT.rst`

For user-visible features, add or update acceptance coverage under `features/`
as well as pytest coverage under `src/pytest_bdd_testing/cases/` when needed.

## Quality Checks

Run focused checks first:

```bash
make test
make ruff-check
```

Use broader gates before release-impacting or cross-platform work:

```bash
make pre-commit
make local-pr-gate
make tox-list
```

tox environments cover Python, pytest, platform, xdist, gherkin, coverage, mypy,
and ruff factors.

## Code Style

- Use `attrs` for structured project models instead of builtin dataclasses.
- Keep `tests/conftest.py` as a thin pytest adapter.
- Keep test-group parsing and xdist barrier logic in
  `src/pytest_bdd/util/test_group_ordering.py`.
- Outside pytest hook implementations, avoid returning `None`; use explicit
  values or deterministic exceptions.
- Use normal pytest marker expressions for group filtering.
- Do not hardcode non-group pytest markers into group ignore lists.

## Documentation

Documentation and planning artifacts must be written in English.

When adding docs:

- Put how-to guides under `docs/guides/`.
- Put architectural decisions under `docs/adr/`.
- Put generated API reference content under `docs/api/`.
- Keep generated files under `docs/features/` derived from `features/`.

## Debugging

Failing pytest runs can be investigated with the MCP pdb flow:

```bash
python -m pytest ... --mcp-pdb-on-fail
```

The failing test writes session data under `.pytest_cache/mcp-pdb/`; connect to
the reported sidecar port, inspect state, then continue the blocked test.
