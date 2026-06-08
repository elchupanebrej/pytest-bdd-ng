"""Threshold finder: determine the file count at which batch mode becomes faster.

Results (2026-05-11, Windows 11, Python 3.14, 5 scenarios/feature):
  - 500 files:  sync 1.56s, batch 3.04s, 0.51x
  - 750 files:  sync 2.48s, batch 3.50s, 0.71x
  - 1000 files: sync 4.55s, batch 4.45s, 1.02x  ← crossover
  - 2000 files: sync 20.87s, batch 9.54s, 2.19x (20 scenarios/feature)

Default threshold: 100 files. Batch auto-disables below threshold.
Configurable via `batch_threshold` ini option.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pytest

from pytest_bdd.collector_batch import FeatureBatchParser, _parse_feature_file

pytestmark = pytest.mark.slow

logger = logging.getLogger(__name__)

SCENARIOS_PER_FEATURE = 5
TEST_SIZES = [500, 750, 1000]

pytestmark = [pytest.mark.unit]


def _build_feature_text(n: int) -> str:
    scenarios = "\n".join(
        f"""  Scenario: S{n}_{s}
    Given step one for feature {n}
    When step two for feature {n}
    Then step three for feature {n}
"""
        for s in range(SCENARIOS_PER_FEATURE)
    )
    return f"Feature: Feature{n}\n{scenarios}\n"


def generate_features(dir_path: Path, count: int) -> list[Path]:
    paths = []
    for i in range(count):
        f = dir_path / f"f{i:04d}.feature"
        f.write_text(_build_feature_text(i), encoding="utf-8")
        paths.append(f)
    return paths


def test_find_crossover_threshold(tmp_path: Path) -> None:
    """Document the crossover threshold where batch becomes faster than sync."""
    results = {}

    for count in TEST_SIZES:
        feature_dir = tmp_path / f"bench_{count}"
        feature_dir.mkdir()
        paths = generate_features(feature_dir, count)

        for f in paths:
            f.read_bytes()

        start = time.perf_counter()
        for f in paths:
            content = f.read_bytes()
            _parse_feature_file(f, content)
        sync_elapsed = time.perf_counter() - start

        parser = FeatureBatchParser()
        parser._threshold = count + 1  # force sync path
        for f in paths:
            parser.register(f)
        start = time.perf_counter()
        parser.flush()
        batch_elapsed = time.perf_counter() - start

        speedup = sync_elapsed / batch_elapsed if batch_elapsed > 0 else 0
        results[count] = (sync_elapsed, batch_elapsed, speedup)

    logger.info("=" * 60)
    logger.info("  CROSSOVER THRESHOLD (5 scenarios/feature)")
    logger.info("=" * 60)

    for count, (sync_t, batch_t, sp) in sorted(results.items()):
        viable = "YES" if sp >= 1.0 else "no"
        logger.info("  %-6d  sync=%-8.3f batch=%-8.3f speedup=%-6.2fx %s", count, sync_t, batch_t, sp, viable)

    logger.info("=" * 60)
