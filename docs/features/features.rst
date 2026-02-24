Features
========

.. NOTE:: Features below are part of executable documentation; user-facing usage
          scenarios are expected to live under ``features/`` so users can learn
          library behavior without inspecting ``tests/``.
          Naming convention: use descriptive Title Case ``*.feature.md`` files
          and keep conversion traceability in
          ``specs/001-add-py314-pytest39-support/conversion-parity-audit.md``.
          Markdown lint and pre-commit checks must pass for converted
          feature documentation before commit.

Execution Context
-----------------
The scenario runner keeps one session-root execution context and maintains
feature/scenario/step child context nodes as the run progresses.
Hook callbacks access this data through the ``execution_context`` field on
existing hook parameter objects (``request``, ``feature``, ``scenario``,
``step`` and ``previous_step`` when present).

Session context distribution:

- ``SessionExecutionContext`` is initialized at ``pytest_sessionstart``.
- It is available through the ``session_execution_context`` session fixture.
- The canonical session object is also stored in ``pytest.config.stash``.

Reporting integration:

- Scenario reporting captures a context snapshot from the active hierarchy when
  available.
- If a specific scope is already inactive, reporting falls back to session-level
  context and records a fallback reason.

Compatibility guarantee:

- Existing public hook and plugin APIs remain backward compatible.
- External API changes for context support are additive and non-breaking.

External API compatibility record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``ExternalApiCompatibilityRecord`` is the runtime/reporting model used to
compare the current public hook/decorator symbols with a saved baseline.

In practice it is used for:

- CI gate for breaking changes:
  if ``removed_symbols`` or ``renamed_symbols`` is not empty, the change is
  treated as migration-breaking.
- Release communication:
  ``additive_symbols`` can be published as newly added public extension points.
- Plugin ecosystem safety:
  maintainers can verify that existing plugin integrations keep working without
  updates.

Current repository usage:

- Baseline file: ``tests/compatibility/hook_public_api_baseline.json``
- Validation tests: ``tests/compatibility/test_hook_execution_context_api_surface.py``

Tutorial
--------
.. toctree::
    :maxdepth: 2

    features/Tutorial/Launch.feature

Step definition
---------------
.. toctree::
    :maxdepth: 2

    features/Step definition/Pytest fixtures substitution.feature
    features/Step definition/Target fixtures specification.feature

Parameters
##########
.. toctree::
    :maxdepth: 2

    features/Step definition/Parameters/Conversion.feature
    features/Step definition/Parameters/Defaults.feature
    features/Step definition/Parameters/Injection as fixtures.feature
    features/Step definition/Parameters/Parsing by custom parser.feature
    features/Step definition/Parameters/Parsing.feature

Step
----
.. toctree::
    :maxdepth: 2

    features/Step/Data table.feature
    features/Step/Doc string.feature
    features/Step/Step definition bounding.feature

Scenario
--------
.. toctree::
    :maxdepth: 2

    features/Scenario/Alias.feature
    features/Scenario/Background.feature
    features/Scenario/Scenario binding.feature
    features/Scenario/Scenarios loader.feature
    features/Scenario/Tag filtering.feature
    features/Scenario/Description.feature
    features/Scenario/Tag.feature

Outline
#######
.. toctree::
    :maxdepth: 2

    features/Scenario/Outline/Examples Tag.feature
    features/Scenario/Outline/Runtime expansion.feature
    features/Scenario/Outline/Empty values.feature

Report
------
.. toctree::
    :maxdepth: 2

    features/Report/Allure outline.feature
    features/Report/Allure scenario.feature
    features/Report/Cucumber JSON reporter.feature
    features/Report/Gherkin terminal reporter.feature
    features/Report/Gathering.feature

Feature
-------
.. toctree::
    :maxdepth: 2

    features/Feature/Description.feature
    features/Feature/Error reporting.feature
    features/Feature/Localization.feature
    features/Feature/Markdown parsing.feature
    features/Feature/Non-strict gherkin.feature
    features/Feature/Rule.feature
    features/Feature/Tag conversion.feature
    features/Feature/Tag.feature

Load
####
.. toctree::
    :maxdepth: 2

    features/Feature/Load/Autoload.feature
    features/Feature/Load/Feature base directory resolution.feature
    features/Feature/Load/Scenario function loader.feature
    features/Feature/Load/Scenario without steps.feature
    features/Feature/Load/Scenario search from base directory.feature
    features/Feature/Load/Scenario search from base url.feature
    features/Feature/Load/HTTP feature loading.feature

StructBDD
---------
.. toctree::
    :maxdepth: 2

    features/StructBDD/Deserialization.feature
    features/StructBDD/Steps.feature
