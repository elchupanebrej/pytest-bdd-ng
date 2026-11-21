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
filesystem. Remote ``--tx`` workers need a socket relay instead:

.. code-block:: ini

   [pytest]
   cuke_test_group_order = unit integration
   cuke_test_group_relay = controller:8889

The controller process binds the relay on every interface at that port, and
workers connect to the same address. Barrier state (the selected manifest,
terminal receipts, item ownership, and dead-worker notices) travels over the
relay, so independent worker containers need no shared volume. Local
``--tx=popen`` workers keep using the default filesystem state and need no
relay. ``--dist=each`` remains unsupported because it duplicates collections.

Each grouped run generates its own credential on the controller. The controller
passes it to its workers through pytest-xdist's worker input, and the relay
rejects every operation from a client without it, including snapshot reads. The
relay listens on all interfaces so worker containers can reach it, and the
credential is not a substitute for network isolation: restrict the relay port
to the worker network with a firewall, security group, or container network
policy.

If a worker stops before it reports a selected test, the controller marks it
down on the relay. Waiting workers then fail immediately with the dead worker,
the outstanding group, and the pending node IDs in the diagnostic. Without a
relay, the same situation fails after ``cuke_test_group_barrier_timeout`` with
the outstanding group and node ID in the diagnostic.

These pytest suite groups control whole-test execution across workers. They are
separate from asynchronous Gherkin step groups, which coordinate steps within
a scenario. The full-port request for ordered test groups supersedes the
earlier #149 decision to omit the historical barrier workflow from the
acceleration port; the opt-in setting keeps fast default suites unaffected.
