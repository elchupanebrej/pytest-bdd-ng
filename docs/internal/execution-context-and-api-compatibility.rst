Execution Context and API Compatibility
=======================================

Execution Context Integration
-----------------------------

The scenario runner keeps one session-root execution context and maintains
feature/scenario/step child context nodes as the run progresses.
Hook callbacks access this data through the ``execution_context`` field on
existing hook parameter objects (``request``, ``feature``, ``scenario``,
``step`` and ``previous_step`` when present).

Session context distribution:

* ``SessionExecutionContext`` is initialized at ``pytest_sessionstart``.
* It is available through the ``session_execution_context`` session fixture.
* The canonical session object is also stored in ``pytest.config.stash``.

External API Compatibility Record
---------------------------------

``ExternalApiCompatibilityRecord`` compares current public hook/decorator
symbols with a saved baseline.

Current repository usage:

* Baseline file: ``tests/compatibility/hook_public_api_baseline.json``
* Validation tests:
  ``tests/compatibility/test_hook_execution_context_api_surface.py``
