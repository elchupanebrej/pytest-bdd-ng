from __future__ import annotations

from collections import defaultdict

import pytest

collect_ignore_glob = ["fixtures/*.feature", "probes/*.feature", "probes/*.py"]


@pytest.fixture
def mandatory_attachment_log() -> dict[str, list[str]]:
    # Tracks runtime-only attachment calls emitted by the dedicated audit suite.
    return defaultdict(list)


def pytest_configure(config) -> None:
    for marker in (
        "feature_tag",
        "rule_tag",
        "scenario_tag",
        "top_scenario_tag",
        "rule_examples_tag",
        "top_outline_tag",
        "top_examples_tag",
    ):
        config.addinivalue_line("markers", marker)
