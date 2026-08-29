from __future__ import annotations

from typing import Any

from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher


class MarkdownTokenMatcher(GherkinInMarkdownTokenMatcher):
    """Token matcher for Gherkin embedded in Markdown documents.

    Fixes upstream comment matching bug where a boolean False was passed as
    matched text causing an AttributeError on string methods.
    """

    def match_Comment(self, token: Any) -> bool:
        if token.line.startswith("|"):
            table_cells = token.line.table_cells
            if self._is_gfm_table_separator(table_cells):
                return True
        self._set_token_matched(token, None)
        return False


__all__ = ["MarkdownTokenMatcher"]
