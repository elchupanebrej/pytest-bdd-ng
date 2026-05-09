"""Provide gherkin helpers."""

from gherkin.parser_types import GherkinDocument as BaseGherkinDocument


class GherkinDocument(BaseGherkinDocument):
    """Represent gherkin document state."""

    uri: str | None
