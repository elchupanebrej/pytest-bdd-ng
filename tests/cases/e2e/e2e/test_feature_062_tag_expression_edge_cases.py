"""Tag expression edge cases are integration tests, not feature-file E2E tests."""

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skip(reason="covered by tests/cases/integration/test_tag_expression_semantics.py"),
]


def test_tag_expression_edge_cases_moved_to_integration() -> None:
    pass
