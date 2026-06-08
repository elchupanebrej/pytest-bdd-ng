from typing import Any

class TestReport:
    when: Any
    failed: Any
    skipped: Any
    passed: Any
    scenario: Any
    item: Any
    nodeid: Any
    outcome: Any
    longrepr: Any
    head_line: Any
    caplog: Any
    capstderr: Any
    capstdout: Any
    duration: Any
    keywords: Any
    user_properties: list[tuple[str, Any]]
