Run-aware lifecycle hooks
=========================

Consumer plugins can inspect the active feature, scenario, current step, and
previous step through the session-owned ``RunContext`` passed as the ``run``
hook argument. The canonical runnable consumer project is
``examples/run-aware-hooks``.

The example's ``conftest.py`` loads its hook plugin through pytest's ordinary
plugin discovery:

.. literalinclude:: ../examples/run-aware-hooks/conftest.py
   :language: python

The hook plugin reads the public run accessors directly. The previous step is
``None`` for a scenario's first step and refers to the immediately preceding
step for later steps. Lifecycle observers see the runtime transition before
the hook executes; for example, ``pytest_cuke_before_step`` observes
``stage == "step-running"`` and ``pytest_cuke_after_scenario`` observes the
``finished`` stage.

Hook implementations may declare a supported subset of the hook arguments.
This example uses the request and run pair for scenario setup, reads step
context from ``run``, and shows run-only implementations for after-step and
after-scenario hooks. It also calls the public ``attach`` fixture from a step;
the consumer's ``pytest_cuke_attach`` hook receives the active run context and
the attachment's body, media type, and file name:

.. literalinclude:: ../examples/run-aware-hooks/run_aware_plugin.py
   :language: python

Run the example from its directory after installing the project dependencies:

.. code-block:: console

   python -m pip install -r requirements.txt
   python -m pytest --cuke-autoload --cuke-features-dir=features --cuke-summary

The plugin records hook order, transition state, step function inputs, and the
attachment event in ``run-aware-observations.jsonl``. Its matcher, caller, and
dispatcher return ``None`` to use pytest-cuke's default implementations. The
E2E suite executes this checked-in directory from an installed consumer
project.
