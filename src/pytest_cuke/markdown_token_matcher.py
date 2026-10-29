from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher

if TYPE_CHECKING:
    from collections.abc import Callable


class MarkdownTokenMatcher(GherkinInMarkdownTokenMatcher):
    """Token matcher for Gherkin embedded in Markdown documents.

    Fixes upstream comment matching bug and un-prefixed Markdown # header feature matching.
    """

    def __init__(self) -> None:
        initialize = cast("Callable[[], None]", super().__init__)
        initialize()

    def _mark_token_matched(self, token: Any, token_type: str | None, **kwargs: Any) -> None:
        marker = cast("Callable[..., None]", self._set_token_matched)
        marker(token, token_type, **kwargs)

    def _is_table_separator(self, table_cells: Any) -> bool:
        separator_check = cast("Callable[[Any], bool]", self._is_gfm_table_separator)
        return separator_check(table_cells)

    def match_FeatureLine(self, token: Any) -> bool:
        if self.matched_feature_line:
            self._mark_token_matched(token, None)
            return False
        line_text = token.line.get_line_text()
        if line_text.startswith("# ") and not line_text.startswith("##"):
            feature_name = line_text[2:].strip()
            for kw in self.dialect.feature_keywords:
                if feature_name.lower().startswith(kw.lower() + ":"):
                    feature_name = feature_name[len(kw) + 1 :].strip()
                    break
                if feature_name.lower().startswith(kw.lower()):
                    feature_name = feature_name[len(kw) :].strip()
                    break
            self._mark_token_matched(token, "FeatureLine", text=feature_name, keyword="Feature")
            self.matched_feature_line = True
            return True
        self._mark_token_matched(token, None)
        return False

    def match_Comment(self, token: Any) -> bool:
        if token.line.startswith("|"):
            table_cells = token.line.table_cells
            if self._is_table_separator(table_cells):
                self._mark_token_matched(token, "Comment", text=token.line.get_line_text(0))
                return True
        self._mark_token_matched(token, None)
        return False


__all__ = ["MarkdownTokenMatcher"]
