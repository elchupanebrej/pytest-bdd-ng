"""Performance benchmark: measure collection time at huge scale (2000 features x 20 scenarios)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pytest

from pytest_bdd._gherkin_go._bridge import gherkin_go_available
from pytest_bdd.collector_batch import FeatureBatchParser, _parse_feature_file

pytestmark = pytest.mark.slow

logger = logging.getLogger(__name__)

FEATURE_COUNT = 2000
SCENARIOS_PER_FEATURE = 20

pytestmark = [pytest.mark.unit]


def _build_feature_text(n: int) -> str:
    """Build a single feature file with SCENARIOS_PER_FEATURE scenarios."""
    scenarios = "\n".join(
        f"""  Scenario: Scenario {n}_{s}
    Given step one for feature {n} scenario {s}
    When step two for feature {n} scenario {s}
    Then step three for feature {n} scenario {s}
"""
        for s in range(SCENARIOS_PER_FEATURE)
    )
    return f"Feature: Feature {n}\n{scenarios}\n"


def generate_features(dir_path: Path, count: int) -> list[Path]:
    """Generate N feature files in dir_path and return their paths."""
    paths = []
    for i in range(count):
        f = dir_path / f"feature_{i:04d}.feature"
        f.write_text(_build_feature_text(i), encoding="utf-8")
        paths.append(f)
    return paths


def test_performance_huge_suite(tmp_path: Path) -> None:
    """Benchmark batch flush vs truly synchronous parse on 2000 features x 20 scenarios.

    Generates 2000 real feature files on disk (40,000 total scenarios), warms
    the VFS cache, then measures:

    1. SYNC baseline: reads files one-by-one, parses serially (no Pool, no asyncio)
    2. BATCH: registers all files, flushes via multiprocessing Pool + concurrent reads

    Reports speedup factor (target >= 1.5x on multi-core machines).
    """
    if not gherkin_go_available():
        pytest.skip("Go gherkin parser shared library unavailable; speedup threshold requires accelerator")

    total_scenarios = FEATURE_COUNT * SCENARIOS_PER_FEATURE

    logger.info("Generating %d feature files (%d total scenarios)...", FEATURE_COUNT, total_scenarios)
    generate_features(tmp_path, FEATURE_COUNT)
    paths = sorted(tmp_path.glob("*.feature"))
    logger.info("Generation complete. %d files created.", len(paths))

    # Warm VFS cache
    for f in paths:
        f.read_bytes()

    # ── TRUE SYNC BASELINE: read+parse each file serially ──────────
    logger.info("Starting true sync baseline (serial read + parse, no Pool)...")
    start = time.perf_counter()
    sync_parsed = 0
    for f in paths:
        content = f.read_bytes()
        try:
            _parse_feature_file(f, content)
            sync_parsed += 1
        except Exception:
            logger.exception("Sync parse failed for %s", f)
    sync_elapsed = time.perf_counter() - start
    logger.info("True sync complete: %d parsed in %.3fs", sync_parsed, sync_elapsed)
    assert sync_parsed == FEATURE_COUNT

    # ── BATCH: multiprocessing Pool + concurrent reads ────────────
    batch_parser = FeatureBatchParser()
    for f in paths:
        batch_parser.register(f)

    logger.info("Starting batch flush (multiprocessing Pool)...")
    start = time.perf_counter()
    batch_count = batch_parser.flush()
    batch_elapsed = time.perf_counter() - start
    logger.info("Batch complete: %d parsed in %.3fs", batch_count, batch_elapsed)
    assert batch_count == FEATURE_COUNT

    # ── REPORT ────────────────────────────────────────────────────
    speedup = sync_elapsed / batch_elapsed if batch_elapsed > 0 else 0

    logger.info("=" * 60)
    logger.info("  PERFORMANCE BENCHMARK (REAL I/O)")
    logger.info("=" * 60)
    logger.info(
        "  Scale:     %d features x %d scenarios = %d total",
        FEATURE_COUNT,
        SCENARIOS_PER_FEATURE,
        total_scenarios,
    )
    logger.info("  Sync (serial read+parse):  %.3fs", sync_elapsed)
    logger.info("  Batch (Pool + async I/O):  %.3fs", batch_elapsed)
    logger.info("  Speedup:                   %.2fx", speedup)
    logger.info("  Per-file batch avg:        %.2fms", batch_elapsed / FEATURE_COUNT * 1000)
    logger.info("=" * 60)

    # Per spec SC-006: batch must be >= 1.5x faster on multi-core
    assert speedup >= 1.5, (
        f"Batch speedup ({speedup:.2f}x) below 1.5x threshold. Sync: {sync_elapsed:.3f}s, Batch: {batch_elapsed:.3f}s"
    )
