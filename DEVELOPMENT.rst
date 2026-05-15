Development Guide
=================

pytest-bdd-ng is a BDD (Behavior-Driven Development) testing plugin for pytest.
It enables users to write Gherkin ``.feature`` files, define step implementations
with ``@given``/``@when``/``@then`` decorators, and receive full Cucumber-compatible
reporting. The library handles Gherkin parsing (plain and Markdown), scenario
collection, step matching, execution lifecycle, and multiple output formatters ---
all integrated natively into pytest's hook system.

This guide covers architecture, conventions, testing strategy, BDD workflow,
CI matrix, and plugin development lifecycle for contributors.

Prerequisites
-------------

- Python 3.10 or higher
- ``uv`` installed (https://docs.astral.sh/uv/)
- Go 1.21+ (build-time only, for cgo shared library compilation in Phase 023;
  not required for standard Python-only development)

Installation
------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/elchupanebrej/pytest-bdd-ng.git
      cd pytest-bdd-ng

2. Provision the preferred Python interpreter for local development:

   .. code-block:: bash

      uv python install 3.14

3. Create and sync the project environment:

   .. code-block:: bash

      uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd

   This command creates the project virtual environment at ``.venv`` and keeps it
   in sync with the selected extras. Use ``uv run ...`` to execute commands inside
   that environment.

   **Extras explained:**

   - ``test``: pytest-xdist, execnet, pytest-httpserver, and other test dependencies
   - ``testtypes``: type checking dependencies (mypy, type stubs)
   - ``doc-gen``: documentation generation tools (pypandoc, Jinja2, Sphinx)
   - ``struct-bdd``: YAML/JSON/HOCON/TOML structured BDD support

Architecture Overview
---------------------

pytest-bdd-ng follows a plugin-oriented architecture layered on pytest's hook
system. The main components are:

**Feature Collection** (``collector_batch.py``, ``collector.py``, ``scenario_locator.py``)
   Discovers and collects Gherkin feature files from filesystem paths or URLs.
   ``FeatureFileModule`` represents a collected feature file. ``FileScenarioLocator``
   and ``UrlScenarioLocator`` resolve scenario locations from different sources.
   ``FeatureBatchParser`` orchestrates batch parsing of collected features.

**Parsing** (``parser.py``)
   ``GherkinParser`` and ``MarkdownGherjanParser`` convert Gherkin source (plain
   ``.feature`` or Markdown ``.feature.md``) into structured AST representations.
   The ``parsers.py`` module defines parser type constants and is frozen during
   stabilization --- tests only, no modifications. An optional Go-ctypes parser
   backend is available for performance (Phase 023).

**Runtime Model** (``model/``)
   Core execution state lives in ``model/scenario_run.py`` (``Run``, ``ScenarioRun``,
   ``FeatureRuntimeBinding``). Configuration and cross-hook state is managed through
   the ``StashBound`` pattern in ``model/stash_access.py``. Message conversion
   between internal dicts and ``cucumber_messages`` types happens in
   ``model/message_converter.py``.

**Step Definitions** (``steps.py``)
   ``StepDefinitionManager`` registers and resolves step definitions. ``Matcher``,
   ``Definition``, and ``Registry`` classes handle pattern matching across 7 parser
   types (re, parse, cfparse, cucumber_expression, etc.). Step decorators
   (``@given``, ``@when``, ``@then``, ``@step``) are defined here and lazy-loaded
   via ``__getattr__`` in ``__init__.py``.

**Plugin System** (``plugin/``)
   17 pytest plugins registered via ``pytest11`` entry points. Each plugin follows
   a class-based pattern: ``entrypoint.py`` (registers plugin class), ``plugin.py``
   (main class using ``StashBound`` for config), ``hook.py`` (pytest hook
   implementations). Cross-plugin communication occurs via hooks, not direct imports.

**Cucumber Messages Bridge** (``plugin/gherkin_message_reporter/``, ``model/message_converter.py``)
   Live formatter bridge that emits Cucumber Messages protocol events during
   scenario execution. ``message_converter.py`` handles bidirectional conversion
   between internal dict representations and ``cucumber_messages`` types.

For detailed internal architecture documentation, see ``docs/internal/``.

Core Patterns
-------------

All contributors must follow these patterns. They are enforced by pre-commit hooks
and code review.

StashBound Pattern
~~~~~~~~~~~~~~~~~~

Plugin configuration and cross-hook state is stored in ``pytest.config.stash``
using the ``StashBound`` base class (``src/pytest_bdd/model/stash_access.py``).

``StashBound`` subclasses automatically bind to a specific stash key via the
``STASH_KEY`` class variable. The base class provides four methods:

- ``find_in_stash(stash)``: Returns ``Maybe[Self]`` --- the stored instance or
  ``Nothing`` if not present. Safe lookup, no exception.
- ``from_stash(stash)``: Returns ``Self`` --- the stored instance, raising
  ``PytestBDDStashLookupError`` if absent. Use when presence is required.
- ``set_in_stash(stash)``: Stores the current instance in the stash.
- ``initialize_in_stash(stash)``: Safely initializes the instance, raising
  ``PytestBDDStashAlreadyInitializedError`` if a value already exists.

Example subclass:

.. code-block:: python

   from attrs import define
   from pytest_bdd.model.stash_access import StashBound

   @define
   class MyPluginConfig(StashBound):
       STASH_KEY = "my-plugin:config"
       verbose: bool = False
       output_dir: str = ".tmp"

   # Usage in a hook:
   def pytest_configure(config):
       config = MyPluginConfig(verbose=True).initialize_in_stash(config.stash)

   # Retrieval in another hook:
   def pytest_runtest_setup(item):
       cfg = MyPluginConfig.from_stash(item.config.stash)

See ``src/pytest_bdd/model/stash_access.py`` for the full implementation.

attrs Library
~~~~~~~~~~~~~

Use ``@define`` from the ``attrs`` library for data classes. Do NOT use stdlib
``dataclass``. This is enforced by AGENTS.md code style rules.

.. code-block:: python

   from attrs import define, field

   @define
   class StepDefinition:
       pattern: str
       parser_type: str
       target_fixture: str | None = None
       converters: dict = field(factory=dict)

Plugin Class Standard
~~~~~~~~~~~~~~~~~~~~~

Every plugin must follow the three-file structure:

1. ``entrypoint.py``: Registers the plugin class with pytest via the
   ``pytest11`` entry point in ``pyproject.toml``.
2. ``plugin.py``: Main plugin class, typically a ``StashBound`` subclass for
   configuration storage.
3. ``hook.py``: pytest hook implementations that retrieve config via
   ``StashBound.from_stash()`` or ``StashBound.find_in_stash()``.

Plugins must NOT import from other plugins directly. All cross-plugin
communication happens through pytest hooks.

No Return None in Non-Hook Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Outside pytest hook implementations, returning ``None`` is an antipattern.
Use explicit sentinel values, typed ``Optional`` returns, or raise deterministic
exceptions. This rule is enforced by Phase 2 quality gate (STAB-02).

Specific Exception Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do not use bare ``except Exception:``. Use specific exception types or
``logger.warning(exc_info=True)`` for catch-all scenarios. This eliminates
silent failures that mask real bugs (STAB-03).

Testing Strategy
----------------

pytest-bdd-ng uses a four-tier testing approach:

Unit Tests (``tests/unit/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fast, isolated tests for core modules. Marked with ``@pytest.mark.unit``.
Target >80% coverage. Test individual functions, classes, and methods without
pytest plugin infrastructure.

.. code-block:: bash

   uv run pytest tests/unit/ -x --tb=short

Feature Tests (``tests/feature/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration tests using the testdir pattern. These tests create temporary pytest
projects and verify plugin behavior end-to-end. They exercise the full plugin
lifecycle without requiring external dependencies.

.. code-block:: bash

   uv run pytest tests/feature/ -x --tb=short

E2E/BDD Tests (``tests/e2e/`` + ``features/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Executable BDD specifications written as ``.feature.md`` files in ``features/NN Topic/``.
Step definitions live in ``tests/e2e/conftest.py``. The test entry point
``tests/e2e/test_e2e.py`` runs ``scenarios(".", ...)`` against the entire
``features/`` directory.

.. code-block:: bash

   uv run pytest tests/e2e/ -x --tb=short

Message Tests (``tests/messages/``, ``tests/messages_coverage/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cucumber Messages protocol tests and coverage probes. Verify that emitted
messages conform to the cucumber-messages schema and that all expected message
types are produced during scenario execution.

.. code-block:: bash

   uv run pytest tests/messages/ tests/messages_coverage/ -x --tb=short

Quick run (all tests):

.. code-block:: bash

   uv run pytest tests/ -x

Full matrix (all Python/pytest combinations):

.. code-block:: bash

   uvx --with tox-uv tox

BDD Workflow
------------

The project uses ATDD/BDD: acceptance tests in ``features/`` before implementation.

1. **Write the feature**: Create a ``.feature.md`` file in ``features/NN Topic/``
   directory following Gherkin syntax.

2. **Implement step definitions**: Add step implementations to
   ``tests/e2e/conftest.py`` using ``@given``, ``@when``, ``@then`` decorators.

3. **Generate documentation**: Render feature docs to RST:

   .. code-block:: bash

      uv run bdd_tree_to_rst features docs/features

4. **Run E2E tests**: Execute the BDD test suite:

   .. code-block:: bash

      uv run pytest tests/e2e/ -x

5. **Plan with GSD**: For new features, use the GSD planning workflow.
   Specifications live in ``specs/NNN-feature-name/``. Phases are tracked in
   ``.planning/phases/``. Follow the SpecKit pipeline:
   ``/speckit.specify`` -> ``/speckit.plan`` -> ``/speckit.tasks`` -> implement.

Plugin Development Lifecycle
----------------------------

To create a new plugin:

1. **Create the plugin directory**:

   .. code-block:: text

      src/pytest_bdd/plugin/your_plugin/
      ├── __init__.py
      ├── entrypoint.py
      ├── plugin.py
      └── hook.py

2. **Define the plugin class** in ``plugin.py``:

   .. code-block:: python

      from attrs import define
      from pytest_bdd.model.stash_access import StashBound

      @define
      class YourPluginConfig(StashBound):
          STASH_KEY = "your-plugin:config"
          option_value: str = "default"

3. **Register the plugin** in ``entrypoint.py``:

   .. code-block:: python

      from pytest_bdd.plugin.your_plugin.plugin import YourPluginConfig

      def pytest_addhooks(pluginmanager):
          from pytest_bdd.plugin.your_plugin import hook
          pluginmanager.register(hook)

4. **Implement hooks** in ``hook.py``:

   .. code-block:: python

      import pytest

      @pytest.hookimpl
      def pytest_configure(config):
          cfg = YourPluginConfig(option_value="custom").initialize_in_stash(config.stash)

      @pytest.hookimpl
      def pytest_runtest_setup(item):
          cfg = YourPluginConfig.from_stash(item.config.stash)
          # Use cfg.option_value

5. **Register in pyproject.toml**:

   .. code-block:: toml

      [project.entry-points."pytest11"]
      your_plugin = "pytest_bdd.plugin.your_plugin.entrypoint"

6. **Write tests**: Add unit tests in ``tests/unit/`` and feature tests in
   ``tests/feature/`` following the testing strategy above.

CI Matrix
---------

All changes are validated against the following CI matrix:

**Python versions**: 3.10, 3.11, 3.12, 3.13, 3.14

**pytest versions**: 8.x, 9.x

**Platforms**: Linux, macOS, Windows

**Pre-commit gate**: ruff linting, mypy type checking, pre-commit hooks

**Local PR gate**:

.. code-block:: bash

   make local-pr-gate

This runs pre-commit, the E2E suite, workflow matrix sanity checks, and
dependency marker validation.

**Release**: Published via GitHub Actions (``.github/workflows/release.yaml``),
not by manual upload. Triggered when a GitHub Release is created.

Running Tests
-------------

To list the supported tox environments using the canonical workflow:

.. code-block:: bash

   uvx --with tox-uv tox -l

To run the full test suite and render one HTML report per pytest-based tox environment:

.. code-block:: bash

   make test

If you run tox directly, it will write one NDJSON artifact per pytest-based environment:

.. code-block:: bash

   uvx --with tox-uv tox

Render HTML reports from the collected tox NDJSON artifacts:

.. code-block:: bash

   make render-tox-reports

By default, tox writes NDJSON artifacts as ``.tox/<envname>.messages.ndjson`` and the
Makefile renders HTML reports to ``.tmp/tox-reports/<envname>.html``.

For a quick test run:

.. code-block:: bash

   uv run pytest tests/ -x

Development Workflow
--------------------

1. Create a feature branch:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. Make your changes

3. Run tests locally:

   .. code-block:: bash

      uv run pytest tests/your_test_file.py

4. Run the full validation suite before pushing:

   .. code-block:: bash

      uvx --with tox-uv tox
      uvx pre-commit run --all-files

5. Commit and push:

   .. code-block:: bash

      git add .
      git commit -m "feat: your feature description"
      git push origin feature/your-feature-name

Release Workflow
----------------

Releases are published by GitHub Actions, not by uploading from a local workstation.
The repository workflow at ``.github/workflows/release.yaml`` runs when a GitHub Release
is created and performs the package build and PyPI upload using the configured
``PYPI_TOKEN`` secret.

Before creating a GitHub Release, verify the package artifacts locally from a clean
working tree:

1. Remove any previous build artifacts:

   .. code-block:: bash

      rm -rf ./dist

2. Build the source and wheel distributions:

   .. code-block:: bash

      uvx --with build python -m build

3. Check the generated distributions:

   .. code-block:: bash

      uvx --with twine twine check dist/*

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

- ``uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd`` - Create or refresh the development environment
- ``uv run <command>`` - Run commands in the project environment
- ``uv run compatibility_matrix --list --compatible-only`` - Inspect the supported compatibility matrix
- ``uv run bdd_tree_to_rst features docs/features`` - Regenerate feature RST documentation
- ``uv run render_cucumber_formatters --messages-ndjson <path> ...`` - Replay formatter outputs from NDJSON
- ``make test`` - Run tox and render one HTML report per pytest-based tox environment
- ``uvx --with tox-uv tox -l`` - List supported tox environments
- ``uvx --with tox-uv tox`` - Run the full tox matrix using ``tox-uv``
- ``make render-tox-reports`` - Render HTML reports from tox NDJSON artifacts
- ``uv run python -m pytest_bdd.script.validate_feature_headings --root-path features`` - Validate feature headings
- ``uv run python -m pytest_bdd.script.sync_messages_contract_schemas`` - Refresh vendored message schemas
- ``uv run python -m pytest_bdd.script.message_capability_governance report --help`` - Inspect message governance commands
- ``uvx --with build python -m build`` - Build release artifacts
- ``uvx --with twine twine check dist/*`` - Validate release artifacts before creating a GitHub Release
- ``uv run pytest <test_path>`` - Run specific tests
- ``uvx pre-commit run --all-files`` - Run all pre-commit checks
- ``make local-pr-gate`` - Run the local PR gate checks
- ``bash scripts/run_messages_coverage_audit.sh`` - Run the messages coverage audit workflow

For more detailed information, see the internal architecture documentation in ``docs/internal/``.
