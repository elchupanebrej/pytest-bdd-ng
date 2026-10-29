Fast debugging: triaging a red run
==================================

This recipe assumes a checkout of ``rewrite-from-2.3.1`` and a tox environment
for the Python and pytest versions you are investigating. The project uses
autoloaded feature files under ``features/`` and Python tests under
``tests/unit``, ``tests/integration`` and ``tests/contract``.

1. Reproduce the failure
------------------------

Start with the failing node and keep the output short::

    tox -e py314-pytestlatest-coverage-lin -- <failing-node> -x -q --tb=short

For a feature acceptance failure, pass its ``features/...`` path. For a Python
test, pass its pytest node id. If the local tox environment is already active,
run ``python -m pytest`` with the same arguments.

2. Check whether it fails on a clean tree
-----------------------------------------

Run the failing node without local changes, using a separate worktree when the
comparison needs to remain available::

    git worktree add ../pytest-cuke-baseline origin/rewrite-from-2.3.1
    cd ../pytest-cuke-baseline
    tox -e py314-pytestlatest-coverage-lin -- <failing-node> -x -q --tb=short

A failure on the clean baseline is not caused by the current diff. Record the
node id and environment, then continue with another failure.

3. Find the affected test zones
-------------------------------

The mapper reads changed paths, includes untracked files, and prints ``FULL``
when a shared config or conftest makes narrowing unsafe::

    BASE=$(git merge-base HEAD origin/rewrite-from-2.3.1)
    { git diff --name-only "$BASE"...HEAD; git ls-files --others --exclude-standard; } \
      | scripts/suspect-zones.sh

Run the paths it prints. Run ``pytest tests`` and ``pytest features`` if it
prints ``FULL``. Feature files are direct pytest targets; there are no mirror
wrapper files under ``tests/``.

4. Read the failure densely
---------------------------

Default to ``-q --tb=short``. Escalate only the failing node::

    python -m pytest <failing-node> -vv --tb=long --showlocals

Use ``--cache-show`` when ``--lf`` behaves unexpectedly after switching
branches; ``--cache-clear`` removes stale cache entries.

5. Run the curated slow tests
-----------------------------

The prefixes in ``tests/slow-tests.txt`` are applied during Python test
collection::

    python -m pytest tests -m slow -q --durations=10
    python -m pytest tests -m "not slow" -q

Feature acceptance scenarios are collected from ``features/`` and marked with
``e2e``; run them with ``python -m pytest features -m e2e``.

6. Before merging
-----------------

The pull request fast lane is a quick signal. For the full runtime, platform,
optional integration, and quality matrix, dispatch ``main.yml`` on the exact
candidate branch and wait for its ``aggregate-proof`` result. The matrix source
is ``config/env-matrix.yaml``.
