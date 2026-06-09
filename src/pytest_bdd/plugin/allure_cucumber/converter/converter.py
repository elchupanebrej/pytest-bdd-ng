"""Core convert() function for NDJSON to Allure3 JSON mapping."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .collector import group_by_test_case
from .emitter import emit_container, emit_results
from .mapper import map_test_case_to_result
from .reader import read_envelopes

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def convert(messages_path: Path, output_dir: Path) -> None:
    """
    Convert Cucumber Messages NDJSON to Allure3 JSON result files.

    Called by CLI, pytest plugin, or standalone scripts.
    """
    projections = list(read_envelopes(messages_path))
    if not projections:
        logger.warning("No projections read from %s — skipping conversion.", messages_path)
        return

    grouped, structural = group_by_test_case(projections)

    results = []
    for case_id, case_projections in grouped.items():
        result = map_test_case_to_result(case_id, case_projections, structural)
        if case_id.startswith("run:") and result.stop == 0:
            continue
        results.append(result)

    emit_results(results, output_dir)
    emit_container(results, output_dir)
