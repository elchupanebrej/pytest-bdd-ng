Tolerant step status
####################

Use ``@tolerant`` on a step definition when an ordinary exception from that
step body may be ignored by policy. With the ``ignored`` policy, pytest-cuke
records the step as failed and continues to later steps; the scenario can then
pass. Reports retain the original exception. Definitions without ``@tolerant``
remain strict.

The status policy accepts ``failed`` or ``ignored``. Its precedence is:

#. a valid ``pytest.mark.tolerant_status("failed"|"ignored")`` marker;
#. a valid ``@tolerant-status-failed`` or ``@tolerant-status-ignored`` Gherkin
   tag;
#. ``--cuke-tolerant-status``;
#. ``cuke_tolerant_status`` in pytest configuration;
#. the default ``failed`` policy.

An invalid local marker or Gherkin tag falls through to the next policy. An
invalid command-line or configuration value is rejected before scenario
execution. ``pytest.skip`` and undefined step bindings keep their own outcomes;
the ignored policy does not turn them into passing steps.

.. code-block:: python

   from pytest_cuke import when
   from pytest_cuke.steps import tolerant

   @tolerant
   @when("an audited operation fails")
   def audited_operation_fails():
       raise AssertionError("the operation failed")

Enable the policy with ``--cuke-tolerant-status=ignored`` or
``cuke_tolerant_status = "ignored"``. The checked-in
`tolerant-steps example <../../examples/tolerant-steps/README.md>`_ runs the
same contract with Messages and Cucumber JSON output. Its consumer scenario is
executed by the E2E suite.
