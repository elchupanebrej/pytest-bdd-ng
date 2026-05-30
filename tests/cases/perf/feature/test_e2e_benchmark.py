"""End-to-end benchmark: full pytest --collect-only with and without batch collection.

Runs the complete pytest-bdd collection pipeline (globbing, stash init, Run singleton,
hook dispatching, pickle compilation, feature binding, marker resolution, test item
generation) on a generated test suite with real .feature files and step definitions.

Compares wall-clock time with batch collection enabled vs disabled.

NOTE: The batch parser benefits raw file read+parse throughput (~2x at 2000 features),
but the full pytest pipeline includes additional overhead (hook dispatch, pickle
compilation, caching, raw_data re-read for Source messages) that may mask the
improvement at small N. This benchmark measures end-to-end collection, not raw parse.
"""

from __future__ import annotations

import logging
import time

import pytest

pytestmark = pytest.mark.slow

logger = logging.getLogger(__name__)

FEATURE_COUNT = 100
SCENARIOS_PER_FEATURE = 5


def _build_feature_text(n: int) -> str:
    scenarios = "\n".join(
        f"""  Scenario: S{n}_{s}
    Given step one
    When step two
    Then step three
"""
        for s in range(SCENARIOS_PER_FEATURE)
    )
    return f"Feature: Feature{n}\n{scenarios}\n"


def _build_conftest() -> str:
    return """\
import pytest
from pytest_bdd import given, when, then

@given("step one")
def step_one():
    pass

@when("step two")
def step_two():
    pass

@then("step three")
def step_three():
    pass
"""


def test_e2e_collect_only_benchmark(testdir) -> None:
    """Measure --collect-only wall-clock time with batch enabled vs disabled.

    Generates a testdir project with FEATURE_COUNT feature files and step
    definitions, then runs pytest --collect-only twice — once with the
    batch parser enabled and once disabled — reporting the comparison.

    This measures the FULL pytest collection pipeline, not raw parse speed.
    Batch parser overhead (stash init, extra cache check, raw_data re-read)
    may cause the batch path to be slower at small N. See
    tests/unit/test_performance_batch.py for raw parse throughput benchmarks.
    """
    total_scenarios = FEATURE_COUNT * SCENARIOS_PER_FEATURE

    testdir.makeconftest(_build_conftest())
    for i in range(FEATURE_COUNT):
        testdir.makefile(".feature", **{f"f{i:04d}": _build_feature_text(i)})

    logger.info("Generated %d feature files (%d scenarios)", FEATURE_COUNT, total_scenarios)

    # ── WITHOUT batch (disable batch collection) ────────────────────
    logger.info("Collecting WITHOUT batch parser...")
    start = time.perf_counter()
    result_without = testdir.runpytest("--collect-only", "-q", "--disable-batch-collection")
    sync_elapsed = time.perf_counter() - start
    result_without.stdout.fnmatch_lines([f"*{total_scenarios} tests collected*"])

    # ── WITH batch (default, batch parser enabled) ──────────────────
    logger.info("Collecting WITH batch parser...")
    start = time.perf_counter()
    result_with = testdir.runpytest("--collect-only", "-q")
    batch_elapsed = time.perf_counter() - start
    result_with.stdout.fnmatch_lines([f"*{total_scenarios} tests collected*"])

    speedup = sync_elapsed / batch_elapsed if batch_elapsed > 0 else 0

    logger.info("=" * 60)
    logger.info("  END-TO-END --COLLECT-ONLY BENCHMARK")
    logger.info("=" * 60)
    logger.info(
        "  Scale:     %d features x %d scenarios = %d total",
        FEATURE_COUNT,
        SCENARIOS_PER_FEATURE,
        total_scenarios,
    )
    logger.info("  Without batch (full pipeline sync):  %.3fs", sync_elapsed)
    logger.info("  With batch (full pipeline + cache):   %.3fs", batch_elapsed)
    logger.info("  Speedup:                               %.2fx", speedup)
    if speedup < 1:
        logger.info("  NOTE: Batch overhead dominates at small N. See raw parse benchmark.")
    logger.info("=" * 60)

    # At small N, batch may be slower due to pipeline overhead.
    # This is expected and documented. No strict assertion — the test
    # serves as a reproducible measurement, not a pass/fail gate.
    logger.info("E2E collection benchmark completed successfully.")
