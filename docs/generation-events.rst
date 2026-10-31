Gather missing bindings and steps
================================

Use the pytest option ``--cuke-gather-missing-steps`` to inspect selected
features without running test bodies or step implementations:

.. code-block:: console

   pytest --cuke-no-autoload --cuke-gather-missing-steps \
     --cuke-feature features/example.feature tests/test-example.py

Repeat ``--cuke-feature`` to select more files or directories. Normal pytest
arguments select the existing test modules to inspect. Disabling feature
autoload lets the command distinguish explicit bindings from unbound scenarios.
The command does not change autoload, test selection, or existing files.

Standard output contains only newline-delimited JSON events. An unbound
scenario produces these fields:

.. code-block:: json

   {"feature": "/project/features/example.feature", "line": 4, "scenario": "unbound", "type": "missing_scenario_binding"}

A missing step in a bound scenario additionally includes the normalized step
keyword and text:

.. code-block:: json

   {"feature": "/project/features/example.feature", "keyword": "Then", "line": 7, "scenario": "bound", "text": "the result exists", "type": "missing_step_definition"}

``feature`` is an absolute source filename. ``line`` is the source line, or
``null`` when unavailable. Missing scenario bindings precede missing step
definitions. Steps belonging only to an unbound scenario do not produce
additional step events. Step events retain their scenario context.

The command returns ``100`` when it finds missing bindings or definitions,
and ``0`` with an empty event stream when none are found. Missing
``--cuke-feature`` selection returns ``100`` with a diagnostic on standard
error. Collection and inspection errors retain their pytest error status and
send diagnostics to standard error; they are not a clean scan.

Inspection imports test modules and plugins and sets up pytest fixtures to
obtain the real step registry. Fixture teardown runs after each inspected
item. Fixture code and matcher hooks can therefore have their normal side
effects, although test bodies and feature steps are not executed.

Existing Cucumber Messages reporting and the default generator exit policy
remain available independently. See :doc:`generation-exit-status` for the
standalone generator's opt-in automation status mapping.
