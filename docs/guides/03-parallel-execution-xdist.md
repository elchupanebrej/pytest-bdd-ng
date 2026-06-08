# How to Run Scenarios in Parallel with pytest-xdist

## Problem

You have 500+ Gherkin scenarios and sequential execution takes too long.
You need to distribute scenario execution across multiple CPU cores while
keeping reporting (Cucumber JSON, JUnit, console output) coherent.

## Solution

Install ``pytest-xdist`` and run pytest with the ``-n`` flag. pytest-bdd-ng
automatically synchronizes workers through the ``gherkin_message_reporter``
plugin, and the ``pickle_runner`` executes scenarios in parallel on each
worker.

### 1. Install pytest-xdist

```bash
pip install pytest-xdist
```

``pytest-xdist>=3.8.0`` is recommended. It is listed in the ``test`` extra
if you installed ``pytest-bdd-ng[test]``.

### 2. Run with -n auto

```bash
pytest -n auto
```

The ``-n auto`` flag tells xdist to spawn one worker per CPU core. For
manual control:

```bash
pytest -n 4       # 4 workers
pytest -n logical  # one worker per logical CPU
```

pytest-bdd-ng automatically configures xdist so that:

* Feature file **collection** happens on the main (controller) node.
* Scenario **execution** is distributed across workers.
* The ``gherkin_message_reporter`` plugin synchronizes Cucumber Messages
  (``Envelope`` NDJSON) across workers so output formatters receive a
  unified stream.

### 3. What Is Parallelized (and What Is Not)

| Operation | Parallelized? | Notes |
|-----------|---------------|-------|
| Feature file collection | No | Single-threaded on controller node. |
| Scenario execution | **Yes** | Each worker runs a subset of scenarios. |
| Step matching | **Yes** | Step registry is replicated per worker. |
| Hook invocation | **Yes** | Hooks fire per-worker, per-scenario. |
| Formatter output | **Yes** | Messages streamed from workers to controller via NDJSON. |

Key insight: **scenarios are the unit of parallelism**, not steps and not
features. Two scenarios from the same feature file can run simultaneously on
different workers.

### 4. Test Group Ordering with xdist

pytest-bdd-ng supports **test group ordering** — semantic groups of tests
that can be ordered by priority. With xdist, group ordering works as
follows:

1. Define groups in ``pyproject.toml``:

   ```toml
   [tool.pytest.ini_options]
   test_group_order = ["unit", "integration", "contract", "e2e", "compat", "perf", "external"]
   test_group_default = "integration"
   test_group_paths = [
     "tests/cases/unit/** = unit",
     "tests/cases/integration/** = integration",
   ]
   ```

2. Run with group ordering + xdist:

   ```bash
   pytest -n auto -m integration
   ```

The xdist scheduler (``xdist_schedule``) respects group ordering: all tests
in group ``unit`` complete before group ``integration`` starts, even across
workers. Group transitions act as implicit xdist barriers.

### 5. CI Configuration

For GitHub Actions, add:

```yaml
- name: Run tests (parallel)
  run: |
    pip install pytest-bdd-ng[struct-bdd,test]
    pytest -n auto -v --cucumber-json-formatter
```

For other CI systems, the same pattern applies:

```bash
pip install pytest-bdd-ng[test]
pytest -n auto --junitxml=results.xml
```

Load balancing strategies:
* ``-n auto``: one worker per CPU core (default).
* ``-n logical``: one worker per logical CPU (hyperthreading).
* ``--dist loadscope``: group tests by module scope (better for heavy
  per-module setup).
* ``--dist loadfile``: group by test file (useful when fixtures are
  file-scoped).

## Complete Example

A project with 200 scenarios across 10 feature files:

```bash
# Sequential (baseline)
pytest features/ -v
# => 200 passed in 120.00s

# Parallel (4 cores)
pytest features/ -n 4 -v
# => 200 passed in 38.00s (3.2x speedup)

# Parallel with output
pytest features/ -n 4 --cucumber-json-formatter --junitxml=results.xml
```

The ``--cucumber-json-formatter`` produces a single JSON file regardless of
worker count because the ``gherkin_message_reporter`` aggregates messages
from all workers during the ``pytest_sessionfinish`` hook.

## Common Mistakes

**Expecting features to be parallelized.** Feature file collection is
single-threaded. If you have one feature file with 500 scenarios,
distribution still works because scenarios are the unit of parallelism — but
collection of that single file happens on one node. Mitigation: split large
feature files into multiple smaller files when collection time becomes the
bottleneck.

**Not configuring xdist barrier sync.** Without proper barrier
synchronization, workers may race when writing to shared output files:

```python
# Pytest xdist hook — runs on every worker
def pytest_configure_node(node):
    node.workerinput["my_data"] = "data"
```

pytest-bdd-ng handles this internally via the ``gherkin_message_reporter``
plugin, which uses the xdist controller-worker protocol. Custom formatter
plugins must account for xdist by implementing
``pytest_configure_node`` and ``pytest_testnodedown`` hooks.

**File-locking issues with formatter output.** When multiple workers write
to the same output file simultaneously, data corruption occurs. Solutions:

* Use worker-specific filenames: ``output_{worker_id}.json``, then merge
  in ``pytest_sessionfinish`` on the controller.
* Use the built-in formatter plugins (cucumber_json, cucumber_junit) —
  they handle xdist aggregation internally.
* If writing a custom formatter, implement the
  ``FormatterReporterPlugin`` base class, which includes xdist-aware
  output management.

**Forgetting to include xdist-safe fixtures.** Fixtures with ``scope="session"``
or ``scope="module"`` may cause deadlocks if they acquire locks or write to
shared resources. Always use ``scope="function"`` for fixtures that are not
designed for concurrent access, or use ``execnet`` / ``filelock`` to protect
shared state.

**Assuming a fixed worker count.** ``-n auto`` picks the number of workers at
runtime based on available CPUs. If your CI machine has 2 CPUs on one run and
16 on another, the worker count varies. Use explicit ``-n 4`` in CI for
deterministic behavior.
