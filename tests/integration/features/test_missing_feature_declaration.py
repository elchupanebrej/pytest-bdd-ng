from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("filename", "content", "expected"),
    [
        ("comments.feature", "# only a comment\n", "does not declare a Feature"),
        ("orphan.feature.md", "## Scenario: Orphan\n* Given a step\n", "ERROR collecting"),
    ],
)
def test_source_without_feature_declaration_fails_collection(pytester, filename, content, expected):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = true\n")
    (pytester.path / filename).write_text(content, encoding="utf-8")
    result = pytester.runpytest_subprocess("-q")
    assert result.ret != 0, result.stdout.str()
    result.stdout.fnmatch_lines([f"*{expected}*"])
