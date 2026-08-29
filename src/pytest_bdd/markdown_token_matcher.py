from __future__ import annotations

from typing import Any

from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher


class MarkdownTokenMatcher(GherkinInMarkdownTokenMatcher):
    """Token matcher for Gherkin embedded in Markdown documents.

    Fixes upstream comment matching bug and un-prefixed Markdown # header feature matching.
    """

    def match_FeatureLine(self, token: Any) -> bool:
        if self.matched_feature_line:
            self._set_token_matched(token, None)
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
            self._set_token_matched(token, "FeatureLine", text=feature_name, keyword="Feature")
            self.matched_feature_line = True
            return True
        self._set_token_matched(token, None)
        return False

    def match_Comment(self, token: Any) -> bool:
        if token.line.startswith("|"):
            table_cells = token.line.table_cells
            if self._is_gfm_table_separator(table_cells):
                self._set_token_matched(token, "Comment", text=token.line.get_line_text(0))
                return True
        self._set_token_matched(token, None)
        return False


__all__ = ["MarkdownTokenMatcher"]
