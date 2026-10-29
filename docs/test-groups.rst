Ordered pytest test groups
==========================

pytest-cuke can optionally run a suite's pytest test groups in a configured
order. This workflow is off by default. Leave ``cuke_test_group_order`` empty
to keep the usual collection and execution behavior; the disabled workflow does
not create barrier state or poll for test completion.

Configure the ordered group names and optional assignment rules in the
``[pytest]`` section:

.. code-block:: ini

   [pytest]
   cuke_test_group_order = unit integration e2e
   cuke_test_group_default = integration
   cuke_test_group_paths =
       tests/unit/** = unit
       tests/e2e/** = e2e
   cuke_test_group_barrier_timeout = 60

The group names in ``cuke_test_group_order`` are pytest marker names. Existing
test markers assign groups directly, and pytest's normal marker selection can
select them:

.. code-block:: python

   import pytest


   @pytest.mark.unit
   def test_parser_contract():
       ...

.. code-block:: console

   pytest -m unit

pytest-cuke also adds the resolved group marker to tests assigned by a path,
directory convention, or default, so ``-m`` selection uses the same group names
for every assignment method.

Assignment precedence is:

#. Markers on the test item. If it has more than one configured group marker,
   the marker with the greatest index in ``cuke_test_group_order`` wins.
#. Markers inherited from its parent collection nodes, including module and
   ``conftest.py`` marks, with the same greatest-index rule.
#. The last matching ``GLOB = GROUP`` entry in ``cuke_test_group_paths``.
#. The first configured group whose name is a directory component in the test
   path relative to pytest's root directory.
#. ``cuke_test_group_default``, or the first configured group when no default
   is set.

Duplicate names in ``cuke_test_group_order`` warn and keep their first
position. An unknown default warns and falls back to the first group. A
malformed path entry or a mapping to an unknown group warns and is ignored;
duplicate valid path mappings are allowed and the last match wins.
``cuke_test_group_barrier_timeout`` must be a positive finite number.

Serial pytest runs keep groups in the configured order and preserve the
existing order of tests within each group, including ordering supplied by
pytest-order. With local xdist workers, a later group waits until every
selected test from earlier groups reaches a terminal result. Passed, failed,
skipped, and fixture-setup-failed items settle the barrier. Tests deselected by
``-m`` do not count. Retry-only reports do not count as terminal, and receipts
are deduplicated by node ID.

Each xdist run has its own coordinator state beneath
``.pytest_cache/pytest-cuke-test-groups``. Local workers must share that
filesystem. Remote ``--tx`` workers and ``--dist=each`` are rejected because
the file barrier cannot coordinate non-shared filesystems or duplicate
collections. If a worker stops before it reports a selected test, waiting
workers fail after the configured timeout with the outstanding group and node
ID in the diagnostic.

These pytest suite groups control whole-test execution across workers. They are
separate from asynchronous Gherkin step groups, which coordinate steps within
a scenario. The full-port request for ordered test groups supersedes the
earlier #149 decision to omit the historical barrier workflow from the
acceleration port; the opt-in setting keeps fast default suites unaffected.
