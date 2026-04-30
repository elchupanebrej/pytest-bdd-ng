Development Guide
================

This guide helps you get started with pytest-bdd-ng using the standardized `uv` workflow.

Prerequisites
-------------

- Python 3.10 or higher
- `uv` installed (https://docs.astral.sh/uv/)

Installation
------------

1. Clone the repository:
   ```bash
   git clone https://github.com/elchupanebrej/pytest-bdd-ng.git
   cd pytest-bdd-ng
   ```

2. Provision the preferred Python interpreter for local development:
   ```bash
   uv python install 3.14
   ```

3. Create and sync the project environment:
   ```bash
   uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd
   ```

   This command creates the project virtual environment at ``.venv`` and keeps it in sync
   with the selected extras. Use ``uv run ...`` to execute commands inside that environment.

Running Tests
-------------

To list the supported tox environments using the canonical workflow:
```bash
uvx --with tox-uv tox -l
```

To run the full test suite and render one HTML report per pytest-based tox environment:
```bash
make test
```

If you run tox directly, it will write one NDJSON artifact per pytest-based environment:
```bash
uvx --with tox-uv tox
```

Render HTML reports from the collected tox NDJSON artifacts:
```bash
make render-tox-reports
```

By default, tox writes NDJSON artifacts as ``.tox/<envname>.messages.ndjson`` and the
Makefile renders HTML reports to ``.tmp/tox-reports/<envname>.html``.

For a quick test run:
```bash
uv run pytest tests/ -x
```

Development Workflow
--------------------

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests locally:
   ```bash
   uv run pytest tests/your_test_file.py
   ```

4. Run the full validation suite before pushing:
   ```bash
   uvx --with tox-uv tox
   uvx pre-commit run --all-files
   ```

5. Commit and push:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

Release Workflow
----------------

Releases are published by GitHub Actions, not by uploading from a local workstation.
The repository workflow at ``.github/workflows/release.yaml`` runs when a GitHub Release
is created and performs the package build and PyPI upload using the configured
``PYPI_TOKEN`` secret.

Before creating a GitHub Release, verify the package artifacts locally from a clean
working tree:

1. Remove any previous build artifacts:
   ```bash
   rm -rf ./dist
   ```

2. Build the source and wheel distributions:
   ```bash
   uvx --with build python -m build
   ```

3. Check the generated distributions:
   ```bash
   uvx --with twine twine check dist/*
   ```

4. Create the GitHub Release so the ``Upload Python Package`` workflow can publish the
   verified artifacts to PyPI.

Using ``uvx`` keeps the local verification tools ephemeral, so a separate installation step
is not required.

Project Tooling
---------------

The repository exposes additional contributor and maintainer tooling beyond the base
test and release flow.

Packaged CLI entry points
~~~~~~~~~~~~~~~~~~~~~~~~~

These commands are defined in ``pyproject.toml`` and can be run with ``uv run``:

- ``compatibility_matrix`` inspects supported Python/pytest combinations.

  .. code-block:: bash

     uv run compatibility_matrix --list --compatible-only
     uv run compatibility_matrix --python 314 --pytest latest

  Make targets: ``make compat-list`` and
  ``make compat-check PYTHON_FACTOR=314 PYTEST_FACTOR=latest``.

- ``bdd_tree_to_rst`` regenerates ordered feature documentation.

  .. code-block:: bash

     uv run bdd_tree_to_rst features docs/features

  Make target: ``make features-docs``.

- ``render_cucumber_formatters`` replays formatter outputs from an existing
  cucumber messages NDJSON stream.

  .. code-block:: bash

     uv run render_cucumber_formatters \
       --messages-ndjson .tmp/messages.ndjson \
       --cucumber-summary

  Make target: ``make render-formatters``.
  Override arguments with ``MESSAGES_NDJSON=...`` and ``FORMATTER_ARGS="..."``.

Module-level maintenance commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some repository tooling is kept as module entry points under
``src/pytest_bdd/script`` and is invoked with ``uv run python -m ...``:

- ``pytest_bdd.script.validate_feature_headings`` validates parsed headings in
  ``features/``.

  .. code-block:: bash

     uv run python -m pytest_bdd.script.validate_feature_headings --root-path features

  Make target: ``make validate-headings``.

- ``pytest_bdd.script.sync_messages_contract_schemas`` refreshes the vendored
  ``cucumber/messages`` JSON schemas used by the project.

  .. code-block:: bash

     uv run python -m pytest_bdd.script.sync_messages_contract_schemas

  Make target: ``make sync-message-schemas``.

- ``pytest_bdd.script.message_capability_governance`` handles governance report,
  checklist, diff, sync, and decision validation subcommands for the message
  coverage workflow.

  .. code-block:: bash

     uv run python -m pytest_bdd.script.message_capability_governance report --help

  This flow is usually driven through ``scripts/run_messages_coverage_audit.sh``
  and the dedicated user guide at ``docs/messages-coverage-user-guide.md``.

Repository shell helpers
~~~~~~~~~~~~~~~~~~~~~~~~

The ``scripts/`` directory contains higher-level workflow wrappers:

- ``scripts/run_messages_coverage_audit.sh`` executes the runtime messages
  coverage audit and governance gate.
  Make target: ``make messages-audit``.

The local PR gate is implemented directly in the Makefile:

- ``make local-pr-gate`` runs pre-commit, the E2E suite, workflow matrix sanity
  checks, and dependency marker validation.
- ``make render-tox-reports`` renders one HTML report per pytest-based tox
  environment from the NDJSON artifacts written by tox.

Available Commands
------------------

- `uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd` - Create or refresh the development environment
- `uv run <command>` - Run commands in the project environment
- `uv run compatibility_matrix --list --compatible-only` - Inspect the supported compatibility matrix
- `uv run bdd_tree_to_rst features docs/features` - Regenerate feature RST documentation
- `uv run render_cucumber_formatters --messages-ndjson <path> ...` - Replay formatter outputs from NDJSON
- `make test` - Run tox and render one HTML report per pytest-based tox environment
- `uvx --with tox-uv tox -l` - List supported tox environments
- `uvx --with tox-uv tox` - Run the full tox matrix using `tox-uv`
- `make render-tox-reports` - Render HTML reports from tox NDJSON artifacts
- `uv run python -m pytest_bdd.script.validate_feature_headings --root-path features` - Validate feature headings
- `uv run python -m pytest_bdd.script.sync_messages_contract_schemas` - Refresh vendored message schemas
- `uv run python -m pytest_bdd.script.message_capability_governance report --help` - Inspect message governance commands
- `uvx --with build python -m build` - Build release artifacts
- `uvx --with twine twine check dist/*` - Validate release artifacts before creating a GitHub Release
- `uv run pytest <test_path>` - Run specific tests
- `uvx pre-commit run --all-files` - Run all pre-commit checks
- `make local-pr-gate` - Run the local PR gate checks
- `bash scripts/run_messages_coverage_audit.sh` - Run the messages coverage audit workflow

For more detailed information, see the full documentation.
