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

Cross-Platform Setup
--------------------

The test suite supports cross-platform execution via Make. Make is the human
entrypoint; tox is the execution engine for platform matrix work. Each platform
requires specific tools. Use the table below to verify your environment.

.. list-table:: Cross-Platform Prerequisites
   :header-rows: 1

   * - Operating System
     - Required Tools
     - Verify Command
     - Install Link
   * - Windows
     - Git for Windows 2.40+, PowerShell, WSL2 with ``uvx``, Docker Desktop 4.34+ (Windows containers for Windows Docker backend)
     - ``make --version`` (in Git Bash), ``powershell.exe -NoProfile -Command '$PSVersionTable.PSVersion'``, ``wsl.exe sh -lc 'uvx --version'``, ``docker info``
     - https://git-scm.com/download/win | https://www.docker.com/products/docker-desktop/
   * - macOS
     - Homebrew or uv, Docker Desktop for Linux backend, ``WINDOWS_TOX_BACKEND_COMMAND`` or Windows-capable remote/VM backend for Windows tox
     - ``make --version``, ``uv --version``, ``docker info``
     - https://docs.astral.sh/uv/getting-started/installation/
   * - Linux
     - uv, Docker for Linux backend, ``WINDOWS_TOX_BACKEND_COMMAND`` or Windows-capable remote/VM backend for Windows tox
     - ``make --version``, ``uv --version``, ``docker info``
     - https://docs.astral.sh/uv/getting-started/installation/

.. note::

   On Windows, all ``make`` commands must be run from Git Bash terminal.
   Running ``make`` from ``cmd.exe`` or PowerShell produces an error with
   instructions to switch to Git Bash.

Canonical Make Commands
~~~~~~~~~~~~~~~~~~~~~~~

``make test``
  Default feasible test suite for the current machine (no surprise provisioning).

``make test-all``
  Tox-backed full cross-platform pipeline. It validates the required native tox
  backend first, then delegates to named platform targets. In default
  ``ARTIFACT_MODE=collect`` mode, unavailable non-native Docker or WSL2 probes
  are reported and skipped while independent platform work continues. Use
  ``FAIL_FAST=1`` to hard-fail missing selected backends and stop after the first
  failed platform target. Use ``REPORT_MODE=skip`` to skip final report
  rendering; default ``REPORT_MODE=render`` renders collected tox artifacts.
  On non-Windows hosts, Windows tox requires either Windows Docker containers or
  a custom ``WINDOWS_TOX_BACKEND_COMMAND``.

``make test-platform-native``
  Native host tox run for the current OS platform factor.

``make test-platform-linux``
  Linux tox run. Windows/Git Bash routes this through WSL2; Linux runs it on the
  host; macOS uses a Docker-backed Linux command.

``make test-platform-windows``
  Windows tox run. Windows/Git Bash launches native Windows tox through
  PowerShell; Linux and macOS use a Windows Docker or equivalent VM-like backend.

``make test-platform-macos``
  macOS tox run on macOS host tox.

``make test-unit``
  Unit test suite only.

``make env-install``
  Provision the development environment (Python 3.14, uv sync).

``make env-install-docker``
  Build Docker images for cross-platform testing.

Argument forwarding is target-specific. For example:

.. code-block:: bash

   make test-all TEST_LINUX_ARGS="-k linux_only" TEST_WINDOWS_ARGS="-k windows_only"

``TEST_LINUX_ARGS`` is forwarded only to Linux tox work, and
``TEST_WINDOWS_ARGS`` is forwarded only to Windows tox work. ``TEST_NATIVE_ARGS``
and ``TEST_MACOS_ARGS`` follow the same matching-target rule. ``TEST_ALL_ARGS``
is appended to every platform target.

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
   - ``doc-gen``: documentation generation tools (Jinja2, MyST, Sphinx)
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

Responsibility Documentation
----------------------------

Every Python module, class, function, async function, method, and async method
under ``src/pytest_bdd/`` must expose a responsibility contract in its
docstring. Preserve existing prose and append the contract; for missing
docstrings, add a short summary before the contract. ``Responsibility`` and
``Reason for existence`` must each be at least 140 characters. ``Reason for
existence`` must explain why the entity is the information expert for its
boundary. The contract records owned responsibility, reason for existence,
delegates, ``Cohesion``, ``Separation``, consumers, state and side effects,
optional function invariants, optional propagation-only failure semantics, and
``#arch-eval`` score tags.

Use these scripts when changing responsibility-bearing code:

  .. code-block:: bash

     uv run python scripts/inject_responsibility_docstrings.py --check
     uv run python scripts/inject_responsibility_docstrings.py --stub
     uv run python scripts/inject_responsibility_docstrings.py --write
     uv run python scripts/collect_arch_scores.py src/pytest_bdd/
     uv run python scripts/analyze_responsibility_zones.py
     uv run pylint --load-plugins=pytest_bdd._pylint --disable=all --enable=missing-responsibility-doc,short-responsibility-doc,legacy-responsibility-doc,missing-architecture-score,unfilled-responsibility-placeholder src/pytest_bdd

Use ``--stub`` to add failing ``<...>`` placeholders for newly created entities;
replace every placeholder with real architecture prose before commit. Use
``--write`` only when intentionally generating evidence-based prose for a broad
documentation pass. ``collect_arch_scores.py`` regenerates
``docs/architecture/OBJECT_MAP.md`` and
``analyze_responsibility_zones.py`` regenerates
``docs/architecture/RESPONSIBILITY_GAPS.md``. Keep the score values evidence
based; low scores are acceptable when the boundary is unclear and should drive
follow-up refactoring work. Pre-commit and CI should run the Pylint validator,
not the generator, so unfilled skeletons remain blocking.

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

__all__ and Redundant Import Aliases are Forbidden
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure strict type checking with mypy and avoid implicit re-exports, ``__all__`` is forbidden in all modules (including source modules, facade modules, compatibility helper modules, and ``__init__.py`` files), which is enforced repository-wide by the custom lint rule ``BLQ1401``.

Furthermore, redundant import aliases of the form ``from X import Y as Y`` or ``import Y as Y`` (where the alias name matches the imported name) are strictly forbidden. Imports must be clean without the duplicate ``as`` alias (e.g., ``from X import Y``). This is enforced repository-wide by the custom lint rule ``BLQ1404``. To satisfy mypy strict type checking, facade and compatibility helper modules should be exempted from implicit re-export checking by configuring ``implicit_reexport = true`` overrides in ``pyproject.toml`` instead of using redundant import aliases.

Imports of Test Cases Must Be from cases Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test modules and test cases (any module or imported name starting with ``test_`` or containing ``.test_``) must only be imported from the ``src/pytest_bdd_testing/cases/`` package. Importing test cases from any other location (such as legacy ``tests/`` paths or old ``pytest_bdd.testing`` paths) is strictly forbidden. This ensures a clean separation between the test harness/helpers and the actual test execution cases. This rule is enforced repository-wide by the custom lint rule ``BLQ1601``.

Custom Pylint Checkers (Static Analysis Rules)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project enforces custom architectural, structural, and code style constraints using a unified Pylint plugin and custom checkers package located in ``src/pytest_bdd/_pylint/``. This replaces the legacy standalone Ruff AST rule scripts to ensure faster linting by running in a single Pylint process.

All custom checkers inherit from ``pylint.checkers.BaseChecker`` and implement visitor methods (e.g., ``visit_import``, ``visit_importfrom``, ``visit_return``) to inspect AST nodes provided by the ``astroid`` library.

Available custom rules include:

- **Quality Gates (BLQ9xx)**:
  - ``BLQ901``: Prohibits explicit ``return None`` statements in non-hook production code.
  - ``BLQ902``: Prohibits bare ``except Exception:`` catch-alls.
- **Plugin Patterns (BLQ10xx)**:
  - ``BLQ1001``: Enforces the three-file structure for plugins (``entrypoint.py``, ``plugin.py``, ``hook.py``).
  - ``BLQ1002``: Prohibits cross-plugin imports (plugins must not import from other plugins).
  - ``BLQ1003``: Enforces the ``StashBound`` pattern for accessing pytest config stash.
- **File and Ignore Limits (BLQ11xx)**:
  - ``BLQ1101``: Detects oversized files (> 400 LOC) and proposes splits.
  - ``BLQ1102``: Enforces disciplined ``type: ignore`` comments (must include error codes and explaining comments).
- **Architectural Layers (BLQ13xx)**:
  - ``BLQ1301``: Prohibits downward layer violations based on boundaries defined in ``docs/architecture/layers.toml``.
  - ``BLQ1302``: Prohibits horizontal layer violations.
- **Namespace and Module Design (BLQ14xx)**:
  - ``BLQ1401``: Prohibits the use of ``__all__`` in any Python module.
  - ``BLQ1402``: Prohibits empty ``__init__.py`` files (they must be deleted per PEP 420).
  - ``BLQ1403``: Prohibits docstring-only ``__init__.py`` files.
  - ``BLQ1404``: Prohibits redundant import aliases (e.g., ``from X import Y as Y``).
- **Layout and Location Rules (BLQ15xx)**:
  - ``BLQ1501``: Enforces correct placement of package markers and layout structure.
- **Test Import Rules (BLQ16xx)**:
  - ``BLQ1601``: Enforces test cases are imported only from ``src/pytest_bdd_testing/cases/``.

Developing and Running Checkers
*******************************

To run custom rules locally, use the Makefile target:

.. code-block:: bash

   make custom-rules

This invokes Pylint with the custom plugin loaded. Pylint is also integrated as a pre-commit hook.

When writing or modifying a custom checker:
1. Implement or update the visitor logic under ``src/pytest_bdd/_pylint/checkers/``.
2. Register the checker in ``src/pytest_bdd/_pylint/__init__.py``.
3. Add unit tests to ``src/pytest_bdd_testing/cases/unit/test_pylint_checkers.py`` to verify the checker catches positive and negative cases.

Specific Exception Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do not use bare ``except Exception:``. Use specific exception types or
``logger.warning(exc_info=True)`` for catch-all scenarios. This eliminates
silent failures that mask real bugs (STAB-03).

Testing Strategy
----------------

pytest-bdd-ng organizes tests into seven semantic groups under ``tests/cases/``.
Each test belongs to exactly one group based on purpose, not legacy path.

The ``tests/assets/`` directory holds passive test data only: fixtures, templates,
golden files, Docker assets, and feature-document fixtures. It does not contain
collected tests. Reusable active helper code lives in ``src/pytest_bdd/testing/``,
which is internal project-owned test infrastructure --- not a public user API.

.. _semantic-groups:

Semantic Groups
~~~~~~~~~~~~~~~

Unit (``tests/cases/unit/``)
    Pure in-process module tests. Fast, isolated, no external dependencies.
    Marked with ``@pytest.mark.unit``. Target >80% coverage.

Integration (``tests/cases/integration/``)
    Local plugin, parser, runtime, pytester, and subprocess-light flows.
    Marked with ``@pytest.mark.integration``. Uses testdir pattern to exercise
    the full plugin lifecycle.

Contract (``tests/cases/contract/``)
    Golden files, boundary contracts, schema contracts, and formatter parity
    contracts. Marked with ``@pytest.mark.contract``.

E2E (``tests/cases/e2e/``)
    Full executable user workflows and feature-doc driven acceptance tests.
    Marked with ``@pytest.mark.e2e``. Each E2E test module binds only the
    feature file or files it owns --- whole-directory scenario loaders are
    forbidden. Step definitions for ``features/`` live in
    ``tests/cases/e2e/conftest.py``.

Compat (``tests/cases/compat/``)
    Python, pytest, dependency, and platform compatibility checks.
    Marked with ``@pytest.mark.compat``.

Perf (``tests/cases/perf/``)
    Benchmarks and intentionally expensive performance probes.
    Marked with ``@pytest.mark.perf``.

External (``tests/cases/external/``)
    Docker, browser, and host-platform harnesses or acceptance wrappers.
    Marked with ``@pytest.mark.external``.

Speed and Environment Facets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the semantic group marker, tests declare speed and environment
requirements through optional markers:

Speed:
    - ``@pytest.mark.slow``: intentionally excluded from default runs

Environment:
    - ``@pytest.mark.docker``: requires Docker-backed environments
    - ``@pytest.mark.windows``: requires Windows or Windows bridge behavior
    - ``@pytest.mark.posix``: requires POSIX host behavior
    - ``@pytest.mark.browser``: requires Playwright browser assets

Environment Validation and Provisioning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Environment checks are read-only and report missing prerequisites without
installing anything. Provisioning is explicit and separate:

.. code-block:: bash

   # Read-only: verify prerequisites exist (exits nonzero if missing)
   make env-check
   make env-check-docker
   make env-check-windows
   make env-check-browser

   # Explicit provisioning: install or prepare prerequisites
   make env-install
   make env-install-docker
   make env-install-windows
   make env-install-browser

Test targets depend on ``env-check-*``, not ``env-install-*``. Run
``env-install-*`` once when setting up the machine for the first time.

Makefile Test API
~~~~~~~~~~~~~~~~~

Make is the human entrypoint for running tests. Tox is the matrix engine behind
full and platform test execution.

.. code-block:: bash

   # Default suite: all feasible tests for current machine (no surprise provisioning)
   make test

   # Tox-backed native, Linux, Windows, and macOS platform targets, then reports
   make test-all

   # Platform tox targets for debugging one backend at a time
   make test-platform-native
   make test-platform-linux
   make test-platform-windows
   make test-platform-macos

   # Individual semantic slices
   make test-unit
   make test-integration
   make test-contract
   make test-e2e
   make test-compat
   make test-perf
   make test-external

   # Docker-backed tests (split by platform)
   make test-docker-linux
   make test-docker-windows

   # Speed and environment slices
   make test-slow
   make test-windows
   make test-posix

BDD Workflow
------------

The project uses ATDD/BDD: acceptance tests in ``features/`` before implementation.

1. **Write the feature**: Create a ``.feature.md`` file in ``features/NN Topic/``
   directory following Gherkin syntax.

2. **Implement step definitions**: Add step implementations to
   ``tests/cases/e2e/conftest.py`` using ``@given``, ``@when``, ``@then``
   decorators.

3. **Generate documentation**: Build the Sphinx HTML documentation:

   .. code-block:: bash

      make docs

   The Sphinx build reads Markdown sources directly and mirrors feature files at
   build time.

4. **Run E2E tests**: Execute the BDD test suite:

   .. code-block:: bash

      make test-e2e

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

6. **Write tests**: Add unit tests in ``tests/cases/unit/`` and integration
   tests in ``tests/cases/integration/`` following the
   :ref:`semantic-groups` above.

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

Make is the recommended human entrypoint for running tests. Tox remains the
matrix engine for full Python/pytest version coverage.

To list the supported tox environments:

.. code-block:: bash

   uvx --with tox-uv tox -l

To run the local feasible default test suite:

.. code-block:: bash

   make test

To run the full tox-backed cross-platform pipeline and render one JSON report per
pytest-based tox environment:

.. code-block:: bash

   make test-all

If you run tox directly, it will write one NDJSON artifact per pytest-based environment:

.. code-block:: bash

   uvx --with tox-uv tox

Render HTML reports from the collected tox NDJSON artifacts:

.. code-block:: bash

   make render-tox-reports

By default, tox writes NDJSON artifacts as ``.tox/<envname>.messages.ndjson`` and the
Makefile renders JSON reports to ``.tmp/tox-reports/<envname>.json``.

For a quick test run with pytest directly:

.. code-block:: bash

   uv run python -m pytest tests/cases -m "not slow and not docker and not windows and not browser and not external"

Development Workflow
--------------------

1. Create a feature branch:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. Make your changes

3. Run tests locally:

   .. code-block:: bash

      make test-unit
      make test-integration

4. Run the full validation suite before pushing:

   .. code-block:: bash

      make test-all
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

.. _debug-mcp:

Debug MCP
=========

The ``--mcp-pdb-on-fail`` flag enables interactive debugging of failed
pytest-bdd scenarios through an MCP (Model Context Protocol) bridge.  When
a test fails, the framework pauses execution on ``remote_pdb.set_trace()``,
exposing the Python runtime state to an external agent via a raw TCP
connection.

Architecture
------------

::

  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
  │  AI Agent    │────▶│  mcp-pdb MCP     │     │  pytest process  │
  │  (client)    │     │  server subproc  │     │  (test runner)   │
  └──────┬───────┘     └────────┬─────────┘     └────────┬─────────┘
         │                      │                        │
         │  MCP protocol        │                        │
         │  stdin/stdout        │                        │
         │                      │                        │
         │           ┌──────────▼──────────┐             │
         │           │  mcp_pdb.main.py   │             │
         │           │  (FastMCP app)     │             │
         │           └──────────┬─────────┘             │
         │                      │                        │
         │   connect_remote_    │                        │
         │   debug(HOST, PORT)  │                        │
         │                      │                        │
         │           ┌──────────▼──────────┐    ┌────────▼────────┐
         └──────────▶│  remote-pdb TCP     │◀───│ set_trace()     │
                     │  socket (sidecar)   │    │ blocks here     │
                     └─────────────────────┘    └─────────────────┘

Two TCP ports are allocated per session:

* ``mcp_pdb.port`` — the ``mcp_pdb.main`` MCP server subprocess.
  Fixed via ``--mcp-pdb-port=N``, auto-allocated otherwise.
* ``sidecar.port`` — the raw TCP ``remote_pdb.RemotePdb`` debugger.
  Always auto-allocated.  The test thread blocks here until a client
  connects.

Discovery file (``.pytest_cache/mcp-pdb/session.json``)
--------------------------------------------------------

The session metadata is written atomically at session start and updated
when a failure is held:

.. code-block:: json

   {
     "session_id": "<hex-uuid>",
     "status": "waiting_for_failure | holding_failure",
     "host": "127.0.0.1",
     "mcp_pdb": {"host": "127.0.0.1", "port": 43210},
     "sidecar": {"host": "127.0.0.1", "port": 54321},
     "active_failure": {
       "sequence_id": 1,
       "nodeid": "tests/test_x.py::test_y",
       "pytest_phase": "call",
       "exception_type": "AssertionError",
       "message": "boom",
       "artifact_status": "missing",
       "bdd": { ... }
     }
   }

Agent Workflow — step by step
-----------------------------

1. **Start pytest** with ``--mcp-pdb-on-fail`` in a subprocess:

   .. code-block:: bash

      python -m pytest <test_target> --mcp-pdb-on-fail

2. **Poll discovery** file every 200 ms until ``status`` becomes
   ``"holding_failure"``.  Read ``sidecar.host``, ``sidecar.port``,
   ``active_failure.*`` from it.

3. **Connect raw TCP** to the sidecar port.  The remote-pdb will
   immediately return the ``(Pdb)`` prompt:

   .. code-block:: python

      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.connect((host, port))
      recv_until_prompt(sock)  # read until (Pdb)

4. **Inspect runtime** by sending PDB commands over the socket.
   Key commands: ``where`` (stack trace), ``list`` (source),
   ``p <variable>`` (print value), ``a`` (arguments), ``up``/``down``
   (frame navigation).

5. **Write investigation artifacts** to
   ``.pytest_cache/mcp-pdb/artifacts/<session_id>/`` with names
   ``failure-{seq:04d}-{safe_nodeid}.{json,md}``.  The JSON payload
   must follow ``InvestigationArtifact`` schema (see
   ``src/pytest_bdd/plugin/debug_mcp/schemas.py``):

   .. code-block:: json

      {
        "artifact_id":     "debug-id-001",
        "nodeid":          "tests/test_x.py::test_y",
        "pytest_phase":    "call",
        "status":          "investigated",
        "summary":         "...",
        "inspected_commands": ["where", "list", "p value"],
        "evidence":        ["...", "..."],
        "suspected_cause": "...",
        "next_action":     "...",
        "bdd_metadata":    {}
      }

6. **Unblock** the session by sending ``continue`` (or ``c``) over the
   socket, then close it.  The test process resumes and exits normally.

7. **Verify** exit code — ``rc=1`` indicates tests failed (expected for
   a debug scenario); ``rc=3`` indicates internal error.

.. note::

   The ``mcp_pdb.rpdb.set_trace()`` call blocks **indefinitely** until a
   client connects.  There is no built-in timeout enforcement (the
   ``mcp_pdb_timeout`` option is read but ``expire_without_client`` is
   never invoked from ``hold_failure``).  The subprocess timeout in the
   agent script must handle this.

Available Commands
------------------

- ``uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd`` - Create or refresh the development environment
- ``uv run <command>`` - Run commands in the project environment
- ``uv run compatibility_matrix --list --compatible-only`` - Inspect the supported compatibility matrix
- ``uv run render_cucumber_formatters --messages-ndjson <path> ...`` - Replay formatter outputs from NDJSON
- ``make docs`` - Build the Sphinx HTML documentation
- ``make test`` - Run the default feasible test suite for the current machine
- ``uvx --with tox-uv tox -l`` - List supported tox environments
- ``uvx --with tox-uv tox`` - Run the full tox matrix using ``tox-uv``
- ``make render-tox-reports`` - Render HTML reports from tox NDJSON artifacts
- ``uv run python -m pytest_bdd.script.validate_feature_headings --root-path features`` - Validate feature headings
- ``uv run python -m pytest_bdd.script.sync_messages_contract_schemas`` - Refresh vendored message schemas
- ``uv run python -m pytest_bdd.script.message_capability_governance report --help`` - Inspect message governance commands
- ``uvx --with build python -m build`` - Build release artifacts
- ``uvx --with twine twine check dist/*`` - Validate release artifacts before creating a GitHub Release
- ``uv run python -m pytest tests/cases/<group>/<file>`` - Run specific tests
- ``uvx pre-commit run --all-files`` - Run all pre-commit checks
- ``make local-pr-gate`` - Run the local PR gate checks
- ``bash scripts/run_messages_coverage_audit.sh`` - Run the messages coverage audit workflow

For more detailed information, see the internal architecture documentation in ``docs/internal/``.

Documentation Maintenance
=========================

Project documentation is split by purpose:

* ``README.md`` introduces the package and points users at published docs.
* ``docs/guides/`` contains task-oriented Markdown guides.
* ``docs/api/`` contains generated API reference pages.
* ``docs/architecture/`` contains architecture maps and decision-support
  material.
* ``docs/features/`` is generated from executable feature files and should not
  be edited by hand.
* ``docs/adr/`` records architectural decisions.

When changing user-visible behavior, update executable features under
``features/`` and regenerate any derived feature documentation. When changing
collection, parsing, runtime, reporting, or plugin loading behavior, update the
matching guide or architecture page in the same change.
