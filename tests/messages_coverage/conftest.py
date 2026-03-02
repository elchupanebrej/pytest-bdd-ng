from __future__ import annotations

from collections import defaultdict

import pytest

collect_ignore_glob = ["fixtures/*.feature"]


@pytest.fixture
def mandatory_attachment_log() -> dict[str, list[str]]:
    return defaultdict(list)


def pytest_configure(config) -> None:
    for marker in ("feature_tag", "rule_tag", "scenario_tag", "top_scenario_tag"):
        config.addinivalue_line("markers", marker)
