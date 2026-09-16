Fast debugging: triaging a red run in minutes
=============================================

A recipe for developers. Assumes a checkout of branch ``rewrite-from-2.3.1``
with the test extras installed (see ``tox.ini``) plus the npm packages from
``.github/workflows/main.yml``.

1. Reproduce the failure locally, failures first
------------------------------------------------

::

    pytest tests/feature -x -q --tb=short --durations=10

Green elsewhere is assumed until proven otherwise: start where it hurts.

2. It failed. Was it already failing before my change?
------------------------------------------------------

::

    git stash -u && pytest <failing-node> -q --tb=short; git stash pop
    pytest --lf -q --tb=short   # tight loop while fixing

If it fails on a clean tree, it is not your regression: note it and move on.

Warning: ``-u`` includes untracked files. If ``stash pop`` conflicts, resolve
the conflict and pop again: nothing is lost while the entry exists (check
``git stash list``). For long-lived comparisons prefer a separate worktree.

3. Find the blast radius, not the world
---------------------------------------

Run only the zones your diff touches. ``scripts/suspect-zones.sh`` maps changed
paths (tracked and untracked) to test directories, and prints ``FULL`` when a
conftest or config change makes narrowing unsafe::

    BASE=$(git merge-base HEAD origin/main)
    { git diff --name-only "$BASE"...HEAD; git ls-files --others --exclude-standard; } \
      | scripts/suspect-zones.sh
    pytest $(git diff --name-only "$BASE"...HEAD | scripts/suspect-zones.sh) -q --ff

If the output contains ``FULL``, run everything (``pytest tests``). A docs-only
change maps to ``tests/doc``.

4. Read the failure densely
---------------------------

Default to ``-q --tb=short``. Escalate presentation only on one node::

    pytest <node> -vv --tb=long --showlocals

Check ``--cache-show`` if ``--lf`` behaves oddly (stale cache after branch
switches); ``--cache-clear`` resets it.

5. Slow tests deserve suspicion first
-------------------------------------

The curated tail is checked in as ``tests/slow-tests.txt`` (25 tests on this
branch: e2e report scenarios and the multi-second pytester-subprocess tier)::

    pytest tests -m slow -q --durations=10

Flaky-looking e2e report test with +-40% wall variance? Re-run it alone three
times before blaming your change.

6. Before pushing
-----------------

Fast gate (what CI's PR path runs on one linux cell)::

    pytest -m "not e2e and not external and not slow" -q -n4

Acceptance is the full matrix: the ``test`` job's 9 cells (5 linux, 2 windows,
2 macOS) plus the dedicated ``e2e`` job. Never a narrowed selection: linux
cells can run locally via ``act``, windows/macOS only in CI.
